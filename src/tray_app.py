"""
AMI - Active Monitor of Internet
System Tray Application

Main application with system tray icon and menu
"""

import sys
import json
import os
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QSystemTrayIcon, QMenu, 
                            QMessageBox)
from PyQt6.QtCore import QTimer, Qt, QThread, pyqtSignal
from PyQt6.QtGui import QIcon, QAction, QPixmap, QPainter, QColor, QFont, QRadialGradient, QPen

from network_monitor import NetworkMonitor
from logger import EventLogger
from notifier import Notifier
from api_server import APIServer
from splash_screen import UltraModernSplashScreen
from settings_dialog import SettingsDialog
from updater import UpdateManager
from update_dialog import UpdateDialog


class MonitorThread(QThread):
    """
    Background thread for network monitoring
    Emits signals when status changes
    """
    status_updated = pyqtSignal(object)  # ConnectionStatus object
    
    def __init__(self, monitor: NetworkMonitor):
        super().__init__()
        self.monitor = monitor
        self.running = True
    
    def run(self):
        """Run a single check"""
        if self.running:
            status = self.monitor.check_connection()
            self.status_updated.emit(status)
    
    def stop(self):
        """Stop the monitoring thread"""
        self.running = False


class SystemTrayApp:
    """
    Main system tray application
    """
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        
        # Show splash screen
        self.splash = UltraModernSplashScreen()
        self.splash.show()
        self.splash.showMessage("Loading configuration...")
        self.app.processEvents()
        
        # Load configuration
        self.config = self.load_config()
        self.splash.showMessage("Initializing network monitor...")
        self.app.processEvents()
        
        # Initialize components
        self.monitor = NetworkMonitor(self.config)
        self.splash.showMessage("Starting logger...")
        self.app.processEvents()
        
        self.logger = EventLogger(self.config)
        self.splash.showMessage("Preparing notifications...")
        self.app.processEvents()
        
        self.notifier = Notifier(self.config)
        self.splash.showMessage("Starting API server...")
        
        self.api_server = APIServer(self.config, self.monitor)
        
        # Current status
        self.current_status = None
        
        # Start API server if enabled
        self.splash.showMessage("Finalizing...")
        self.app.processEvents()
        self.api_server.start()
        
        # Create tray icon
        self.tray_icon = QSystemTrayIcon(self.app)
        self.tray_icon.setToolTip("AMI - Starting...")
        # Attach tray icon to notifier for cross-platform notifications
        try:
            self.notifier.tray_icon = self.tray_icon
        except Exception:
            pass
        
        # Set initial icon
        self.update_icon('offline')
        
        # Initialize updater BEFORE creating menu so menu item is present
        self.updater = None
        self.update_timer = None
        if self.config.get('updates', {}).get('enabled', True):
            app_version = self.config.get('app', {}).get('version', '1.0.0')
            github_repo = self.config.get('updates', {}).get('github_repo', 'dgiovannetti/AMI')
            self.updater = UpdateManager(app_version, github_repo)
            
            # Check for updates on startup if configured
            if self.config.get('updates', {}).get('check_on_startup', True):
                QTimer.singleShot(5000, self.check_for_updates)  # Check 5s after startup
            
            # Set up periodic update checks
            check_interval = self.config.get('updates', {}).get('check_interval_hours', 24)
            self.update_timer = QTimer()
            self.update_timer.timeout.connect(self.check_for_updates)
            self.update_timer.start(check_interval * 3600 * 1000)  # Convert hours to ms

        # Create context menu (after updater is ready)
        self.create_menu()
        
        # Double-click to show dashboard
        self.tray_icon.activated.connect(self.on_tray_activated)
        
        # Set up monitoring timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_connection)
        interval = self.config['monitoring']['polling_interval'] * 1000  # Convert to ms
        self.timer.start(interval)
        
        # Show tray icon
        self.tray_icon.show()
        
        # Perform initial check
        self.check_connection()
        
        # Reference to dashboard window (will be created on demand)
        self.dashboard = None
        
        # Close splash screen with fade out (3 seconds display)
        QTimer.singleShot(3000, self.close_splash)
        
        # Show dashboard on start if configured or forced via env variable
        show_dashboard = (
            self.config.get('ui', {}).get('show_dashboard_on_start', False) or
            os.environ.get('AMI_FORCE_DASHBOARD') == '1'
        )
        if show_dashboard:
            QTimer.singleShot(3500, self.show_dashboard)  # Delay 3.5s for splash to close
    
    def close_splash(self):
        """Close splash screen with animation"""
        if hasattr(self, 'splash'):
            self.splash.fade_out()
    
    def load_config(self) -> dict:
        """Load configuration from config.json"""
        # Get base path - works for both development and PyInstaller
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            base_path = Path(sys._MEIPASS)
        else:
            # Running as script
            base_path = Path(__file__).parent.parent

        self.base_path = base_path
        self.config_path = base_path / 'config.json'

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            QMessageBox.critical(None, "Error", f"Failed to load config.json: {e}\nPath: {self.config_path}")
            sys.exit(1)

    def save_config(self):
        """Persist current config to config.json"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            QMessageBox.critical(None, "Error", f"Failed to save config.json: {e}\nPath: {self.config_path}")

    def apply_config(self, new_config: dict):
        """Apply config changes to running components"""
        self.config = new_config
        # Apply to monitor
        mon = self.monitor
        mon.hosts = new_config['monitoring']['ping_hosts']
        mon.http_test_url = new_config['monitoring']['http_test_url']
        mon.timeout = new_config['monitoring']['timeout']
        mon.retry_count = new_config['monitoring']['retry_count']
        mon.enable_http_test = new_config['monitoring']['enable_http_test']
        mon.unstable_latency = new_config['thresholds']['unstable_latency_ms']
        mon.unstable_loss = new_config['thresholds']['unstable_loss_percent']

        # Timer interval
        try:
            interval = int(new_config['monitoring']['polling_interval']) * 1000
            self.timer.setInterval(interval)
        except Exception:
            pass

        # Notifier flags
        notif = self.notifier
        ncfg = new_config.get('notifications', {})
        notif.enabled = ncfg.get('enabled', notif.enabled)
        notif.silent_mode = ncfg.get('silent_mode', notif.silent_mode)
        notif.notify_on_disconnect = ncfg.get('notify_on_disconnect', notif.notify_on_disconnect)
        notif.notify_on_reconnect = ncfg.get('notify_on_reconnect', notif.notify_on_reconnect)
        notif.notify_on_unstable = ncfg.get('notify_on_unstable', notif.notify_on_unstable)

        # Logger: reinitialize so new size/path take effect immediately
        try:
            self.logger = EventLogger(new_config)
        except Exception:
            pass

    
    def create_menu(self):
        """Create system tray context menu"""
        menu = QMenu()
        
        # Status display (disabled, just for info)
        self.status_action = QAction("Status: Checking...", menu)
        self.status_action.setEnabled(False)
        menu.addAction(self.status_action)
        
        self.latency_action = QAction("Latency: --", menu)
        self.latency_action.setEnabled(False)
        menu.addAction(self.latency_action)
        
        self.uptime_action = QAction("Uptime: --", menu)
        self.uptime_action.setEnabled(False)
        menu.addAction(self.uptime_action)
        
        # ISP and VPN info
        self.isp_action = QAction("ISP: --", menu)
        self.isp_action.setEnabled(False)
        menu.addAction(self.isp_action)
        
        self.vpn_action = QAction("VPN: --", menu)
        self.vpn_action.setEnabled(False)
        menu.addAction(self.vpn_action)
        
        menu.addSeparator()
        
        # Test now
        test_action = QAction("🔄 Test Now", menu)
        test_action.triggered.connect(self.manual_test)
        menu.addAction(test_action)
        
        # Dashboard
        dashboard_action = QAction("📊 Dashboard", menu)
        dashboard_action.triggered.connect(self.show_dashboard)
        menu.addAction(dashboard_action)
        
        menu.addSeparator()
        
        # Settings
        settings_action = QAction("⚙️ Settings", menu)
        settings_action.triggered.connect(self.show_settings)
        menu.addAction(settings_action)
        
        # View Logs
        logs_action = QAction("📄 View Logs", menu)
        logs_action.triggered.connect(self.view_logs)
        menu.addAction(logs_action)
        
        # Test Notification
        test_notif_action = QAction("🔔 Test Notification", menu)
        test_notif_action.triggered.connect(self.test_notification)
        menu.addAction(test_notif_action)
        
        # Check for updates (if enabled)
        if getattr(self, 'updater', None):
            update_action = QAction("🔄 Check for Updates", menu)
            update_action.triggered.connect(lambda: self.check_for_updates(manual=True))
            menu.addAction(update_action)
        
        menu.addSeparator()
        
        # About
        about_action = QAction("ℹ️ About", menu)
        about_action.triggered.connect(self.show_about)
        menu.addAction(about_action)
        
        # Exit
        exit_action = QAction("❌ Exit", menu)
        exit_action.triggered.connect(self.exit_app)
        menu.addAction(exit_action)
        
        self.tray_icon.setContextMenu(menu)
    
    def test_notification(self):
        """Trigger a sample notification to validate settings"""
        try:
            self.notifier.notify_test()
        except Exception:
            try:
                self.tray_icon.showMessage(
                    "AMI",
                    "Test notification",
                    QSystemTrayIcon.MessageIcon.Information,
                    2000
                )
            except Exception:
                pass
    
    def create_icon(self, color: str) -> QIcon:
        """
        Create accessible tray icon: color + symbol for colorblind users

        Args:
            color: Color name ('green', 'yellow', 'red')

        Returns:
            QIcon object with both color and symbol indicators
        """
        # Create VERY large 512x512 for maximum visibility
        pixmap = QPixmap(512, 512)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Modern colors + symbols for accessibility
        if color == 'green':
            main_color = QColor(16, 185, 129)  # Green-500
            symbol = '✓'  # Checkmark for online
        elif color == 'yellow':
            main_color = QColor(245, 158, 11)  # Amber-500
            symbol = '!'  # Exclamation for unstable
        else:  # red
            main_color = QColor(239, 68, 68)   # Red-500
            symbol = '✕'  # X for offline

        # HUGE filled circle - almost fills entire space
        painter.setBrush(main_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(16, 16, 480, 480)

        # Add white symbol on top - VERY large font
        painter.setPen(QColor(255, 255, 255))
        font = painter.font()
        font.setPointSize(280)  # HUGE symbol
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(16, 16, 480, 480, Qt.AlignmentFlag.AlignCenter, symbol)

        painter.end()

        return QIcon(pixmap)
    
    def update_icon(self, status: str):
        """
        Update tray icon based on status
        
        Args:
            status: 'online', 'unstable', or 'offline'
        """
        if status == 'online':
            icon = self.create_icon('green')
        elif status == 'unstable':
            icon = self.create_icon('yellow')
        else:
            icon = self.create_icon('red')
        
        self.tray_icon.setIcon(icon)
    
    def update_tooltip(self, status):
        """
        Update tooltip with current status information
        
        Args:
            status: ConnectionStatus object
        """
        tooltip_parts = ["AMI - Active Monitor of Internet"]
        
        # Status
        status_emoji = {'online': '🟢', 'unstable': '🟡', 'offline': '🔴'}
        tooltip_parts.append(f"{status_emoji.get(status.status, '⚫')} {status.status.upper()}")
        
        # Latency
        if status.avg_latency_ms:
            tooltip_parts.append(f"Latency: {status.avg_latency_ms:.0f}ms")
        
        # Uptime
        uptime_pct = self.monitor.get_uptime_percentage()
        tooltip_parts.append(f"Uptime: {uptime_pct:.1f}%")
        
        # ISP and VPN
        try:
            if getattr(status, 'isp', None):
                isp_line = f"ISP: {status.isp}"
                if getattr(status, 'public_ip', None):
                    isp_line += f" ({status.public_ip})"
                tooltip_parts.append(isp_line)
            if getattr(status, 'vpn_connected', None) is not None:
                if status.vpn_connected:
                    vpnt = "VPN: ON"
                    if getattr(status, 'vpn_provider', None):
                        vpnt += f" [{status.vpn_provider}]"
                    tooltip_parts.append(vpnt)
                else:
                    tooltip_parts.append("VPN: OFF")
        except Exception:
            pass
        
        self.tray_icon.setToolTip("\n".join(tooltip_parts))
    
    def update_menu_info(self, status):
        """
        Update menu items with current status
        
        Args:
            status: ConnectionStatus object
        """
        # Status
        status_emoji = {'online': '🟢', 'unstable': '🟡', 'offline': '🔴'}
        self.status_action.setText(f"Status: {status_emoji.get(status.status, '⚫')} {status.status.upper()}")
        
        # Latency
        if status.avg_latency_ms:
            self.latency_action.setText(f"Latency: {status.avg_latency_ms:.0f}ms")
        else:
            self.latency_action.setText("Latency: N/A")
        
        # Uptime
        uptime_pct = self.monitor.get_uptime_percentage()
        uptime_dur = self.monitor.get_uptime_duration()
        self.uptime_action.setText(f"Uptime: {uptime_pct:.1f}% ({uptime_dur})")
        
        # ISP
        try:
            if getattr(status, 'isp', None):
                isp_line = f"ISP: {status.isp}"
                if getattr(status, 'public_ip', None):
                    isp_line += f" ({status.public_ip})"
                self.isp_action.setText(isp_line)
            else:
                self.isp_action.setText("ISP: N/A")
        except Exception:
            self.isp_action.setText("ISP: N/A")
        
        # VPN
        try:
            if getattr(status, 'vpn_connected', None) is True:
                text = "VPN: ON"
                if getattr(status, 'vpn_provider', None):
                    text += f" [{status.vpn_provider}]"
                self.vpn_action.setText(text)
            elif getattr(status, 'vpn_connected', None) is False:
                self.vpn_action.setText("VPN: OFF")
            else:
                self.vpn_action.setText("VPN: Unknown")
        except Exception:
            self.vpn_action.setText("VPN: Unknown")
    
    def check_connection(self):
        """Perform connection check in background thread"""
        # Create and start monitor thread
        self.monitor_thread = MonitorThread(self.monitor)
        self.monitor_thread.status_updated.connect(self.on_status_updated)
        self.monitor_thread.start()
    
    def on_status_updated(self, status):
        """
        Handle status update from monitor thread
        
        Args:
            status: ConnectionStatus object
        """
        self.current_status = status
        
        # Update UI
        self.update_icon(status.status)
        self.update_tooltip(status)
        self.update_menu_info(status)
        
        # Log event
        self.logger.log_status(status)
        
        # Show notification if status changed
        self.notifier.notify_status_change(status)
        
        # Update dashboard if open
        if self.dashboard and self.dashboard.isVisible():
            self.dashboard.update_data(status, self.monitor.get_statistics())
    
    def manual_test(self):
        """Perform manual connection test"""
        self.tray_icon.showMessage(
            "AMI",
            "Running connection test...",
            QSystemTrayIcon.MessageIcon.Information,
            2000
        )
        self.check_connection()
    
    def on_tray_activated(self, reason):
        """Handle tray icon activation (clicks)"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.toggle_dashboard()
    
    def toggle_dashboard(self):
        """Toggle dashboard visibility"""
        if self.dashboard and self.dashboard.isVisible():
            self.dashboard.hide()
        else:
            self.show_dashboard()
    
    def show_dashboard(self):
        """Show dashboard window"""
        if self.dashboard is None:
            from dashboard import EnterpriseDashboard
            self.dashboard = EnterpriseDashboard(self.config, self.monitor, self.tray_icon)
        
        if self.current_status:
            self.dashboard.update_data(self.current_status, self.monitor.get_statistics())
        
        self.dashboard.show()
        self.dashboard.raise_()
        self.dashboard.activateWindow()
    
    def show_settings(self):
        """Show settings dialog and apply changes"""
        dlg = SettingsDialog(self.config)
        if dlg.exec():
            new_cfg = dlg.get_config()
            self.apply_config(new_cfg)
            self.save_config()
            # Inform user
            try:
                self.tray_icon.showMessage(
                    "AMI Settings",
                    "Settings saved and applied",
                    QSystemTrayIcon.MessageIcon.Information,
                    2000
                )
            except Exception:
                pass
            # Trigger an immediate check using new settings
            self.check_connection()
    
    def view_logs(self):
        """Open log file"""
        log_file = self.config['logging']['log_file']
        if os.path.exists(log_file):
            # Open with default application
            import subprocess
            if sys.platform == 'win32':
                os.startfile(log_file)
            elif sys.platform == 'darwin':
                subprocess.call(['open', log_file])
            else:
                subprocess.call(['xdg-open', log_file])
        else:
            QMessageBox.information(None, "Logs", "No log file found yet.")
    
    def check_for_updates(self, manual: bool = False):
        """Check for available updates
        
        Args:
            manual: True when invoked by user from tray menu; shows toasts for results
        """
        if not self.updater:
            return
        
        print("[UPDATE] Checking for updates...")
        
        try:
            update_info = self.updater.check_for_updates()
            
            if update_info:
                print(f"[UPDATE] New version available: {update_info['version']}")
                
                # Check if update is mandatory
                can_postpone = self.updater.can_postpone()
                
                # Show update notification in tray
                if manual or self.config.get('updates', {}).get('notify_on_update', True):
                    message = f"Version {update_info['version']} is available!"
                    if not can_postpone:
                        message += " (Update required)"
                    # Use notifier for cross-platform delivery (macOS AppleScript fallback)
                    try:
                        self.notifier.notify_message("AMI Update Available", message, level='info', respect_enabled=True, play_sound=True)
                    except Exception:
                        pass
                
                # Show update dialog
                dlg = UpdateDialog(self.updater, update_info)
                dlg.exec()
            else:
                print("[UPDATE] No updates available")
                if manual:
                    try:
                        self.notifier.notify_message("AMI", "No updates available", level='info', respect_enabled=False, play_sound=False)
                    except Exception:
                        pass
        
        except Exception as e:
            print(f"[UPDATE] Error checking for updates: {e}")
            if manual:
                try:
                    self.notifier.notify_message("AMI", f"Update check failed: {e}", level='warning', respect_enabled=False, play_sound=False)
                except Exception:
                    pass
    
    def show_about(self):
        """Show about dialog"""
        about_text = """
        <h2>AMI - Active Monitor of Internet</h2>
        <p><b>Version:</b> {version}</p>
        <p><i>"Sai se sei davvero online."</i></p>
        <br>
        <p>AMI monitors your internet connection in real-time,<br>
        distinguishing between local network and actual<br>
        internet connectivity.</p>
        <br>
        <p><b>Features:</b></p>
        <ul>
        <li>Real-time connection monitoring</li>
        <li>System tray integration (Windows & macOS)</li>
        <li>Minimize to tray support</li>
        <li>Multi-host ping testing</li>
        <li>Connection statistics and graphs</li>
        <li>Event logging & notifications</li>
        <li>Automatic OTA updates</li>
        </ul>
        <br>
        <p>© 2025 <b>CiaoIM™</b> di Daniel Giovannetti</p>
        <p><a href="https://ciaoim.tech">ciaoim.tech</a></p>
        <p style="font-size: 9px; color: #666;"><i>Crafted logic. Measured force. Front-end vision,<br>
        compiled systems, and hardcoded ethics.</i></p>
        <p style="font-size: 8px; color: #888;"><i>Intuizione colta insieme a Giovanni Calvario in aliscafo<br>
        per il 40° Convegno di Capri dei Giovani Imprenditori</i></p>
        """.format(version=self.config['app']['version'])
        
        msg = QMessageBox()
        msg.setWindowTitle("About AMI")
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setText(about_text)
        msg.exec()
    
    def exit_app(self):
        """Exit the application"""
        self.timer.stop()
        self.api_server.stop()
        self.tray_icon.hide()
        QApplication.quit()
    
    def run(self):
        """Run the application"""
        return self.app.exec()


def main():
    """Main entry point"""
    # Set application info
    QApplication.setApplicationName("AMI")
    QApplication.setApplicationDisplayName("AMI - Active Monitor of Internet")
    QApplication.setOrganizationName("AMI Project")
    
    # Create and run app
    app = SystemTrayApp()
    sys.exit(app.run())


if __name__ == '__main__':
    main()
