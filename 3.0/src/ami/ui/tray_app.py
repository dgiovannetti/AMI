"""
AMI 3.0 - System tray application: menu, monitoring timer, lazy dashboard.
"""

import html
import os
import sys
import threading
from pathlib import Path

from PyQt6.QtCore import QObject, QTimer, Qt, QThread, pyqtSignal
from PyQt6.QtGui import QAction, QColor, QCursor, QIcon, QImage, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QMenu,
    QMessageBox,
    QSystemTrayIcon,
)

from ami import __version__
from ami.core.config import get_config_path_for_ui, load_config, save_config
from ami.core.paths import get_base_path, get_user_data_dir
from ami.services.api_server import APIServer
from ami.services.logger import EventLogger
from ami.services.network_monitor import NetworkMonitor
from ami.services.notifier import Notifier
from ami.services.speed_test import run_speed_test
from ami.services.updater import UpdateManager
from ami.ui.compact_status import CompactStatusWindow
from ami.ui.settings_dialog import SettingsDialog
from ami.ui.splash_screen import UltraModernSplashScreen
from ami.ui.update_dialog import UpdateDialog


def _is_pyinstaller_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def _tray_debug(msg: str) -> None:
    if os.environ.get("AMI_DEBUG_TRAY", "").strip() in ("1", "true", "yes"):
        print(f"[AMI tray] {msg}", file=sys.stderr, flush=True)


def _effective_compact_status_window(config: dict) -> bool:
    """Default: off — menu bar + Dock; compact window only if explicitly enabled."""
    v = config.get("ui", {}).get("compact_status_window")
    if v is None:
        return False
    return bool(v)


class _SpeedTestDoneBridge(QObject):
    """Emit from background thread; slot runs on GUI thread (QueuedConnection)."""

    finished = pyqtSignal()


class MonitorThread(QThread):
    status_updated = pyqtSignal(object)

    def __init__(self, monitor: NetworkMonitor):
        super().__init__()
        self.monitor = monitor
        self.running = True

    def run(self) -> None:
        if self.running:
            status = self.monitor.check_connection()
            self.status_updated.emit(status)

    def stop(self) -> None:
        self.running = False


