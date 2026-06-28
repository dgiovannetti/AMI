"""
Menu bar macOS nativa (NSStatusItem): icone PNG a colori (✓ / ! / ✕).
Qt QSystemTrayIcon su macOS spesso non disegna PNG a colori (geometry ok, icona invisibile).
"""

from __future__ import annotations

import sys
from pathlib import Path

from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from PyQt6.QtGui import QCursor, QIcon
from PyQt6.QtWidgets import QApplication, QMenu, QSystemTrayIcon


def _tray_debug(msg: str) -> None:
    import os

    if os.environ.get("AMI_DEBUG_TRAY", "").strip() in ("1", "true", "yes"):
        print(f"[AMI tray] {msg}", file=sys.stderr, flush=True)


if sys.platform == "darwin":
    import objc
    from AppKit import NSImage, NSStatusBar, NSVariableStatusItemLength
    from Foundation import NSObject

    class _MacTrayClickTarget(NSObject):  # type: ignore[misc]
        def initWithOwner_(self, owner):  # noqa: N802
            self = objc.super(_MacTrayClickTarget, self).init()
            if self is None:
                return None
            self._owner = owner
            return self

        def handleClick_(self, _sender):  # noqa: N802
            owner = getattr(self, "_owner", None)
            if owner is not None:
                owner._on_status_click()


class MacOSTrayIcon(QObject):
    """Facciata compatibile con QSystemTrayIcon; NSStatusItem per icone a colori."""

    activated = pyqtSignal(object)

    def __init__(self, app: QApplication | None = None) -> None:
        super().__init__()
        if sys.platform != "darwin":
            raise RuntimeError("MacOSTrayIcon is macOS only")

        self._app = app or QApplication.instance()
        self._context_menu: QMenu | None = None
        self._icon = QIcon()
        self._visible = False
        self._tooltip = ""
        self._click_target = _MacTrayClickTarget.alloc().initWithOwner_(self)
        self._status_item = NSStatusBar.systemStatusBar().statusItemWithLength_(
            NSVariableStatusItemLength
        )
        btn = self._status_item.button()
        btn.setTarget_(self._click_target)
        btn.setAction_("handleClick:")
        self._message_tray = QSystemTrayIcon(self._app)

    def _on_status_click(self) -> None:
        self.activated.emit(QSystemTrayIcon.ActivationReason.Trigger)
        if self._context_menu is not None:
            QTimer.singleShot(0, lambda: self._context_menu.popup(QCursor.pos()))

    def set_icon_from_path(self, path: Path | str) -> None:
        fp = str(path)
        img = NSImage.alloc().initWithContentsOfFile_(fp)
        if img is None:
            _tray_debug(f"native tray: NSImage failed for {fp}")
            return
        img.setTemplate_(False)
        img.setSize_((18.0, 18.0))
        self._status_item.button().setImage_(img)
        self._icon = QIcon(fp)
        _tray_debug(f"native tray: image from {Path(fp).name}")

    def setIcon(self, icon: QIcon) -> None:
        self._icon = icon
        pm = icon.pixmap(22, 22)
        if pm.isNull():
            return
        from PyQt6.QtCore import QBuffer, QIODevice

        buf = QBuffer()
        buf.open(QIODevice.OpenModeFlag.WriteOnly)
        pm.save(buf, b"PNG")
        data = bytes(buf.data())
        img = NSImage.alloc().initWithData_(data)
        if img is not None:
            img.setTemplate_(False)
            img.setSize_((18.0, 18.0))
            self._status_item.button().setImage_(img)

    def icon(self) -> QIcon:
        return self._icon

    def setToolTip(self, tip: str) -> None:
        self._tooltip = tip
        self._status_item.button().setToolTip_(tip)

    def setContextMenu(self, menu: QMenu | None) -> None:
        self._context_menu = menu

    def show(self) -> None:
        self._visible = True
        self._status_item.setVisible_(True)

    def hide(self) -> None:
        self._visible = False
        self._status_item.setVisible_(False)

    def setVisible(self, visible: bool) -> None:
        if visible:
            self.show()
        else:
            self.hide()

    def isVisible(self) -> bool:
        return bool(self._visible and self._status_item.isVisible())

    def showMessage(
        self,
        title: str,
        message: str,
        icon: QSystemTrayIcon.MessageIcon = QSystemTrayIcon.MessageIcon.Information,
        timeout_ms: int = 10000,
    ) -> None:
        self._message_tray.showMessage(title, message, icon, timeout_ms)

    def geometry(self):
        from PyQt6.QtCore import QRect

        btn = self._status_item.button()
        if btn is None:
            return QRect(0, 0, 22, 22)
        return QRect(0, 0, 22, 22)


def create_macos_tray_icon(app: QApplication) -> MacOSTrayIcon | QSystemTrayIcon:
    """NSStatusItem nativo salvo AMI_TRAY_QT=1 (solo Qt, spesso invisibile a colori)."""
    import os

    if os.environ.get("AMI_TRAY_QT", "").strip() in ("1", "true", "yes"):
        _tray_debug("macOS tray: forced QSystemTrayIcon (AMI_TRAY_QT=1)")
        return QSystemTrayIcon(app)
    try:
        native = MacOSTrayIcon(app)
        _tray_debug("macOS tray: using native NSStatusItem")
        return native
    except Exception as exc:
        _tray_debug(f"macOS tray: native failed ({exc}), fallback QSystemTrayIcon")
        return QSystemTrayIcon(app)
