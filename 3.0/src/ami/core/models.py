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


@dataclass
class ConnectionStatus:
    """Overall connection status."""

    status: str  # 'online' | 'unstable' | 'offline'
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
    speed_mbps: Optional[float] = None
    speed_tier: Optional[str] = None  # 'slow' | 'medium' | 'fast'
