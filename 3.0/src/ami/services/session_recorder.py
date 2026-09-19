"""
Dedicated ISP evidence session: one CSV plus a readable summary.
The always-on ami_log.csv is unchanged.
"""

import csv
from datetime import datetime
from pathlib import Path
from typing import Optional

from ami.core.models import reason_text
from ami.core.paths import get_user_data_dir

_HEADER = [
    "Timestamp",
    "Status",
    "Reason",
    "Latency ms",
    "Ping OK",
    "Total pings",
    "LAN",
    "HTTP",
    "ISP",
    "Public IP",
    "VPN",
    "VPN provider",
    "Speed Mbps",
]

_STATUS_IT = {
    "online": "Online",
    "unstable": "Instabile",
    "captive": "Captive",
    "offline": "Offline",
}


class SessionRecorder:
    """Start/stop a folder of files meant to be sent to an ISP."""

    def __init__(self, records_dir: Optional[Path] = None, version: str = ""):
        self.records_dir = Path(records_dir) if records_dir else get_user_data_dir() / "records"
        self.version = version or ""
        self._csv_path: Optional[Path] = None
        self._samples: list = []

    @property
    def recording(self) -> bool:
        return self._csv_path is not None

    @property
    def csv_path(self) -> Optional[Path]:
        return self._csv_path

    def start(self) -> Path:
        if self._csv_path is not None:
            return self._csv_path
        self.records_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        path = self.records_dir / f"ami-isp-{stamp}.csv"
        self._samples = []
        with open(path, "w", newline="", encoding="utf-8") as handle:
            csv.writer(handle).writerow(_HEADER)
        self._csv_path = path
        return path

    def record(self, status) -> None:
        if self._csv_path is None or status is None:
            return
        ts = getattr(status, "timestamp", None) or datetime.now()
        latency = getattr(status, "avg_latency_ms", None)
        speed = getattr(status, "speed_mbps", None)
        vpn = getattr(status, "vpn_connected", None)
        if vpn is True:
            vpn_text = "On"
        elif vpn is False:
            vpn_text = "Off"
        else:
            vpn_text = ""
        row = [
            ts.strftime("%Y-%m-%d %H:%M:%S"),
            getattr(status, "status", "") or "",
            reason_text(getattr(status, "reason", None)),
            f"{latency:.1f}" if latency is not None else "",
            getattr(status, "successful_pings", 0),
            getattr(status, "total_pings", 0),
            "Yes" if getattr(status, "local_network_ok", False) else "No",
            "Yes" if getattr(status, "http_test_ok", False) else "No",
            getattr(status, "isp", None) or "",
            getattr(status, "public_ip", None) or "",
            vpn_text,
            getattr(status, "vpn_provider", None) or "",
            f"{speed:.1f}" if speed is not None else "",
        ]
        self._samples.append(
            {
                "timestamp": ts,
                "status": row[1],
                "reason": row[2],
                "latency": latency,
                "isp": row[8],
                "ip": row[9],
                "vpn": vpn_text,
                "provider": row[11],
            }
        )
        with open(self._csv_path, "a", newline="", encoding="utf-8") as handle:
            csv.writer(handle).writerow(row)

    def stop(self) -> Optional[tuple[Path, Path]]:
        if self._csv_path is None:
            return None
        csv_path = self._csv_path
        txt_path = csv_path.with_suffix(".txt")
        txt_path.write_text(self._summary(), encoding="utf-8")
        self._csv_path = None
        self._samples = []
        return csv_path, txt_path

    def _summary(self) -> str:
        samples = list(self._samples)
        if samples:
            start = samples[0]["timestamp"]
            end = samples[-1]["timestamp"]
        else:
            start = end = datetime.now()
        span = end - start
        minutes = int(span.total_seconds() // 60)
        seconds = int(span.total_seconds() % 60)
        total = len(samples)
        lines = [
            "AMI — resoconto connettività",
            f"Dal {start.strftime('%Y-%m-%d %H:%M:%S')} al {end.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Durata: {minutes} min {seconds} s",
            f"Campioni: {total}",
            "",
        ]
        for key in ("online", "unstable", "captive", "offline"):
            count = sum(1 for sample in samples if sample["status"] == key)
            pct = (count / total * 100) if total else 0.0
            lines.append(f"{_STATUS_IT[key]}: {count} ({pct:.1f}%)")
        latencies = [sample["latency"] for sample in samples if sample["latency"] is not None]
        lines.append("")
        if latencies:
            avg = sum(latencies) / len(latencies)
            lines.append(
                f"Latenza ms: min {min(latencies):.0f}, media {avg:.0f}, max {max(latencies):.0f}"
            )
        else:
            lines.append("Latenza ms: n/d")
        incidents = _incident_runs(samples)
        lines.append("")
        lines.append("Interruzioni e degrado:")
        if incidents:
            for item in incidents:
                lines.append(
                    f"- {item['start'].strftime('%H:%M:%S')}–{item['end'].strftime('%H:%M:%S')} "
                    f"{_STATUS_IT.get(item['status'], item['status'])}"
                    + (f" — {item['reason']}" if item["reason"] else "")
                )
        else:
            lines.append("- nessuna")
        isps = sorted({sample["isp"] for sample in samples if sample["isp"]})
        ips = sorted({sample["ip"] for sample in samples if sample["ip"]})
        vpns = sorted({sample["vpn"] for sample in samples if sample["vpn"]})
        providers = sorted({sample["provider"] for sample in samples if sample["provider"]})
        lines.extend(
            [
                "",
                "ISP: " + (", ".join(isps) if isps else "n/d"),
                "IP pubblico: " + (", ".join(ips) if ips else "n/d"),
                "VPN: " + (", ".join(vpns) if vpns else "n/d"),
            ]
        )
        if providers:
            lines.append("Provider VPN: " + ", ".join(providers))
        version = self.version or "3"
        lines.extend(["", f"Generato da AMI {version}"])
        return "\n".join(lines) + "\n"


def _incident_runs(samples: list) -> list:
    runs = []
    current = None
    for sample in samples:
        if sample["status"] == "online":
            current = None
            continue
        if current and current["status"] == sample["status"] and current["reason"] == sample["reason"]:
            current["end"] = sample["timestamp"]
            continue
        current = {
            "start": sample["timestamp"],
            "end": sample["timestamp"],
            "status": sample["status"],
            "reason": sample["reason"],
        }
        runs.append(current)
    return runs
