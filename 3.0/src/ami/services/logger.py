"""
AMI 3.0 - Event logging to CSV with rotation.
Log file in user data dir.
"""

import csv
import io
import os
from datetime import datetime
from pathlib import Path

from ami.core.paths import get_user_data_dir


class EventLogger:
    """CSV event logger with size-based rotation."""

    def __init__(self, config: dict):
        self.enabled = config["logging"]["enabled"]
        log_filename = config["logging"]["log_file"]
        self.log_file = str(get_user_data_dir() / log_filename)
        self.max_size_mb = config["logging"].get("max_log_size_mb", 1)
        self.max_size_bytes = int(self.max_size_mb * 1024 * 1024)
        if self.enabled:
            Path(self.log_file).parent.mkdir(parents=True, exist_ok=True)
        if self.enabled and not os.path.exists(self.log_file):
            self._create_log_file()

    def _create_log_file(self) -> None:
        with open(self.log_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "Timestamp",
                    "Status",
                    "Avg Latency (ms)",
                    "Successful Pings",
                    "Total Pings",
                    "Local Network",
                    "Internet OK",
                    "HTTP Test OK",
                ]
            )

    def _check_log_size(self, next_bytes: int = 0) -> None:
        if not os.path.exists(self.log_file):
            return
        size = os.path.getsize(self.log_file)
        if size + max(0, next_bytes) > self.max_size_bytes:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            os.rename(self.log_file, f"{self.log_file}.{ts}.bak")
            self._create_log_file()

    def _estimate_row_bytes(self, row: list) -> int:
        try:
            buf = io.StringIO()
            writer = csv.writer(buf, lineterminator="\r\n")
            writer.writerow(row)
            return len(buf.getvalue().encode("utf-8", errors="ignore"))
        except Exception:
            return 256

    def log_status(self, status) -> None:
        if not self.enabled:
            return
        try:
            row = [
                status.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                status.status,
                f"{status.avg_latency_ms:.2f}" if status.avg_latency_ms else "N/A",
                status.successful_pings,
                status.total_pings,
                "Yes" if status.local_network_ok else "No",
                "Yes" if status.internet_ok else "No",
                "Yes" if status.http_test_ok else "No",
            ]
            self._check_log_size(self._estimate_row_bytes(row))
            with open(self.log_file, "a", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow(row)
        except Exception as e:
            print(f"Error logging status: {e}")

    def get_recent_logs(self, count: int = 100) -> list:
        if not os.path.exists(self.log_file):
            return []
        try:
            with open(self.log_file, "r", encoding="utf-8") as f:
                logs = list(csv.DictReader(f))
            return logs[-count:] if len(logs) > count else logs
        except Exception as e:
            print(f"Error reading logs: {e}")
            return []

    def get_log_path(self) -> Path:
        return Path(self.log_file)
