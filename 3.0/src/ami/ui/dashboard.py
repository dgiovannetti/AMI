"""
AMI 3.0 - Dashboard with theme support and responsive layout.
"""

import sys
from pathlib import Path

import numpy as np
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QFont, QPixmap
from PyQt6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ami.core.paths import get_base_path
from ami.ui.themes import get_stylesheet, resolve_theme

# Lazy matplotlib import (only when dashboard is shown)
_matplotlib_canvas = None


def _get_figure_canvas():
    global _matplotlib_canvas
    if _matplotlib_canvas is not None:
        return _matplotlib_canvas
    import matplotlib
    matplotlib.use("QtAgg")
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    _matplotlib_canvas = (Figure, FigureCanvas)
    return _matplotlib_canvas


class StatCard(QFrame):
    def __init__(self, title: str, accent_color: str, initial_value: str = "--", dark: bool = False):
        super().__init__()
        self.accent_color = accent_color
        bg = "#1e293b" if dark else "#ffffff"
        border = "#334155" if dark else "#e5e7eb"
        title_color = "#94a3b8" if dark else "#6b7280"
        self.setStyleSheet(f"QFrame {{ background-color: {bg}; border: 1px solid {border}; border-radius: 12px; }}")
        shadow = QGraphicsDropShadowEffect()
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)
        col = QVBoxLayout(self)
        col.setSpacing(12)
        col.setContentsMargins(20, 20, 20, 20)
        self.title = QLabel(title)
        self.title.setFont(QFont("", 11, QFont.Weight.Medium))
        self.title.setStyleSheet(f"color: {title_color};")
        col.addWidget(self.title)
        self.value = QLabel(initial_value)
        self.value.setFont(QFont("", 32, QFont.Weight.Bold))
        self.value.setStyleSheet(f"color: {accent_color};")
        col.addWidget(self.value)

    def set_value(self, text: str) -> None:
        self.value.setText(text)

    def set_accent_color(self, color: str) -> None:
        self.accent_color = color
        self.value.setStyleSheet(f"color: {color};")

    def pulse(self) -> None:
        pass


