"""
AMI 3.0 — Compact status window (Dock fallback): minimal chrome, no nested frames.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QIcon
from PyQt6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from ami.core.paths import get_base_path
from ami.ui.themes import resolve_theme


class CompactStatusWindow(QFrame):
    """Small floating status; avoids global theme QFrame borders on content."""

    def __init__(self, config: dict, monitor, tray_icon, parent=None):
        super().__init__(parent)
        self.config = config
        self.monitor = monitor
        self.tray_icon = tray_icon
        self.setObjectName("CompactStatusWindow")
        self.setWindowTitle("AMI")
        self.setWindowFlags(Qt.WindowType.Window)
        self.setFixedSize(168, 128)

        theme = config.get("ui", {}).get("theme", "auto")
        self._dark = resolve_theme(theme) == "dark"
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(32)
        shadow.setOffset(0, 12)
        shadow.setColor(QColor(0, 0, 0, 38 if self._dark else 22))
        self.setGraphicsEffect(shadow)

        self.setStyleSheet(self._shell_qss())

        lay = QVBoxLayout(self)
        lay.setSpacing(2)
        lay.setContentsMargins(16, 14, 16, 12)

        # Single visual anchor: large status dot (no extra pill / box)
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
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #0c1220, stop:1 #111827);
                    border: none;
                    border-radius: 20px;
                }
            """
        return """
            QFrame#CompactStatusWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #faf8f6, stop:1 #f0ebe6);
                border: none;
                border-radius: 20px;
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
        elif status.status == "unstable":
            color = "#fbbf24"
        else:
            color = "#fb7185"
        self.status_label.setText("●")
        self.status_label.setStyleSheet(self._lbl_qss(color))

        if getattr(status, "avg_latency_ms", None) is not None:
            self.latency_label.setText(f"{status.avg_latency_ms:.0f}")
            self.latency_unit.setVisible(True)
        else:
            self.latency_label.setText("—")
            self.latency_unit.setVisible(False)

    def _show_menu(self) -> None:
        if self.tray_icon and self.tray_icon.contextMenu():
            menu = self.tray_icon.contextMenu()
            menu.exec(self.menu_btn.mapToGlobal(self.menu_btn.rect().bottomLeft()))
