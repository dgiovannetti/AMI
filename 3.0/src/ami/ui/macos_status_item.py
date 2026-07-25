"""
Menu bar macOS nativa (NSStatusItem): icone da status_*.png (✓ / ! / ✕).
Default: PNG a colori (visibili come icone tray). Titolo testo: AMI_TRAY_TITLE=1.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from PyQt6.QtGui import QCursor, QIcon, QImage, QColor
from PyQt6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from ami.core.paths import get_base_path


def _tray_debug(msg: str) -> None:
    if os.environ.get("AMI_DEBUG_TRAY", "").strip() in ("1", "true", "yes"):
        print(f"[AMI tray] {msg}", file=sys.stderr, flush=True)


def _status_label_for_path(fp: str) -> str:
    sym = {
        "status_green.png": "✓",
        "status_yellow.png": "!",
        "status_red.png": "✕",
    }.get(Path(fp).name, "●")
    return f"AMI {sym}"


def macos_reassert_regular_activation_policy() -> None:
    try:
        from AppKit import NSApplication, NSApplicationActivationPolicyRegular

        ns = NSApplication.sharedApplication()
        ns.setActivationPolicy_(NSApplicationActivationPolicyRegular)
        if hasattr(ns, "finishLaunching"):
            ns.finishLaunching()
    except Exception:
        pass


def _pin_status_item_left() -> None:
    """Posizione sinistra nella menu bar (meno probabile finire nel overflow «»)."""
    try:
        from Foundation import NSUserDefaults

        ud = NSUserDefaults.standardUserDefaults()
        ud.setObject_forKey_(0.0, "NSStatusItem Preferred Position tech.ciaoim.ami.status")
        ud.removeObjectForKey_("NSStatusItem Visible tech.ciaoim.ami.status")
        ud.synchronize()
    except Exception:
        pass


def _clear_stale_status_item_autosave() -> None:
    """Rimuove solo «nascosto»; non sovrascrive la posizione preferita dell'utente."""
    try:
        from Foundation import NSUserDefaults

        ud = NSUserDefaults.standardUserDefaults()
        ud.removeObjectForKey_("NSStatusItem Visible tech.ciaoim.ami.status")
        ud.synchronize()
    except Exception:
        pass


if sys.platform == "darwin":
    import objc
    from AppKit import (
        NSFont,
        NSImage,
        NSSquareStatusItemLength,
        NSStatusBar,
        NSVariableStatusItemLength,
    )
    from Foundation import NSObject

    class _MacTrayClickTarget(NSObject):  # type: ignore[misc]
        def initWithOwner_(self, owner):  # noqa: N802
            self = objc.super(_MacTrayClickTarget, self).init()
            if self is None:
                return None
            self._owner = owner
            return self

        def handleClick_(self, _sender):  # noqa: N802
            try:
                owner = getattr(self, "_owner", None)
                if owner is not None:
                    owner._on_status_click()
            except Exception as exc:
                _tray_debug(f"status click error: {exc}")


def _tray_length(*, title_mode: bool):
    if title_mode:
        return NSVariableStatusItemLength
    return NSSquareStatusItemLength


