"""
AMI 3.0 - Network monitoring engine.
Multi-host ping (parallel threads), HTTP test(s), connection status, statistics.
Optional multiple http_test_urls; runs in thread (call check_connection from MonitorThread).
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
        self.max_history = 100

        self._last_public_ip: Optional[str] = None
        self._last_isp_info: Optional[Dict] = None
        self._last_isp_check_ts: float = 0.0
        self._last_vpn_status: Optional[Tuple[bool, str]] = None
        self._last_vpn_check_ts: float = 0.0
        self._last_speed_mbps: Optional[float] = None
        self._last_speed_tier: Optional[str] = None

    def set_speed_result(self, speed_mbps: Optional[float], tier: Optional[str]) -> None:
        """Update last speed test result (called from speed test thread)."""
        self._last_speed_mbps = speed_mbps
        self._last_speed_tier = tier

    def ping_host(self, host: str, timeout: int = 5) -> PingResult:
        """Ping a single host (ICMP or TCP fallback)."""
        try:
            if sys.platform in ["darwin", "linux"]:
                try:
                    param = "-n" if sys.platform == "win32" else "-c"
                    timeout_param = "-W"
                    timeout_seconds = str(timeout)
                    kwargs = {"capture_output": True, "text": True}
                    if sys.platform == "win32":
                        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
                    result = subprocess.run(
                        ["ping", param, "1", timeout_param, timeout_seconds, host],
                        **kwargs,
                        timeout=timeout + 1,
                    )
                    if result.returncode == 0 and "time=" in result.stdout:
                        time_str = result.stdout.split("time=")[1].split()[0]
                        latency = float(time_str.replace("ms", ""))
                        return PingResult(host=host, success=True, latency_ms=latency)
                except (subprocess.TimeoutExpired, subprocess.SubprocessError, ValueError):
                    pass

            try:
                import ping3
                ping3.EXCEPTIONS = True
                delay = ping3.ping(host, timeout=timeout, unit="ms")
                if delay is not None and delay is not False:
                    return PingResult(host=host, success=True, latency_ms=delay)
            except Exception:
                pass

            tcp_start = time.time()
            port = 443 if "https" in host or not any(c.isdigit() for c in host) else 80
            try:
                ip = socket.gethostbyname(
                    host.replace("https://", "").replace("http://", "").split("/")[0]
                )
            except socket.gaierror:
                return PingResult(host=host, success=False, error="DNS resolution failed")
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            try:
                sock.connect((ip, port))
                latency = (time.time() - tcp_start) * 1000
                return PingResult(host=host, success=True, latency_ms=latency)
            except (socket.timeout, socket.error) as e:
                return PingResult(host=host, success=False, error=f"Connection failed: {str(e)}")
            finally:
                sock.close()
        except Exception as e:
            return PingResult(host=host, success=False, error=str(e))

    def test_http_connectivity(self) -> bool:
        """Test HTTP connectivity (primary URL + optional http_test_urls)."""
        if not self.enable_http_test:
            return True
        urls = [self.http_test_url] + list(self.http_test_urls)[:5]
        for url in urls:
            if not url or not url.strip():
                continue
            try:
                r = requests.get(url.strip(), timeout=self.timeout, allow_redirects=False)
                if r.status_code in (200, 204):
                    return True
            except Exception:
                continue
        return False

    def check_local_network(self) -> bool:
        """Check if local network is available."""
        try:
            if sys.platform == "win32":
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                try:
                    for gateway in ["192.168.1.1", "192.168.0.1", "10.0.0.1"]:
                        try:
                            sock.connect((gateway, 80))
                            sock.close()
                            return True
                        except Exception:
                            continue
                    return False
                finally:
                    try:
                        sock.close()
                    except Exception:
                        pass
            return True
        except Exception:
            return False

    def ping_all_hosts(self) -> List[PingResult]:
        """Ping all configured hosts in parallel."""
        results: List[PingResult] = []

        def worker(h: str) -> None:
            results.append(self.ping_host(h, self.timeout))

        threads = [threading.Thread(target=worker, args=(h,)) for h in self.hosts]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=self.timeout + 1)
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

        if success_count == 0:
            status = "offline"
        elif success_rate < (100 - self.unstable_loss) or (
            avg_latency and avg_latency > self.unstable_latency
        ):
            status = "unstable"
        else:
            status = "online"

        return ConnectionStatus(
            status=status,
            avg_latency_ms=avg_latency,
            successful_pings=success_count,
            total_pings=total,
            local_network_ok=local_ok,
            internet_ok=internet_ok,
            http_test_ok=http_ok,
        )

    def check_connection(self) -> ConnectionStatus:
        """Perform full connection check (run from worker thread)."""
        self.total_checks += 1
        if self.internal_test_mode:
            status = self._simulate_connection()
        else:
            ping_results = self.ping_all_hosts()
            http_ok = self.test_http_connectivity()
            local_ok = self.check_local_network()
            status = self.analyze_connection(ping_results, http_ok, local_ok)

        if self.total_checks > 1:
            try:
                isp_info = self._get_public_network_info()
                if isp_info:
                    status.public_ip = isp_info.get("ip")
                    status.isp = isp_info.get("isp")
            except Exception:
                pass
            try:
                vpn_connected, vpn_hint = self._detect_vpn(status.isp)
                status.vpn_connected = vpn_connected
                status.vpn_provider = vpn_hint
            except Exception:
                pass

        status.speed_mbps = self._last_speed_mbps
        status.speed_tier = self._last_speed_tier

        if status.status in ("online", "unstable"):
            self.successful_checks += 1
        self.status_history.append(status)
        if len(self.status_history) > self.max_history:
            self.status_history.pop(0)
        self.last_status = status
        return status

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
            )
        return ConnectionStatus(
            status="offline",
            avg_latency_ms=None,
            successful_pings=0,
            total_pings=3,
            local_network_ok=True,
            internet_ok=False,
            http_test_ok=False,
        )

    def _get_public_network_info(self) -> Optional[Dict]:
        now = time.time()
        if self._last_isp_info and (now - self._last_isp_check_ts) < 1800:
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

    def _detect_vpn(self, isp_text: Optional[str]) -> Tuple[bool, str]:
        now = time.time()
        if self._last_vpn_status and (now - self._last_vpn_check_ts) < 10:
            return self._last_vpn_status
        try:
            org = (isp_text or "").lower()
            for kw in [
                "vpn",
                "nord",
                "mullvad",
                "express",
                "surfshark",
                "proton",
                "wireguard",
                "tailscale",
            ]:
                if kw in org:
                    self._last_vpn_status = (True, f"org:{kw}")
                    self._last_vpn_check_ts = now
                    return self._last_vpn_status
        except Exception:
            pass
        try:
            if sys.platform == "darwin":
                try:
                    out = subprocess.check_output(
                        ["scutil", "--nc", "list"], text=True, timeout=2
                    )
                    if "Connected" in out:
                        self._last_vpn_status = (True, "scutil")
                        self._last_vpn_check_ts = now
                        return self._last_vpn_status
                except Exception:
                    pass
                try:
                    out = subprocess.check_output(["ifconfig"], text=True, timeout=2)
                    if re.search(r"\butun\d+\b", out) or "utun" in out or "tun" in out:
                        self._last_vpn_status = (True, "tun/utun")
                        self._last_vpn_check_ts = now
                        return self._last_vpn_status
                except Exception:
                    pass
            elif sys.platform == "win32":
                try:
                    out = subprocess.check_output(
                        ["ipconfig", "/all"],
                        text=True,
                        timeout=3,
                        creationflags=subprocess.CREATE_NO_WINDOW,
                    )
                    if any(
                        p in out.lower()
                        for p in ["tap", "tun", "wireguard", "nordlynx"]
                    ):
                        self._last_vpn_status = (True, "adapter")
                        self._last_vpn_check_ts = now
                        return self._last_vpn_status
                except Exception:
                    pass
            procs = [p.name().lower() for p in psutil.process_iter(attrs=["name"])]
            for kw in [
                "openvpn",
                "wireguard",
                "nordvpn",
                "tailscale",
                "mullvad",
                "expressvpn",
                "protonvpn",
            ]:
                if any(kw in pn for pn in procs):
                    self._last_vpn_status = (True, f"proc:{kw}")
                    self._last_vpn_check_ts = now
                    return self._last_vpn_status
        except Exception:
            pass
        self._last_vpn_status = (False, "")
        self._last_vpn_check_ts = now
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
