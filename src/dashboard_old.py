"""
AMI - Active Monitor of Internet
Dashboard Window

Displays detailed statistics, graphs, and connection history
"""

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QLabel, QGroupBox, QPushButton, QTextEdit, QSplitter)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QPalette, QColor
import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt


class DashboardWindow(QMainWindow):
    """
    Main dashboard window showing connection statistics and graphs
    """
    
    def __init__(self, config: dict, monitor, tray_icon=None):
        super().__init__()
        self.config = config
        self.monitor = monitor
        self.tray_icon = tray_icon  # Reference to system tray icon
        
        # Window setup - resizable
        self.setWindowTitle("AMI Dashboard - Active Monitor of Internet")
        self.setGeometry(100, 100, 950, 600)
        self.setMinimumSize(800, 500)
        
        # Setup UI
        self.setup_ui()
        
        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(5000)  # Refresh every 5 seconds
    
    def setup_ui(self):
        """Setup the user interface"""
        # Professional modern style
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0f172a, stop:0.5 #1e293b, stop:1 #0f172a);
            }
            QGroupBox {
                background-color: rgba(30, 41, 59, 0.6);
                border: 2px solid rgba(52, 211, 153, 0.3);
                border-radius: 8px;
                margin-top: 12px;
                padding: 12px;
                color: #e2e8f0;
                font-size: 13px;
                font-weight: 500;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 12px;
                top: 6px;
                padding: 3px 8px;
                background-color: rgba(52, 211, 153, 0.15);
                border-radius: 6px;
                color: #34d399;
                font-size: 14px;
                font-weight: bold;
            }
            QLabel {
                color: #e2e8f0;
                font-size: 13px;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1e40af, stop:1 #1e3a8a);
                color: white;
                border: 2px solid rgba(52, 211, 153, 0.4);
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2563eb, stop:1 #1e40af);
                border: 2px solid rgba(52, 211, 153, 0.6);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1e3a8a, stop:1 #172554);
            }
        """)
        
        # Main widget and layout - optimized
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(12, 12, 12, 12)
        
        # Professional header with gradient background
        header_widget = QWidget()
        header_widget.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 rgba(52, 211, 153, 0.05),
                stop:0.5 rgba(52, 211, 153, 0.1),
                stop:1 rgba(52, 211, 153, 0.05));
            border-radius: 8px;
            padding: 8px;
        """)
        header_layout = QVBoxLayout(header_widget)
        header_layout.setSpacing(2)
        header_layout.setContentsMargins(10, 6, 10, 6)
        
        # Title
        header = QLabel("AMI - Active Monitor of Internet")
        header_font = QFont()
        header_font.setPointSize(16)
        header_font.setBold(True)
        header.setFont(header_font)
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("color: #34d399; background: transparent;")
        header_layout.addWidget(header)
        
        # Credits
        credits = QLabel("© 2025 CiaoIM™ di Daniel Giovannetti • ciaoim.tech")
        credits_font = QFont()
        credits_font.setPointSize(9)
        credits.setFont(credits_font)
        credits.setAlignment(Qt.AlignmentFlag.AlignCenter)
        credits.setStyleSheet("color: #94a3b8; background: transparent;")
        header_layout.addWidget(credits)
        
        # Tagline
        tagline = QLabel("Crafted logic. Measured force. Front-end vision, compiled systems, hardcoded ethics.")
        tagline_font = QFont()
        tagline_font.setPointSize(8)
        tagline_font.setItalic(True)
        tagline.setFont(tagline_font)
        tagline.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tagline.setStyleSheet("color: #64748b; background: transparent;")
        header_layout.addWidget(tagline)
        
        # Inspiration
        inspiration = QLabel("Intuizione colta insieme a Giovanni C. in aliscafo per il 40° Convegno di Capri dei Giovani Imprenditori")
        inspiration_font = QFont()
        inspiration_font.setPointSize(7)
        inspiration_font.setItalic(True)
        inspiration.setFont(inspiration_font)
        inspiration.setAlignment(Qt.AlignmentFlag.AlignCenter)
        inspiration.setStyleSheet("color: #64748b; background: transparent;")
        header_layout.addWidget(inspiration)
        
        main_layout.addWidget(header_widget)
        
        # Current Status Section
        status_group = self.create_status_section()
        main_layout.addWidget(status_group)
        
        # Statistics Section
        stats_group = self.create_statistics_section()
        main_layout.addWidget(stats_group)
        
        # Graph Section
        graph_group = self.create_graph_section()
        main_layout.addWidget(graph_group, stretch=2)
        
        # Optimized buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh_data)
        button_layout.addWidget(refresh_btn)
        
        reset_btn = QPushButton("🔄 Reset")
        reset_btn.clicked.connect(self.reset_statistics)
        button_layout.addWidget(reset_btn)
        
        button_layout.addStretch()
        
        hide_btn = QPushButton("⬇️ Hide to Tray")
        hide_btn.clicked.connect(self.hide)
        button_layout.addWidget(hide_btn)
        
        close_btn = QPushButton("❌ Close")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        
        main_layout.addLayout(button_layout)
    
    def create_status_section(self) -> QGroupBox:
        """Create current status section"""
        group = QGroupBox("🌐 Current Status")
        group.setStyleSheet(group.styleSheet() + """
            QGroupBox {
                font-size: 14px;
            }
        """)
        
        # Optimized horizontal layout
        layout = QHBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Optimized status display
        self.status_label = QLabel("⚫ Status: --")
        status_font = QFont()
        status_font.setPointSize(14)
        status_font.setBold(True)
        self.status_label.setFont(status_font)
        layout.addWidget(self.status_label)
        
        layout.addSpacing(15)
        
        self.latency_label = QLabel("⚡ Latency: --")
        latency_font = QFont()
        latency_font.setPointSize(12)
        self.latency_label.setFont(latency_font)
        self.latency_label.setStyleSheet("color: #fbbf24;")
        layout.addWidget(self.latency_label)
        
        self.success_label = QLabel("✓ Success: --%")
        success_font = QFont()
        success_font.setPointSize(12)
        self.success_label.setFont(success_font)
        self.success_label.setStyleSheet("color: #86efac;")
        layout.addWidget(self.success_label)
        
        layout.addStretch()
        
        # Compact legend
        legend = QLabel(" 🟢 OK • 🟡 Unstable • 🔴 Offline ")
        legend_font = QFont()
        legend_font.setPointSize(9)
        legend.setFont(legend_font)
        legend.setStyleSheet("""
            color: #94a3b8;
            background-color: rgba(52, 211, 153, 0.1);
            border-radius: 4px;
            padding: 5px 10px;
        """)
        layout.addWidget(legend)
        
        group.setLayout(layout)
        return group
    
    def create_statistics_section(self) -> QGroupBox:
        """Create statistics section"""
        group = QGroupBox("📊 Statistics")
        layout = QHBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Create clean stat labels
        stats = [
            ("total_checks_label", "📈 Total: 0", "#93c5fd"),
            ("successful_checks_label", "✅ Success: 0", "#86efac"),
            ("uptime_pct_label", "⏱️ Uptime: 0.0%", "#fde047"),
            ("uptime_dur_label", "🕐 Duration: 0m", "#c4b5fd")
        ]
        
        for attr_name, text, color in stats:
            label = QLabel(text)
            font = QFont()
            font.setPointSize(11)
            label.setFont(font)
            label.setStyleSheet(f"""
                color: {color};
                background-color: rgba(30, 41, 59, 0.5);
                border-radius: 6px;
                padding: 6px 10px;
            """)
            setattr(self, attr_name, label)
            layout.addWidget(label)
        
        layout.addStretch()
        
        group.setLayout(layout)
        return group
    
    def create_graph_section(self) -> QGroupBox:
        """Create graph section with matplotlib"""
        group = QGroupBox("📉 Connection History")
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)
        
        # Optimized figure size
        self.figure = Figure(figsize=(9.5, 3.8), facecolor='#1e293b')
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setStyleSheet("""
            background-color: #1e293b;
            border-radius: 8px;
        """)
        self.canvas.setMinimumHeight(280)
        layout.addWidget(self.canvas)
        
        # Optimized plot spacing
        self.figure.subplots_adjust(left=0.08, right=0.97, top=0.93, bottom=0.12, hspace=0.38)
        self.ax1 = self.figure.add_subplot(211, facecolor='#0f172a')
        self.ax2 = self.figure.add_subplot(212, facecolor='#0f172a')
        
        # Style ax1 - optimized
        self.ax1.set_title('Connection Status Over Time', color='#e2e8f0', fontsize=11, fontweight='bold', pad=8)
        self.ax1.set_ylabel('Status', color='#94a3b8', fontsize=10)
        self.ax1.set_ylim(-0.5, 2.5)
        self.ax1.set_yticks([0, 1, 2])
        self.ax1.set_yticklabels(['Offline', 'Unstable', 'Online'])
        self.ax1.tick_params(colors='#94a3b8')
        self.ax1.grid(True, alpha=0.2, color='#475569')
        self.ax1.spines['bottom'].set_color('#475569')
        self.ax1.spines['top'].set_color('#475569')
        self.ax1.spines['left'].set_color('#475569')
        self.ax1.spines['right'].set_color('#475569')
        
        # Style ax2 - optimized
        self.ax2.set_title('Latency Over Time', color='#e2e8f0', fontsize=11, fontweight='bold', pad=8)
        self.ax2.set_ylabel('Latency (ms)', color='#94a3b8', fontsize=10)
        self.ax2.set_xlabel('Recent Checks', color='#94a3b8', fontsize=9)
        self.ax2.tick_params(colors='#94a3b8')
        self.ax2.grid(True, alpha=0.2, color='#475569')
        self.ax2.spines['bottom'].set_color('#475569')
        self.ax2.spines['top'].set_color('#475569')
        self.ax2.spines['left'].set_color('#475569')
        self.ax2.spines['right'].set_color('#475569')
        
        # Don't use tight_layout, we have custom spacing
        # self.figure.tight_layout()
        
        group.setLayout(layout)
        return group
    
    def update_data(self, status, statistics):
        """
        Update dashboard with new data
        
        Args:
            status: ConnectionStatus object
            statistics: Statistics dictionary
        """
        # Update status labels with icons
        status_icons = {
            'online': '🟢',
            'unstable': '🟡',
            'offline': '🔴'
        }
        status_text = status.status.upper()
        status_icon = status_icons.get(status.status, '⚫')
        status_color = {
            'online': '#34d399',
            'unstable': '#fbbf24',
            'offline': '#ef4444'
        }.get(status.status, '#808080')
        
        self.status_label.setText(f"{status_icon}  {status_text}")
        self.status_label.setStyleSheet(f"color: {status_color}; font-weight: bold; padding: 5px;")
        
        # Update latency
        if status.avg_latency_ms:
            self.latency_label.setText(f"⚡ Latency: {status.avg_latency_ms:.0f}ms")
        else:
            self.latency_label.setText("⚡ Latency: N/A")
        
        # Update success rate
        if status.total_pings > 0:
            success_pct = (status.successful_pings / status.total_pings) * 100
            self.success_label.setText(f"✓ Success: {success_pct:.0f}%")
        
        # Update statistics - compact
        self.total_checks_label.setText(f"📈 Total: {statistics['total_checks']}")
        self.successful_checks_label.setText(f"✅ Success: {statistics['successful_checks']}")
        self.uptime_pct_label.setText(f"⏱️ Uptime: {statistics['uptime_percentage']:.1f}%")
        self.uptime_dur_label.setText(f"🕐 Duration: {statistics['uptime_duration']}")
        
        # Update graphs
        self.update_graphs()
    
    def update_graphs(self):
        """Update matplotlib graphs with history data"""
        history = self.monitor.status_history
        
        if not history:
            return
        
        # Prepare data
        status_values = []
        latencies = []
        indices = list(range(len(history)))
        
        for h in history:
            # Map status to number
            status_map = {'online': 2, 'unstable': 1, 'offline': 0}
            status_values.append(status_map.get(h.status, 0))
            latencies.append(h.avg_latency_ms if h.avg_latency_ms else 0)
        
        # Clear and update status plot - optimized
        self.ax1.clear()
        self.ax1.set_facecolor('#0f172a')
        self.ax1.set_title('Connection Status Over Time', color='#e2e8f0', fontsize=11, fontweight='bold', pad=8)
        self.ax1.set_ylabel('Status', color='#94a3b8', fontsize=10)
        self.ax1.set_ylim(-0.5, 2.5)
        self.ax1.set_yticks([0, 1, 2])
        self.ax1.set_yticklabels(['Offline', 'Unstable', 'Online'], fontsize=9)
        self.ax1.tick_params(colors='#94a3b8', labelsize=9)
        self.ax1.grid(True, alpha=0.2, color='#475569', linewidth=1)
        for spine in self.ax1.spines.values():
            spine.set_color('#475569')
            spine.set_linewidth(1.5)
        
        # Color segments based on status (modern vibrant colors)
        colors = []
        for sv in status_values:
            if sv == 2:
                colors.append('#34d399')  # Emerald
            elif sv == 1:
                colors.append('#fbbf24')  # Amber
            else:
                colors.append('#ef4444')  # Red
        
        self.ax1.scatter(indices, status_values, c=colors, s=80, alpha=0.9, edgecolors='white', linewidths=1.5, zorder=3)
        self.ax1.plot(indices, status_values, '-', color='#64748b', alpha=0.5, linewidth=2.5, zorder=2)
        
        # Clear and update latency plot - optimized
        self.ax2.clear()
        self.ax2.set_facecolor('#0f172a')
        self.ax2.set_title('Latency Over Time', color='#e2e8f0', fontsize=11, fontweight='bold', pad=8)
        self.ax2.set_ylabel('Latency (ms)', color='#94a3b8', fontsize=10)
        self.ax2.set_xlabel('Recent Checks', color='#94a3b8', fontsize=9)
        self.ax2.tick_params(colors='#94a3b8', labelsize=9)
        self.ax2.grid(True, alpha=0.2, color='#475569', linewidth=1)
        for spine in self.ax2.spines.values():
            spine.set_color('#475569')
            spine.set_linewidth(1.5)
        
        # Plot latency with modern vibrant style
        self.ax2.plot(indices, latencies, '-o', color='#60a5fa', markersize=6, linewidth=2.5, 
                     markeredgecolor='white', markeredgewidth=1.5, zorder=3)
        self.ax2.fill_between(indices, latencies, alpha=0.25, color='#60a5fa', zorder=2)
        
        # Use our custom spacing instead of tight_layout
        # self.figure.tight_layout()
        self.canvas.draw()
    
    def refresh_data(self):
        """Refresh dashboard data"""
        if self.monitor.last_status:
            stats = self.monitor.get_statistics()
            self.update_data(self.monitor.last_status, stats)
    
    def reset_statistics(self):
        """Reset all statistics"""
        from PyQt6.QtWidgets import QMessageBox
        
        reply = QMessageBox.question(
            self,
            'Reset Statistics',
            'Are you sure you want to reset all statistics?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.monitor.reset_statistics()
            self.refresh_data()
            QMessageBox.information(self, 'Reset', 'Statistics have been reset.')
    
    def closeEvent(self, event):
        """Override close event to minimize to tray instead of closing"""
        if self.tray_icon and self.tray_icon.isVisible():
            # Minimize to tray instead of closing
            event.ignore()
            self.hide()
            if self.tray_icon:
                from PyQt6.QtWidgets import QSystemTrayIcon
                self.tray_icon.showMessage(
                    "AMI Dashboard",
                    "Dashboard minimized to tray. Click the tray icon to show it again.",
                    QSystemTrayIcon.MessageIcon.Information,
                    2000
                )
        else:
            # No tray icon, allow normal close
            event.accept()
    
    def changeEvent(self, event):
        """Handle window state changes (minimize, etc)"""
        from PyQt6.QtCore import QEvent
        if event.type() == QEvent.Type.WindowStateChange:
            if self.isMinimized() and self.tray_icon and self.tray_icon.isVisible():
                # Minimize to tray
                event.ignore()
                self.hide()
        super().changeEvent(event)
