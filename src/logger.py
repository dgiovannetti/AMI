"""
AMI - Active Monitor of Internet
Logging System

Handles event logging to CSV files with automatic rotation
"""

import csv
import os
import io
from datetime import datetime
from typing import Optional
from pathlib import Path


class EventLogger:
    """
    Logger for AMI connection events
    Writes to CSV file with automatic size management
    """
    
    def __init__(self, config: dict):
        self.enabled = config['logging']['enabled']
        self.log_file = config['logging']['log_file']
        self.max_size_mb = config['logging'].get('max_log_size_mb', 1)
        self.max_size_bytes = int(self.max_size_mb * 1024 * 1024)
        
        # Ensure log file exists with headers
        if self.enabled and not os.path.exists(self.log_file):
            self._create_log_file()
    
    def _create_log_file(self):
        """Create log file with CSV headers"""
        try:
            with open(self.log_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'Timestamp',
                    'Status',
                    'Avg Latency (ms)',
                    'Successful Pings',
                    'Total Pings',
                    'Local Network',
                    'Internet OK',
                    'HTTP Test OK'
                ])
        except Exception as e:
            print(f"Error creating log file: {e}")
    
    def _check_log_size(self, next_bytes: int = 0):
        """Check log file size and rotate if needed before appending next_bytes"""
        try:
            if os.path.exists(self.log_file):
                size = os.path.getsize(self.log_file)
                if size + max(0, next_bytes) > self.max_size_bytes:
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    backup_file = f"{self.log_file}.{timestamp}.bak"
                    os.rename(self.log_file, backup_file)
                    self._create_log_file()
        except Exception as e:
            print(f"Error checking log size: {e}")

    def _estimate_row_bytes(self, row) -> int:
        try:
            buf = io.StringIO()
            writer = csv.writer(buf, lineterminator='\r\n')
            writer.writerow(row)
            data = buf.getvalue().encode('utf-8', errors='ignore')
            return len(data)
        except Exception:
            return 256
    
    def log_status(self, status):
        """
        Log a connection status event
        
        Args:
            status: ConnectionStatus object
        """
        if not self.enabled:
            return
        
        try:
            row = [
                status.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                status.status,
                f"{status.avg_latency_ms:.2f}" if status.avg_latency_ms else "N/A",
                status.successful_pings,
                status.total_pings,
                'Yes' if status.local_network_ok else 'No',
                'Yes' if status.internet_ok else 'No',
                'Yes' if status.http_test_ok else 'No'
            ]
            est = self._estimate_row_bytes(row)
            self._check_log_size(est)
            with open(self.log_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(row)
        except Exception as e:
            print(f"Error logging status: {e}")
    
    def get_recent_logs(self, count: int = 100):
        """
        Get recent log entries
        
        Args:
            count: Number of recent entries to retrieve
            
        Returns:
            List of log entries (as dictionaries)
        """
        if not os.path.exists(self.log_file):
            return []
        
        try:
            logs = []
            with open(self.log_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                logs = list(reader)
            
            # Return last 'count' entries
            return logs[-count:] if len(logs) > count else logs
        except Exception as e:
            print(f"Error reading logs: {e}")
            return []
