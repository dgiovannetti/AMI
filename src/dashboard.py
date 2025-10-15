"""
AMI - Active Monitor of Internet
Dashboard - Dark Neon Compact UI

Compact, legible, dark-themed dashboard with accent StatCards
"""

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QLabel, QPushButton, QFrame, QGridLayout,
                            QGraphicsDropShadowEffect, QGraphicsOpacityEffect)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QColor, QPixmap
from pathlib import Path
import sys
import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class StatCard(QFrame):
    """Compact stat card with left accent bar and large value"""
    def __init__(self, title: str, accent_color: str, initial_value: str = "--"):
        super().__init__()
        self.accent_color = accent_color
        self.setStyleSheet(
            """
            QFrame {
                background-color: rgba(15, 23, 42, 0.8);
                border: 1px solid #334155;
                border-radius: 8px;
            }
            QLabel { color: #e2e8f0; }
            """
        )

        root = QHBoxLayout(self)
        root.setContentsMargins(10, 8, 10, 8)
        root.setSpacing(10)

        self.accent = QFrame()
        self.accent.setFixedWidth(4)
        self.accent.setStyleSheet(f"background-color: {self.accent_color}; border-radius: 2px;")
        root.addWidget(self.accent)
        # subtle glow effect for pulse animation
        self.glow = QGraphicsDropShadowEffect(self.accent)
        self.glow.setOffset(0, 0)
        self.glow.setBlurRadius(0)
        self.glow.setColor(QColor(self.accent_color))
        self.accent.setGraphicsEffect(self.glow)

        col = QVBoxLayout()
        col.setSpacing(2)
        col.setContentsMargins(0, 0, 0, 0)

        self.title = QLabel(title.upper())
        tf = QFont()
        tf.setPointSize(9)
        tf.setBold(True)
        self.title.setFont(tf)
        self.title.setStyleSheet(f"color: {self.accent_color};")
        col.addWidget(self.title)

        self.value = QLabel(initial_value)
        vf = QFont()
        vf.setPointSize(20)
        vf.setBold(True)
        self.value.setFont(vf)
        self.value.setStyleSheet("color: #e2e8f0;")
        col.addWidget(self.value)
        # opacity effect to flash on value updates
        self.value_fx = QGraphicsOpacityEffect(self.value)
        self.value.setGraphicsEffect(self.value_fx)
        self.value_fx.setOpacity(1.0)

        root.addLayout(col)

    def set_value(self, text: str):
        self.value.setText(text)
        self.flash_value()

    def set_accent_color(self, color: str):
        self.accent_color = color
        self.accent.setStyleSheet(f"background-color: {color}; border-radius: 2px;")
        self.title.setStyleSheet(f"color: {color};")
        if hasattr(self, 'glow'):
            self.glow.setColor(QColor(color))

    def pulse(self):
        if not hasattr(self, 'glow'):
            return
        anim = QPropertyAnimation(self.glow, b"blurRadius")
        anim.setDuration(400)
        anim.setStartValue(0)
        anim.setKeyValueAt(0.5, 18)
        anim.setEndValue(0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.start()
        self._glow_anim = anim  # keep reference

    def flash_value(self):
        if not hasattr(self, 'value_fx'):
            return
        anim = QPropertyAnimation(self.value_fx, b"opacity")
        anim.setDuration(220)
        anim.setStartValue(0.35)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.start()
        self._val_anim = anim  # keep reference


class EnterpriseDashboard(QMainWindow):
    """Ultra professional enterprise dashboard"""

    def __init__(self, config: dict, monitor, tray_icon=None):
        super().__init__()
        self.config = config
        self.monitor = monitor
        self.tray_icon = tray_icon

        # Window setup - dark compact
        self.setWindowTitle("AMI - Dashboard")
        self.setGeometry(100, 100, 950, 600)
        # Allow smaller sizes and switch to compact UI automatically
        self.setMinimumSize(280, 200)
        self.setStyleSheet("""
            QMainWindow { background-color: #0b1220; }
            QPushButton {
                background-color: #1f2937;
                color: #e5e7eb;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
            }
            QPushButton:hover { border-color: #34d399; background-color: #111827; }
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

        # === TOP BAR ===
        top_bar = QFrame()
        top_bar.setStyleSheet("""
            QFrame { background-color: #0f172a; border-bottom: 1px solid #1f2937; padding: 10px 14px; }
        """)
        top_layout = QHBoxLayout(top_bar)

        # Logo area (use resources/ami_logo.png)
        self.logo_label = QLabel()
        self.logo_label.setObjectName("ami_logo")
        self._set_logo_pixmap(self.logo_label, height=28)
        top_layout.addWidget(self.logo_label)

        top_layout.addStretch()

        # Credits (from config)
        app_cfg = self.config.get('app', {})
        copyright_text = app_cfg.get('copyright', '© 2025 CiaoIM™')
        website = app_cfg.get('website', '')
        extra_credits = app_cfg.get('credits', '')
        top_text = " • ".join([t for t in [copyright_text, extra_credits, website] if t])
        credits = QLabel(top_text)
        credits_font = QFont()
        credits_font.setPointSize(9)
        credits.setFont(credits_font)
        credits.setStyleSheet("color: #94a3b8;")
        top_layout.addWidget(credits)

        main_layout.addWidget(top_bar)

        # === MAIN CONTENT ===
        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("""
            QWidget { background-color: #0b1220; padding: 12px; }
        """)
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setSpacing(12)

        # Title section
        title_section = QFrame()
        title_section.setStyleSheet("""
            QFrame { background-color: #0f172a; border: 1px solid #334155; border-radius: 8px; padding: 10px; }
        """)
        title_layout = QVBoxLayout(title_section)

        self.main_title = QLabel("AMI • Active Monitor of Internet")
        main_title_font = QFont()
        main_title_font.setPointSize(18)
        main_title_font.setBold(True)
        self.main_title.setFont(main_title_font)
        self.main_title.setStyleSheet("color: #e2e8f0;")
        title_layout.addWidget(self.main_title)

        self.subtitle = QLabel("Sai se sei davvero online • Real-time monitoring • Notifications • Analytics")
        subtitle_font = QFont()
        subtitle_font.setPointSize(10)
        self.subtitle.setFont(subtitle_font)
        self.subtitle.setStyleSheet("color: #94a3b8; margin-top: 2px;")
        title_layout.addWidget(self.subtitle)

        content_layout.addWidget(title_section)

        # === STATUS GRID ===
        self.status_grid = QGridLayout()
        self.status_grid.setSpacing(10)
        self.status_grid.setContentsMargins(0, 0, 0, 0)

        # Stat cards (dark neon)
        self.card_status = StatCard("Connection Status", "#34d399", "--")
        self.card_latency = StatCard("Latency", "#fbbf24", "--")
        self.card_uptime = StatCard("Uptime", "#60a5fa", "--")
        self.card_success = StatCard("Success Rate", "#a78bfa", "--")

        self.status_cards = [self.card_status, self.card_latency, self.card_uptime, self.card_success]
        self.rebuild_status_grid(cols=4)

        content_layout.addLayout(self.status_grid)

        # === CHARTS SECTION ===
        charts_section = QFrame()
        charts_section.setStyleSheet("""
            QFrame { background-color: #0f172a; border: 1px solid #334155; border-radius: 8px; padding: 8px; }
        """)
        charts_layout = QVBoxLayout(charts_section)

        charts_title = QLabel("Connection Analytics")
        charts_title_font = QFont()
        charts_title_font.setPointSize(12)
        charts_title_font.setBold(True)
        charts_title.setFont(charts_title_font)
        charts_title.setStyleSheet("color: #e2e8f0;")
        charts_layout.addWidget(charts_title)

        # Charts area
        self.figure = Figure(figsize=(10.5, 4.2), facecolor='#0f172a')
        self.canvas = FigureCanvas(self.figure)
        charts_layout.addWidget(self.canvas)

        # Create subplots
        self.figure.subplots_adjust(left=0.07, right=0.98, top=0.92, bottom=0.12, hspace=0.32)
        self.ax1 = self.figure.add_subplot(211, facecolor='#0b1220')
        self.ax2 = self.figure.add_subplot(212, facecolor='#0b1220')

        # Style charts - dark neon
        for ax in [self.ax1, self.ax2]:
            ax.tick_params(colors='#94a3b8', labelsize=9)
            ax.grid(True, alpha=0.25, color='#334155', linewidth=0.7)
            for spine in ax.spines.values():
                spine.set_color('#334155')
                spine.set_linewidth(1)

        self.ax1.set_title('Connection Status', color='#e2e8f0', fontsize=11, fontweight='bold')
        self.ax1.set_ylabel('Status', color='#cbd5e1', fontsize=10)
        self.ax1.set_ylim(-0.5, 2.5)
        self.ax1.set_yticks([0, 1, 2])
        self.ax1.set_yticklabels(['Offline', 'Unstable', 'Online'])

        self.ax2.set_title('Latency (ms)', color='#e2e8f0', fontsize=11, fontweight='bold')
        self.ax2.set_ylabel('Latency (ms)', color='#cbd5e1', fontsize=10)
        self.ax2.set_xlabel('Recent Checks', color='#94a3b8', fontsize=9)

        content_layout.addWidget(charts_section)

        # === BOTTOM BAR ===
        self.bottom_bar = QFrame()
        self.bottom_bar.setStyleSheet("""
            QFrame { background-color: #0f172a; border-top: 1px solid #1f2937; padding: 10px 14px; }
        """)
        bottom_layout = QHBoxLayout(self.bottom_bar)

        # Left - company info (from config)
        tagline = app_cfg.get('tagline', '')
        bottom_text = " • ".join([t for t in [copyright_text, extra_credits, tagline] if t])
        company_info = QLabel(bottom_text)
        company_info.setStyleSheet("color: #94a3b8; font-size: 10px;")
        bottom_layout.addWidget(company_info)

        bottom_layout.addStretch()

        # Right - controls
        controls_layout = QHBoxLayout()

        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh_data)
        controls_layout.addWidget(refresh_btn)

        controls_layout.addSpacing(8)

        hide_btn = QPushButton("⬇ Minimize")
        hide_btn.clicked.connect(self.hide)
        controls_layout.addWidget(hide_btn)

        controls_layout.addSpacing(8)

        close_btn = QPushButton("✕ Close")
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
        f = self.main_title.font(); f.setPointSize(int(18 * scale)); self.main_title.setFont(f)
        f2 = self.subtitle.font(); f2.setPointSize(int(10 * scale)); self.subtitle.setFont(f2)
        for card in self.status_cards:
            vf = card.value.font(); vf.setPointSize(max(14, int(20 * scale))); card.value.setFont(vf)
            tf = card.title.font(); tf.setPointSize(max(8, int(9 * scale))); card.title.setFont(tf)
        try:
            self.canvas.setMinimumHeight(int(220 * scale))
        except Exception:
            pass

    def resizeEvent(self, event):
        w = self.width()
        if w >= 1100:
            cols = 4
        elif w >= 880:
            cols = 2
        else:
            cols = 1
        self.rebuild_status_grid(cols)
        self.apply_scale(w / 950.0)
        # Toggle compact mode when window is too small
        h = self.height()
        compact = (w < 720 or h < 420)
        self._set_compact_mode(compact)
        super().resizeEvent(event)

    def update_data(self, status, statistics):
        """Update cards and charts"""
        status_map = {
            'online': ('🟢 Online', '#34d399'),
            'unstable': ('🟡 Unstable', '#fbbf24'),
            'offline': ('🔴 Offline', '#ef4444')
        }
        st_text, st_color = status_map.get(status.status, ('⚫ Unknown', '#94a3b8'))
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

        # Update compact traffic light
        try:
            light = '🟢' if status.status == 'online' else '🟡' if status.status == 'unstable' else '🔴'
            self.compact_light.setText(light)
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

        # Status plot - dark
        self.ax1.clear()
        self.ax1.set_facecolor('#0b1220')
        self.ax1.set_title('Connection Status', color='#e2e8f0', fontsize=11, fontweight='bold')
        self.ax1.set_ylabel('Status', color='#cbd5e1', fontsize=10)
        self.ax1.set_ylim(-0.5, 2.5)
        self.ax1.set_yticks([0, 1, 2])
        self.ax1.set_yticklabels(['Offline', 'Unstable', 'Online'])
        self.ax1.tick_params(colors='#94a3b8', labelsize=9)
        self.ax1.grid(True, alpha=0.25, color='#334155', linewidth=0.7)
        for spine in self.ax1.spines.values():
            spine.set_color('#334155')
            spine.set_linewidth(1)

        colors = ['#34d399' if sv == 2 else '#fbbf24' if sv == 1 else '#ef4444' for sv in status_values]
        self.ax1.scatter(indices, status_values, c=colors, s=60, alpha=0.9, edgecolors='white', linewidths=1.5, zorder=3)
        self.ax1.plot(indices, status_values, '-', color='#64748b', alpha=0.4, linewidth=2, zorder=2)

        # Latency plot - dark
        self.ax2.clear()
        self.ax2.set_facecolor('#0b1220')
        self.ax2.set_title('Latency (ms)', color='#e2e8f0', fontsize=11, fontweight='bold')
        self.ax2.set_ylabel('Latency (ms)', color='#cbd5e1', fontsize=10)
        self.ax2.set_xlabel('Recent Checks', color='#94a3b8', fontsize=9)
        self.ax2.tick_params(colors='#94a3b8', labelsize=9)
        self.ax2.grid(True, alpha=0.25, color='#334155', linewidth=0.7)
        for spine in self.ax2.spines.values():
            spine.set_color('#334155')
            spine.set_linewidth(1)

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
            QFrame { background-color: #0f172a; border: none; }
            QLabel { color: #e2e8f0; }
        """)
        lay = QVBoxLayout(cw)
        lay.setContentsMargins(16, 20, 16, 16)
        lay.setSpacing(10)
        # Logo on top
        self.compact_logo = QLabel()
        self._set_logo_pixmap(self.compact_logo, height=40)
        self.compact_logo.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        lay.addWidget(self.compact_logo)
        # Row: traffic light + ping
        row = QHBoxLayout()
        row.setSpacing(8)
        row.setContentsMargins(0, 0, 0, 0)
        self.compact_light = QLabel('•')
        lf = QFont(); lf.setPointSize(28); lf.setBold(True)
        self.compact_light.setFont(lf)
        row.addWidget(self.compact_light)
        self.compact_ping = QLabel('-- ms')
        pf = QFont(); pf.setPointSize(18); pf.setBold(True)
        self.compact_ping.setFont(pf)
        row.addWidget(self.compact_ping)
        row.addStretch()
        lay.addLayout(row)
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
        except Exception:
            pass
