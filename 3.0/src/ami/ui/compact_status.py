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

from ami.core.paths import get_base_path
from ami.ui.themes import resolve_theme


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
        self.setFixedSize(180, 140)

        theme = config.get("ui", {}).get("theme", "auto")
        self._dark = resolve_theme(theme) == "dark"
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(self._shell_qss())

        lay = QVBoxLayout(self)
        lay.setSpacing(2)
        lay.setContentsMargins(16, 14, 16, 12)

        title = QLabel("AMI")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Helvetica Neue", 12, QFont.Weight.Bold))
        title.setStyleSheet(self._lbl_qss("#94a3b8" if self._dark else "#57534e"))
        lay.addWidget(title)

        self.status_label = QLabel("●")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setFont(QFont("Helvetica Neue", 36, QFont.Weight.Black))
        self.status_label.setStyleSheet(self._lbl_qss("#fb7185"))
        lay.addWidget(self.status_label)

        self.latency_label = QLabel("—")
        self.latency_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.latency_label.setFont(QFont("Helvetica Neue", 22, QFont.Weight.Black))
        self.latency_label.setStyleSheet(self._lbl_qss(self._muted()))
        lay.addWidget(self.latency_label)

        self.latency_unit = QLabel("ms")
        self.latency_unit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.latency_unit.setFont(QFont("Helvetica Neue", 10, QFont.Weight.Medium))
        self.latency_unit.setStyleSheet(self._lbl_qss(self._muted()))
        lay.addWidget(self.latency_unit)

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

    def _muted(self) -> str:
        return "#94a3b8" if self._dark else "#78716c"

    def _lbl_qss(self, color: str) -> str:
        return f"border: none; outline: none; background: transparent; color: {color};"

    def _shell_qss(self) -> str:
        if self._dark:
            return """
                QFrame#CompactStatusWindow {
                    background: #0f172a;
                    border: 2px solid #10b981;
                    border-radius: 16px;
                }
            """
        return """
            QFrame#CompactStatusWindow {
                background: #ffffff;
                border: 2px solid #10b981;
                border-radius: 16px;
            }
        """

    def _menu_qss(self) -> str:
        c = "#64748b" if self._dark else "#57534e"
        h = "#e2e8f0" if self._dark else "#1c1917"
        return f"""
            QPushButton {{
                border: none;
                background: transparent;
                color: {c};
                padding: 4px 12px;
                font-weight: 600;
            }}
            QPushButton:hover {{ color: {h}; }}
            QPushButton:pressed {{ color: {h}; }}
        """

    def update_status(self, status) -> None:
        if status.status == "online":
            color = "#2dd4bf"
            border = "#10b981"
        elif status.status == "unstable":
            color = "#fbbf24"
            border = "#f59e0b"
        else:
            color = "#fb7185"
            border = "#ef4444"
        self.status_label.setText("●")
        self.status_label.setStyleSheet(self._lbl_qss(color))
        bg = "#0f172a" if self._dark else "#ffffff"
        self.setStyleSheet(
            f"""
            QFrame#CompactStatusWindow {{
                background: {bg};
                border: 2px solid {border};
                border-radius: 16px;
            }}
            """
        )

        if getattr(status, "avg_latency_ms", None) is not None:
            self.latency_label.setText(f"{status.avg_latency_ms:.0f}")
            self.latency_unit.setVisible(True)
        else:
            self.latency_label.setText("—")
            self.latency_unit.setVisible(False)

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
