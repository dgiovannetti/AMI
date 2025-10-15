"""
AMI - Active Monitor of Internet
Network Monitoring Engine

This module handles the core network monitoring functionality:
- Multi-host ping testing
- HTTP connectivity tests
- Connection status detection
- Statistics tracking
"""

import asyncio
import time
import socket
import sys
import subprocess
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime
import re
import psutil
import threading
import requests


@dataclass
class PingResult:
    """Result of a single ping test"""
    host: str
    success: bool
    latency_ms: Optional[float] = None
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ConnectionStatus:
    """Overall connection status"""
    status: str  # 'online', 'unstable', 'offline'
    avg_latency_ms: Optional[float] = None
    successful_pings: int = 0
    total_pings: int = 0
    local_network_ok: bool = False
    internet_ok: bool = False
    http_test_ok: bool = False
    timestamp: datetime = field(default_factory=datetime.now)
    public_ip: Optional[str] = None
    isp: Optional[str] = None
    vpn_connected: Optional[bool] = None
    vpn_provider: Optional[str] = None


class NetworkMonitor:
    """
    Core network monitoring engine with async ping and HTTP testing
    """
    
    def __init__(self, config: dict):
        self.config = config
        self.hosts = config['monitoring']['ping_hosts']
        self.http_test_url = config['monitoring']['http_test_url']
        self.timeout = config['monitoring']['timeout']
        self.retry_count = config['monitoring']['retry_count']
        self.enable_http_test = config['monitoring']['enable_http_test']
        
        # Thresholds
        self.unstable_latency = config['thresholds']['unstable_latency_ms']
        self.unstable_loss = config['thresholds']['unstable_loss_percent']
        
        # Statistics
        self.total_checks = 0
        self.successful_checks = 0
        self.uptime_start = datetime.now()
        self.last_status: Optional[ConnectionStatus] = None
        
        # History for statistics (keep last 100 checks)
        self.status_history: List[ConnectionStatus] = []
        self.max_history = 100
        # ISP/VPN cache
        self._last_public_ip: Optional[str] = None
        self._last_isp_info: Optional[Dict] = None
        self._last_isp_check_ts: float = 0.0
        self._last_vpn_status: Optional[Tuple[bool, str]] = None
        self._last_vpn_check_ts: float = 0.0
        
    def ping_host(self, host: str, timeout: int = 5) -> PingResult:
        """
        Ping a single host using ICMP or TCP fallback
        
        Args:
            host: IP address or hostname to ping
            timeout: Timeout in seconds
            
        Returns:
            PingResult with success status and latency
        """
        try:
            # On macOS/Linux, use system ping command (more reliable, no sudo needed)
            if sys.platform in ['darwin', 'linux']:
                try:
                    param = '-n' if sys.platform == 'win32' else '-c'
                    timeout_param = '-W' if sys.platform == 'linux' else '-W'
                    timeout_ms = str(timeout * 1000)
                    
                    # Run ping command
                    result = subprocess.run(
                        ['ping', param, '1', timeout_param, timeout_ms, host],
                        capture_output=True,
                        text=True,
                        timeout=timeout + 1
                    )
                    
                    if result.returncode == 0:
                        # Parse ping output for latency
                        output = result.stdout
                        # Look for time= in output
                        if 'time=' in output:
                            time_str = output.split('time=')[1].split()[0]
                            latency = float(time_str.replace('ms', ''))
                            return PingResult(host=host, success=True, latency_ms=latency)
                except (subprocess.TimeoutExpired, subprocess.SubprocessError, ValueError):
                    # System ping failed, try ping3 or TCP fallback
                    pass
            
            # Try ICMP ping using ping3 library (requires root on some systems)
            try:
                import ping3
                ping3.EXCEPTIONS = True
                delay = ping3.ping(host, timeout=timeout, unit='ms')
                
                if delay is not None and delay is not False:
                    latency = delay
                    return PingResult(host=host, success=True, latency_ms=latency)
                else:
                    # ICMP failed, try TCP fallback
                    pass
            except (ImportError, Exception) as e:
                # ping3 not available or failed, use TCP fallback
                pass
            
            # TCP fallback: try to connect to port 80 or 443
            # IMPORTANT: Reset timer for TCP test to avoid inflated latency
            tcp_start = time.time()
            
            port = 443 if 'https' in host or not any(c.isdigit() for c in host) else 80
            
            # Resolve hostname if needed
            try:
                ip = socket.gethostbyname(host.replace('https://', '').replace('http://', '').split('/')[0])
            except socket.gaierror:
                return PingResult(host=host, success=False, error="DNS resolution failed")
            
            # Try TCP connection
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            
            try:
                sock.connect((ip, port))
                latency = (time.time() - tcp_start) * 1000  # Convert to ms - only TCP time
                sock.close()
                return PingResult(host=host, success=True, latency_ms=latency)
            except (socket.timeout, socket.error) as e:
                return PingResult(host=host, success=False, error=f"Connection failed: {str(e)}")
            finally:
                sock.close()
                
        except Exception as e:
            return PingResult(host=host, success=False, error=str(e))
    
    def test_http_connectivity(self) -> bool:
        """
        Test HTTP connectivity using a known URL
        
        Returns:
            True if HTTP request succeeds, False otherwise
        """
        if not self.enable_http_test:
            return True
        
        try:
            response = requests.get(
                self.http_test_url,
                timeout=self.timeout,
                allow_redirects=False
            )
            # Google's generate_204 returns 204 No Content
            return response.status_code in [200, 204]
        except Exception:
            return False
    
    def check_local_network(self) -> bool:
        """
        Check if local network is available (can reach gateway)
        
        Returns:
            True if local network is reachable
        """
        try:
            # Try to get default gateway
            import subprocess
            import platform
            
            if platform.system() == "Windows":
                # On Windows, try to reach 192.168.1.1 (common gateway)
                # This is a simplified check
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                try:
                    # Try common gateway addresses
                    for gateway in ['192.168.1.1', '192.168.0.1', '10.0.0.1']:
                        try:
                            sock.connect((gateway, 80))
                            sock.close()
                            return True
                        except:
                            continue
                    return False
                finally:
                    try:
                        sock.close()
                    except:
                        pass
            else:
                return True  # Simplified for non-Windows
        except Exception:
            return False
    
    def ping_all_hosts(self) -> List[PingResult]:
        """
        Ping all configured hosts in parallel using threading
        
        Returns:
            List of PingResult objects
        """
        results = []
        threads = []
        
        def ping_worker(host):
            result = self.ping_host(host, self.timeout)
            results.append(result)
        
        # Create and start threads
        for host in self.hosts:
            thread = threading.Thread(target=ping_worker, args=(host,))
            thread.start()
            threads.append(thread)
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=self.timeout + 1)
        
        return results
    
    def analyze_connection(self, ping_results: List[PingResult], http_ok: bool, local_ok: bool) -> ConnectionStatus:
        """
        Analyze ping results and determine overall connection status
        
        Args:
            ping_results: List of ping results
            http_ok: HTTP test result
            local_ok: Local network test result
            
        Returns:
            ConnectionStatus object
        """
        successful = [r for r in ping_results if r.success]
        total = len(ping_results)
        success_count = len(successful)
        
        # Calculate average latency
        avg_latency = None
        if successful:
            avg_latency = sum(r.latency_ms for r in successful) / len(successful)
        
        # Calculate success rate
        success_rate = (success_count / total * 100) if total > 0 else 0
        
        # Determine status
        internet_ok = success_count > 0 and http_ok
        
        if success_count == 0:
            status = 'offline'
        elif success_rate < (100 - self.unstable_loss) or (avg_latency and avg_latency > self.unstable_latency):
            status = 'unstable'
        else:
            status = 'online'
        
        return ConnectionStatus(
            status=status,
            avg_latency_ms=avg_latency,
            successful_pings=success_count,
            total_pings=total,
            local_network_ok=local_ok,
            internet_ok=internet_ok,
            http_test_ok=http_ok
        )
    
    def check_connection(self) -> ConnectionStatus:
        """
        Perform a complete connection check
        
        Returns:
            ConnectionStatus object with current status
        """
        self.total_checks += 1
        
        # Ping all hosts
        ping_results = self.ping_all_hosts()
        
        # Test HTTP connectivity
        http_ok = self.test_http_connectivity()
        
        # Check local network
        local_ok = self.check_local_network()
        
        # Analyze results
        status = self.analyze_connection(ping_results, http_ok, local_ok)

        # Refresh ISP info at most every 30 minutes or on IP change
        try:
            isp_info = self._get_public_network_info()
            if isp_info:
                status.public_ip = isp_info.get('ip')
                status.isp = isp_info.get('isp')
        except Exception:
            pass

        # Refresh VPN detection at most every 10 seconds
        try:
            vpn_connected, vpn_hint = self._detect_vpn(status.isp)
            status.vpn_connected = vpn_connected
            status.vpn_provider = vpn_hint
        except Exception:
            pass
        
        # Update statistics
        if status.status in ['online', 'unstable']:
            self.successful_checks += 1
        
        # Store in history
        self.status_history.append(status)
        if len(self.status_history) > self.max_history:
            self.status_history.pop(0)
        
        self.last_status = status
        return status

    # ===== ISP / VPN helpers =====
    def _get_public_network_info(self) -> Optional[Dict]:
        now = time.time()
        # 30 minutes cache
        if self._last_isp_info and (now - self._last_isp_check_ts) < 1800:
            return self._last_isp_info
        endpoints = [
            ('https://ipinfo.io/json', lambda j: {
                'ip': j.get('ip'),
                'isp': j.get('org') or j.get('hostname') or j.get('org')
            }),
            ('https://ipapi.co/json', lambda j: {
                'ip': j.get('ip'),
                'isp': j.get('org') or j.get('asn_org') or j.get('org')
            }),
            ('https://ifconfig.co/json', lambda j: {
                'ip': j.get('ip'),
                'isp': j.get('asn_org') or j.get('asn')
            }),
        ]
        for url, parser in endpoints:
            try:
                r = requests.get(url, timeout=3)
                if r.status_code == 200:
                    data = parser(r.json())
                    self._last_isp_info = data
                    self._last_public_ip = data.get('ip')
                    self._last_isp_check_ts = now
                    return data
            except Exception:
                continue
        return self._last_isp_info

    def _detect_vpn(self, isp_text: Optional[str]) -> Tuple[bool, str]:
        now = time.time()
        if self._last_vpn_status and (now - self._last_vpn_check_ts) < 10:
            return self._last_vpn_status
        hint = ''
        # Heuristic 1: ISP/org keyword check
        try:
            org = (isp_text or '').lower()
            keywords = ['vpn', 'nord', 'mullvad', 'express', 'surfshark', 'proton', 'pias', 'private internet', 'tunnelbear', 'hidemy', 'cyberghost', 'windscribe', 'ivpn']
            for kw in keywords:
                if kw in org:
                    self._last_vpn_status = (True, f'org:{kw}')
                    self._last_vpn_check_ts = now
                    return self._last_vpn_status
        except Exception:
            pass
        # Heuristic 2: OS-specific interface/process checks
        try:
            plat = sys.platform
            if plat == 'darwin':
                try:
                    out = subprocess.check_output(['scutil', '--nc', 'list'], text=True, timeout=2)
                    if 'Connected' in out:
                        self._last_vpn_status = (True, 'scutil')
                        self._last_vpn_check_ts = now
                        return self._last_vpn_status
                except Exception:
                    pass
                try:
                    out = subprocess.check_output(['ifconfig'], text=True, timeout=2)
                    if re.search(r'\butun\d+\b', out) or re.search(r'\bwg\d*\b', out) or 'utun' in out or 'tun' in out:
                        self._last_vpn_status = (True, 'tun/utun')
                        self._last_vpn_check_ts = now
                        return self._last_vpn_status
                except Exception:
                    pass
            elif plat == 'win32':
                try:
                    out = subprocess.check_output(['ipconfig', '/all'], text=True, timeout=3, creationflags=0)
                    patterns = ['TAP', 'TUN', 'WireGuard', 'PPP adapter', 'NordLynx']
                    if any(pat.lower() in out.lower() for pat in patterns):
                        self._last_vpn_status = (True, 'adapter')
                        self._last_vpn_check_ts = now
                        return self._last_vpn_status
                except Exception:
                    pass
            # Process scan fallback
            try:
                procs = [p.name().lower() for p in psutil.process_iter(attrs=['name'])]
                for kw in ['openvpn', 'wireguard', 'wg-quick', 'nordvpn', 'tailscaled', 'tailscale', 'mullvad', 'expressvpn', 'protonvpn']:
                    if any(kw in pn for pn in procs):
                        self._last_vpn_status = (True, f'proc:{kw}')
                        self._last_vpn_check_ts = now
                        return self._last_vpn_status
            except Exception:
                pass
        finally:
            self._last_vpn_status = (False, '')
            self._last_vpn_check_ts = now
        return self._last_vpn_status
    
    def get_uptime_percentage(self) -> float:
        """
        Calculate uptime percentage since monitoring started
        
        Returns:
            Uptime percentage (0-100)
        """
        if self.total_checks == 0:
            return 0.0
        return (self.successful_checks / self.total_checks) * 100
    
    def get_uptime_duration(self) -> str:
        """
        Get uptime duration as a formatted string
        
        Returns:
            Formatted uptime duration (e.g., "2h 15m")
        """
        duration = datetime.now() - self.uptime_start
        hours = duration.seconds // 3600
        minutes = (duration.seconds % 3600) // 60
        
        if duration.days > 0:
            return f"{duration.days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    
    def get_statistics(self) -> Dict:
        """
        Get current monitoring statistics
        
        Returns:
            Dictionary with various statistics
        """
        return {
            'total_checks': self.total_checks,
            'successful_checks': self.successful_checks,
            'uptime_percentage': self.get_uptime_percentage(),
            'uptime_duration': self.get_uptime_duration(),
            'last_status': self.last_status,
            'history_count': len(self.status_history)
        }
    
    def reset_statistics(self):
        """Reset all statistics and history"""
        self.total_checks = 0
        self.successful_checks = 0
        self.uptime_start = datetime.now()
        self.status_history.clear()