class SystemTrayApp:
    def __init__(self) -> None:
        try:
            QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
        except (AttributeError, TypeError):
            pass
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        # Non collegare applicationStateChanged qui: durante __init__ processEvents() può
        # emettere ApplicationActive; aprire finestre da quello stack su macOS → qFatal/SIGABRT (Qt 6 + Cocoa).
        self._startup_complete = False
        self.config = self.load_config()
        app_version = self.config.get("app", {}).get("version", __version__)
        use_compact = _effective_compact_status_window(self.config)
        # Cache icone tray macOS (template da PNG per path)
        self._macos_tray_icon_cache: dict[str, QIcon] = {}

        self.updater = None
        self.update_timer = None
        self._update_check_busy = False
        if self.config.get("updates", {}).get("enabled", True):
            github_repo = self.config.get("updates", {}).get("github_repo", "dgiovannetti/AMI")
            max_postpone = self.config.get("updates", {}).get("max_postponements", 3)
            self.updater = UpdateManager(
                current_version=app_version,
                github_repo=github_repo,
                max_postponements=max_postpone,
            )
            if self.config.get("updates", {}).get("check_on_startup", True):
                QTimer.singleShot(5000, lambda: self.check_for_updates(False))
            check_interval = self.config.get("updates", {}).get("check_interval_hours", 24)
            self.update_timer = QTimer()
            self.update_timer.timeout.connect(lambda: self.check_for_updates(False))
            self.update_timer.start(check_interval * 3600 * 1000)

        # Tray: su macOS il primo show sincrono in __init__ può dare geometry altezza 0 (invisibile).
        self.tray_icon = QSystemTrayIcon(self.app)
        self._apply_tray_icon_for_status("offline")
        self.tray_icon.setToolTip("AMI - Starting...")
        self.create_menu()
        self.tray_icon.activated.connect(self.on_tray_activated)
        if sys.platform == "darwin":
            QTimer.singleShot(0, self._first_show_macos_tray)
        else:
            self.tray_icon.show()
            self.app.processEvents()
        _tray_debug(
            f"frozen={_is_pyinstaller_frozen()} tray_available={QSystemTrayIcon.isSystemTrayAvailable()} "
            f"icon_null={self.tray_icon.icon().isNull()}"
        )
        if sys.platform == "darwin":
            for ms in (50, 150, 400, 1000, 2500):
                QTimer.singleShot(ms, self._reassert_macos_tray)
        if sys.platform == "darwin" and not QSystemTrayIcon.isSystemTrayAvailable():
            QMessageBox.warning(
                None,
                "AMI",
                "L’area tray della menu bar non risulta disponibile.\n\n"
                "• Controlla le icone nascoste dietro «>>» in alto a destra.\n"
                "• Impostazioni → Controllo Centro → Menu bar.\n"
                "• Resta la finestra compatta «AMI» se abilitata.",
            )

        # Splash solo se la finestra compatta è disattivata (evita doppia UI all’avvio).
        self.splash = None
        self._splash_closed = True
        self._splash_closable = False
        if not use_compact:
            self._splash_closed = False
            self.splash = UltraModernSplashScreen(version=app_version)
            self.splash.show()
            self.splash.showMessage("Loading configuration...")
            self.app.processEvents()

        def splash_msg(msg: str) -> None:
            if self.splash:
                self.splash.showMessage(msg)

        splash_msg("Initializing network monitor...")
        self.app.processEvents()
        self.monitor = NetworkMonitor(self.config)
        splash_msg("Starting logger...")
        self.app.processEvents()
        self.logger = EventLogger(self.config)
        splash_msg("Preparing notifications...")
        self.app.processEvents()
        self.notifier = Notifier(self.config)
        self.notifier.tray_icon = self.tray_icon
        splash_msg("Starting API server...")
        self.app.processEvents()
        self.api_server = APIServer(self.config, self.monitor)
        self.current_status = None
        self.monitor_thread = None
        splash_msg("Finalizing...")
        self.app.processEvents()
        self.api_server.start()
        self.update_icon("offline")
        interval = self.config["monitoring"]["polling_interval"] * 1000
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_connection)
        self.timer.start(interval)
        self.compact_status = None
        if use_compact:
            self.compact_status = CompactStatusWindow(self.config, self.monitor, self.tray_icon)
            self.compact_status.show()
        self.check_connection()
        self.dashboard = None
        self._speed_test_busy = False
        self._speed_test_bridge = _SpeedTestDoneBridge(self.app)
        self._speed_test_bridge.finished.connect(self._on_speed_test_finished)
        self.speed_test_timer = None
        st_cfg = self.config.get("speed_test", {})
        if st_cfg.get("enabled", False):
            interval_ms = int(st_cfg.get("interval_minutes", 30)) * 60 * 1000
            self.speed_test_timer = QTimer()
            self.speed_test_timer.timeout.connect(self._run_speed_test)
            self.speed_test_timer.start(interval_ms)
            QTimer.singleShot(15000, self._run_speed_test)
        if self.splash:
            self._splash_closable = False
            QTimer.singleShot(1500, self._allow_splash_close)
            QTimer.singleShot(3000, self.close_splash)
        if self.config.get("ui", {}).get("show_dashboard_on_start", False) or os.environ.get("AMI_FORCE_DASHBOARD") == "1":
            QTimer.singleShot(2500, self.show_dashboard)

        self._startup_complete = True
        if sys.platform == "darwin":
            self.app.applicationStateChanged.connect(self._on_application_state_changed)

    def _allow_splash_close(self) -> None:
        self._splash_closable = True
        if self.current_status and not self._splash_closed:
            self.close_splash()

    def close_splash(self) -> None:
        if self._splash_closed:
            return
        self._splash_closed = True
        if self.splash is not None:
            self.splash.fade_out()

    def _main_ui_is_visible(self) -> bool:
        """True se c’è almeno una finestra principale visibile (esclusi menu popup)."""
        for w in self.app.topLevelWidgets():
            if not w.isVisible():
                continue
            if isinstance(w, QMenu):
                continue
            if self.splash is not None and w is self.splash:
                return True
            return True
        return False

    def _on_application_state_changed(self, state: Qt.ApplicationState) -> None:
        """Dock: differito — mai show()/dashboard dallo stack di setApplicationState (crash Qt macOS)."""
        if sys.platform != "darwin":
            return
        if state != Qt.ApplicationState.ApplicationActive:
            return
        QTimer.singleShot(0, self._deferred_application_active_from_dock)

    def _deferred_application_active_from_dock(self) -> None:
        if not getattr(self, "_startup_complete", False):
            return
        if self.app.applicationState() != Qt.ApplicationState.ApplicationActive:
            return
        if self._main_ui_is_visible():
            return
        if _effective_compact_status_window(self.config) and getattr(self, "compact_status", None):
            self.compact_status.show()
            self.compact_status.raise_()
            self.compact_status.activateWindow()
            return
        self.show_dashboard()

    def show_compact_status_window(self) -> None:
        if not _effective_compact_status_window(self.config):
            self.tray_icon.showMessage(
                "AMI",
                "Enable “Compact status window” in Settings → UI, or use Dashboard from the menu.",
                QSystemTrayIcon.MessageIcon.Information,
                4000,
            )
            return
        if self.compact_status is None:
            self.compact_status = CompactStatusWindow(self.config, self.monitor, self.tray_icon)
            if self.current_status:
                self.compact_status.update_status(self.current_status)
        self.compact_status.show()
        self.compact_status.raise_()
        self.compact_status.activateWindow()

    def load_config(self) -> dict:
        self.base_path = get_base_path()
        self.config_path = get_config_path_for_ui()
        try:
            return load_config()
        except Exception as e:
            QMessageBox.critical(None, "Error", f"Failed to load config: {e}\nPath: {self.config_path}")
            sys.exit(1)

    def save_config(self) -> None:
        try:
            save_config(self.config)
        except Exception as e:
            QMessageBox.critical(None, "Error", f"Failed to save config: {e}\nPath: {self.config_path}")

    def apply_config(self, new_config: dict) -> None:
        self.config = new_config
        mon = self.monitor
        mon.hosts = new_config["monitoring"]["ping_hosts"]
        mon.http_test_url = new_config["monitoring"].get("http_test_url", mon.http_test_url)
        mon.http_test_urls = new_config["monitoring"].get("http_test_urls") or []
        mon.timeout = new_config["monitoring"]["timeout"]
        mon.retry_count = new_config["monitoring"].get("retry_count", 2)
        mon.enable_http_test = new_config["monitoring"].get("enable_http_test", True)
        mon.internal_test_mode = new_config["monitoring"].get("internal_test_mode", False)
        mon.unstable_latency = new_config["thresholds"]["unstable_latency_ms"]
        mon.unstable_loss = new_config["thresholds"]["unstable_loss_percent"]
        try:
            self.timer.setInterval(int(new_config["monitoring"]["polling_interval"]) * 1000)
        except Exception:
            pass
        n = self.notifier
        nc = new_config.get("notifications", {})
        n.enabled = nc.get("enabled", n.enabled)
        n.silent_mode = nc.get("silent_mode", n.silent_mode)
        n.notify_on_disconnect = nc.get("notify_on_disconnect", n.notify_on_disconnect)
        n.notify_on_reconnect = nc.get("notify_on_reconnect", n.notify_on_reconnect)
        n.notify_on_unstable = nc.get("notify_on_unstable", n.notify_on_unstable)
        try:
            self.logger = EventLogger(new_config)
        except Exception:
            pass
        self.api_server.stop()
        self.api_server.enabled = new_config["api"].get("enabled", False)
        self.api_server.port = new_config["api"].get("port", 7212)
        self.api_server.auth_token = (new_config["api"].get("auth_token") or "").strip()
        self.api_server.start()
        use_compact = _effective_compact_status_window(new_config)
        if use_compact and not getattr(self, "compact_status", None):
            self.compact_status = CompactStatusWindow(self.config, self.monitor, self.tray_icon)
            self.compact_status.show()
            if self.current_status:
                self.compact_status.update_status(self.current_status)
        elif not use_compact and getattr(self, "compact_status", None):
            self.compact_status.close()
            self.compact_status = None
        if getattr(self, "speed_test_timer", None):
            self.speed_test_timer.stop()
        st_cfg = new_config.get("speed_test", {})
        if st_cfg.get("enabled", False):
            interval_ms = int(st_cfg.get("interval_minutes", 30)) * 60 * 1000
            self.speed_test_timer = QTimer()
            self.speed_test_timer.timeout.connect(self._run_speed_test)
            self.speed_test_timer.start(interval_ms)
        else:
            self.speed_test_timer = None

    def create_menu(self) -> None:
        self._tray_menu = QMenu()
        menu = self._tray_menu
        self.status_action = QAction("Status: Checking...", menu)
        self.status_action.setEnabled(False)
        menu.addAction(self.status_action)
        self.latency_action = QAction("Latency: --", menu)
        self.latency_action.setEnabled(False)
        menu.addAction(self.latency_action)
        self.uptime_action = QAction("Uptime: --", menu)
        self.uptime_action.setEnabled(False)
        menu.addAction(self.uptime_action)
        self.isp_action = QAction("ISP: --", menu)
        self.isp_action.setEnabled(False)
        menu.addAction(self.isp_action)
        self.vpn_action = QAction("VPN: --", menu)
        self.vpn_action.setEnabled(False)
        menu.addAction(self.vpn_action)
        self.speed_action = QAction("Speed: --", menu)
        self.speed_action.setEnabled(False)
        menu.addAction(self.speed_action)
        menu.addSeparator()
        menu.addAction("📌 Show status window").triggered.connect(self.show_compact_status_window)
        menu.addAction("🔄 Test Now").triggered.connect(self.manual_test)
        menu.addAction("⚡ Speed test now").triggered.connect(self._speed_test_now)
        menu.addAction("📊 Dashboard").triggered.connect(self.show_dashboard)
        menu.addSeparator()
        menu.addAction("⚙️ Settings").triggered.connect(self.show_settings)
        menu.addAction("📄 View Logs").triggered.connect(self.view_logs)
        menu.addAction("🔔 Test Notification").triggered.connect(self.test_notification)
        if self.updater:
            menu.addAction("🔄 Check for Updates").triggered.connect(lambda: self.check_for_updates(True))
        menu.addSeparator()
        menu.addAction("ℹ️ About").triggered.connect(self.show_about)
        menu.addAction("❌ Exit").triggered.connect(self.exit_app)
        self.tray_icon.setContextMenu(menu)

    def _apply_tray_icon_for_status(self, status: str) -> None:
        """Icona tray prima dell’init pesante (menu bar macOS)."""
        path = get_base_path() / "resources" / {
            "online": "status_green.png",
            "unstable": "status_yellow.png",
        }.get(status, "status_red.png")
        self.tray_icon.setIcon(self._resolve_tray_icon(path, status))

    def _resolve_tray_icon(self, path: Path, status: str) -> QIcon:
        color_key = "green" if status == "online" else "yellow" if status == "unstable" else "red"
        if sys.platform == "darwin":
            return self._macos_tray_icon_from_status_png(path, color_key)
        if path.exists():
            return QIcon(str(path))
        return self._create_icon(color_key)

    def _macos_tray_icon_from_status_png(self, path: Path, color_key: str) -> QIcon:
        """
        Menu bar macOS: **PNG ufficiali a colori** (`status_green|yellow|red.png` con ✓ ! ✕).
        Con `get_base_path()` corretto (cartella `3.0/`) le risorse si trovano sempre.
        Opzionale `AMI_TRAY_TEMPLATE=1`: maschera monocromatica (solo se l’icona a colori non compare).
        """
        if not path.is_file():
            _tray_debug(f"macOS tray: missing {path}")
            return self._create_icon(color_key)
        fp = os.fspath(path.resolve())

        if fp in self._macos_tray_icon_cache:
            return self._macos_tray_icon_cache[fp]

        if os.environ.get("AMI_TRAY_TEMPLATE", "").strip() in ("1", "true", "yes"):
            icon_t = self._build_macos_template_icon_from_png(fp)
            if icon_t is not None and not icon_t.isNull():
                self._macos_tray_icon_cache[fp] = icon_t
                return icon_t

        icon = self._macos_tray_colored_pixmaps_from_png(fp, path.name, color_key)
        self._macos_tray_icon_cache[fp] = icon
        return icon

    def _build_macos_template_icon_from_png(self, fp: str) -> QIcon | None:
        """Solo con AMI_TRAY_TEMPLATE=1 — fallback se il tray non disegna le PNG a colori."""
        img = QImage(fp)
        if img.isNull():
            return None
        max_side = 128
        if max(img.width(), img.height()) > max_side:
            img = img.scaled(
                max_side,
                max_side,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        img = img.convertToFormat(QImage.Format.Format_ARGB32)
        w, h = img.width(), img.height()
        out = QImage(w, h, QImage.Format.Format_ARGB32)
        out.fill(0)
        for y in range(h):
            for x in range(w):
                c = img.pixelColor(x, y)
                a = c.alpha()
                if a <= 0:
                    continue
                out.setPixelColor(x, y, QColor(0, 0, 0, a))
        icon = QIcon()
        for s in (16, 18, 22, 32, 44):
            sc = out.scaled(
                s,
                s,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            pm = QPixmap.fromImage(sc)
            if not pm.isNull():
                icon.addPixmap(pm, QIcon.Mode.Normal, QIcon.State.Off)
        if icon.isNull():
            return None
        try:
            icon.setIsMask(True)
        except (AttributeError, TypeError):
            pass
        return icon

    def _macos_tray_colored_pixmaps_from_png(self, fp: str, name: str, color_key: str) -> QIcon:
        """PNG ufficiali a colori: più tagli 1x e 2x (@2x) per menu bar nitida."""
        img = QImage(fp)
        if img.isNull():
            return self._create_icon(color_key)
        img = img.convertToFormat(QImage.Format.Format_ARGB32)
        icon = QIcon()
        for side in (18, 22, 32, 44):
            scaled = img.scaled(
                side,
                side,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            pm = QPixmap.fromImage(scaled)
            if not pm.isNull():
                icon.addPixmap(pm, QIcon.Mode.Normal, QIcon.State.Off)
        for logical in (22, 32):
            px = logical * 2
            scaled = img.scaled(
                px,
                px,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            pm = QPixmap.fromImage(scaled)
            if not pm.isNull():
                pm.setDevicePixelRatio(2.0)
                icon.addPixmap(pm, QIcon.Mode.Normal, QIcon.State.Off)
        if not icon.isNull():
            _tray_debug(f"macOS tray: colored {name}")
            return icon
        return self._create_icon(color_key)

    def _first_show_macos_tray(self) -> None:
        try:
            self._apply_tray_icon_for_status("offline")
            self.tray_icon.setVisible(True)
            self.tray_icon.show()
            self.app.processEvents()
            g = self.tray_icon.geometry()
            _tray_debug(
                f"first_show macOS geometry={g.x()},{g.y()},{g.width()}x{g.height()} "
                f"icon_null={self.tray_icon.icon().isNull()}"
            )
        except Exception:
            pass

    def _reassert_macos_tray(self) -> None:
        try:
            st = getattr(self, "current_status", None)
            key = st.status if st and getattr(st, "status", None) else "offline"
            self._apply_tray_icon_for_status(key)
            self.tray_icon.setVisible(True)
            self.tray_icon.show()
            self.app.processEvents()
            g = self.tray_icon.geometry()
            _tray_debug(
                f"reassert status={key} icon_null={self.tray_icon.icon().isNull()} "
                f"geometry={g.x()},{g.y()},{g.width()}x{g.height()}"
            )
        except Exception:
            pass

    def _create_icon(self, color: str) -> QIcon:
        side = 512
        margin = 16
        ellipse = side - 2 * margin
        sym_pt = 280
        pixmap = QPixmap(side, side)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if color == "green":
            main_color = QColor(16, 185, 129)
            symbol = "✓"
        elif color == "yellow":
            main_color = QColor(245, 158, 11)
            symbol = "!"
        else:
            main_color = QColor(239, 68, 68)
            symbol = "✕"
        painter.setBrush(main_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(margin, margin, ellipse, ellipse)
        painter.setPen(QColor(255, 255, 255))
        font = painter.font()
        font.setPointSize(sym_pt)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(0, 0, side, side, Qt.AlignmentFlag.AlignCenter, symbol)
        painter.end()
        return QIcon(pixmap)

    def update_icon(self, status: str) -> None:
        path = get_base_path() / "resources" / {"online": "status_green.png", "unstable": "status_yellow.png"}.get(status, "status_red.png")
        self.tray_icon.setIcon(self._resolve_tray_icon(path, status))

    def update_tooltip(self, status) -> None:
        parts = ["AMI - Active Monitor of Internet", f"{'🟢' if status.status == 'online' else '🟡' if status.status == 'unstable' else '🔴'} {status.status.upper()}"]
        if status.avg_latency_ms:
            parts.append(f"Latency: {status.avg_latency_ms:.0f}ms")
        parts.append(f"Uptime: {self.monitor.get_uptime_percentage():.1f}%")
        if getattr(status, "isp", None):
            parts.append(f"ISP: {status.isp}" + (f" ({status.public_ip})" if getattr(status, "public_ip", None) else ""))
        if getattr(status, "vpn_connected", None) is not None:
            parts.append("VPN: ON" if status.vpn_connected else "VPN: OFF")
        speed_mbps = getattr(status, "speed_mbps", None)
        speed_tier = getattr(status, "speed_tier", None)
        if speed_tier is not None and speed_mbps is not None:
            if speed_mbps >= 1000:
                parts.append(f"Speed: {speed_mbps / 1000:.2f} Gbps ({speed_tier.capitalize()})")
            else:
                parts.append(f"Speed: {speed_mbps:.0f} Mbps ({speed_tier.capitalize()})")
        else:
            parts.append("Speed: —")
        self.tray_icon.setToolTip("\n".join(parts))

    def update_menu_info(self, status) -> None:
        self.status_action.setText(f"{'🟢' if status.status == 'online' else '🟡' if status.status == 'unstable' else '🔴'} {status.status.upper()}")
        self.latency_action.setText(f"Latency: {status.avg_latency_ms:.0f}ms" if status.avg_latency_ms else "Latency: N/A")
        self.uptime_action.setText(f"Uptime: {self.monitor.get_uptime_percentage():.1f}% ({self.monitor.get_uptime_duration()})")
        try:
            self.isp_action.setText(f"ISP: {status.isp} ({status.public_ip})" if getattr(status, "isp", None) else "ISP: N/A")
        except Exception:
            self.isp_action.setText("ISP: N/A")
        try:
            self.vpn_action.setText("VPN: ON" + (f" [{status.vpn_provider}]" if getattr(status, "vpn_provider", None) else "") if getattr(status, "vpn_connected", None) else "VPN: OFF")
        except Exception:
            self.vpn_action.setText("VPN: Unknown")
        speed_mbps = getattr(status, "speed_mbps", None)
        speed_tier = getattr(status, "speed_tier", None)
        if speed_tier is not None and speed_mbps is not None:
            if speed_mbps >= 1000:
                self.speed_action.setText(f"Speed: {speed_mbps / 1000:.2f} Gbps ({speed_tier.capitalize()})")
            else:
                self.speed_action.setText(f"Speed: {speed_mbps:.0f} Mbps ({speed_tier.capitalize()})")
        else:
            self.speed_action.setText("Speed: —")

    def check_connection(self) -> None:
        if self.monitor_thread is not None:
            try:
                if self.monitor_thread.isRunning():
                    return
            except RuntimeError:
                self.monitor_thread = None
        self.monitor_thread = MonitorThread(self.monitor)
        self.monitor_thread.status_updated.connect(self.on_status_updated)
        self.monitor_thread.finished.connect(self.on_monitor_thread_finished)
        self.monitor_thread.start()

    def on_monitor_thread_finished(self) -> None:
        try:
            thread = self.sender()
        except Exception:
            thread = None
        self.monitor_thread = None
        if thread is not None:
            try:
                thread.deleteLater()
            except RuntimeError:
                pass

    def on_status_updated(self, status) -> None:
        self.current_status = status
        if getattr(self, "_splash_closable", False) and not getattr(self, "_splash_closed", True):
            self.close_splash()
        self.update_icon(status.status)
        self.update_tooltip(status)
        self.update_menu_info(status)
        self.logger.log_status(status)
        self.notifier.notify_status_change(status)
        if self.dashboard and self.dashboard.isVisible():
            self.dashboard.update_data(status, self.monitor.get_statistics())
        if self.compact_status:
            self.compact_status.update_status(status)

    def _on_speed_test_finished(self) -> None:
        self._speed_test_busy = False
        self.check_connection()

    def _speed_test_now(self) -> None:
        st_cfg = self.config.get("speed_test", {})
        if not st_cfg.get("enabled", False):
            self.tray_icon.showMessage(
                "AMI",
                "Speed test is disabled in Settings.",
                QSystemTrayIcon.MessageIcon.Warning,
                2500,
            )
            return
        self.tray_icon.showMessage(
            "AMI",
            "Running download speed test…",
            QSystemTrayIcon.MessageIcon.Information,
            2000,
        )
        self._run_speed_test()

    def _run_speed_test(self) -> None:
        st_cfg = self.config.get("speed_test", {})
        if not st_cfg.get("enabled", False):
            return
        if self.current_status is None or self.current_status.status == "offline":
            return
        url = st_cfg.get("test_url", "").strip()
        if not url:
            return
        if self._speed_test_busy:
            return
        self._speed_test_busy = True
        size_mb = float(st_cfg.get("download_size_mb", 10))
        warmup_mb = float(st_cfg.get("warmup_mb", 2))
        timeout = int(st_cfg.get("timeout_seconds", 30))
        low = float(st_cfg.get("tier_low_mbps", 100))
        high = float(st_cfg.get("tier_high_mbps", 1000))
        monitor = self.monitor
        bridge = self._speed_test_bridge

        def run() -> None:
            try:
                mbps, tier = run_speed_test(url, size_mb, timeout, low, high, warmup_mb=warmup_mb)
                monitor.set_speed_result(mbps, tier)
            finally:
                bridge.finished.emit()

        threading.Thread(target=run, daemon=True).start()

    def manual_test(self) -> None:
        self.tray_icon.showMessage("AMI", "Running connection test...", QSystemTrayIcon.MessageIcon.Information, 2000)
        self.check_connection()

    def on_tray_activated(self, reason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            if self.dashboard and self.dashboard.isVisible():
                self.dashboard.hide()
            else:
                self.show_dashboard()
            return
        # macOS: non chiamare popup() qui — `setContextMenu` fa già aprire il menu al click;
        # un secondo popup su Trigger causava due menu sovrapposti.

    def show_dashboard(self) -> None:
        if self.dashboard is None:
            from ami.ui.dashboard import EnterpriseDashboard
            self.dashboard = EnterpriseDashboard(self.config, self.monitor, self.tray_icon)
        if self.current_status:
            self.dashboard.update_data(self.current_status, self.monitor.get_statistics())
        self.dashboard.show()
        self.dashboard.raise_()
        self.dashboard.activateWindow()

    def show_settings(self) -> None:
        dlg = SettingsDialog(self.config)
        if dlg.exec():
            new_cfg = dlg.get_config()
            self.apply_config(new_cfg)
            self.save_config()
            self.tray_icon.showMessage("AMI Settings", "Settings saved and applied", QSystemTrayIcon.MessageIcon.Information, 2000)
            self.check_connection()

    def view_logs(self) -> None:
        log_path = get_user_data_dir() / self.config["logging"]["log_file"]
        if log_path.exists():
            if sys.platform == "win32":
                os.startfile(str(log_path))
            elif sys.platform == "darwin":
                import subprocess
                subprocess.call(["open", str(log_path)])
            else:
                import subprocess
                subprocess.call(["xdg-open", str(log_path)])
        else:
            QMessageBox.information(None, "Logs", "No log file found yet.")

    def test_notification(self) -> None:
        try:
            self.notifier.notify_test()
        except Exception:
            self.tray_icon.showMessage("AMI", "Test notification", QSystemTrayIcon.MessageIcon.Information, 2000)

    def check_for_updates(self, manual: bool = False) -> None:
        if not self.updater:
            return
        if self._update_check_busy:
            if manual:
                self.notifier.notify_message(
                    "AMI",
                    "Controllo aggiornamenti già in corso.",
                    level="info",
                    respect_enabled=False,
                    play_sound=False,
                )
            return
        self._update_check_busy = True
        try:
            update_info = self.updater.check_for_updates()
            if update_info:
                can_postpone = self.updater.can_postpone()
                if manual or self.config.get("updates", {}).get("notify_on_update", True):
                    self.notifier.notify_message("AMI Update Available", f"Version {update_info['version']} is available!" + (" (Update required)" if not can_postpone else ""), respect_enabled=True, play_sound=True)
                dlg = UpdateDialog(self.updater, update_info)
                dlg.exec()
            elif manual:
                self.notifier.notify_message("AMI", "No updates available", respect_enabled=False, play_sound=False)
        except Exception as e:
            if manual:
                self.notifier.notify_message("AMI", f"Update check failed: {e}", level="warning", respect_enabled=False, play_sound=False)
        finally:
            self._update_check_busy = False

    def show_about(self) -> None:
        v = html.escape(self.config["app"].get("version", __version__))
        app = self.config.get("app", {})
        web = (app.get("website") or "https://ciaoim.tech/projects/ami").strip()
        if web and not web.startswith(("http://", "https://")):
            web = "https://" + web.lstrip("/")
        web_esc = html.escape(web, quote=True)
        copy_line = html.escape(app.get("copyright", "© 2025–2026 CiaoIM™ by Daniel Giovannetti"))
        about_text = f"""
        <h2>AMI - Active Monitor of Internet</h2>
        <p><b>Version:</b> {v}</p>
        <p><i>"Sai se sei davvero online."</i></p>
        <br>
        <p>{copy_line}</p>
        <p><a href="{web_esc}">Sito — ciaoim.tech</a>
        &nbsp;·&nbsp;
        <a href="https://github.com/dgiovannetti/AMI">GitHub</a></p>
        """
        msg = QMessageBox()
        msg.setWindowTitle("About AMI")
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setText(about_text)
        msg.exec()

    def exit_app(self) -> None:
        self.timer.stop()
        if getattr(self, "update_timer", None):
            self.update_timer.stop()
        if getattr(self, "speed_test_timer", None):
            self.speed_test_timer.stop()
        if self.monitor_thread is not None:
            try:
                if self.monitor_thread.isRunning():
                    self.monitor_thread.wait(3000)
            except RuntimeError:
                pass
            self.monitor_thread = None
        self.api_server.stop()
        self.tray_icon.hide()
        if getattr(self, "compact_status", None):
            self.compact_status.close()
        self.app.quit()

    def run(self) -> int:
        return self.app.exec()


def main() -> None:
    QApplication.setApplicationName("AMI")
    QApplication.setApplicationDisplayName("AMI - Active Monitor of Internet")
    QApplication.setOrganizationName("AMI Project")
    app = SystemTrayApp()
    sys.exit(app.run())
