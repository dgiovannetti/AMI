"""ISP session recorder: CSV plus a readable summary."""

from datetime import datetime, timedelta

from ami.core.models import ConnectionStatus
from ami.services.session_recorder import SessionRecorder


def test_session_writes_csv_and_summary(tmp_path):
    rec = SessionRecorder(tmp_path, version="3.3.0")
    csv_path = rec.start()
    start = datetime(2026, 9, 19, 18, 0, 0)
    rec.record(
        ConnectionStatus(
            status="online",
            avg_latency_ms=20,
            reason="ok",
            isp="Fastweb",
            public_ip="1.2.3.4",
            vpn_connected=False,
            timestamp=start,
            successful_pings=3,
            total_pings=3,
            local_network_ok=True,
            http_test_ok=True,
        )
    )
    rec.record(
        ConnectionStatus(
            status="unstable",
            avg_latency_ms=800,
            reason="high_latency",
            isp="Fastweb",
            public_ip="1.2.3.4",
            vpn_connected=False,
            timestamp=start + timedelta(seconds=30),
            successful_pings=1,
            total_pings=3,
            local_network_ok=True,
            http_test_ok=True,
        )
    )
    stopped = rec.stop()
    assert stopped is not None
    written_csv, txt_path = stopped
    assert written_csv == csv_path
    body = csv_path.read_text(encoding="utf-8")
    assert "Latency ms" in body
    assert "Public IP" in body
    assert "unstable" in body
    assert "1.2.3.4" in body
    summary = txt_path.read_text(encoding="utf-8")
    assert "50.0%" in summary
    assert "Instabile" in summary
    assert "High latency" in summary
    assert "Generato da AMI 3.3.0" in summary
    assert rec.recording is False
