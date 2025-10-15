"""
AMI - Active Monitor of Internet
Notification System

Cross-platform notifications:
- Windows: native toasts (windows_toasts or win10toast)
- macOS/Linux: QSystemTrayIcon balloon via tray_icon
"""

from typing import Optional
import platform
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon
import subprocess


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
        
        # Will be set by tray_app after QSystemTrayIcon is created
        self.tray_icon = None
    
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
            system = platform.system()
            # Prefer native Windows toast when available
            if system == 'Windows' and self.windows_toast_available:
                self._notify_windows(title, full_message)
            elif system == 'Darwin':
                # Use AppleScript notification with optional sound
                self._notify_macos(title, full_message)
            # Use tray balloon if tray icon is available (macOS/Linux/Windows fallback)
            elif self.tray_icon is not None:
                try:
                    self.tray_icon.showMessage(
                        title,
                        full_message,
                        QSystemTrayIcon.MessageIcon.Information,
                        4000
                    )
                except Exception:
                    print(f"\n[NOTIFICATION] {title}\n{full_message}\n")
            else:
                print(f"\n[NOTIFICATION] {title}\n{full_message}\n")

            # Play a simple system beep if not in silent mode
            if not self.silent_mode:
                try:
                    QApplication.beep()
                except Exception:
                    pass
        except Exception as e:
            print(f"Error showing notification: {e}")
        
        self.last_status = status

    def notify_test(self):
        """Show a quick test notification to validate settings"""
        if not self.enabled:
            return
        # Bypass should_notify to always show test
        title = "AMI - Test Notification"
        message = "This is a test notification from AMI."
        try:
            system = platform.system()
            if system == 'Windows' and self.windows_toast_available:
                self._notify_windows(title, message)
            elif system == 'Darwin':
                self._notify_macos(title, message)
            elif self.tray_icon is not None:
                self.tray_icon.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, 3000)
            else:
                print(f"\n[NOTIFICATION] {title}\n{message}\n")
            if not self.silent_mode:
                try:
                    QApplication.beep()
                except Exception:
                    pass
        except Exception as e:
            print(f"Error showing test notification: {e}")

    def notify_message(self, title: str, message: str, level: str = 'info', respect_enabled: bool = True, play_sound: bool = False):
        """Show a generic message (bypasses should_notify)
        
        Args:
            title: Title of the notification
            message: Body text
            level: 'info' | 'warning' | 'error'
            respect_enabled: if True, respects notifications.enabled; if False, always show
            play_sound: if True and not silent_mode, play system beep
        """
        if respect_enabled and not self.enabled:
            return
        try:
            system = platform.system()
            if system == 'Windows' and self.windows_toast_available:
                self._notify_windows(title, message)
            elif system == 'Darwin':
                self._notify_macos(title, message)
            elif self.tray_icon is not None:
                icon_map = {
                    'info': QSystemTrayIcon.MessageIcon.Information,
                    'warning': QSystemTrayIcon.MessageIcon.Warning,
                    'error': QSystemTrayIcon.MessageIcon.Critical,
                }
                self.tray_icon.showMessage(title, message, icon_map.get(level, QSystemTrayIcon.MessageIcon.Information), 3500)
            else:
                print(f"\n[NOTIFICATION] {title}\n{message}\n")
            if play_sound and not self.silent_mode:
                try:
                    QApplication.beep()
                except Exception:
                    pass
        except Exception as e:
            print(f"Error showing message notification: {e}")
    
    def _notify_macos(self, title: str, message: str):
        """Show macOS notification via AppleScript with optional sound"""
        try:
            # Escape quotes and newlines for AppleScript
            esc_title = title.replace('"', '\\"')
            esc_message = message.replace('"', '\\"').replace('\n', ' ')
            if self.silent_mode:
                script = f'display notification "{esc_message}" with title "{esc_title}"'
            else:
                # Use a built-in macOS sound
                script = f'display notification "{esc_message}" with title "{esc_title}" sound name "Glass"'
            subprocess.run(['osascript', '-e', script], check=False)
        except Exception as e:
            print(f"macOS notification error: {e}")
    
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
