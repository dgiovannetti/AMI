"""
AMI - Active Monitor of Internet
Notification System

Handles Windows toast notifications for connection state changes
"""

from typing import Optional
import platform


class Notifier:
    """
    Cross-platform notification system
    Uses Windows 10/11 toast notifications on Windows
    """
    
    def __init__(self, config: dict):
        self.enabled = config['notifications']['enabled']
        self.silent_mode = config['notifications']['silent_mode']
        self.notify_on_disconnect = config['notifications']['notify_on_disconnect']
        self.notify_on_reconnect = config['notifications']['notify_on_reconnect']
        self.notify_on_unstable = config['notifications']['notify_on_unstable']
        
        self.last_status = None
        
        # Try to import Windows toast notifications
        self.windows_toast_available = False
        if platform.system() == 'Windows':
            try:
                from windows_toasts import Toast, WindowsToaster
                self.Toast = Toast
                self.WindowsToaster = WindowsToaster
                self.windows_toast_available = True
            except ImportError:
                # Fallback to win10toast if available
                try:
                    from win10toast import ToastNotifier
                    self.toaster = ToastNotifier()
                    self.windows_toast_available = True
                except ImportError:
                    print("Warning: No Windows toast notification library available")
    
    def should_notify(self, new_status: str) -> bool:
        """
        Determine if a notification should be shown based on status change
        
        Args:
            new_status: New connection status
            
        Returns:
            True if notification should be shown
        """
        if not self.enabled or self.silent_mode:
            return False
        
        # First check (no previous status)
        if self.last_status is None:
            return False
        
        # Status changed
        if new_status != self.last_status:
            if new_status == 'offline' and self.notify_on_disconnect:
                return True
            elif new_status == 'online' and self.last_status in ['offline', 'unstable'] and self.notify_on_reconnect:
                return True
            elif new_status == 'unstable' and self.notify_on_unstable:
                return True
        
        return False
    
    def notify(self, status: str, message: str):
        """
        Show a notification
        
        Args:
            status: Connection status ('online', 'unstable', 'offline')
            message: Notification message
        """
        if not self.should_notify(status):
            self.last_status = status
            return
        
        title = "AMI - Active Monitor of Internet"
        
        # Customize message based on status
        if status == 'online':
            icon = '🟢'
            full_message = f"{icon} Connection Restored\n{message}"
        elif status == 'unstable':
            icon = '🟡'
            full_message = f"{icon} Unstable Connection\n{message}"
        else:  # offline
            icon = '🔴'
            full_message = f"{icon} Connection Lost\n{message}"
        
        try:
            if platform.system() == 'Windows' and self.windows_toast_available:
                self._notify_windows(title, full_message)
            else:
                # Fallback: print to console
                print(f"\n[NOTIFICATION] {title}\n{full_message}\n")
        except Exception as e:
            print(f"Error showing notification: {e}")
        
        self.last_status = status
    
    def _notify_windows(self, title: str, message: str):
        """
        Show Windows toast notification
        
        Args:
            title: Notification title
            message: Notification message
        """
        try:
            # Try windows_toasts first (modern)
            if hasattr(self, 'WindowsToaster'):
                toaster = self.WindowsToaster('AMI')
                toast = self.Toast()
                toast.text_fields = [title, message]
                toaster.show_toast(toast)
            # Fallback to win10toast
            elif hasattr(self, 'toaster'):
                self.toaster.show_toast(
                    title,
                    message,
                    icon_path=None,
                    duration=5,
                    threaded=True
                )
        except Exception as e:
            print(f"Windows notification error: {e}")
    
    def notify_status_change(self, connection_status):
        """
        Notify based on ConnectionStatus object
        
        Args:
            connection_status: ConnectionStatus object
        """
        status = connection_status.status
        
        # Build message
        if connection_status.avg_latency_ms:
            latency_msg = f"Latency: {connection_status.avg_latency_ms:.0f}ms"
        else:
            latency_msg = "No response"
        
        success_rate = (connection_status.successful_pings / connection_status.total_pings * 100) if connection_status.total_pings > 0 else 0
        
        message = f"{latency_msg} | Success: {success_rate:.0f}%"
        
        self.notify(status, message)