class MacOSTrayIcon(QObject):
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
        self._ns_image = None
        self._title_mode = False
        _clear_stale_status_item_autosave()
        _pin_status_item_left()
        self._click_target = _MacTrayClickTarget.alloc().initWithOwner_(self)
        self._status_item = NSStatusBar.systemStatusBar().statusItemWithLength_(
            NSSquareStatusItemLength
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
        btn.setTitle_("")
        # Placeholder finché arriva status_*.png — evita slot vuoto invisibile.
        btn.setTitle_("●")
        btn.setFont_(NSFont.boldSystemFontOfSize_(14.0))
        try:
            # 0 = nessuna removal/termination automatica
            self._status_item.setBehavior_(0)
        except (AttributeError, TypeError):
            pass
        macos_reassert_regular_activation_policy()
        self._status_item.setVisible_(True)
        self._visible = True

    def _on_status_click(self) -> None:
        self.activated.emit(QSystemTrayIcon.ActivationReason.Trigger)
        if self._context_menu is not None:
            QTimer.singleShot(0, lambda: self._context_menu.popup(QCursor.pos()))

    def _finalize_nsimage(self, img: object, *, template: bool) -> object | None:
        if img is None:
            return None
        img.setTemplate_(template)
        # 22pt = dimensione tipica menu bar (Retina gestito dal sistema).
        img.setSize_((22.0, 22.0))
        return img

    def _load_nsimage_from_file(self, fp: str, *, template: bool) -> object | None:
        """Caricamento nativo AppKit (affidabile nel bundle PyInstaller)."""
        img = NSImage.alloc().initWithContentsOfFile_(fp)
        if img is not None and img.isValid():
            return self._finalize_nsimage(img, template=template)
        return None

    def _qimage_to_nsimage(self, qimg: QImage, *, template: bool) -> object | None:
        from PyQt6.QtCore import Qt, QBuffer, QIODevice

        scaled = qimg.scaled(
            44,
            44,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        buf = QBuffer()
        buf.open(QIODevice.OpenModeFlag.WriteOnly)
        scaled.save(buf, b"PNG")
        data = bytes(buf.data())
        img = NSImage.alloc().initWithData_(data)
        return self._finalize_nsimage(img, template=template)

    def _load_template_nsimage(self, fp: str) -> object | None:
        """Template: alpha della PNG come maschera (visibile chiaro/scuro)."""
        native = self._load_nsimage_from_file(fp, template=True)
        if native is not None:
            return native
        qimg = QImage(fp)
        if qimg.isNull():
            return None
        qimg = qimg.convertToFormat(QImage.Format.Format_ARGB32)
        w, h = qimg.width(), qimg.height()
        out = QImage(w, h, QImage.Format.Format_ARGB32)
        out.fill(0)
        for y in range(h):
            for x in range(w):
                c = qimg.pixelColor(x, y)
                a = c.alpha()
                if a <= 0:
                    continue
                out.setPixelColor(x, y, QColor(0, 0, 0, a))
        return self._qimage_to_nsimage(out, template=True)

    def _load_colored_nsimage(self, fp: str) -> object | None:
        native = self._load_nsimage_from_file(fp, template=False)
        if native is not None:
            return native
        qimg = QImage(fp)
        if qimg.isNull():
            return None
        return self._qimage_to_nsimage(qimg.convertToFormat(QImage.Format.Format_ARGB32), template=False)

    def _apply_title_label(self, fp: str) -> None:
        btn = self._status_item.button()
        if btn is None:
            return
        label = _status_label_for_path(fp)
        self._title_mode = True
        try:
            self._status_item.setLength_(NSVariableStatusItemLength)
        except Exception:
            pass
        btn.setImage_(None)
        self._ns_image = None
        btn.setFont_(NSFont.boldSystemFontOfSize_(13.0))
        btn.setTitle_(label)
        btn.setHidden_(False)
        self._status_item.setVisible_(True)
        _tray_debug(f"native tray: title {label!r}")

    def set_icon_from_path(self, path: Path | str) -> None:
        fp = str(path.resolve())
        if not Path(fp).is_file():
            _tray_debug(f"native tray: missing {fp}")
            return

        # Default: PNG a colori (icone tray riconoscibili).
        # AMI_TRAY_TITLE=1 forza testo; AMI_TRAY_TEMPLATE=1 maschera mono.
        use_title = os.environ.get("AMI_TRAY_TITLE", "").strip() in ("1", "true", "yes")
        use_template = os.environ.get("AMI_TRAY_TEMPLATE", "").strip() in ("1", "true", "yes")
        use_color = os.environ.get("AMI_TRAY_COLOR", "1").strip() not in ("0", "false", "no")

        # Stesso path: refresh visibilità (macOS può nascondere lo slot).
        if fp == self._last_icon_path and self.menu_bar_present():
            self._status_item.setVisible_(True)
            return

        self._last_icon_path = fp

        if use_title and not use_template:
            self._apply_title_label(fp)
            self._icon = QIcon(fp)
            return

        img = self._load_template_nsimage(fp) if use_template else self._load_colored_nsimage(fp)
        if img is None and use_color and not use_template:
            img = self._load_template_nsimage(fp)
        if img is None:
            self._apply_title_label(fp)
            self._icon = QIcon(fp)
            return

        self._title_mode = False
        self._ns_image = img
        try:
            self._status_item.setLength_(NSSquareStatusItemLength)
        except Exception:
            pass
        btn = self._status_item.button()
        btn.setTitle_("")
        btn.setImage_(self._ns_image)
        btn.setHidden_(False)
        try:
            self._status_item.setBehavior_(0)
        except (AttributeError, TypeError):
            pass
        self._status_item.setVisible_(True)
        self._icon = QIcon(fp)
        mode = "template" if use_template else "color"
        has_img = btn.image() is not None
        _tray_debug(
            f"native tray: {mode} from {Path(fp).name} "
            f"btn_image={has_img} visible={self._status_item.isVisible()}"
        )
        if not has_img:
            self._apply_title_label(fp)

    def setIcon(self, icon: QIcon) -> None:
        self._icon = icon

    def icon(self) -> QIcon:
        return self._icon

    def setToolTip(self, tip: str) -> None:
        self._tooltip = tip
        btn = self._status_item.button()
        if btn is not None:
            btn.setToolTip_(tip)

    def toolTip(self) -> str:
        return self._tooltip

    def setContextMenu(self, menu: QMenu | None) -> None:
        self._context_menu = menu

    def contextMenu(self) -> QMenu | None:
        return self._context_menu

    def show(self) -> None:
        self.reassert()

    def reassert(self) -> None:
        macos_reassert_regular_activation_policy()
        try:
            self._status_item.setBehavior_(0)
        except (AttributeError, TypeError):
            pass
        self._visible = True
        try:
            self._status_item.setVisible_(True)
        except Exception:
            self.recreate()
            return
        btn = self._status_item.button()
        if btn is not None:
            btn.setHidden_(False)
            if self._last_icon_path:
                title = btn.title() or ""
                if not title and btn.image() is None:
                    self._apply_title_label(self._last_icon_path)
                elif self._ns_image is not None and btn.image() is None:
                    btn.setImage_(self._ns_image)
        if self._last_icon_path and Path(self._last_icon_path).is_file():
            cur = btn.image() if btn is not None else None
            title = btn.title() if btn is not None else ""
            if cur is None and not title:
                saved = self._last_icon_path
                self._last_icon_path = None
                self.set_icon_from_path(saved)

    def recreate(self) -> bool:
        """Remove and recreate NSStatusItem when macOS drops it from the menu bar."""
        saved_path = self._last_icon_path
        saved_tip = self._tooltip
        saved_menu = self._context_menu
        try:
            bar = NSStatusBar.systemStatusBar()
            if self._status_item is not None:
                try:
                    bar.removeStatusItem_(self._status_item)
                except Exception:
                    pass
            _clear_stale_status_item_autosave()
            length = _tray_length(title_mode=self._title_mode)
            self._status_item = bar.statusItemWithLength_(length)
            try:
                self._status_item.setAutosaveName_("tech.ciaoim.ami.status")
            except (AttributeError, TypeError):
                pass
            self._click_target = _MacTrayClickTarget.alloc().initWithOwner_(self)
            btn = self._status_item.button()
            if btn is None:
                _tray_debug("native tray recreate: button() is None")
                return False
            btn.setTarget_(self._click_target)
            btn.setAction_("handleClick:")
            btn.setTitle_("AMI")
            btn.setFont_(NSFont.boldSystemFontOfSize_(13.0))
            try:
                self._status_item.setBehavior_(0)
            except (AttributeError, TypeError):
                pass
            self._status_item.setVisible_(True)
            self._visible = True
            self._last_icon_path = None
            self._ns_image = None
            if saved_path and Path(saved_path).is_file():
                self.set_icon_from_path(saved_path)
            else:
                btn.setTitle_("AMI")
            if saved_tip:
                self.setToolTip(saved_tip)
            self._context_menu = saved_menu
            _tray_debug("native tray: recreated NSStatusItem")
            return True
        except Exception as exc:
            _tray_debug(f"native tray recreate failed: {exc}")
            return False

    def menu_bar_present(self) -> bool:
        """Best-effort: status item still known to AppKit and marked visible."""
        try:
            if self._status_item is None:
                return False
            if not self._status_item.isVisible():
                return False
            btn = self._status_item.button()
            if btn is None:
                return False
            title = btn.title() or ""
            has_image = btn.image() is not None
            return bool(title or has_image)
        except Exception:
            return False

    def force_title_mode(self) -> None:
        """Fallback visibile: etichetta testo «AMI ✓» in menu bar."""
        fp = self._last_icon_path
        if not fp or not Path(fp).is_file():
            for name in ("status_red.png", "status_yellow.png", "status_green.png"):
                candidate = get_base_path() / "resources" / name
                if candidate.is_file():
                    fp = str(candidate)
                    break
        if not fp:
            fp = "status_red.png"
        self._last_icon_path = None
        self._apply_title_label(fp)
        if Path(fp).is_file():
            self._icon = QIcon(fp)

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
        _tray_debug(f"native tray message: {title}: {message}")
        try:
            import subprocess

            esc_title = title.replace('"', '\\"')
            esc_message = message.replace('"', '\\"').replace("\n", " ")
            script = f'display notification "{esc_message}" with title "{esc_title}"'
            subprocess.run(["osascript", "-e", script], check=False)
        except Exception as exc:
            _tray_debug(f"native tray notification failed: {exc}")

    def geometry(self):
        from PyQt6.QtCore import QRect

        return QRect(0, 0, 22, 22)


def create_macos_tray_icon(app: QApplication) -> MacOSTrayIcon | QSystemTrayIcon:
    if os.environ.get("AMI_TRAY_QT", "").strip() in ("1", "true", "yes"):
        _tray_debug("macOS tray: forced QSystemTrayIcon (AMI_TRAY_QT=1)")
        return QSystemTrayIcon(app)
    try:
        native = MacOSTrayIcon(app)
        _tray_debug("macOS tray: using native NSStatusItem (default: colored status PNG)")
        return native
    except Exception as exc:
        _tray_debug(f"macOS tray: native failed ({exc}), fallback QSystemTrayIcon")
        return QSystemTrayIcon(app)
