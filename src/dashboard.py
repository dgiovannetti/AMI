"""
AMI - Active Monitor of Internet
Dashboard - Dark Neon Compact UI

Compact, legible, dark-themed dashboard with accent StatCards
"""

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QLabel, QPushButton, QFrame, QGridLayout,
                            QGraphicsDropShadowEffect, QGraphicsOpacityEffect, QGraphicsBlurEffect)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint, QPropertyAnimation, QParallelAnimationGroup
from PyQt6.QtGui import QFont, QColor, QPixmap, QPainter, QLinearGradient, QPen
from pathlib import Path
import sys
import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class StatCard(QFrame):
    """Modern metric card: clean, professional, Stripe-inspired"""
    def __init__(self, title: str, accent_color: str, initial_value: str = "--"):
        super().__init__()
        self.accent_color = accent_color
        self.setStyleSheet(f"""
            QFrame {{
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 12px;
            }}
        """)
        
        # Subtle shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

        col = QVBoxLayout(self)
        col.setSpacing(12)
        col.setContentsMargins(20, 20, 20, 20)

        # Title - clean, readable
        self.title = QLabel(title)
        title_font = QFont()
        title_font.setPointSize(11)
        title_font.setWeight(QFont.Weight.Medium)
        self.title.setFont(title_font)
        self.title.setStyleSheet("color: #6B7280;")
        col.addWidget(self.title)

        # Value - large, bold
        self.value = QLabel(initial_value)
        vf = QFont()
        vf.setPointSize(32)
        vf.setWeight(QFont.Weight.Bold)
        self.value.setFont(vf)
        self.value.setStyleSheet(f"color: {accent_color};")
        col.addWidget(self.value)

    def set_value(self, text: str):
        self.value.setText(text)

    def set_accent_color(self, color: str):
        self.accent_color = color
        self.value.setStyleSheet(f"color: {self.accent_color};")

    def pulse(self):
        pass

    def flash_value(self):
        pass


