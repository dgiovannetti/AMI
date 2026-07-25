"""Tests for network status analysis and local network helpers."""

from ami.core.models import PingResult
from ami.services.network_monitor import NetworkMonitor


def _monitor(**overrides) -> NetworkMonitor:
    config = {
        "monitoring": {
            "ping_hosts": ["8.8.8.8"],
            "http_test_url": "https://example.com/generate_204",
            "timeout": 5,
            "enable_http_test": True,
            "internal_test_mode": False,
        },
        "thresholds": {"unstable_latency_ms": 500, "unstable_loss_percent": 30},
    }
    config.update(overrides)
    return NetworkMonitor(config)


def test_analyze_connection_online():
    mon = _monitor()
    pings = [
        PingResult(host="8.8.8.8", success=True, latency_ms=20),
        PingResult(host="1.1.1.1", success=True, latency_ms=25),
    ]
    status = mon.analyze_connection(pings, http_ok=True, local_ok=True)
    assert status.status == "online"
    assert status.internet_ok is True


def test_analyze_connection_offline_no_pings():
    mon = _monitor()
    pings = [PingResult(host="8.8.8.8", success=False)]
    status = mon.analyze_connection(pings, http_ok=False, local_ok=True)
    assert status.status == "offline"
    assert status.internet_ok is False


def test_analyze_connection_unstable_high_latency():
    mon = _monitor()
    pings = [PingResult(host="8.8.8.8", success=True, latency_ms=900)]
    status = mon.analyze_connection(pings, http_ok=True, local_ok=True)
    assert status.status == "unstable"


def test_analyze_connection_offline_when_lan_down_and_no_http():
    mon = _monitor()
    pings = [PingResult(host="8.8.8.8", success=False)]
    status = mon.analyze_connection(pings, http_ok=False, local_ok=False)
    assert status.status == "offline"
    assert status.local_network_ok is False


def test_has_active_lan_interface_skips_loopback(monkeypatch):
    import socket

    import psutil

    mon = _monitor()

    class Addr:
        def __init__(self, family, address):
            self.family = family
            self.address = address

    class Stat:
        isup = True

    monkeypatch.setattr(
        psutil,
        "net_if_addrs",
        lambda: {
            "lo0": [Addr(socket.AF_INET, "127.0.0.1")],
            "en0": [Addr(socket.AF_INET, "192.168.1.10")],
        },
    )
    monkeypatch.setattr(psutil, "net_if_stats", lambda: {"lo0": Stat(), "en0": Stat()})
    assert mon._has_active_lan_interface() is True
