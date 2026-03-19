"""
AMI 3.0 - Optional local HTTP API for status/stats.
Supports optional auth_token in config.
"""

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Optional


class APIHandler(BaseHTTPRequestHandler):
    """GET /status, /health, /stats. Optional Authorization: Bearer <token>."""

    def _get_server_attrs(self):
        s = self.server
        return getattr(s, "monitor", None), getattr(s, "config", None), getattr(s, "auth_token", None)

    def _check_auth(self) -> bool:
        token = self._get_server_attrs()[2]
        if not token or not token.strip():
            return True
        auth = self.headers.get("Authorization")
        if not auth:
            return False
        parts = auth.split()
        return len(parts) == 2 and parts[0].lower() == "bearer" and parts[1] == token

    def do_GET(self):
        if not self._check_auth():
            self.send_response(401)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"error":"Unauthorized"}')
            return
        if self.path == "/status":
            self.send_status()
        elif self.path == "/health":
            self.send_health()
        elif self.path == "/stats":
            self.send_statistics()
        else:
            self.send_error(404, "Endpoint not found")

    def send_status(self):
        monitor, _, _ = self._get_server_attrs()
        if not monitor or not monitor.last_status:
            self.send_json_response({"error": "No status available yet"}, 503)
            return
        status = monitor.last_status
        payload = {
            "status": status.status,
            "timestamp": status.timestamp.isoformat(),
            "avg_latency_ms": status.avg_latency_ms,
            "successful_pings": status.successful_pings,
            "total_pings": status.total_pings,
            "local_network_ok": status.local_network_ok,
            "internet_ok": status.internet_ok,
            "http_test_ok": status.http_test_ok,
        }
        if getattr(status, "speed_mbps", None) is not None:
            payload["speed_mbps"] = status.speed_mbps
        if getattr(status, "speed_tier", None) is not None:
            payload["speed_tier"] = status.speed_tier
        self.send_json_response(payload)

    def send_health(self):
        _, config, _ = self._get_server_attrs()
        version = "3.1.4"
        if config:
            version = config.get("app", {}).get("version", version)
        self.send_json_response({
            "service": "AMI",
            "status": "running",
            "version": version,
        })

    def send_statistics(self):
        monitor, _, _ = self._get_server_attrs()
        if not monitor:
            self.send_json_response({"error": "Monitor not available"}, 503)
            return
        stats = monitor.get_statistics()
        self.send_json_response({
            "total_checks": stats["total_checks"],
            "successful_checks": stats["successful_checks"],
            "uptime_percentage": stats["uptime_percentage"],
            "uptime_duration": stats["uptime_duration"],
            "history_count": stats["history_count"],
        })

    def send_json_response(self, data: dict, status_code: int = 200):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())

    def log_message(self, format, *args):
        pass


class APIServer:
    """HTTP API server in a background thread."""

    def __init__(self, config: dict, monitor):
        self.config = config
        self.monitor = monitor
        self.enabled = config["api"]["enabled"]
        self.port = config["api"]["port"]
        self.auth_token = (config["api"].get("auth_token") or "").strip()
        self.server: Optional[HTTPServer] = None
        self.thread: Optional[threading.Thread] = None

    def start(self) -> None:
        if not self.enabled:
            return
        try:
            self.server = HTTPServer(("127.0.0.1", self.port), APIHandler)
            self.server.monitor = self.monitor
            self.server.config = self.config
            self.server.auth_token = self.auth_token
            self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.thread.start()
            print(f"API server started on http://localhost:{self.port}")
        except Exception as e:
            print(f"Failed to start API server: {e}")

    def stop(self) -> None:
        if self.server:
            self.server.shutdown()
            self.server = None
            print("API server stopped")
