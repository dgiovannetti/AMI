"""
Menu bar macOS nativa (NSStatusItem): icone PNG a colori (✓ / ! / ✕).
Qt QSystemTrayIcon su macOS spesso non disegna PNG a colori (geometry ok, icona invisibile).
"""

from __future__ import annotations

import sys
from pathlib import Path

from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from PyQt6.QtGui import QCursor, QIcon, QImage
from PyQt6.QtWidgets import QApplication, QMenu, QSystemTrayIcon


def _tray_debug(msg: str) -> None:
    import os

    if os.environ.get("AMI_DEBUG_TRAY", "").strip() in ("1", "true", "yes"):
        print(f"[AMI tray] {msg}", file=sys.stderr, flush=True)


def macos_reassert_regular_activation_policy() -> None:
    """Qt può ripristinare Accessory dopo init tray — forza di nuovo Regular."""
    try:
        from AppKit import NSApplication, NSApplicationActivationPolicyRegular

        NSApplication.sharedApplication().setActivationPolicy_(
            NSApplicationActivationPolicyRegular
        )
    except Exception:
        pass


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
        self._last_icon_path: str | None = None
        self._ns_image = None  # retain forte — altrimenti GC rimuove l'icona dal pulsante
        self._click_target = _MacTrayClickTarget.alloc().initWithOwner_(self)
        self._status_item = NSStatusBar.systemStatusBar().statusItemWithLength_(
            NSVariableStatusItemLength
        )
        try:
            self._status_item.setAutosaveName_("tech.ciaoim.ami.status")
        except (AttributeError, TypeError):
            pass
        btn = self._status_item.button()
        if btn is None:
            raise RuntimeError("NSStatusItem.button() is None")
        btn.setTarget_(self._click_target)
        btn.setAction_("handleClick:")
        macos_reassert_regular_activation_policy()
        self._status_item.setVisible_(True)
        self._visible = True

    def _on_status_click(self) -> None:
        self.activated.emit(QSystemTrayIcon.ActivationReason.Trigger)
        if self._context_menu is not None:
            QTimer.singleShot(0, lambda: self._context_menu.popup(QCursor.pos()))

    def _load_nsimage_from_path(self, fp: str) -> object | None:
        """PNG → NSImage 18pt (@2x pixel) per menu bar Retina."""
        qimg = QImage(fp)
        if qimg.isNull():
            return None
        # 36 px = 18pt @2x (standard menu bar)
        from PyQt6.QtCore import Qt

        scaled = qimg.scaled(
            36,
            36,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        from PyQt6.QtCore import QBuffer, QIODevice

        buf = QBuffer()
        buf.open(QIODevice.OpenModeFlag.WriteOnly)
        scaled.save(buf, b"PNG")
        data = bytes(buf.data())
        img = NSImage.alloc().initWithData_(data)
        if img is None:
            return None
        img.setTemplate_(False)
        img.setSize_((18.0, 18.0))
        return img

    def set_icon_from_path(self, path: Path | str) -> None:
        fp = str(path.resolve())
        if fp == self._last_icon_path and self._ns_image is not None:
            return
        img = self._load_nsimage_from_path(fp)
        if img is None:
            _tray_debug(f"native tray: NSImage failed for {fp}")
            return
        self._ns_image = img
        self._last_icon_path = fp
        btn = self._status_item.button()
        btn.setImage_(self._ns_image)
        # Fallback testo se l'immagine non si vede (menu bar stretta / Retina)
        sym = {
            "status_green.png": "✓",
            "status_yellow.png": "!",
            "status_red.png": "✕",
        }.get(Path(fp).name, "●")
        btn.setTitle_(sym)
        btn.setHidden_(False)
        self._status_item.setVisible_(True)
        self._icon = QIcon(fp)
        _tray_debug(f"native tray: image from {Path(fp).name}")

    def setIcon(self, icon: QIcon) -> None:
        self._icon = icon
        pm = icon.pixmap(36, 36)
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
            self._ns_image = img
            self._last_icon_path = None
            self._status_item.button().setImage_(self._ns_image)

    def icon(self) -> QIcon:
        return self._icon

    def setToolTip(self, tip: str) -> None:
        self._tooltip = tip
        btn = self._status_item.button()
        if btn is not None:
            btn.setToolTip_(tip)

    def setContextMenu(self, menu: QMenu | None) -> None:
        self._context_menu = menu

    def show(self) -> None:
        macos_reassert_regular_activation_policy()
        self._visible = True
        self._status_item.setVisible_(True)
        btn = self._status_item.button()
        if btn is not None:
            btn.setHidden_(False)

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
        # Nessun QSystemTrayIcon permanente: su macOS crea un secondo slot menu bar vuoto.
        _tray_debug(f"native tray message: {title}: {message}")

    def geometry(self):
        from PyQt6.QtCore import QRect

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
