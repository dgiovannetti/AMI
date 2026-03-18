"""
AMI 3.0 - Cross-platform notifications.
Windows: native toasts; macOS: AppleScript (or tray fallback); Linux: tray balloon.
"""

import platform
import subprocess
from typing import Optional


class Notifier:
    """Cross-platform notification system."""

    def __init__(self, config: dict):
        self.enabled = config["notifications"]["enabled"]
        self.silent_mode = config["notifications"]["silent_mode"]
        self.notify_on_disconnect = config["notifications"]["notify_on_disconnect"]
        self.notify_on_reconnect = config["notifications"]["notify_on_reconnect"]
        self.notify_on_unstable = config["notifications"]["notify_on_unstable"]
        self.last_status: Optional[str] = None
        self.windows_toast_available = False
        if platform.system() == "Windows":
            try:
                from windows_toasts import Toast, WindowsToaster
                self.Toast = Toast
                self.WindowsToaster = WindowsToaster
                self.windows_toast_available = True
            except ImportError:
                try:
                    from win10toast import ToastNotifier
                    self.toaster = ToastNotifier()
                    self.windows_toast_available = True
                except ImportError:
                    pass
        self.tray_icon = None

    def should_notify(self, new_status: str) -> bool:
        if not self.enabled or self.silent_mode:
            return False
        if self.last_status is None:
            return False
        if new_status != self.last_status:
            if new_status == "offline" and self.notify_on_disconnect:
                return True
            if new_status == "online" and self.last_status in ("offline", "unstable") and self.notify_on_reconnect:
                return True
            if new_status == "unstable" and self.notify_on_unstable:
                return True
        return False

    def notify(self, status: str, message: str) -> None:
        if not self.should_notify(status):
            self.last_status = status
            return
        title = "AMI - Active Monitor of Internet"
        if status == "online":
            full_message = f"🟢 Connection Restored\n{message}"
        elif status == "unstable":
            full_message = f"🟡 Unstable Connection\n{message}"
        else:
            full_message = f"🔴 Connection Lost\n{message}"
        try:
            from PyQt6.QtWidgets import QApplication
            system = platform.system()
            if system == "Windows" and self.windows_toast_available:
                self._notify_windows(title, full_message)
            elif system == "Darwin":
                self._notify_macos(title, full_message)
            elif self.tray_icon is not None:
                self.tray_icon.showMessage(
                    title,
                    full_message,
                    self.tray_icon.MessageIcon.Information,
                    4000,
                )
            else:
                print(f"\n[NOTIFICATION] {title}\n{full_message}\n")
            if not self.silent_mode:
                try:
                    QApplication.beep()
                except Exception:
                    pass
        except Exception as e:
            print(f"Error showing notification: {e}")
        self.last_status = status

    def notify_test(self) -> None:
        if not self.enabled:
            return
        title = "AMI - Test Notification"
        message = "This is a test notification from AMI."
        try:
            from PyQt6.QtWidgets import QApplication
            system = platform.system()
            if system == "Windows" and self.windows_toast_available:
                self._notify_windows(title, message)
            elif system == "Darwin":
                self._notify_macos(title, message)
            elif self.tray_icon is not None:
                self.tray_icon.showMessage(
                    title, message, self.tray_icon.MessageIcon.Information, 3000
                )
            else:
                print(f"\n[NOTIFICATION] {title}\n{message}\n")
            if not self.silent_mode:
                try:
                    QApplication.beep()
                except Exception:
                    pass
        except Exception as e:
            print(f"Error showing test notification: {e}")

    def notify_message(
        self,
        title: str,
        message: str,
        level: str = "info",
        respect_enabled: bool = True,
        play_sound: bool = False,
    ) -> None:
        if respect_enabled and not self.enabled:
            return
        try:
            from PyQt6.QtWidgets import QApplication
            system = platform.system()
            if system == "Windows" and self.windows_toast_available:
                self._notify_windows(title, message)
            elif system == "Darwin":
                self._notify_macos(title, message)
            elif self.tray_icon is not None:
                icon_map = {
                    "info": self.tray_icon.MessageIcon.Information,
                    "warning": self.tray_icon.MessageIcon.Warning,
                    "error": self.tray_icon.MessageIcon.Critical,
                }
                self.tray_icon.showMessage(
                    title, message, icon_map.get(level, self.tray_icon.MessageIcon.Information), 3500
                )
            else:
                print(f"\n[NOTIFICATION] {title}\n{message}\n")
            if play_sound and not self.silent_mode:
                try:
                    QApplication.beep()
                except Exception:
                    pass
        except Exception as e:
            print(f"Error showing message notification: {e}")

    def _notify_macos(self, title: str, message: str) -> None:
        try:
            esc_title = title.replace('"', '\\"')
            esc_message = message.replace('"', '\\"').replace("\n", " ")
            if self.silent_mode:
                script = f'display notification "{esc_message}" with title "{esc_title}"'
            else:
                script = f'display notification "{esc_message}" with title "{esc_title}" sound name "Glass"'
            subprocess.run(["osascript", "-e", script], check=False)
        except Exception as e:
            print(f"macOS notification error: {e}")

    def _notify_windows(self, title: str, message: str) -> None:
        try:
            if hasattr(self, "WindowsToaster"):
                toaster = self.WindowsToaster("AMI")
                toast = self.Toast()
                toast.text_fields = [title, message]
                toaster.show_toast(toast)
            elif hasattr(self, "toaster"):
                self.toaster.show_toast(
                    title, message, icon_path=None, duration=5, threaded=True
                )
        except Exception as e:
            print(f"Windows notification error: {e}")

    def notify_status_change(self, connection_status) -> None:
        status = connection_status.status
        if connection_status.avg_latency_ms:
            latency_msg = f"Latency: {connection_status.avg_latency_ms:.0f}ms"
        else:
            latency_msg = "No response"
        rate = (
            (connection_status.successful_pings / connection_status.total_pings * 100)
            if connection_status.total_pings > 0
            else 0
        )
        message = f"{latency_msg} | Success: {rate:.0f}%"
        self.notify(status, message)
