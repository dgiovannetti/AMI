"""
AMI 3.0 - Data models for connection status and ping results.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class PingResult:
    """Result of a single ping test."""

    host: str
    success: bool
    latency_ms: Optional[float] = None
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


# Why the status is what it is. Shown in tray, dashboard, CSV, and the local API.
REASON_TEXT = {
    "ok": "Reachable",
    "high_latency": "High latency",
    "packet_loss": "Packet loss",
    "captive": "Captive portal or HTTP blocked",
    "http_failed": "HTTP failed",
    "lan_only": "LAN only, no internet",
    "offline": "No route",
    "monitor_error": "Monitor error",
}


def reason_text(reason: Optional[str]) -> str:
    """Human label for a ConnectionStatus.reason code."""
    if not reason:
        return ""
    return REASON_TEXT.get(reason, reason.replace("_", " "))


@dataclass
class ConnectionStatus:
    """Overall connection status."""

    status: str  # 'online' | 'unstable' | 'captive' | 'offline'
    avg_latency_ms: Optional[float] = None
    successful_pings: int = 0
    total_pings: int = 0
    local_network_ok: bool = False
    internet_ok: bool = False
    http_test_ok: bool = False
    timestamp: datetime = field(default_factory=datetime.now)
    reason: str = "ok"
    public_ip: Optional[str] = None
    isp: Optional[str] = None
    vpn_connected: Optional[bool] = None
    vpn_provider: Optional[str] = None
    speed_mbps: Optional[float] = None
    speed_tier: Optional[str] = None  # 'slow' | 'medium' | 'fast'
