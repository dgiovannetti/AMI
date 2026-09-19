"""
AMI - Active Monitor of Internet
Optional Local API Server

Provides a simple HTTP API to query connection status
Endpoint: http://localhost:7212/status
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import threading
from typing import Optional


class APIHandler(BaseHTTPRequestHandler):
    """HTTP request handler for API endpoints. Gets monitor from server (DI, no class variable)."""

    def _get_monitor(self):
        return getattr(self.server, 'monitor', None)

    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/status':
            self.send_status()
        elif self.path == '/health':
            self.send_health()
        elif self.path == '/stats':
            self.send_statistics()
        else:
            self.send_error(404, "Endpoint not found")

    def send_status(self):
        """Send current connection status"""
        monitor = self._get_monitor()
        if not monitor or not monitor.last_status:
            self.send_json_response({'error': 'No status available yet'}, 503)
            return

        status = monitor.last_status
        response = {
            'status': status.status,
            'timestamp': status.timestamp.isoformat(),
            'avg_latency_ms': status.avg_latency_ms,
            'successful_pings': status.successful_pings,
            'total_pings': status.total_pings,
            'local_network_ok': status.local_network_ok,
            'internet_ok': status.internet_ok,
            'http_test_ok': status.http_test_ok
        }
        
        self.send_json_response(response)
    
    def send_health(self):
        """Send health check response"""
        version = '2.0.0'
        if hasattr(self.server, 'config') and self.server.config:
            version = self.server.config.get('app', {}).get('version', version)
        response = {
            'service': 'AMI',
            'status': 'running',
            'version': version
        }
        self.send_json_response(response)
    
    def send_statistics(self):
        """Send monitoring statistics"""
        monitor = self._get_monitor()
        if not monitor:
            self.send_json_response({'error': 'Monitor not available'}, 503)
            return

        stats = monitor.get_statistics()
        response = {
            'total_checks': stats['total_checks'],
            'successful_checks': stats['successful_checks'],
            'uptime_percentage': stats['uptime_percentage'],
            'uptime_duration': stats['uptime_duration'],
            'history_count': stats['history_count']
        }
        
        self.send_json_response(response)
    
    def send_json_response(self, data: dict, status_code: int = 200):
        """Send JSON response"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())
    
    def log_message(self, format, *args):
        """Override to suppress request logging"""
        pass  # Silent by default


class APIServer:
    """
    Simple HTTP API server for querying AMI status
    Runs in a background thread
    """
    
    def __init__(self, config: dict, monitor):
        self.config = config
        self.monitor = monitor
        self.enabled = config['api']['enabled']
        self.port = config['api']['port']
        
        self.server: Optional[HTTPServer] = None
        self.thread: Optional[threading.Thread] = None
    
    def start(self):
        """Start the API server in a background thread"""
        if not self.enabled:
            return

        try:
            # Create server with monitor injected (handler gets it via self.server.monitor)
            self.server = HTTPServer(('127.0.0.1', self.port), APIHandler)
            self.server.monitor = self.monitor
            self.server.config = self.config
            
            # Start in background thread
            self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.thread.start()
            
            print(f"API server started on http://localhost:{self.port}")
            print(f"  - Status: http://localhost:{self.port}/status")
            print(f"  - Health: http://localhost:{self.port}/health")
            print(f"  - Stats: http://localhost:{self.port}/stats")
            
        except Exception as e:
            print(f"Failed to start API server: {e}")
    
    def stop(self):
        """Stop the API server"""
        if self.server:
            self.server.shutdown()
            self.server = None
            print("API server stopped")
