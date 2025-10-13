"""
AMI - Active Monitor of Internet
Logging System

Handles event logging to CSV files with automatic rotation
"""

import csv
import os
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
        self.max_size_mb = config['logging']['max_log_size_mb']
        
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
    
    def _check_log_size(self):
        """Check log file size and rotate if needed"""
        try:
            if os.path.exists(self.log_file):
                size_mb = os.path.getsize(self.log_file) / (1024 * 1024)
                
                if size_mb > self.max_size_mb:
                    # Rotate log file
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    backup_file = f"{self.log_file}.{timestamp}.bak"
                    os.rename(self.log_file, backup_file)
                    self._create_log_file()
        except Exception as e:
            print(f"Error checking log size: {e}")
    
    def log_status(self, status):
        """
        Log a connection status event
        
        Args:
            status: ConnectionStatus object
        """
        if not self.enabled:
            return
        
        try:
            self._check_log_size()
            
            with open(self.log_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    status.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    status.status,
                    f"{status.avg_latency_ms:.2f}" if status.avg_latency_ms else "N/A",
                    status.successful_pings,
                    status.total_pings,
                    'Yes' if status.local_network_ok else 'No',
                    'Yes' if status.internet_ok else 'No',
                    'Yes' if status.http_test_ok else 'No'
                ])
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
