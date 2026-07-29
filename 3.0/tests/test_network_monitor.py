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


def test_detect_timeout_capped_at_two():
    mon = _monitor()
    mon.timeout = 5
    assert mon._detect_timeout() == 2
    mon.timeout = 1
    assert mon._detect_timeout() == 1


def test_check_connection_short_circuits_http_when_pings_fail(monkeypatch):
    mon = _monitor()
    mon.hosts = ["8.8.8.8", "1.1.1.1"]

    def fake_ping_all():
        return [
            PingResult(host="8.8.8.8", success=False),
            PingResult(host="1.1.1.1", success=False),
        ]

    http_calls = {"n": 0}

    def fake_http(**kwargs):
        http_calls["n"] += 1
        return True

    def fake_local(*, fast=False):
        assert fast is True
        return True

    monkeypatch.setattr(mon, "ping_all_hosts", fake_ping_all)
    monkeypatch.setattr(mon, "test_http_connectivity", fake_http)
    monkeypatch.setattr(mon, "check_local_network", fake_local)

    status = mon.check_connection()
    assert status.status == "offline"
    assert http_calls["n"] == 0


def test_check_local_network_fast_skips_gateway_ping(monkeypatch):
    mon = _monitor()
    monkeypatch.setattr(mon, "_has_active_lan_interface", lambda: False)

    def boom_gateway():
        raise AssertionError("gateway must not be queried in fast mode")

    monkeypatch.setattr(mon, "_default_gateway", boom_gateway)
    assert mon.check_local_network(fast=True) is False


def test_check_local_network_prefers_lan_iface(monkeypatch):
    mon = _monitor()
    monkeypatch.setattr(mon, "_has_active_lan_interface", lambda: True)

    def boom_gateway():
        raise AssertionError("gateway must not be queried when LAN is up")

    monkeypatch.setattr(mon, "_default_gateway", boom_gateway)
    assert mon.check_local_network(fast=False) is True


def test_check_connection_does_not_block_on_isp_vpn(monkeypatch):
    mon = _monitor()

    monkeypatch.setattr(
        mon,
        "ping_all_hosts",
        lambda: [PingResult(host="8.8.8.8", success=True, latency_ms=20)],
    )
    monkeypatch.setattr(mon, "test_http_connectivity", lambda **kw: True)
    monkeypatch.setattr(mon, "check_local_network", lambda **kw: True)

    def boom_isp():
        raise AssertionError("ISP must be deferred")

    def boom_vpn(_isp):
        raise AssertionError("VPN must be deferred")

    monkeypatch.setattr(mon, "_get_public_network_info", boom_isp)
    monkeypatch.setattr(mon, "_detect_vpn", boom_vpn)

    status = mon.check_connection()
    assert status.status == "online"


def test_enrich_status_fills_isp_without_changing_line_state(monkeypatch):
    mon = _monitor()
    mon.total_checks = 2
    status = mon.analyze_connection(
        [PingResult(host="8.8.8.8", success=True, latency_ms=20)],
        http_ok=True,
        local_ok=True,
    )
    monkeypatch.setattr(
        mon, "_get_public_network_info", lambda: {"ip": "1.2.3.4", "isp": "TestISP"}
    )
    monkeypatch.setattr(mon, "_detect_vpn", lambda isp: (False, ""))
    enriched = mon.enrich_status(status)
    assert enriched.status == "online"
    assert enriched.public_ip == "1.2.3.4"
    assert enriched.isp == "TestISP"


def test_seed_history_from_logs_keeps_offline_and_unstable():
    mon = _monitor()
    mon.max_history = 10
    rows = [
        {
            "Timestamp": "2026-07-29 10:00:00",
            "Status": "online",
            "Avg Latency (ms)": "30.0",
            "Successful Pings": "3",
            "Total Pings": "3",
            "Local Network": "Yes",
            "Internet OK": "Yes",
            "HTTP Test OK": "Yes",
        },
        {
            "Timestamp": "2026-07-29 10:00:01",
            "Status": "unstable",
            "Avg Latency (ms)": "800.5",
            "Successful Pings": "2",
            "Total Pings": "3",
            "Local Network": "Yes",
            "Internet OK": "Yes",
            "HTTP Test OK": "Yes",
        },
        {
            "Timestamp": "2026-07-29 10:00:02",
            "Status": "offline",
            "Avg Latency (ms)": "N/A",
            "Successful Pings": "0",
            "Total Pings": "3",
            "Local Network": "No",
            "Internet OK": "No",
            "HTTP Test OK": "No",
        },
    ]
    mon.seed_history_from_logs(rows)
    assert [h.status for h in mon.status_history] == ["online", "unstable", "offline"]
    assert mon.status_history[1].avg_latency_ms == 800.5
    assert mon.status_history[2].avg_latency_ms is None
    # Do not overwrite live history.
    mon.seed_history_from_logs(rows)
    assert len(mon.status_history) == 3


def test_default_max_history_is_long_enough_for_chart():
    mon = _monitor()
    assert mon.max_history >= 600
