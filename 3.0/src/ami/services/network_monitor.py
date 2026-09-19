"""
AMI 3.0 - Network monitoring engine.
Multi-host ping (parallel threads), HTTP test(s), connection status, statistics.
Optional multiple http_test_urls; call check_connection from a background worker.
"""

import re
import socket
import subprocess
import sys
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import psutil
import requests

from ami.core.models import ConnectionStatus, PingResult

# Windows ping.exe localizes "time="; also accept time<1ms.
_PING_LATENCY_RE = re.compile(
    r"(?:time|durata|zeit|temps|tiempo)\s*[=<]\s*([\d.,]+)\s*ms",
    re.IGNORECASE,
)


_VPN_IFACE_RE = re.compile(r"^(?:utun|tun|ppp|ipsec|wg)\d*$", re.IGNORECASE)
_INET_RE = re.compile(r"\binet\s+(\d+\.\d+\.\d+\.\d+)")
_VPN_PROC_KEYWORDS = (
    "openvpn",
    "wireguard",
    "nordvpn",
    "tailscale",
    "mullvad",
    "expressvpn",
    "protonvpn",
)


def _ifconfig_blocks(text: str) -> List[str]:
    return [block for block in re.split(r"\n(?=\S)", text or "") if block.strip()]


def vpn_ifaces_with_ipv4(text: str) -> str:
    """tun/utun/ppp/ipsec/wg interfaces that currently have an IPv4 address."""
    found = []
    for block in _ifconfig_blocks(text):
        name = block.split(":", 1)[0].strip()
        if not _VPN_IFACE_RE.match(name):
            continue
        match = _INET_RE.search(block)
        if match:
            found.append(f"{name}={match.group(1)}")
    return ",".join(found)


def p2p_vpn_adapter(text: str) -> str:
    """First VPN-like interface with IPv4 and a point-to-point flag. Plain utun inet is not enough."""
    for block in _ifconfig_blocks(text):
        name = block.split(":", 1)[0].strip()
        if not _VPN_IFACE_RE.match(name):
            continue
        header = block.splitlines()[0].lower()
        if "pointopoint" not in header and "-->" not in block:
            continue
        if _INET_RE.search(block):
            return name
    return ""


def parse_ping_latency_ms(stdout: str) -> Optional[float]:
    """Extract RTT ms from OS ping stdout (EN/IT/DE/FR/ES)."""
    if not stdout:
        return None
    m = _PING_LATENCY_RE.search(stdout)
    if not m:
        return None
    raw = m.group(1).replace(",", ".")
    try:
        return float(raw)
    except ValueError:
        return None


