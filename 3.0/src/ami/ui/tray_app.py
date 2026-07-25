"""
AMI 3.0 - System tray application: menu, monitoring timer, lazy dashboard.
"""

import html
import os
import sys
import threading
import time
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
from ami.services.startup import sync_autostart
from ami.services.updater import UpdateManager
from ami.ui.compact_status import CompactStatusWindow
from ami.ui.qt_safe import install_exception_handlers, safe_slot
from ami.ui.settings_dialog import SettingsDialog
from ami.ui.splash_screen import UltraModernSplashScreen
from ami.ui.update_dialog import UpdateDialog


def _is_pyinstaller_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def _tray_debug(msg: str) -> None:
    if os.environ.get("AMI_DEBUG_TRAY", "").strip() in ("1", "true", "yes"):
        print(f"[AMI tray] {msg}", file=sys.stderr, flush=True)


def _process_init_events(app: QApplication) -> None:
    """Process pending events during init without handling user input (macOS crash guard)."""
    try:
        from PyQt6.QtCore import QEventLoop

        app.processEvents(QEventLoop.ProcessEventsFlag.ExcludeUserInputEvents)
    except (AttributeError, TypeError, ImportError):
        app.processEvents()


def _log_ami_quit() -> None:
    try:
        from datetime import datetime, timezone

        with open("/tmp/ami-quit.log", "a", encoding="utf-8") as f:
            f.write(f"{datetime.now(timezone.utc).isoformat()} aboutToQuit\n")
    except OSError:
        pass


def _apply_macos_dock_presence(app: QApplication) -> None:
    """
    Dock su macOS: app solo tray + splash → senza policy Regular l’icona Dock sparisce
    appena chiude lo splash (macOS tratta il processo come accessory/agent).
    Da sorgente imposta anche setWindowIcon (al posto dell’icona Python).
    """
    try:
        from AppKit import NSApplication, NSApplicationActivationPolicyRegular

        ns = NSApplication.sharedApplication()
        ns.setActivationPolicy_(NSApplicationActivationPolicyRegular)
        _tray_debug("macOS Dock: NSApplicationActivationPolicyRegular")
    except Exception as exc:
        _tray_debug(f"macOS Dock policy skipped: {exc}")

    res = get_base_path() / "resources"
    for name in ("ami.png", "ami.icns"):
        p = res / name
        if not p.is_file():
            continue
        ic = QIcon(str(p))
        if ic.isNull():
            continue
        app.setWindowIcon(ic)
        _tray_debug(f"macOS Dock: setWindowIcon from resources/{name}")
        return


def _effective_compact_status_window(config: dict) -> bool:
    """Rispetta config; override con AMI_FORCE_COMPACT / AMI_NO_COMPACT."""
    if os.environ.get("AMI_FORCE_COMPACT", "").strip() in ("1", "true", "yes"):
        return True
    if os.environ.get("AMI_NO_COMPACT", "").strip() in ("1", "true", "yes"):
        return False
    v = config.get("ui", {}).get("compact_status_window")
    if v is None:
        return False
    return bool(v)


def _macos_use_menu_badge(native_tray: bool) -> bool:
    """Badge flottante: OFF di default (interrompe e va in sovrimpressione). Solo con AMI_FORCE_BADGE=1."""
    if os.environ.get("AMI_NO_MENU_BADGE", "").strip() in ("1", "true", "yes"):
        return False
    if os.environ.get("AMI_FORCE_BADGE", "").strip() in ("1", "true", "yes"):
        return True
    # Tray nativa in menu bar è sufficiente; niente pannello sotto la barra.
    return False


def _position_macos_floating_window(win, *, margin: int = 12, offset_x: int = 0) -> None:
    """Ancora una finestra in alto a destra, subito sotto la menu bar (senza ruba-focus)."""
    app = QApplication.instance()
    if app is None or win is None:
        return
    screen = None
    try:
        pt = QCursor.pos()
        for s in app.screens():
            if s.geometry().contains(pt):
                screen = s
                break
    except Exception:
        screen = None
    if screen is None:
        screen = app.primaryScreen()
    if screen is None:
        return
    ag = screen.availableGeometry()
    x = ag.right() - win.width() - margin - offset_x
    y = ag.top() + margin
    if win.pos().x() != x or win.pos().y() != y:
        win.move(x, y)
    if not win.isVisible():
        win.show()
    # Non chiamare raise_()/activateWindow(): causa flicker in sovrimpressione.


