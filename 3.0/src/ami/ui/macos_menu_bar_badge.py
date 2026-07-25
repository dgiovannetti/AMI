"""
Indicatore AMI sempre in primo piano (macOS).

Non nella menu bar (più piena → overflow «»): sottostante, a destra, always-on-top.
Clic = menu tray.
"""

from __future__ import annotations

import os
import sys
from ctypes import c_void_p
from pathlib import Path

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QCursor, QFont, QMouseEvent, QPixmap
from PyQt6.QtWidgets import QApplication, QFrame, QHBoxLayout, QLabel, QMenu, QVBoxLayout


def _tray_debug(msg: str) -> None:
    if os.environ.get("AMI_DEBUG_TRAY", "").strip() in ("1", "true", "yes"):
        print(f"[AMI tray] {msg}", file=sys.stderr, flush=True)


class MacOSMenuBarBadge(QFrame):
    """Pannello fisso AMI — impossibile da perdere, sempre sopra le altre finestre."""

    clicked = pyqtSignal()

    _W = 142
    _H = 46

    def __init__(self, app: QApplication | None = None) -> None:
        super().__init__(
            None,
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool,
        )
        self._app = app or QApplication.instance()
        self._context_menu: QMenu | None = None
        self._tooltip = ""
        self.setObjectName("MacOSMenuBarBadge")
        self.setFixedSize(self._W, self._H)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 6, 12, 6)
        root.setSpacing(0)

        row = QHBoxLayout()
        row.setSpacing(8)
        self._icon = QLabel()
        self._icon.setFixedSize(22, 22)
        self._icon.setScaledContents(True)
        row.addWidget(self._icon)

        self._label = QLabel("AMI")
        self._label.setFont(QFont("Helvetica Neue", 16, QFont.Weight.Black))
        self._label.setStyleSheet("color: #ffffff; background: transparent;")
        row.addWidget(self._label)
        row.addStretch(1)
        root.addLayout(row)

        self._status = QLabel("avvio…")
        self._status.setFont(QFont("Helvetica Neue", 10, QFont.Weight.DemiBold))
        self._status.setStyleSheet("color: #a7f3d0; background: transparent;")
        root.addWidget(self._status)

        self._apply_border("#10b981")

        screen = self._app.primaryScreen() if self._app else None
        if screen is not None:
            screen.geometryChanged.connect(self._reposition)
            screen.availableGeometryChanged.connect(self._reposition)

        self._watch = QTimer(self)
        self._watch.timeout.connect(self._reposition)
        self._watch.start(2000)

    def _apply_border(self, color: str) -> None:
        self.setStyleSheet(
            f"""
            QFrame#MacOSMenuBarBadge {{
                background: #0f172a;
                border: 3px solid {color};
                border-radius: 10px;
            }}
            """
        )

    def _ns_window(self):
        """Resolve the underlying NSWindow from the Qt widget (post-show)."""
        try:
            import objc

            handle = self.windowHandle()
            wid = int(handle.winId()) if handle is not None else int(self.winId())
            if wid == 0:
                return None
            view = objc.objc_object(c_void_p=wid)
            return view.window()
        except Exception as exc:
            _tray_debug(f"badge ns_window lookup failed ({exc})")
            return None

    def _elevate(self) -> None:
        try:
            from AppKit import NSFloatingWindowLevel, NSWindowCollectionBehaviorCanJoinAllSpaces

            ns_window = self._ns_window()
            if ns_window is not None:
                # Floating: sopra le app, SOTTO la menu bar (visibile sempre).
                ns_window.setLevel_(NSFloatingWindowLevel)
                ns_window.setCollectionBehavior_(NSWindowCollectionBehaviorCanJoinAllSpaces)
                ns_window.setHidesOnDeactivate_(False)
                ns_window.setIgnoresMouseEvents_(False)
                _tray_debug("badge elevated to NSFloatingWindowLevel")
        except Exception as exc:
            _tray_debug(f"badge elevate skipped ({exc})")

    def _active_screen(self):
        if self._app is None:
            return None
        # Preferisci lo schermo dove c’è il cursore (più di una display).
        try:
            from PyQt6.QtGui import QCursor

            pt = QCursor.pos()
            for s in self._app.screens():
                if s.geometry().contains(pt):
                    return s
        except Exception:
            pass
        return self._app.primaryScreen()

    def _reposition(self) -> None:
        screen = self._active_screen()
        if screen is None:
            return
        ag = screen.availableGeometry()
        # Sotto la menu bar, angolo in alto a destra — offset extra dalle icone di sistema.
        x = ag.right() - self.width() - 24
        y = ag.top() + 12
        # Solo riposiziona se serve: niente raise_() periodico (ruba focus ogni 2s).
        if self.pos().x() != x or self.pos().y() != y:
            self.move(x, y)
        if not self.isVisible():
            super().show()
            self._elevate()


    def set_status_icon_path(self, path: Path | str) -> None:
        fp = Path(path)
        if not fp.is_file():
            return
        pm = QPixmap(str(fp))
        if pm.isNull():
            return
        self._icon.setPixmap(
            pm.scaled(22, 22, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        )
        name = fp.name
        if "green" in name:
            border, text, lbl = "#10b981", "#a7f3d0", "online"
        elif "yellow" in name:
            border, text, lbl = "#f59e0b", "#fde68a", "instabile"
        else:
            border, text, lbl = "#ef4444", "#fecaca", "offline"
        self._apply_border(border)
        self._status.setText(lbl)
        self._status.setStyleSheet(f"color: {text}; background: transparent;")

    def setContextMenu(self, menu: QMenu | None) -> None:
        self._context_menu = menu

    def setToolTip(self, tip: str) -> None:
        self._tooltip = tip
        super().setToolTip(tip)

    def show(self) -> None:
        super().show()
        self._reposition()
        QTimer.singleShot(100, self._reposition)
        QTimer.singleShot(500, self._reposition)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
            if self._context_menu is not None:
                self._context_menu.popup(QCursor.pos())
        super().mousePressEvent(event)


def create_macos_menu_bar_badge(app: QApplication) -> MacOSMenuBarBadge | None:
    if sys.platform != "darwin":
        return None
    if os.environ.get("AMI_NO_MENU_BADGE", "").strip() in ("1", "true", "yes"):
        return None
    # Opt-in only: floating badge steals focus / overlays other apps every reposition.
    if os.environ.get("AMI_FORCE_BADGE", "").strip() not in ("1", "true", "yes"):
        return None
    badge = MacOSMenuBarBadge(app)
    _tray_debug("macOS badge: floating panel top-right (AMI_FORCE_BADGE=1)")
    return badge