class EnterpriseDashboard(QMainWindow):
    """Ultra professional enterprise dashboard"""

    def __init__(self, config: dict, monitor, tray_icon=None):
        super().__init__()
        self.config = config
        self.monitor = monitor
        self.tray_icon = tray_icon

        # Window setup - Modern clean
        self.setWindowTitle("AMI - Network Monitor")
        self.setGeometry(100, 100, 1100, 700)
        self.setMinimumSize(900, 600)
        self.setStyleSheet("""
            QMainWindow { 
                background-color: #F9FAFB;
            }
            QPushButton {
                background-color: #3B82F6;
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
            QPushButton:pressed {
                background-color: #1D4ED8;
            }
        """)

        self.setup_ui()

        # Auto-refresh
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(5000)

    def setup_ui(self):
        """Setup ultra clean enterprise UI"""

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # === TOP BAR === Modern header
        self.top_bar = QFrame()
        self.top_bar.setStyleSheet("""
            QFrame { 
                background-color: #FFFFFF; 
                border-bottom: 1px solid #E5E7EB; 
                padding: 16px 32px;
            }
        """)
        top_layout = QHBoxLayout(self.top_bar)

        # Logo area (use resources/ami_logo.png)
        self.logo_label = QLabel()
        self.logo_label.setObjectName("ami_logo")
        self._set_logo_pixmap(self.logo_label, height=28)
        top_layout.addWidget(self.logo_label)

        top_layout.addStretch()

        # Modern branding
        app_cfg = self.config.get('app', {})
        brand = QLabel("AMI")
        brand_font = QFont()
        brand_font.setPointSize(20)
        brand_font.setWeight(QFont.Weight.Bold)
        brand.setFont(brand_font)
        brand.setStyleSheet("color: #111827;")
        top_layout.addWidget(brand)
        
        subtitle = QLabel("Network Monitor")
        subtitle_font = QFont()
        subtitle_font.setPointSize(11)
        subtitle.setFont(subtitle_font)
        subtitle.setStyleSheet("color: #6B7280; margin-left: 12px;")
        top_layout.addWidget(subtitle)

        main_layout.addWidget(self.top_bar)

        # === MAIN CONTENT === Clean canvas
        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("""
            QWidget { background-color: #F9FAFB; }
        """)
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setSpacing(24)
        content_layout.setContentsMargins(32, 32, 32, 32)

        # Hero section - clean title
        hero = QFrame()
        hero.setStyleSheet("""
            QFrame { background-color: transparent; border: none; }
        """)
        hero_layout = QVBoxLayout(hero)
        hero_layout.setSpacing(4)
        hero_layout.setContentsMargins(0, 0, 0, 16)

        self.main_title = QLabel("Connection Status")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setWeight(QFont.Weight.Bold)
        self.main_title.setFont(title_font)
        self.main_title.setStyleSheet("color: #111827;")
        hero_layout.addWidget(self.main_title)
        
        subtitle = QLabel("Real-time network monitoring")
        subtitle_font = QFont()
        subtitle_font.setPointSize(13)
        subtitle.setFont(subtitle_font)
        subtitle.setStyleSheet("color: #6B7280;")
        hero_layout.addWidget(subtitle)

        content_layout.addWidget(hero)

        # === STATUS GRID ===
        self.status_grid = QGridLayout()
        self.status_grid.setSpacing(10)
        self.status_grid.setContentsMargins(0, 0, 0, 0)

        # Stat cards (Modern colors)
        self.card_status = StatCard("Connection Status", "#10B981", "--")
        self.card_latency = StatCard("Average Latency", "#3B82F6", "--")
        self.card_uptime = StatCard("Uptime", "#8B5CF6", "--")
        self.card_success = StatCard("Success Rate", "#F59E0B", "--")

        self.status_cards = [self.card_status, self.card_latency, self.card_uptime, self.card_success]
        self.rebuild_status_grid(cols=4)

        content_layout.addLayout(self.status_grid)

        # Charts section - modern container
        charts_section = QFrame()
        charts_section.setStyleSheet("""
            QFrame { 
                background-color: #FFFFFF; 
                border: 1px solid #E5E7EB; 
                border-radius: 12px; 
                padding: 24px;
            }
        """)
        # Subtle shadow
        chart_shadow = QGraphicsDropShadowEffect()
        chart_shadow.setColor(QColor(0, 0, 0, 30))
        chart_shadow.setBlurRadius(20)
        chart_shadow.setOffset(0, 4)
        charts_section.setGraphicsEffect(chart_shadow)
        charts_layout = QVBoxLayout(charts_section)

        charts_title = QLabel("Network Analytics")
        ct_font = QFont()
        ct_font.setPointSize(16)
        ct_font.setWeight(QFont.Weight.Bold)
        charts_title.setFont(ct_font)
        charts_title.setStyleSheet("color: #111827; margin-bottom: 12px;")
        charts_layout.addWidget(charts_title)

        # Charts area
        self.figure = Figure(figsize=(10.5, 4.2), facecolor='#FFFFFF')
        self.canvas = FigureCanvas(self.figure)
        charts_layout.addWidget(self.canvas)

        # Create subplots
        self.figure.subplots_adjust(left=0.07, right=0.98, top=0.92, bottom=0.12, hspace=0.32)
        self.ax1 = self.figure.add_subplot(211, facecolor='#F9FAFB')
        self.ax2 = self.figure.add_subplot(212, facecolor='#F9FAFB')

        # Style charts - modern
        for ax in [self.ax1, self.ax2]:
            ax.set_title('Connection Status', color='#111827', fontsize=11, fontweight='bold')
        self.ax1.set_ylabel('Status', color='#6B7280', fontsize=10)
        self.ax1.set_xlabel('Recent Checks', color='#9CA3AF', fontsize=9)
        self.ax1.grid(True, alpha=0.1, color='#D1D5DB')
        self.ax1.tick_params(colors='#6B7280', labelsize=9)
        self.ax1.spines['top'].set_visible(False)
        self.ax1.spines['right'].set_visible(False)
        self.ax1.spines['left'].set_color('#E5E7EB')
        self.ax1.spines['bottom'].set_color('#E5E7EB')
        self.ax1.set_ylim(-0.5, 2.5)
        self.ax1.set_yticks([0, 1, 2])
        self.ax1.set_yticklabels(['Offline', 'Unstable', 'Online'])

        self.ax2.set_title('Latency (ms)', color='#111827', fontsize=11, fontweight='bold')
        self.ax2.set_ylabel('Latency (ms)', color='#6B7280', fontsize=10)
        self.ax2.set_xlabel('Recent Checks', color='#9CA3AF', fontsize=9)

        content_layout.addWidget(charts_section)

        # === BOTTOM BAR === Modern footer
        self.bottom_bar = QFrame()
        self.bottom_bar.setStyleSheet("""
            QFrame { 
                background-color: #FFFFFF; 
                border-top: 1px solid #E5E7EB; 
                padding: 16px 32px;
            }
        """)
        bottom_layout = QHBoxLayout(self.bottom_bar)

        # Footer text
        footer_text = app_cfg.get('copyright', ' 2025 CiaoIM')
        company_info = QLabel(footer_text)
        company_info.setStyleSheet("color: #9CA3AF; font-size: 11px;")
        bottom_layout.addWidget(company_info)

        bottom_layout.addStretch()

        # Right - controls
        controls_layout = QHBoxLayout()

        refresh_btn = QPushButton(" Refresh")
        refresh_btn.clicked.connect(self.refresh_data)
        controls_layout.addWidget(refresh_btn)

        controls_layout.addSpacing(8)

        hide_btn = QPushButton(" Minimize")
        hide_btn.clicked.connect(self.hide)
        controls_layout.addWidget(hide_btn)

        controls_layout.addSpacing(8)

        close_btn = QPushButton(" Close")
        close_btn.clicked.connect(self.close)
        controls_layout.addWidget(close_btn)

        bottom_layout.addLayout(controls_layout)

        # Compact widget (hidden by default) - logo + traffic light + ping
        self.compact_widget = self._build_compact_widget()
        self.compact_widget.setVisible(False)

        # add content first, then compact placeholder, then bottom bar (footer)
        main_layout.addWidget(self.content_widget)
        main_layout.addWidget(self.compact_widget)
        main_layout.addWidget(self.bottom_bar)
        
        # Apply initial layout logic based on current size
        self._apply_layout_for_size()

    def rebuild_status_grid(self, cols: int):
        # clear grid
        while self.status_grid.count():
            item = self.status_grid.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
        # re-add
        for i, card in enumerate(self.status_cards):
            r = i // cols
            c = i % cols
            self.status_grid.addWidget(card, r, c)

    def apply_scale(self, scale: float):
        scale = max(0.7, min(scale, 1.15))
        # Title scaling
        try:
            f = self.main_title.font()
            f.setPointSize(int(11 * scale))
            self.main_title.setFont(f)
        except Exception:
            pass
        # Card scaling
        for card in self.status_cards:
            try:
                vf = card.value.font()
                vf.setPointSize(max(16, int(20 * scale)))
                card.value.setFont(vf)
                tf = card.title.font()
                tf.setPointSize(max(7, int(8 * scale)))
                card.title.setFont(tf)
            except Exception:
                pass
        # Canvas scaling
        try:
            self.canvas.setMinimumHeight(int(220 * scale))
        except Exception:
            pass

    def resizeEvent(self, event):
        self._apply_layout_for_size()
        super().resizeEvent(event)

    def showEvent(self, event):
        self._apply_layout_for_size()
        super().showEvent(event)

    def _apply_layout_for_size(self):
        w = self.width()
        if w >= 1100:
            cols = 4
        elif w >= 880:
            cols = 2
        else:
            cols = 1
        self.rebuild_status_grid(cols)
        self.apply_scale(w / 950.0)
        h = self.height()
        compact = (w < 720 or h < 420)
        self._set_compact_mode(compact)

    def update_data(self, status, statistics):
        """Update cards and charts"""
        # Accessible status indicators: color + symbol
        status_map = {
            'online': ('✓ Online', '#34d399'),
            'unstable': ('! Unstable', '#fbbf24'),
            'offline': ('✕ Offline', '#ef4444')
        }
        st_text, st_color = status_map.get(status.status, ('? Unknown', '#94a3b8'))
        self.card_status.set_value(st_text)
        self.card_status.set_accent_color(st_color)
        self.card_status.pulse()

        if getattr(status, 'avg_latency_ms', None):
            self.card_latency.set_value(f"{status.avg_latency_ms:.0f} ms")
            # Update compact ping
            try:
                self.compact_ping.setText(f"{status.avg_latency_ms:.0f} ms")
            except Exception:
                pass
        else:
            self.card_latency.set_value("N/A")
            try:
                self.compact_ping.setText("N/A")
            except Exception:
                pass

        uptime_pct = statistics.get('uptime_percentage')
        if uptime_pct is None:
            try:
                uptime_pct = self.monitor.get_uptime_percentage()
            except Exception:
                uptime_pct = None
        self.card_uptime.set_value(f"{uptime_pct:.1f}%" if uptime_pct is not None else "N/A")

        success_pct = statistics.get('success_rate')
        if success_pct is None and getattr(status, 'total_pings', 0) > 0:
            success_pct = (status.successful_pings / status.total_pings) * 100
        self.card_success.set_value(f"{success_pct:.1f}%" if success_pct is not None else "N/A")

        # Update compact traffic light with accessible symbols
        try:
            # Use symbols that are distinguishable even without color
            if status.status == 'online':
                light = '✓'  # Checkmark
                color = '#34d399'
            elif status.status == 'unstable':
                light = '!'  # Exclamation
                color = '#fbbf24'
            else:  # offline
                light = '✕'  # X mark
                color = '#ef4444'
            
            self.compact_light.setText(light)
            self.compact_light.setStyleSheet(f"color: {color};")
        except Exception:
            pass

        self.update_graphs()

    def update_graphs(self):
        """Update enterprise graphs"""
        history = self.monitor.status_history
        if not history:
            return

        status_values = []
        latencies = []
        indices = list(range(len(history)))

        for h in history:
            status_map = {'online': 2, 'unstable': 1, 'offline': 0}
            status_values.append(status_map.get(h.status, 0))
            latencies.append(h.avg_latency_ms if h.avg_latency_ms else 0)

        # Status plot - modern
        self.ax1.clear()
        self.ax1.set_facecolor('#F9FAFB')
        self.ax1.set_title('Connection Status', color='#111827', fontsize=11, fontweight='bold')
        self.ax1.set_ylabel('Status', color='#6B7280', fontsize=10)
        self.ax1.set_xlabel('Recent Checks', color='#9CA3AF', fontsize=9)
        self.ax1.grid(True, alpha=0.1, color='#D1D5DB')
        self.ax1.tick_params(colors='#6B7280', labelsize=9)
        self.ax1.spines['top'].set_visible(False)
        self.ax1.spines['right'].set_visible(False)
        self.ax1.spines['left'].set_color('#E5E7EB')
        self.ax1.spines['bottom'].set_color('#E5E7EB')
        self.ax1.set_ylim(-0.5, 2.5)
        self.ax1.set_yticks([0, 1, 2])
        self.ax1.set_yticklabels(['Offline', 'Unstable', 'Online'])

        colors = ['#34d399' if sv == 2 else '#fbbf24' if sv == 1 else '#ef4444' for sv in status_values]
        self.ax1.scatter(indices, status_values, c=colors, s=60, alpha=0.9, edgecolors='white', linewidths=1.5, zorder=3)
        self.ax1.plot(indices, status_values, '-', color='#64748b', alpha=0.4, linewidth=2, zorder=2)

        # Latency plot - modern
        self.ax2.clear()
        self.ax2.set_facecolor('#F9FAFB')
        self.ax2.set_title('Latency (ms)', color='#111827', fontsize=11, fontweight='bold')
        self.ax2.set_ylabel('Latency (ms)', color='#6B7280', fontsize=10)
        self.ax2.set_xlabel('Recent Checks', color='#9CA3AF', fontsize=9)
        self.ax2.grid(True, alpha=0.1, color='#D1D5DB')
        self.ax2.tick_params(colors='#6B7280', labelsize=9)
        self.ax2.spines['top'].set_visible(False)
        self.ax2.spines['right'].set_visible(False)
        self.ax2.spines['left'].set_color('#E5E7EB')
        self.ax2.spines['bottom'].set_color('#E5E7EB')

        self.ax2.plot(indices, latencies, '-o', color='#60a5fa', linewidth=2, markersize=4, markeredgecolor='white', markeredgewidth=1.5, zorder=3)
        self.ax2.fill_between(indices, latencies, alpha=0.15, color='#60a5fa', zorder=2)

        self.canvas.draw()

    def refresh_data(self):
        """Refresh data"""
        if self.monitor.last_status:
            stats = self.monitor.get_statistics()
            self.update_data(self.monitor.last_status, stats)

    def reset_statistics(self):
        """Reset stats"""
        from PyQt6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self, 'Reset Statistics',
            'Reset all statistics?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.monitor.reset_statistics()
            self.refresh_data()

    def closeEvent(self, event):
        """Minimize to tray"""
        if self.tray_icon and self.tray_icon.isVisible():
            event.ignore()
            self.hide()
            if self.tray_icon:
                from PyQt6.QtWidgets import QSystemTrayIcon
                self.tray_icon.showMessage(
                    "AMI Dashboard",
                    "Minimized to system tray",
                    QSystemTrayIcon.MessageIcon.Information,
                    2000
                )
        else:
            event.accept()

    def changeEvent(self, event):
        """Handle minimize"""
        from PyQt6.QtCore import QEvent
        if event.type() == QEvent.Type.WindowStateChange:
            if self.isMinimized() and self.tray_icon and self.tray_icon.isVisible():
                event.ignore()
                self.hide()
        super().changeEvent(event)

    # === Helper methods for compact mode and resources ===
    def _get_resource_path(self, filename: str) -> str:
        try:
            base = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parents[1]
        except Exception:
            base = Path.cwd()
        p = base / 'resources' / filename
        if not p.exists():
            p = Path('resources') / filename
        return str(p)

    def _set_logo_pixmap(self, label: QLabel, height: int = 28):
        try:
            path = self._get_resource_path('ami_logo.png')
            pm = QPixmap(path)
            if not pm.isNull():
                label.setPixmap(pm.scaledToHeight(height, Qt.TransformationMode.SmoothTransformation))
        except Exception:
            pass

    def _build_compact_widget(self) -> QWidget:
        cw = QFrame()
        cw.setStyleSheet("""
            QFrame { background-color: #F9FAFB; border: none; }
            QLabel { color: #111827; }
        """)
        lay = QVBoxLayout(cw)
        lay.setContentsMargins(32, 48, 32, 32)
        lay.setSpacing(24)
        
        # Brand name
        brand = QLabel("AMI")
        brand_font = QFont()
        brand_font.setPointSize(24)
        brand_font.setWeight(QFont.Weight.Bold)
        brand.setFont(brand_font)
        brand.setStyleSheet("color: #111827;")
        brand.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        lay.addWidget(brand)
        
        # Status indicator
        self.compact_light = QLabel('●')
        lf = QFont()
        lf.setPointSize(72)
        self.compact_light.setFont(lf)
        self.compact_light.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        lay.addWidget(self.compact_light)
        
        # Ping
        self.compact_ping = QLabel('-- ms')
        pf = QFont()
        pf.setPointSize(32)
        pf.setWeight(QFont.Weight.Bold)
        self.compact_ping.setFont(pf)
        self.compact_ping.setStyleSheet("color: #6B7280;")
        self.compact_ping.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        lay.addWidget(self.compact_ping)
        
        lay.addStretch()
        return cw

    def _set_compact_mode(self, enabled: bool):
        # Avoid unnecessary toggles
        if getattr(self, '_compact_mode', None) == enabled:
            return
        self._compact_mode = enabled
        try:
            self.compact_widget.setVisible(enabled)
            self.content_widget.setVisible(not enabled)
            self.bottom_bar.setVisible(not enabled)
            self.top_bar.setVisible(not enabled)
        except Exception:
            pass