class EnterpriseDashboard(QMainWindow):
    def __init__(self, config: dict, monitor, tray_icon=None):
        super().__init__()
        self.config = config
        self.monitor = monitor
        self.tray_icon = tray_icon
        self._compact_mode = False
        theme = config.get("ui", {}).get("theme", "auto")
        self._dark = resolve_theme(theme) == "dark"
        self.setWindowTitle("AMI - Network Monitor")
        self.setGeometry(100, 100, 1100, 700)
        self.setMinimumSize(900, 600)
        self.setStyleSheet(get_stylesheet(theme))
        self.setup_ui()
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(5000)

    def setup_ui(self) -> None:
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.top_bar = QFrame()
        self.top_bar.setStyleSheet("QFrame { padding: 16px 32px; border-bottom: 1px solid #334155;" if self._dark else "QFrame { background-color: #ffffff; border-bottom: 1px solid #e5e7eb; padding: 16px 32px; }")
        top_layout = QHBoxLayout(self.top_bar)
        self.logo_label = QLabel()
        logo_path = get_base_path() / "resources" / "ami_logo.png"
        if logo_path.exists():
            pm = QPixmap(str(logo_path))
            if not pm.isNull():
                self.logo_label.setPixmap(pm.scaledToHeight(28, Qt.TransformationMode.SmoothTransformation))
        top_layout.addWidget(self.logo_label)
        top_layout.addStretch()
        brand = QLabel("AMI")
        brand.setFont(QFont("", 20, QFont.Weight.Bold))
        brand.setStyleSheet("color: #e2e8f0;" if self._dark else "color: #111827;")
        top_layout.addWidget(brand)
        subtitle = QLabel("Network Monitor")
        subtitle.setStyleSheet("color: #94a3b8; margin-left: 12px;" if self._dark else "color: #6b7280; margin-left: 12px;")
        top_layout.addWidget(subtitle)
        main_layout.addWidget(self.top_bar)
        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("QWidget { background-color: #0f172a; }" if self._dark else "QWidget { background-color: #f9fafb; }")
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setSpacing(24)
        content_layout.setContentsMargins(32, 32, 32, 32)
        self.main_title = QLabel("Connection Status")
        self.main_title.setFont(QFont("", 24, QFont.Weight.Bold))
        self.main_title.setStyleSheet("color: #e2e8f0;" if self._dark else "color: #111827;")
        content_layout.addWidget(self.main_title)
        sub = QLabel("Real-time network monitoring")
        sub.setStyleSheet("color: #94a3b8;" if self._dark else "color: #6b7280;")
        content_layout.addWidget(sub)
        self.status_grid = QGridLayout()
        self.card_status = StatCard("Connection Status", "#10b981", "--", self._dark)
        self.card_latency = StatCard("Average Latency", "#3b82f6", "--", self._dark)
        self.card_uptime = StatCard("Uptime", "#8b5cf6", "--", self._dark)
        self.card_success = StatCard("Success Rate", "#f59e0b", "--", self._dark)
        self.status_cards = [self.card_status, self.card_latency, self.card_uptime, self.card_success]
        for i, card in enumerate(self.status_cards):
            self.status_grid.addWidget(card, i // 4, i % 4)
        content_layout.addLayout(self.status_grid)
        Figure, FigureCanvas = _get_figure_canvas()
        self.figure = Figure(figsize=(10.5, 4.2), facecolor="#1e293b" if self._dark else "#ffffff")
        self.canvas = FigureCanvas(self.figure)
        content_layout.addWidget(self.canvas)
        self.figure.subplots_adjust(left=0.07, right=0.98, top=0.92, bottom=0.12, hspace=0.32)
        self.ax1 = self.figure.add_subplot(211, facecolor="#0f172a" if self._dark else "#f9fafb")
        self.ax2 = self.figure.add_subplot(212, facecolor="#0f172a" if self._dark else "#f9fafb")
        for ax in (self.ax1, self.ax2):
            ax.tick_params(colors="#94a3b8" if self._dark else "#6b7280")
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
        self.ax1.set_ylim(-0.5, 2.5)
        self.ax1.set_yticks([0, 1, 2])
        self.ax1.set_yticklabels(["Offline", "Unstable", "Online"])
        self.ax1.set_ylabel("Status")
        self.ax2.set_ylabel("Latency (ms)")
        self._scatter1 = self.ax1.scatter([], [], s=60, alpha=0.9, edgecolors="white", linewidths=1.5, zorder=3)
        self._line1, = self.ax1.plot([], [], "-", color="#64748b", alpha=0.4, linewidth=2, zorder=2)
        self._line2, = self.ax2.plot([], [], "-o", color="#60a5fa", linewidth=2, markersize=4, markeredgecolor="white", markeredgewidth=1.5, zorder=3)
        self._fill2 = None
        main_layout.addWidget(self.content_widget)
        self.compact_widget = QFrame()
        compact_lay = QVBoxLayout(self.compact_widget)
        self.compact_light = QLabel("●")
        self.compact_light.setFont(QFont("", 72))
        self.compact_light.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        compact_lay.addWidget(self.compact_light)
        self.compact_ping = QLabel("-- ms")
        self.compact_ping.setFont(QFont("", 32, QFont.Weight.Bold))
        self.compact_ping.setStyleSheet("color: #6b7280;")
        self.compact_ping.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        compact_lay.addWidget(self.compact_ping)
        self.compact_widget.setVisible(False)
        self.bottom_bar = QFrame()
        self.bottom_bar.setStyleSheet("QFrame { padding: 16px 32px; border-top: 1px solid #334155; }" if self._dark else "QFrame { background-color: #ffffff; border-top: 1px solid #e5e7eb; padding: 16px 32px; }")
        bottom_layout = QHBoxLayout(self.bottom_bar)
        app_cfg = self.config.get("app", {})
        bottom_layout.addWidget(QLabel(app_cfg.get("copyright", "© 2025 CiaoIM™")))
        bottom_layout.addStretch()
        refresh_btn = QPushButton(" Refresh")
        refresh_btn.clicked.connect(self.refresh_data)
        bottom_layout.addWidget(refresh_btn)
        hide_btn = QPushButton(" Minimize")
        hide_btn.clicked.connect(self.hide)
        bottom_layout.addWidget(hide_btn)
        close_btn = QPushButton(" Close")
        close_btn.clicked.connect(self.close)
        bottom_layout.addWidget(close_btn)
        main_layout.addWidget(self.compact_widget)
        main_layout.addWidget(self.bottom_bar)

    def resizeEvent(self, event) -> None:
        w = self.width()
        cols = 4 if w >= 1100 else (2 if w >= 880 else 1)
        while self.status_grid.count():
            item = self.status_grid.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
        for i, card in enumerate(self.status_cards):
            self.status_grid.addWidget(card, i // cols, i % cols)
        compact = w < 720 or self.height() < 420
        if getattr(self, "_compact_mode", None) != compact:
            self._compact_mode = compact
            self.top_bar.setVisible(not compact)
            self.compact_widget.setVisible(compact)
            self.content_widget.setVisible(not compact)
            self.bottom_bar.setVisible(not compact)
        super().resizeEvent(event)

    def update_data(self, status, statistics: dict) -> None:
        status_map = {"online": ("✓ Online", "#34d399"), "unstable": ("! Unstable", "#fbbf24"), "offline": ("✕ Offline", "#ef4444")}
        st_text, st_color = status_map.get(status.status, ("? Unknown", "#94a3b8"))
        self.card_status.set_value(st_text)
        self.card_status.set_accent_color(st_color)
        if getattr(status, "avg_latency_ms", None) is not None:
            self.card_latency.set_value(f"{status.avg_latency_ms:.0f} ms")
            try:
                self.compact_ping.setText(f"{status.avg_latency_ms:.0f} ms")
            except Exception:
                pass
        else:
            self.card_latency.set_value("N/A")
        uptime_pct = statistics.get("uptime_percentage")
        if uptime_pct is None:
            uptime_pct = getattr(self.monitor, "get_uptime_percentage", lambda: None)()
        self.card_uptime.set_value(f"{uptime_pct:.1f}%" if uptime_pct is not None else "N/A")
        success_pct = (status.successful_pings / status.total_pings * 100) if getattr(status, "total_pings", 0) > 0 else None
        self.card_success.set_value(f"{success_pct:.1f}%" if success_pct is not None else "N/A")
        try:
            if status.status == "online":
                light, color = "✓", "#34d399"
            elif status.status == "unstable":
                light, color = "!", "#fbbf24"
            else:
                light, color = "✕", "#ef4444"
            self.compact_light.setText(light)
            self.compact_light.setStyleSheet(f"color: {color};")
        except Exception:
            pass
        self.update_graphs()

    def update_graphs(self) -> None:
        history = getattr(self.monitor, "status_history", [])
        if not history:
            return
        status_values = [{"online": 2, "unstable": 1, "offline": 0}.get(h.status, 0) for h in history]
        latencies = [h.avg_latency_ms if h.avg_latency_ms else 0 for h in history]
        idx = np.arange(len(history), dtype=float)
        sv = np.array(status_values, dtype=float)
        lat = np.array(latencies, dtype=float)
        colors = ["#34d399" if v == 2 else "#fbbf24" if v == 1 else "#ef4444" for v in status_values]
        self._scatter1.set_offsets(np.c_[idx, sv])
        self._scatter1.set_facecolors(colors)
        self._line1.set_data(idx, sv)
        self._line2.set_data(idx, lat)
        if self._fill2 is not None:
            self._fill2.remove()
        self._fill2 = self.ax2.fill_between(idx, lat, alpha=0.15, color="#60a5fa", zorder=2)
        self.canvas.draw_idle()

    def refresh_data(self) -> None:
        if self.monitor.last_status:
            self.update_data(self.monitor.last_status, self.monitor.get_statistics())

    def closeEvent(self, event) -> None:
        if self.tray_icon and self.tray_icon.isVisible():
            event.ignore()
            self.hide()
        else:
            event.accept()
