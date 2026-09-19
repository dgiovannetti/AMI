"""
AMI - Compact Status Window
Small always-visible window with status (fallback when menu bar icon is not visible on macOS)
"""

from PyQt6.QtWidgets import QVBoxLayout, QLabel, QFrame, QPushButton
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QFont

from core.paths import get_base_path


class CompactStatusWindow(QFrame):
    """
    Small floating window with connection status.
    Always visible in Dock when open. Click to show main menu.
    Fallback for macOS when menu bar icon is not visible.
    """
    
    def __init__(self, config, monitor, tray_icon, parent=None):
        super().__init__(parent)
        self.config = config
        self.monitor = monitor
        self.tray_icon = tray_icon
        self._menu = None
        
        self.setWindowTitle("AMI")
        self.setWindowFlags(Qt.WindowType.Window)
        self.setFixedSize(140, 100)
        self.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 12px;
            }
            QLabel { color: #111827; }
            QPushButton {
                background-color: transparent;
                border: none;
                color: #6B7280;
                font-size: 11px;
            }
            QPushButton:hover { color: #111827; }
        """)
        
        lay = QVBoxLayout(self)
        lay.setSpacing(4)
        lay.setContentsMargins(12, 12, 12, 12)
        
        # Status indicator
        self.status_label = QLabel("●")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        f = QFont()
        f.setPointSize(28)
        f.setBold(True)
        self.status_label.setFont(f)
        self.status_label.setStyleSheet("color: #ef4444;")
        lay.addWidget(self.status_label)
        
        # Latency
        self.latency_label = QLabel("-- ms")
        self.latency_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pf = QFont()
        pf.setPointSize(12)
        pf.setWeight(QFont.Weight.Medium)
        self.latency_label.setFont(pf)
        self.latency_label.setStyleSheet("color: #6B7280;")
        lay.addWidget(self.latency_label)
        
        # Menu button
        self.menu_btn = QPushButton("Menu ▼")
        self.menu_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.menu_btn.clicked.connect(self._show_menu)
        lay.addWidget(self.menu_btn)
        
        # Set app icon so Dock shows it
        icon_path = get_base_path() / 'resources' / 'ami.png'
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
    
    def update_status(self, status):
        """Update displayed status"""
        if status.status == 'online':
            sym, color = '✓', '#10B981'
        elif status.status == 'unstable':
            sym, color = '!', '#F59E0B'
        else:
            sym, color = '✕', '#EF4444'
        
        self.status_label.setText(sym)
        self.status_label.setStyleSheet(f"color: {color};")
        
        if getattr(status, 'avg_latency_ms', None):
            self.latency_label.setText(f"{status.avg_latency_ms:.0f} ms")
        else:
            self.latency_label.setText("N/A")
    
    def _show_menu(self):
        """Show tray context menu at button position"""
        if self.tray_icon and self.tray_icon.contextMenu():
            menu = self.tray_icon.contextMenu()
            menu.exec(self.menu_btn.mapToGlobal(self.menu_btn.rect().bottomLeft()))
