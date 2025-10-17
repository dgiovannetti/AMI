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
    """Cyberpunk metric card: neon borders, glitch aesthetic, monospace"""
    def __init__(self, title: str, accent_color: str, initial_value: str = "--"):
        super().__init__()
        self.accent_color = accent_color
        # Cyberpunk: angled corners, thick neon borders
        self.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0D0221, stop:1 #160633);
                border: 2px solid {accent_color};
                border-radius: 0px;
                padding: 20px 24px;
            }}
        """)

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

        # Title - cyberpunk style: monospace, cyan
        self.title = QLabel(f"// {title.upper()}")
        title_font = QFont("Courier New", 9)
        title_font.setBold(True)
        title_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 2)
        self.title.setFont(title_font)
        self.title.setStyleSheet("color: #00F5FF; text-transform: uppercase;")
        col.addWidget(self.title)

        # Value - huge monospace with neon glow
        self.value = QLabel(initial_value)
        vf = QFont("Courier New", 28)
        vf.setBold(True)
        self.value.setFont(vf)
        self.value.setStyleSheet(f"color: {accent_color}; text-shadow: 0 0 10px {accent_color};")
        col.addWidget(self.value)
        # Neon glow effect
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
        self.setWindowTitle("AMI // NETWORK MONITOR")
        self.setGeometry(100, 100, 1200, 750)
        self.setMinimumSize(900, 600)
        # Cyberpunk: deep purple background with scanlines
        self.setStyleSheet("""
            QMainWindow { 
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0D0221, stop:1 #1a0933);
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7209B7, stop:1 #9D4EDD);
                color: #00F5FF;
                border: 2px solid #00F5FF;
                border-radius: 0px;
                padding: 12px 28px;
                font-family: 'Courier New';
                font-size: 12px;
                font-weight: 700;
                letter-spacing: 2px;
                text-transform: uppercase;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #9D4EDD, stop:1 #C77DFF);
                border-color: #00F5FF;
                box-shadow: 0 0 20px #00F5FF;
            }
            QPushButton:pressed {
                background: #560bad;
                border-color: #7209B7;
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

        # === TOP BAR === Cyberpunk header with neon accent
        self.top_bar = QFrame()
        self.top_bar.setStyleSheet("""
            QFrame { 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0D0221, stop:1 #1a0933);
                border-bottom: 3px solid #00F5FF;
                padding: 24px 40px;
            }
        """)
        top_layout = QHBoxLayout(self.top_bar)

        # Logo area (use resources/ami_logo.png)
        self.logo_label = QLabel()
        self.logo_label.setObjectName("ami_logo")
        self._set_logo_pixmap(self.logo_label, height=28)
        top_layout.addWidget(self.logo_label)

        top_layout.addStretch()

        # Cyberpunk branding with glitch effect
        app_cfg = self.config.get('app', {})
        brand = QLabel("[AMI]")
        brand_font = QFont("Courier New", 22)
        brand_font.setBold(True)
        brand_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 4)
        brand.setFont(brand_font)
        brand.setStyleSheet("""
            color: #00F5FF;
            text-shadow: 2px 2px 0px #7209B7, -2px -2px 0px #C77DFF;
        """)
        top_layout.addWidget(brand)
        
        # Status indicator
        status_label = QLabel(">> ONLINE")
        status_font = QFont("Courier New", 10)
        status_font.setBold(True)
        status_label.setFont(status_font)
        status_label.setStyleSheet("color: #00FF41; margin-left: 20px;")
        top_layout.addWidget(status_label)

        main_layout.addWidget(self.top_bar)

        # === MAIN CONTENT === Cyberpunk dark canvas
        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("""
            QWidget { 
                background: transparent;
                padding: 40px;
            }
        """)
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setSpacing(32)

        # Hero section - cyberpunk terminal style
        hero = QFrame()
        hero.setStyleSheet("""
            QFrame { 
                background: transparent;
                border: none;
                padding: 0;
                margin-bottom: 24px;
            }
        """)
        hero_layout = QHBoxLayout(hero)
        hero_layout.setSpacing(12)

        # Terminal prompt
        prompt = QLabel(">_")
        prompt_font = QFont("Courier New", 16)
        prompt_font.setBold(True)
        prompt.setFont(prompt_font)
        prompt.setStyleSheet("color: #00F5FF;")
        hero_layout.addWidget(prompt)
        
        self.main_title = QLabel("NETWORK_STATUS.EXE")
        title_font = QFont("Courier New", 14)
        title_font.setBold(True)
        title_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 3)
        self.main_title.setFont(title_font)
        self.main_title.setStyleSheet("color: #C77DFF;")
        hero_layout.addWidget(self.main_title)
        
        hero_layout.addStretch()
        
        # Timestamp
        import datetime
        timestamp = QLabel(f"[{datetime.datetime.now().strftime('%H:%M:%S')}]")
        ts_font = QFont("Courier New", 10)
        timestamp.setFont(ts_font)
        timestamp.setStyleSheet("color: #7209B7;")
        hero_layout.addWidget(timestamp)

        content_layout.addWidget(hero)

        # === STATUS GRID ===
        self.status_grid = QGridLayout()
        self.status_grid.setSpacing(10)
        self.status_grid.setContentsMargins(0, 0, 0, 0)

        # Stat cards - cyberpunk neon colors
        self.card_status = StatCard("STATUS", "#00FF41", "--")
        self.card_latency = StatCard("LATENCY", "#00F5FF", "--")
        self.card_uptime = StatCard("UPTIME", "#C77DFF", "--")
        self.card_success = StatCard("SUCCESS", "#FF006E", "--")

        self.status_cards = [self.card_status, self.card_latency, self.card_uptime, self.card_success]
        self.rebuild_status_grid(cols=4)

        content_layout.addLayout(self.status_grid)

        # Charts section - cyberpunk terminal window
        charts_section = QFrame()
        charts_section.setStyleSheet("""
            QFrame { 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0D0221, stop:1 #160633);
                border: 3px solid #7209B7;
                border-radius: 0px;
                padding: 28px;
            }
        """)
        charts_layout = QVBoxLayout(charts_section)

        # Terminal-style header
        header_row = QHBoxLayout()
        charts_title = QLabel("// DATA_STREAM")
        ct_font = QFont("Courier New", 11)
        ct_font.setBold(True)
        ct_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 2)
        charts_title.setFont(ct_font)
        charts_title.setStyleSheet("color: #00F5FF; margin-bottom: 16px;")
        header_row.addWidget(charts_title)
        header_row.addStretch()
        
        # Terminal buttons
        for color in ['#FF006E', '#00FF41', '#00F5FF']:
            dot = QLabel("●")
            dot.setStyleSheet(f"color: {color}; font-size: 16px;")
            header_row.addWidget(dot)
        
        charts_layout.addLayout(header_row)

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

        # === BOTTOM BAR === Minimal footer
        self.bottom_bar = QFrame()
        self.bottom_bar.setStyleSheet("""
            QFrame { 
                background-color: #000000; 
                border-top: 1px solid #1a1a1a; 
                padding: 16px 32px;
            }
        """)
        bottom_layout = QHBoxLayout(self.bottom_bar)

        # Minimal footer text
        footer_text = app_cfg.get('copyright', '© 2025 CiaoIM™')
        company_info = QLabel(footer_text)
        company_info.setStyleSheet("color: #333333; font-size: 10px; letter-spacing: 0.5px;")
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
            QFrame { 
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0D0221, stop:1 #1a0933);
                border: none;
            }
            QLabel { color: #00F5FF; }
        """)
        lay = QVBoxLayout(cw)
        lay.setContentsMargins(40, 48, 40, 40)
        lay.setSpacing(32)
        
        # Cyberpunk brand
        brand = QLabel("[AMI]")
        brand_font = QFont("Courier New", 28)
        brand_font.setBold(True)
        brand_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 4)
        brand.setFont(brand_font)
        brand.setStyleSheet("""
            color: #00F5FF;
            text-shadow: 2px 2px 0px #7209B7, -2px -2px 0px #C77DFF;
        """)
        brand.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        lay.addWidget(brand)
        
        # Status indicator - huge neon circle
        self.compact_light = QLabel('◉')
        lf = QFont("Courier New", 72)
        lf.setBold(True)
        self.compact_light.setFont(lf)
        self.compact_light.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        lay.addWidget(self.compact_light)
        
        # Ping - monospace terminal style
        self.compact_ping = QLabel('-- ms')
        pf = QFont("Courier New", 32)
        pf.setBold(True)
        self.compact_ping.setFont(pf)
        self.compact_ping.setStyleSheet("color: #C77DFF;")
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
