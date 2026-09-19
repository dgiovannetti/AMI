"""
AMI 3.0 — Compact status window (Dock / menu-bar fallback).
"""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon, QCloseEvent
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from ami.core.models import reason_text
from ami.core.paths import get_base_path
from ami.ui.themes import palette, status_color


class CompactStatusWindow(QFrame):
    """Small floating status; always-on-top on macOS."""

    def __init__(self, config: dict, monitor, tray_icon, parent=None):
        super().__init__(parent)
        self.config = config
        self.monitor = monitor
        self.tray_icon = tray_icon
        self.setObjectName("CompactStatusWindow")
        self.setWindowTitle("AMI")
        flags = Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.setFixedWidth(220)

        theme = config.get("ui", {}).get("theme", "auto")
        self._pal = palette(theme)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(self._shell_qss())

        lay = QVBoxLayout(self)
        lay.setSpacing(4)
        lay.setContentsMargins(16, 14, 16, 12)

        title = QLabel("AMI")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Helvetica Neue", 11, QFont.Weight.DemiBold))
        title.setStyleSheet(self._lbl_qss(self._pal.muted))
        lay.addWidget(title)

        self.status_label = QLabel("—")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setFont(QFont("Helvetica Neue", 16, QFont.Weight.Bold))
        self.status_label.setStyleSheet(self._lbl_qss(self._pal.text))
        lay.addWidget(self.status_label)

        self.reason_label = QLabel("")
        self.reason_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.reason_label.setWordWrap(True)
        self.reason_label.setFont(QFont("Helvetica Neue", 11, QFont.Weight.Medium))
        self.reason_label.setStyleSheet(self._lbl_qss(self._pal.muted))
        self.reason_label.setVisible(False)
        lay.addWidget(self.reason_label)

        self.latency_label = QLabel("—")
        self.latency_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.latency_label.setFont(QFont("Helvetica Neue", 22, QFont.Weight.Bold))
        self.latency_label.setStyleSheet(self._lbl_qss(self._pal.text))
        lay.addWidget(self.latency_label)

        lay.addStretch(1)

        row = QHBoxLayout()
        row.addStretch()
        self.menu_btn = QPushButton("Menu")
        self.menu_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.menu_btn.setFont(QFont("Helvetica Neue", 11, QFont.Weight.DemiBold))
        self.menu_btn.setStyleSheet(self._menu_qss())
        self.menu_btn.clicked.connect(self._show_menu)
        row.addWidget(self.menu_btn)
        row.addStretch()
        lay.addLayout(row)

        icon_path = get_base_path() / "resources" / "ami.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

    def _lbl_qss(self, color: str) -> str:
        return f"border: none; outline: none; background: transparent; color: {color};"

    def _shell_qss(self) -> str:
        p = self._pal
        return f"""
            QFrame#CompactStatusWindow {{
                background: {p.surface};
                border: 1px solid {p.border};
                border-radius: 12px;
            }}
        """

    def _menu_qss(self) -> str:
        p = self._pal
        return f"""
            QPushButton {{
                border: 1px solid {p.border};
                background: {p.surface};
                color: {p.text};
                border-radius: 8px;
                padding: 4px 12px;
                font-weight: 600;
            }}
            QPushButton:hover {{ border-color: {p.text}; }}
        """

    def update_status(self, status) -> None:
        glyphs = {"online": "✓", "unstable": "!", "captive": "!", "offline": "✕"}
        names = {"online": "Online", "unstable": "Unstable", "captive": "Captive", "offline": "Offline"}
        glyph = glyphs.get(status.status, "✕")
        name = names.get(status.status, "Unknown")
        color = status_color(self._pal, status.status)
        self.status_label.setText(f"{glyph}  {name}")
        self.status_label.setAccessibleName(name)
        self.status_label.setStyleSheet(self._lbl_qss(color))
        reason = getattr(status, "reason", None)
        if reason and reason != "ok":
            text = reason_text(reason)
            self.reason_label.setText(text)
            self.reason_label.setVisible(True)
            self.status_label.setAccessibleDescription(text)
        else:
            self.reason_label.setText("")
            self.reason_label.setVisible(False)
            self.status_label.setAccessibleDescription("")

        if getattr(status, "avg_latency_ms", None) is not None:
            self.latency_label.setText(f"{status.avg_latency_ms:.0f} ms")
        else:
            self.latency_label.setText("—")
        self.adjustSize()

    def _show_menu(self) -> None:
        menu = None
        if self.tray_icon is not None:
            getter = getattr(self.tray_icon, "contextMenu", None)
            if callable(getter):
                menu = getter()
            if menu is None:
                menu = getattr(self.tray_icon, "_context_menu", None)
        if menu is not None:
            menu.exec(self.menu_btn.mapToGlobal(self.menu_btn.rect().bottomLeft()))

    def closeEvent(self, event: QCloseEvent) -> None:
        event.ignore()
        self.hide()