class NetworkMonitor:
    """Core network monitoring engine."""

    def __init__(self, config: dict):
        self.config = config
        mon = config["monitoring"]
        self.hosts = mon["ping_hosts"]
        self.http_test_url = mon.get("http_test_url", "https://www.google.com/generate_204")
        self.http_test_urls = mon.get("http_test_urls") or []
        self.timeout = mon["timeout"]
        self.retry_count = mon.get("retry_count", 2)
        self.enable_http_test = mon.get("enable_http_test", True)
        self.internal_test_mode = mon.get("internal_test_mode", False)
        self._test_counter = 0

        th = config["thresholds"]
        self.unstable_latency = th["unstable_latency_ms"]
        self.unstable_loss = th["unstable_loss_percent"]

        self.total_checks = 0
        self.successful_checks = 0
        self.uptime_start = datetime.now()
        self.last_status: Optional[ConnectionStatus] = None
        self.status_history: List[ConnectionStatus] = []
        # ~10 min at 1s poll; keeps offline/unstable visible on the dashboard chart.
        self.max_history = int(mon.get("max_history", 600))

        self._last_public_ip: Optional[str] = None
        self._last_isp_info: Optional[Dict] = None
        self._last_isp_check_ts: float = 0.0
        self._last_vpn_status: Optional[Tuple[bool, str]] = None
        self._last_vpn_check_ts: float = 0.0
        self._last_path_fp: Optional[str] = None
        self._last_speed_mbps: Optional[float] = None
        self._last_speed_tier: Optional[str] = None
        self.lookup_public_network = bool(
            (config.get("privacy") or {}).get("lookup_public_network", True)
        )

    def _probe_attempts(self) -> int:
        """1 + retry_count. Zero retries keeps the fail-fast single probe."""
        try:
            extra = int(self.retry_count)
        except (TypeError, ValueError):
            extra = 0
        return 1 + max(0, extra)

    def _detect_timeout(self) -> int:
        """Short timeout for online/offline detection (fail-fast)."""
        return max(1, min(2, int(self.timeout)))

    def set_speed_result(self, speed_mbps: Optional[float], tier: Optional[str]) -> None:
        """Update last speed test result (called from speed test thread)."""
        self._last_speed_mbps = speed_mbps
        self._last_speed_tier = tier

    def ping_host(self, host: str, timeout: int = 5, *, quick: bool = False) -> PingResult:
        """Ping a single host. Failed probes are retried monitoring.retry_count times."""
        last: Optional[PingResult] = None
        for _ in range(self._probe_attempts()):
            last = self._ping_host_once(host, timeout, quick=quick)
            if last.success:
                return last
        assert last is not None
        return last

    def _ping_host_once(self, host: str, timeout: int = 5, *, quick: bool = False) -> PingResult:
        """One ICMP or TCP attempt. quick=True uses short detect timeouts."""
        try:
            # Windows: trust ping.exe outcome; do not cascade into ping3/DNS if it ran.
            if sys.platform == "win32":
                try:
                    result = subprocess.run(
                        ["ping", "-n", "1", "-w", str(timeout * 1000), host],
                        capture_output=True,
                        text=True,
                        creationflags=subprocess.CREATE_NO_WINDOW,
                        timeout=timeout + 1,
                    )
                    latency = parse_ping_latency_ms(result.stdout or "")
                    if result.returncode == 0:
                        return PingResult(host=host, success=True, latency_ms=latency)
                    return PingResult(
                        host=host,
                        success=False,
                        error="ping failed",
                        latency_ms=latency,
                    )
                except (subprocess.TimeoutExpired, subprocess.SubprocessError, ValueError, OSError):
                    # ping.exe missing / killed — fall through to ping3/TCP.
                    pass
            elif sys.platform in ("darwin", "linux"):
                try:
                    # macOS -W is milliseconds; Linux -w is seconds.
                    if sys.platform == "darwin":
                        wait_arg = str(max(1, int(timeout) * 1000))
                        timeout_flag = "-W"
                    else:
                        wait_arg = str(timeout)
                        timeout_flag = "-w"
                    result = subprocess.run(
                        ["ping", "-c", "1", timeout_flag, wait_arg, host],
                        capture_output=True,
                        text=True,
                        timeout=timeout + 1,
                    )
                    latency = parse_ping_latency_ms(result.stdout or "")
                    if result.returncode == 0:
                        return PingResult(host=host, success=True, latency_ms=latency)
                except (subprocess.TimeoutExpired, subprocess.SubprocessError, ValueError, OSError):
                    pass

            # ping3 / TCP: used when OS ping is unavailable (or non-Windows soft-fail).
            try:
                import ping3
                ping3.EXCEPTIONS = True
                delay = ping3.ping(host, timeout=timeout, unit="ms")
                if delay is not None and delay is not False:
                    return PingResult(host=host, success=True, latency_ms=delay)
            except Exception:
                pass

            tcp_start = time.time()
            bare = host.replace("https://", "").replace("http://", "").split("/")[0]
            try:
                ip = socket.gethostbyname(bare)
            except socket.gaierror:
                return PingResult(host=host, success=False, error="DNS resolution failed")
            # Detect path always uses 443; full path keeps legacy port choice for hostnames.
            if quick:
                port = 443
            else:
                port = 443 if "https" in host or not any(c.isdigit() for c in bare) else 80
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            try:
                sock.connect((ip, port))
                latency = (time.time() - tcp_start) * 1000
                return PingResult(host=host, success=True, latency_ms=latency)
            except (socket.timeout, socket.error) as e:
                return PingResult(host=host, success=False, error=f"Connection failed: {e}")
            finally:
                sock.close()
        except Exception as e:
            return PingResult(host=host, success=False, error=str(e))

    def test_http_connectivity(self, *, fast: bool = True) -> bool:
        """Test HTTP connectivity (primary URL + optional http_test_urls)."""
        if not self.enable_http_test:
            return True
        # Fail-fast for tray status; speed test uses its own timeouts.
        if fast:
            req_timeout: float | tuple[float, float] = (1.5, float(min(2, max(1, int(self.timeout)))))
        else:
            req_timeout = float(self.timeout)
        urls = [self.http_test_url] + list(self.http_test_urls)[:5]
        for _attempt in range(self._probe_attempts()):
            for url in urls:
                if not url or not url.strip():
                    continue
                try:
                    r = requests.get(url.strip(), timeout=req_timeout, allow_redirects=False)
                    # 200/204 only. A 302 with redirects disabled is a captive portal.
                    if r.status_code in (200, 204):
                        return True
                except Exception:
                    continue
        return False

    def _default_gateway(self) -> Optional[str]:
        """Best-effort default gateway for the current platform."""
        try:
            if sys.platform == "darwin":
                out = subprocess.check_output(
                    ["route", "-n", "get", "default"], text=True, timeout=2
                )
                for line in out.splitlines():
                    if line.strip().startswith("gateway:"):
                        gw = line.split(":", 1)[1].strip()
                        if gw:
                            return gw
            elif sys.platform == "linux":
                out = subprocess.check_output(["ip", "route"], text=True, timeout=2)
                for line in out.splitlines():
                    if line.startswith("default"):
                        parts = line.split()
                        if len(parts) >= 3:
                            return parts[2]
            elif sys.platform == "win32":
                out = subprocess.check_output(
                    ["ipconfig"],
                    text=True,
                    timeout=3,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
                for line in out.splitlines():
                    if "Default Gateway" in line:
                        gw = line.split(":")[-1].strip()
                        if gw and gw != "0.0.0.0":
                            return gw
        except Exception:
            pass
        return None

    def _has_active_lan_interface(self) -> bool:
        """True if a non-loopback IPv4 interface is up (no gateway required)."""
        try:
            addrs = psutil.net_if_addrs()
            stats = psutil.net_if_stats()
            skip_prefixes = ("lo", "awdl", "llw", "bridge")
            for name, stat in stats.items():
                if not stat.isup or name.startswith(skip_prefixes):
                    continue
                for addr in addrs.get(name, []):
                    if addr.family == socket.AF_INET and not addr.address.startswith("127."):
                        return True
        except Exception:
            pass
        return False

    def check_local_network(self, *, fast: bool = False) -> bool:
        """Check if local network is available (LAN iface first; gateway only if needed)."""
        try:
            # Instant path: any non-loopback IPv4 interface up.
            if self._has_active_lan_interface():
                return True
            if fast:
                return False

            if sys.platform == "win32":
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                try:
                    candidates = []
                    gw = self._default_gateway()
                    if gw:
                        candidates.append(gw)
                    candidates.extend(["192.168.1.1", "192.168.0.1", "10.0.0.1"])
                    seen = set()
                    for gateway in candidates:
                        if not gateway or gateway in seen:
                            continue
                        seen.add(gateway)
                        try:
                            sock.connect((gateway, 80))
                            sock.close()
                            return True
                        except Exception:
                            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            sock.settimeout(1)
                            continue
                    return False
                finally:
                    try:
                        sock.close()
                    except Exception:
                        pass

            gateway = self._default_gateway()
            if gateway:
                return self.ping_host(gateway, timeout=1).success
            return False
        except Exception:
            return False

    def ping_all_hosts(self) -> List[PingResult]:
        """Ping all configured hosts in parallel (fail-fast detect timeout)."""
        results: List[PingResult] = []
        lock = threading.Lock()
        dt = self._detect_timeout()

        def worker(h: str) -> None:
            result = self.ping_host(h, dt, quick=True)
            with lock:
                results.append(result)

        threads = [threading.Thread(target=worker, args=(h,), daemon=True) for h in self.hosts]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=dt + 1)
        return results

    def analyze_connection(
        self, ping_results: List[PingResult], http_ok: bool, local_ok: bool
    ) -> ConnectionStatus:
        """Analyze ping and HTTP results into ConnectionStatus."""
        successful = [r for r in ping_results if r.success]
        total = len(ping_results)
        success_count = len(successful)
        avg_latency = (
            sum(r.latency_ms for r in successful) / len(successful) if successful else None
        )
        success_rate = (success_count / total * 100) if total > 0 else 0
        internet_ok = success_count > 0 and http_ok
        loss_bad = total > 0 and success_rate < (100 - self.unstable_loss)
        latency_bad = bool(avg_latency and avg_latency > self.unstable_latency)

        if success_count == 0:
            status = "offline"
            reason = "lan_only" if local_ok else "offline"
        elif not http_ok:
            # ICMP often passes on a captive portal. HTTP is "really online".
            if local_ok:
                status = "captive"
                reason = "captive"
            else:
                status = "offline"
                reason = "http_failed"
        elif loss_bad or latency_bad:
            status = "unstable"
            reason = "packet_loss" if loss_bad else "high_latency"
        else:
            status = "online"
            reason = "ok"

        return ConnectionStatus(
            status=status,
            avg_latency_ms=avg_latency,
            successful_pings=success_count,
            total_pings=total,
            local_network_ok=local_ok,
            internet_ok=internet_ok,
            http_test_ok=http_ok,
            reason=reason,
        )

    def check_connection(self) -> ConnectionStatus:
        """Perform connection check for tray status (fail-fast; ISP/VPN deferred)."""
        self.total_checks += 1
        if self.internal_test_mode:
            status = self._simulate_connection()
        else:
            ping_results = self.ping_all_hosts()
            success_count = sum(1 for r in ping_results if r.success)
            if success_count == 0:
                # Short-circuit offline: no HTTP / gateway ping — LAN iface only.
                http_ok = False
                local_ok = self.check_local_network(fast=True)
            else:
                http_ok = self.test_http_connectivity(fast=True)
                local_ok = self.check_local_network(fast=False)
            status = self.analyze_connection(ping_results, http_ok, local_ok)

        # Apply cached enrichment instantly (no network); refresh happens via enrich_status().
        self._apply_cached_enrichment(status)

        status.speed_mbps = self._last_speed_mbps
        status.speed_tier = self._last_speed_tier

        # Uptime is time really online, not "a packet got through".
        if status.status == "online":
            self.successful_checks += 1
        self.status_history.append(status)
        if len(self.status_history) > self.max_history:
            self.status_history.pop(0)
        self.last_status = status
        return status

    def seed_history_from_logs(self, rows: List[dict]) -> None:
        """Hydrate chart history from CSV log rows (keeps offline/unstable across restarts)."""
        if self.status_history or not rows:
            return
        seeded: List[ConnectionStatus] = []
        for row in rows:
            raw = (row.get("Status") or row.get("status") or "").strip().lower()
            if raw not in ("online", "unstable", "captive", "offline"):
                continue
            lat_raw = row.get("Avg Latency (ms)") or row.get("avg_latency_ms") or "N/A"
            avg: Optional[float] = None
            if lat_raw not in ("N/A", "", None):
                try:
                    avg = float(lat_raw)
                except (TypeError, ValueError):
                    avg = None
            try:
                ok_pings = int(row.get("Successful Pings") or row.get("successful_pings") or 0)
            except (TypeError, ValueError):
                ok_pings = 0
            try:
                total_pings = int(row.get("Total Pings") or row.get("total_pings") or 0)
            except (TypeError, ValueError):
                total_pings = 0
            ts_raw = row.get("Timestamp") or row.get("timestamp")
            ts = datetime.now()
            if ts_raw:
                try:
                    ts = datetime.strptime(str(ts_raw), "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    pass
            local_ok = str(row.get("Local Network") or "").strip().lower() in ("yes", "true", "1")
            internet_ok = str(row.get("Internet OK") or "").strip().lower() in ("yes", "true", "1")
            http_ok = str(row.get("HTTP Test OK") or "").strip().lower() in ("yes", "true", "1")
            reason = (row.get("Reason") or row.get("reason") or "").strip()
            if not reason:
                reason = {
                    "online": "ok",
                    "unstable": "high_latency",
                    "captive": "captive",
                    "offline": "offline",
                }.get(raw, "offline")
            seeded.append(
                ConnectionStatus(
                    status=raw,
                    avg_latency_ms=avg,
                    successful_pings=ok_pings,
                    total_pings=total_pings,
                    local_network_ok=local_ok,
                    internet_ok=internet_ok,
                    http_test_ok=http_ok,
                    timestamp=ts,
                    reason=reason,
                )
            )
        if not seeded:
            return
        self.status_history = seeded[-self.max_history :]

    def _apply_cached_enrichment(self, status: ConnectionStatus) -> None:
        if self.lookup_public_network and self._last_isp_info:
            status.public_ip = self._last_isp_info.get("ip")
            status.isp = self._last_isp_info.get("isp")
        elif not self.lookup_public_network:
            status.public_ip = None
            status.isp = None
        if self._last_vpn_status is not None:
            status.vpn_connected = self._last_vpn_status[0]
            status.vpn_provider = self._last_vpn_status[1] or None

    def enrich_status(self, status: ConnectionStatus) -> ConnectionStatus:
        """
        ISP/VPN enrichment for tooltip/menu — call after tray icon update.
        Does not change online/offline/unstable.
        A local path change drops the ISP and VPN caches so the next lookup is fresh.
        """
        if self.total_checks <= 1:
            return status
        path_changed = self._note_path_change()
        if self.lookup_public_network:
            try:
                isp_info = self._get_public_network_info(force=path_changed)
                if isp_info:
                    status.public_ip = isp_info.get("ip")
                    status.isp = isp_info.get("isp")
            except Exception:
                pass
        else:
            status.public_ip = None
            status.isp = None
            self._last_isp_info = None
            self._last_public_ip = None
        try:
            vpn_connected, vpn_hint = self._detect_vpn(status.isp)
            status.vpn_connected = vpn_connected
            status.vpn_provider = vpn_hint or None
        except Exception:
            pass
        if self.last_status is status or (
            self.last_status is not None and self.last_status.status == status.status
        ):
            self.last_status = status
        return status

    def _note_path_change(self) -> bool:
        fp = self._path_fingerprint()
        prev = self._last_path_fp
        self._last_path_fp = fp
        if prev is None or fp == prev:
            return False
        self._last_isp_info = None
        self._last_public_ip = None
        self._last_isp_check_ts = 0.0
        self._last_vpn_status = None
        self._last_vpn_check_ts = 0.0
        return True

    def _path_fingerprint(self) -> str:
        """Cheap local route/interface signature. No public HTTP."""
        try:
            if sys.platform == "darwin":
                return self._darwin_path_fingerprint()
            if sys.platform == "win32":
                return self._windows_path_fingerprint()
        except Exception:
            pass
        return self._last_path_fp or ""

    def _cmd(self, args: List[str], timeout: int = 2) -> str:
        kwargs = {"text": True, "timeout": timeout}
        if sys.platform == "win32":
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
        return subprocess.check_output(args, **kwargs)

    def _darwin_path_fingerprint(self) -> str:
        route = ""
        try:
            out = self._cmd(["route", "-n", "get", "default"])
            iface = gateway = ""
            for line in out.splitlines():
                stripped = line.strip()
                if stripped.startswith("interface:"):
                    iface = stripped.split(":", 1)[1].strip()
                elif stripped.startswith("gateway:"):
                    gateway = stripped.split(":", 1)[1].strip()
            route = f"{iface}:{gateway}"
        except Exception:
            route = ""
        scutil = "0"
        try:
            out = self._cmd(["scutil", "--nc", "list"])
            scutil = "1" if re.search(r"\bConnected\b", out) else "0"
        except Exception:
            scutil = ""
        ifaces = ""
        try:
            ifaces = vpn_ifaces_with_ipv4(self._cmd(["ifconfig"]))
        except Exception:
            ifaces = ""
        return f"darwin|{route}|{scutil}|{ifaces}"

    def _windows_path_fingerprint(self) -> str:
        out = self._cmd(["ipconfig", "/all"], timeout=3).lower()
        flags = [name for name in ("tap", "tun", "wireguard", "nordlynx") if name in out]
        gateways = re.findall(r"default gateway[^\n:]*:\s*(\d+\.\d+\.\d+\.\d+)", out)
        return "win|" + ",".join(flags) + "|" + ",".join(gateways)

    def _simulate_connection(self) -> ConnectionStatus:
        """Simulate status for internal testing."""
        self._test_counter += 1
        phase = self._test_counter % 12
        if phase <= 5:
            return ConnectionStatus(
                status="online",
                avg_latency_ms=40.0,
                successful_pings=3,
                total_pings=3,
                local_network_ok=True,
                internet_ok=True,
                http_test_ok=True,
                reason="ok",
            )
        if phase <= 8:
            return ConnectionStatus(
                status="unstable",
                avg_latency_ms=800.0,
                successful_pings=1,
                total_pings=3,
                local_network_ok=True,
                internet_ok=True,
                http_test_ok=True,
                reason="high_latency",
            )
        return ConnectionStatus(
            status="offline",
            avg_latency_ms=None,
            successful_pings=0,
            total_pings=3,
            local_network_ok=True,
            internet_ok=False,
            http_test_ok=False,
            reason="lan_only",
        )

    def _get_public_network_info(self, force: bool = False) -> Optional[Dict]:
        now = time.time()
        if (
            not force
            and self._last_isp_info
            and (now - self._last_isp_check_ts) < 1800
        ):
            return self._last_isp_info
        endpoints = [
            (
                "https://ipinfo.io/json",
                lambda j: {"ip": j.get("ip"), "isp": j.get("org") or j.get("hostname")},
            ),
            (
                "https://ipapi.co/json",
                lambda j: {"ip": j.get("ip"), "isp": j.get("org") or j.get("asn_org")},
            ),
            (
                "https://ifconfig.co/json",
                lambda j: {"ip": j.get("ip"), "isp": j.get("asn_org") or j.get("asn")},
            ),
        ]
        for url, parser in endpoints:
            try:
                r = requests.get(url, timeout=3)
                if r.status_code == 200:
                    data = parser(r.json())
                    self._last_isp_info = data
                    self._last_public_ip = data.get("ip")
                    self._last_isp_check_ts = now
                    return data
            except Exception:
                continue
        return self._last_isp_info

    def _scutil_connected(self) -> bool:
        if sys.platform != "darwin":
            return False
        try:
            out = self._cmd(["scutil", "--nc", "list"])
        except Exception:
            return False
        return re.search(r"\bConnected\b", out) is not None

    def _local_vpn_adapter(self) -> str:
        """Point-to-point tunnel name, or Windows TAP/TUN marker. Empty if none."""
        try:
            if sys.platform == "darwin":
                return p2p_vpn_adapter(self._cmd(["ifconfig"]))
            if sys.platform == "win32":
                out = self._cmd(["ipconfig", "/all"], timeout=3).lower()
                if any(name in out for name in ("tap", "tun", "wireguard", "nordlynx")):
                    return "adapter"
        except Exception:
            return ""
        return ""

    def _vpn_process_hint(self) -> str:
        try:
            names = [proc.name().lower() for proc in psutil.process_iter(attrs=["name"])]
        except Exception:
            return ""
        for keyword in _VPN_PROC_KEYWORDS:
            if any(keyword in name for name in names):
                return f"proc:{keyword}"
        return ""

    def _detect_vpn(self, isp_text: Optional[str] = None) -> Tuple[bool, str]:
        """Local tunnel only. An ISP name like ProtonVPN is not a live tunnel."""
        del isp_text
        try:
            if self._scutil_connected():
                self._last_vpn_status = (True, "scutil")
                return self._last_vpn_status
            adapter = self._local_vpn_adapter()
            if adapter:
                proc = self._vpn_process_hint()
                # A running app without a tunnel is not connected. Adapter alone is.
                self._last_vpn_status = (True, proc or adapter)
                return self._last_vpn_status
        except Exception:
            pass
        self._last_vpn_status = (False, "")
        return self._last_vpn_status

    def get_uptime_percentage(self) -> float:
        if self.total_checks == 0:
            return 0.0
        return (self.successful_checks / self.total_checks) * 100

    def get_uptime_duration(self) -> str:
        duration = datetime.now() - self.uptime_start
        hours = duration.seconds // 3600
        minutes = (duration.seconds % 3600) // 60
        if duration.days > 0:
            return f"{duration.days}d {hours}h {minutes}m"
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"

    def get_statistics(self) -> Dict:
        return {
            "total_checks": self.total_checks,
            "successful_checks": self.successful_checks,
            "uptime_percentage": self.get_uptime_percentage(),
            "uptime_duration": self.get_uptime_duration(),
            "last_status": self.last_status,
            "history_count": len(self.status_history),
        }

    def reset_statistics(self) -> None:
        self.total_checks = 0
        self.successful_checks = 0
        self.uptime_start = datetime.now()
        self.status_history.clear()