def _effective_app_version(config: dict) -> str:
    """Versione per OTA/splash: mai inferiore al codice in esecuzione (`ami.__version__`)."""
    cfg_v = config.get("app", {}).get("version", __version__)
    try:
        from packaging.version import InvalidVersion, parse as vparse

        return str(max(vparse(cfg_v), vparse(__version__)))
    except InvalidVersion:
        return __version__


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
        self.app.aboutToQuit.connect(_log_ami_quit)
        if sys.platform == "darwin":
            _apply_macos_dock_presence(self.app)
        self.app.setQuitOnLastWindowClosed(False)
        # Evita che il click Dock riapra la dashboard subito dopo splash/avvio.
        self._dock_resume_blocked_until = time.monotonic() + 8.0
        # Non collegare applicationStateChanged qui: durante __init__ processEvents() può
        # emettere ApplicationActive; aprire finestre da quello stack su macOS → qFatal/SIGABRT (Qt 6 + Cocoa).
        self._startup_complete = False
        self._macos_post_splash_finalized = False
        self._macos_startup_panel_shown = False
        self._macos_tray_title_fallback = False
        self.config = self.load_config()
        app_version = _effective_app_version(self.config)
        use_compact = _effective_compact_status_window(self.config)
        sync_autostart(self.config.get("startup", {}).get("auto_start", False))
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

        # Tray: su macOS NSStatusItem nativo (PNG a colori); Qt spesso invisibile in menu bar.
        if sys.platform == "darwin":
            from ami.ui.macos_status_item import create_macos_tray_icon, macos_reassert_regular_activation_policy

            self.tray_icon = create_macos_tray_icon(self.app)
            self._native_macos_tray = hasattr(self.tray_icon, "set_icon_from_path")
            if self._native_macos_tray:
                macos_reassert_regular_activation_policy()
        else:
            self.tray_icon = QSystemTrayIcon(self.app)
            self._native_macos_tray = False
        self._apply_tray_icon_for_status("offline")
        self.tray_icon.setToolTip("AMI - Starting...")
        self.create_menu()
        self.tray_icon.activated.connect(self.on_tray_activated)
        self._macos_menu_badge = None
        self._macos_control_panel = None
        if sys.platform == "darwin":
            from ami.ui.macos_control_panel import create_macos_control_panel
            from ami.ui.macos_menu_bar_badge import create_macos_menu_bar_badge

            self._macos_control_panel = create_macos_control_panel(self.tray_icon)
            if self._macos_control_panel is not None:
                self._macos_control_panel.set_dashboard_callback(self.show_dashboard)

            self._macos_menu_badge = None
            if _macos_use_menu_badge(self._native_macos_tray):
                self._macos_menu_badge = create_macos_menu_bar_badge(self.app)
            if self._macos_menu_badge is not None:
                self._macos_menu_badge.setContextMenu(self._tray_menu)
                st = getattr(self, "current_status", None)
                sk = st.status if st and getattr(st, "status", None) else "offline"
                self._apply_tray_icon_for_status(sk)
        if self._native_macos_tray:
            self.tray_icon.show()
        elif sys.platform == "darwin":
            QTimer.singleShot(0, self._first_show_macos_tray)
        else:
            self.tray_icon.show()
            _process_init_events(self.app)
        _tray_debug(
            f"frozen={_is_pyinstaller_frozen()} tray_available={QSystemTrayIcon.isSystemTrayAvailable()} "
            f"icon_null={self.tray_icon.icon().isNull()}"
        )
        if sys.platform == "darwin":
            # Pochi reassert all'avvio: troppi facevano lampeggiare l'icona in menu bar.
            for ms in (0, 400):
                QTimer.singleShot(ms, self._reassert_macos_tray)
            if self._native_macos_tray:
                self._tray_heartbeat = QTimer()
                self._tray_heartbeat.timeout.connect(self._heartbeat_macos_tray)
                self._tray_heartbeat.start(15000)
        if sys.platform == "darwin" and not self._native_macos_tray and not QSystemTrayIcon.isSystemTrayAvailable():
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

        def splash_msg(msg: str) -> None:
            if self.splash:
                self.splash.showMessage(msg)

        splash_msg("Initializing network monitor...")
        self.monitor = NetworkMonitor(self.config)
        splash_msg("Starting logger...")
        self.logger = EventLogger(self.config)
        splash_msg("Preparing notifications...")
        self.notifier = Notifier(self.config)
        self.notifier.tray_icon = self.tray_icon
        splash_msg("Starting API server...")
        self.api_server = APIServer(self.config, self.monitor)
        self.current_status = None
        self.monitor_thread = None
        splash_msg("Finalizing...")
        if self.splash:
            _process_init_events(self.app)
        self.api_server.start()
        self.update_icon("offline")
        interval = self.config["monitoring"]["polling_interval"] * 1000
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_connection)
        self.timer.start(interval)
        self.compact_status = None
        if use_compact:
            self.compact_status = CompactStatusWindow(self.config, self.monitor, self.tray_icon)
            badge_offset = 150 if getattr(self, "_macos_menu_badge", None) is not None else 0
            _position_macos_floating_window(self.compact_status, margin=16, offset_x=badge_offset)
            self.compact_status.show()
            self.compact_status.raise_()
        if sys.platform == "darwin" and use_compact:
            self._macos_compact_keepalive = QTimer()
            self._macos_compact_keepalive.timeout.connect(self._ensure_macos_compact_visible)
            self._macos_compact_keepalive.start(5000)
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
        elif sys.platform == "darwin":
            QTimer.singleShot(0, self._finalize_macos_startup_ui)
        if self.config.get("ui", {}).get("show_dashboard_on_start", False) or os.environ.get("AMI_FORCE_DASHBOARD") == "1":
            if sys.platform == "darwin" and getattr(self, "_macos_control_panel", None) is not None:
                QTimer.singleShot(400, self._macos_control_panel.show_centered)
            else:
                QTimer.singleShot(2500, self.show_dashboard)
        elif sys.platform == "darwin" and getattr(self, "_macos_control_panel", None) is not None:
            if self._should_auto_show_macos_control_panel():
                QTimer.singleShot(400, self._macos_control_panel.show_centered)

        self._startup_complete = True
        self._macos_tray_misses = 0
        if sys.platform == "darwin":
            # Differisci: collegare troppo presto → applicationStateChanged + show UI → qFatal.
            QTimer.singleShot(8000, self._connect_macos_dock_handler)
            if getattr(self, "_macos_menu_badge", None) is not None:
                QTimer.singleShot(0, safe_slot(lambda: self._macos_menu_badge.show()))

    def _connect_macos_dock_handler(self) -> None:
        try:
            self.app.applicationStateChanged.connect(self._on_application_state_changed)
            _tray_debug("macOS dock handler connected (post grace period)")
        except Exception as exc:
            _tray_debug(f"dock handler connect failed: {exc}")

    def _should_auto_show_macos_control_panel(self) -> bool:
        if os.environ.get("AMI_SHOW_PANEL", "").strip() in ("1", "true", "yes"):
            return True
        if os.environ.get("AMI_NO_PANEL", "").strip() in ("1", "true", "yes"):
            return False
        if getattr(self, "_native_macos_tray", False):
            return False
        return True

    def _notify_user(
        self,
        title: str,
        message: str,
        level: str = "info",
        *,
        respect_enabled: bool = False,
    ) -> None:
        notifier = getattr(self, "notifier", None)
        if notifier is not None:
            notifier.notify_message(
                title,
                message,
                level=level,
                respect_enabled=respect_enabled,
                play_sound=False,
            )
            return
        icon_map = {
            "info": QSystemTrayIcon.MessageIcon.Information,
            "warning": QSystemTrayIcon.MessageIcon.Warning,
            "error": QSystemTrayIcon.MessageIcon.Critical,
        }
        self.tray_icon.showMessage(
            title,
            message,
            icon_map.get(level, QSystemTrayIcon.MessageIcon.Information),
            3500,
        )

    @safe_slot
    def _macos_activate_front(self) -> None:
        """Raise already-visible UI only — never force-create the control panel (crash path)."""
        if getattr(self, "_native_macos_tray", False):
            if hasattr(self.tray_icon, "reassert"):
                self.tray_icon.reassert()
            return
        panel = getattr(self, "_macos_control_panel", None)
        if panel is not None and panel.isVisible():
            panel.raise_()
            panel.activateWindow()

    @safe_slot
    def _ensure_macos_compact_visible(self) -> None:
        cs = getattr(self, "compact_status", None)
        if cs is None:
            return
        # Non forzare raise periodico: solo ripristina se l'utente l'ha chiusa per sbaglio.
        if cs.isVisible():
            return
        badge_offset = 150 if getattr(self, "_macos_menu_badge", None) is not None else 0
        _position_macos_floating_window(cs, margin=16, offset_x=badge_offset)

    def _allow_splash_close(self) -> None:
        self._splash_closable = True
        if self.current_status and not self._splash_closed:
            self.close_splash()

    @safe_slot
    def close_splash(self) -> None:
        if self._splash_closed:
            return
        self._splash_closed = True
        if self.splash is not None:
            splash = self.splash
            splash.fade_out(callback=lambda: QTimer.singleShot(0, self._on_splash_closed))

    @safe_slot
    def _on_splash_closed(self) -> None:
        self.splash = None
        if sys.platform == "darwin":
            QTimer.singleShot(0, self._finalize_macos_startup_ui)

    @safe_slot
    def _finalize_macos_startup_ui(self) -> None:
        """Stabilize macOS UI after splash closes — never run synchronously from fade_out stack."""
        if getattr(self, "_macos_post_splash_finalized", False):
            return
        self._macos_post_splash_finalized = True
        _tray_debug("macOS post-splash finalize")
        try:
            from ami.ui.macos_status_item import macos_reassert_regular_activation_policy

            macos_reassert_regular_activation_policy()
        except Exception as exc:
            _tray_debug(f"post-splash activation policy skipped: {exc}")
        if hasattr(self.tray_icon, "reassert"):
            self.tray_icon.reassert()
        self._recover_macos_tray_visibility()
        badge = getattr(self, "_macos_menu_badge", None)
        if badge is not None:
            badge.show()
        # Solo tray: non aprire pannello/badge se la menu bar ha già l'icona nativa.
        if getattr(self, "_native_macos_tray", False):
            return
        if not self._main_ui_is_visible():
            self._show_macos_startup_anchor()

    @safe_slot
    def _recover_macos_tray_visibility(self) -> None:
        """Recreate tray, fall back to title mode, then badge/control panel."""
        if not getattr(self, "_native_macos_tray", False):
            return
        tray = self.tray_icon
        present = bool(tray.menu_bar_present()) if hasattr(tray, "menu_bar_present") else False
        if present and not getattr(self, "_macos_tray_title_fallback", False):
            return
        if hasattr(tray, "recreate") and tray.recreate():
            if tray.menu_bar_present():
                _tray_debug("macOS tray recovered via recreate")
                return
        if hasattr(tray, "force_title_mode") and not getattr(self, "_macos_tray_title_fallback", False):
            tray.force_title_mode()
            self._macos_tray_title_fallback = True
            _tray_debug("macOS tray recovered via title fallback")
            return
        self._ensure_macos_badge_fallback()
        panel = getattr(self, "_macos_control_panel", None)
        if panel is not None:
            QTimer.singleShot(0, panel.show_centered)

    @safe_slot
    def _show_macos_startup_anchor(self) -> None:
        """Brief centered panel when no window remains after splash (tray-only mode)."""
        if getattr(self, "_macos_startup_panel_shown", False):
            return
        if self._main_ui_is_visible():
            return
        badge = getattr(self, "_macos_menu_badge", None)
        if badge is not None:
            badge.show()
        panel = getattr(self, "_macos_control_panel", None)
        if panel is None:
            return
        self._macos_startup_panel_shown = True
        QTimer.singleShot(0, panel.show_centered)
        QTimer.singleShot(5000, self._hide_macos_startup_panel_if_idle)

    @safe_slot
    def _hide_macos_startup_panel_if_idle(self) -> None:
        panel = getattr(self, "_macos_control_panel", None)
        if panel is None or not panel.isVisible():
            return
        compact = getattr(self, "compact_status", None)
        if compact is not None and compact.isVisible():
            return
        try:
            panel.hide()
        except Exception:
            pass

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

    @safe_slot
    def _on_application_state_changed(self, state: Qt.ApplicationState) -> None:
        """Dock: differito — mai show() dallo stack di setApplicationState (crash Qt macOS)."""
        if sys.platform != "darwin":
            return
        if state != Qt.ApplicationState.ApplicationActive:
            return
        QTimer.singleShot(50, self._deferred_application_active_from_dock)

    @safe_slot
    def _deferred_application_active_from_dock(self) -> None:
        """Dock click: solo superfici leggere già create; niente dashboard/pannello forzati."""
        if not getattr(self, "_startup_complete", False):
            return
        if time.monotonic() < getattr(self, "_dock_resume_blocked_until", 0):
            return
        if self.app.applicationState() != Qt.ApplicationState.ApplicationActive:
            return
        if self._main_ui_is_visible():
            return
        # Prefer compact / tray reassert — never open dashboard from dock (qFatal risk).
        if getattr(self, "compact_status", None) is not None:
            self.compact_status.show()
            self.compact_status.raise_()
            return
        if hasattr(self.tray_icon, "reassert"):
            self.tray_icon.reassert()
            return
        badge = getattr(self, "_macos_menu_badge", None)
        if badge is not None:
            badge.show()
            return
        panel = getattr(self, "_macos_control_panel", None)
        if panel is not None and panel.isVisible():
            panel.raise_()

    def show_compact_status_window(self) -> None:
        if not _effective_compact_status_window(self.config):
            self._notify_user(
                "AMI",
                "Enable “Compact status window” in Settings → UI, or use Dashboard from the menu.",
            )
            return
        if self.compact_status is None:
            self.compact_status = CompactStatusWindow(self.config, self.monitor, self.tray_icon)
            if self.current_status:
                self.compact_status.update_status(self.current_status)
        _position_macos_floating_window(
            self.compact_status,
            margin=16,
            offset_x=150 if getattr(self, "_macos_menu_badge", None) is not None else 0,
        )
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
        sync_autostart(new_config.get("startup", {}).get("auto_start", False))

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
        """Icona tray (menu bar): PNG ufficiali status_green|yellow|red."""
        path = get_base_path() / "resources" / {
            "online": "status_green.png",
            "unstable": "status_yellow.png",
        }.get(status, "status_red.png")
        badge = getattr(self, "_macos_menu_badge", None)
        if badge is not None and path.is_file():
            badge.set_status_icon_path(path)
        panel = getattr(self, "_macos_control_panel", None)
        if panel is not None and path.is_file():
            panel.set_status_icon_path(path)
        if getattr(self, "_native_macos_tray", False) and path.is_file():
            self.tray_icon.set_icon_from_path(path)
            return
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
            _process_init_events(self.app)
            g = self.tray_icon.geometry()
            _tray_debug(
                f"first_show macOS geometry={g.x()},{g.y()},{g.width()}x{g.height()} "
                f"icon_null={self.tray_icon.icon().isNull()}"
            )
        except Exception:
            pass

    @safe_slot
    def _reassert_macos_tray(self) -> None:
        if getattr(self, "_native_macos_tray", False) and hasattr(self.tray_icon, "reassert"):
            self.tray_icon.reassert()
        st = getattr(self, "current_status", None)
        key = st.status if st and getattr(st, "status", None) else "offline"
        self._apply_tray_icon_for_status(key)
        if not getattr(self, "_native_macos_tray", False):
            self.tray_icon.setVisible(True)
            self.tray_icon.show()
        g = self.tray_icon.geometry()
        _tray_debug(
            f"reassert status={key} icon_null={self.tray_icon.icon().isNull()} "
            f"geometry={g.x()},{g.y()},{g.width()}x{g.height()}"
        )

    @safe_slot
    def _heartbeat_macos_tray(self) -> None:
        """Keep NSStatusItem alive; recreate or enable badge fallback if it vanishes."""
        if not getattr(self, "_native_macos_tray", False):
            return
        tray = self.tray_icon
        present = True
        if hasattr(tray, "menu_bar_present"):
            present = bool(tray.menu_bar_present())
        elif hasattr(tray, "isVisible"):
            present = bool(tray.isVisible())
        if present:
            self._macos_tray_misses = 0
            # Non chiamare reassert() a ogni heartbeat: fa lampeggiare l'icona in menu bar.
            return
        self._macos_tray_misses = getattr(self, "_macos_tray_misses", 0) + 1
        _tray_debug(f"native tray miss count={self._macos_tray_misses}")
        self._recover_macos_tray_visibility()

    def _ensure_macos_badge_fallback(self) -> None:
        """Badge solo se esplicitamente abilitato (AMI_FORCE_BADGE); altrimenti solo tray."""
        if not _macos_use_menu_badge(getattr(self, "_native_macos_tray", False)):
            _tray_debug("macOS badge fallback skipped (tray-only mode)")
            return
        if getattr(self, "_macos_menu_badge", None) is not None:
            try:
                self._macos_menu_badge.show()
            except Exception:
                pass
            return
        try:
            from ami.ui.macos_menu_bar_badge import MacOSMenuBarBadge

            badge = MacOSMenuBarBadge(self.app)
            badge.setContextMenu(getattr(self, "_tray_menu", None))
            self._macos_menu_badge = badge
            st = getattr(self, "current_status", None)
            key = st.status if st and getattr(st, "status", None) else "offline"
            self._apply_tray_icon_for_status(key)
            badge.show()
            _tray_debug("macOS badge fallback enabled after tray misses")
        except Exception as exc:
            _tray_debug(f"badge fallback failed: {exc}")

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
        self._apply_tray_icon_for_status(status)

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
        tip = "\n".join(parts)
        self.tray_icon.setToolTip(tip)
        badge = getattr(self, "_macos_menu_badge", None)
        if badge is not None:
            badge.setToolTip(tip)

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

    @safe_slot
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

    @safe_slot
    def on_status_updated(self, status) -> None:
        self._on_status_updated_impl(status)

    def _on_status_updated_impl(self, status) -> None:
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
        panel = getattr(self, "_macos_control_panel", None)
        if panel is not None:
            lat = getattr(status, "avg_latency_ms", None)
            panel.update_status(status.status, lat)

    @safe_slot
    def _on_speed_test_finished(self) -> None:
        self._speed_test_busy = False
        self.check_connection()

    def _speed_test_now(self) -> None:
        st_cfg = self.config.get("speed_test", {})
        if not st_cfg.get("enabled", False):
            self._notify_user("AMI", "Speed test is disabled in Settings.", level="warning")
            return
        self._notify_user("AMI", "Running download speed test…")
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
        self._notify_user("AMI", "Running connection test...")
        self.check_connection()

    @safe_slot
    def on_tray_activated(self, reason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            if self.dashboard and self.dashboard.isVisible():
                self.dashboard.hide()
            else:
                QTimer.singleShot(0, self._show_dashboard_deferred)
            return
        # macOS: non chiamare popup() qui — `setContextMenu` fa già aprire il menu al click;
        # un secondo popup su Trigger causava due menu sovrapposti.

    @safe_slot
    def _show_dashboard_deferred(self) -> None:
        self.show_dashboard()

    @safe_slot
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
            self._notify_user("AMI Settings", "Settings saved and applied")
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
            self._notify_user("AMI", "Test notification")

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
        v = html.escape(_effective_app_version(self.config))
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
        if getattr(self, "_macos_menu_badge", None):
            self._macos_menu_badge.hide()
        if getattr(self, "_macos_control_panel", None):
            self._macos_control_panel.hide()
        if getattr(self, "compact_status", None):
            self.compact_status.close()
        self.app.quit()

    def run(self) -> int:
        if sys.platform == "darwin":
            if getattr(self, "_native_macos_tray", False):
                QTimer.singleShot(0, self._reassert_macos_tray)
            badge = getattr(self, "_macos_menu_badge", None)
            if badge is not None:
                QTimer.singleShot(100, badge.show)
                QTimer.singleShot(800, badge.show)
        return self.app.exec()


def main() -> None:
    install_exception_handlers()
    QApplication.setApplicationName("AMI")
    QApplication.setApplicationDisplayName("AMI - Active Monitor of Internet")
    QApplication.setOrganizationName("AMI Project")
    app = SystemTrayApp()
    sys.exit(app.run())
