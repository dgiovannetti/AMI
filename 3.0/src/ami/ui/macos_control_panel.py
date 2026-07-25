"""
Pannello AMI centrato su schermo (macOS).

Finestra normale (non overlay menu bar): impossibile da perdere all'avvio.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QVBoxLayout,
)

from ami.core.paths import get_base_path


class MacOSControlPanel(QDialog):
    """Finestra centrale AMI — visibile, riducibile al Dock."""

    def __init__(self, tray_icon, parent=None) -> None:
        super().__init__(parent)
        self.tray_icon = tray_icon
        self.setWindowTitle("AMI — Active Monitor of Internet")
        self.setMinimumSize(320, 260)
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.WindowCloseButtonHint
            | Qt.WindowType.WindowMinimizeButtonHint
        )

        icon_path = get_base_path() / "resources" / "ami.png"
        if icon_path.is_file():
            self.setWindowIcon(QIcon(str(icon_path)))

        root = QVBoxLayout(self)
        root.setSpacing(12)
        root.setContentsMargins(24, 20, 24, 20)

        title = QLabel("AMI")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Helvetica Neue", 28, QFont.Weight.Black))
        root.addWidget(title)

        subtitle = QLabel("Monitor connessione internet")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setFont(QFont("Helvetica Neue", 12))
        subtitle.setStyleSheet("color: #64748b;")
        root.addWidget(subtitle)

        self._dot = QLabel("●")
        self._dot.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._dot.setFont(QFont("Helvetica Neue", 48, QFont.Weight.Black))
        self._dot.setStyleSheet("color: #ef4444;")
        root.addWidget(self._dot)

        self._status = QLabel("offline")
        self._status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status.setFont(QFont("Helvetica Neue", 14, QFont.Weight.Bold))
        root.addWidget(self._status)

        self._hint = QLabel(
            "AMI resta attiva nel Dock.\n"
            "Menu bar: «AMI ✓» (o nel menu «» se la barra è piena)."
        )
        self._hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._hint.setWordWrap(True)
        self._hint.setStyleSheet("color: #64748b; font-size: 11px;")
        root.addWidget(self._hint)

        row = QHBoxLayout()
        self._menu_btn = QPushButton("Menu")
        self._menu_btn.clicked.connect(self._open_menu)
        self._dash_btn = QPushButton("Dashboard")
        self._hide_btn = QPushButton("Nascondi")
        self._hide_btn.clicked.connect(self.hide)
        row.addWidget(self._menu_btn)
        row.addWidget(self._dash_btn)
        row.addWidget(self._hide_btn)
        root.addLayout(row)

        self._dashboard_cb = None

    def set_dashboard_callback(self, cb) -> None:
        self._dashboard_cb = cb
        self._dash_btn.clicked.connect(cb)

    def show_centered(self) -> None:
        app = QApplication.instance()
        screen = app.primaryScreen() if app else None
        if screen is not None:
            ag = screen.availableGeometry()
            self.adjustSize()
            w, h = self.width(), self.height()
            self.move(ag.x() + (ag.width() - w) // 2, ag.y() + (ag.height() - h) // 2)
        self.show()
        self.raise_()
        self.activateWindow()
        try:
            from AppKit import NSApplication

            NSApplication.sharedApplication().activateIgnoringOtherApps_(True)
        except Exception:
            pass

    def update_status(self, status_key: str, latency_ms: float | None = None) -> None:
        if status_key == "online":
            color, label = "#10b981", "ONLINE"
        elif status_key == "unstable":
            color, label = "#f59e0b", "INSTABILE"
        else:
            color, label = "#ef4444", "OFFLINE"
        self._dot.setStyleSheet(f"color: {color};")
        self._status.setText(label)
        if latency_ms is not None:
            self._status.setText(f"{label} — {latency_ms:.0f} ms")

    def set_status_icon_path(self, path: Path | str) -> None:
        name = Path(path).name
        key = "online" if "green" in name else "unstable" if "yellow" in name else "offline"
        self.update_status(key)

    def _open_menu(self) -> None:
        menu = None
        if self.tray_icon is not None:
            getter = getattr(self.tray_icon, "contextMenu", None)
            if callable(getter):
                menu = getter()
            if menu is None:
                menu = getattr(self.tray_icon, "_context_menu", None)
        if menu is not None:
            menu.exec(self._menu_btn.mapToGlobal(self._menu_btn.rect().bottomLeft()))

    def closeEvent(self, event) -> None:
        event.ignore()
        self.hide()


def create_macos_control_panel(tray_icon) -> MacOSControlPanel | None:
    if sys.platform != "darwin":
        return None
    return MacOSControlPanel(tray_icon)
