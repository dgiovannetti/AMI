"""
AMI 3.0 - Compact status window (Dock fallback when menu bar icon is hidden).
"""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout

from ami.core.paths import get_base_path


class CompactStatusWindow(QFrame):
    def __init__(self, config: dict, monitor, tray_icon, parent=None):
        super().__init__(parent)
        self.config = config
        self.monitor = monitor
        self.tray_icon = tray_icon
        self.setWindowTitle("AMI")
        self.setWindowFlags(Qt.WindowType.Window)
        self.setFixedSize(140, 100)
        theme = config.get("ui", {}).get("theme", "auto")
        from ami.ui.themes import get_stylesheet
        self.setStyleSheet(get_stylesheet(theme) + """
            QFrame { border-radius: 12px; }
            QLabel { color: #111827; }
            QPushButton { background-color: transparent; border: none; color: #6b7280; font-size: 11px; }
            QPushButton:hover { color: #111827; }
        """)
        lay = QVBoxLayout(self)
        lay.setSpacing(4)
        lay.setContentsMargins(12, 12, 12, 12)
        self.status_label = QLabel("●")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        f = QFont()
        f.setPointSize(28)
        f.setBold(True)
        self.status_label.setFont(f)
        self.status_label.setStyleSheet("color: #ef4444;")
        lay.addWidget(self.status_label)
        self.latency_label = QLabel("-- ms")
        self.latency_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pf = QFont()
        pf.setPointSize(12)
        pf.setWeight(QFont.Weight.Medium)
        self.latency_label.setFont(pf)
        self.latency_label.setStyleSheet("color: #6b7280;")
        lay.addWidget(self.latency_label)
        self.menu_btn = QPushButton("Menu ▼")
        self.menu_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.menu_btn.clicked.connect(self._show_menu)
        lay.addWidget(self.menu_btn)
        icon_path = get_base_path() / "resources" / "ami.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

    def update_status(self, status) -> None:
        if status.status == "online":
            sym, color = "✓", "#10b981"
        elif status.status == "unstable":
            sym, color = "!", "#f59e0b"
        else:
            sym, color = "✕", "#ef4444"
        self.status_label.setText(sym)
        self.status_label.setStyleSheet(f"color: {color};")
        if getattr(status, "avg_latency_ms", None) is not None:
            self.latency_label.setText(f"{status.avg_latency_ms:.0f} ms")
        else:
            self.latency_label.setText("N/A")

    def _show_menu(self) -> None:
        if self.tray_icon and self.tray_icon.contextMenu():
            menu = self.tray_icon.contextMenu()
            menu.exec(self.menu_btn.mapToGlobal(self.menu_btn.rect().bottomLeft()))
