"""
AMI 3.0 — Dashboard: paper canvas, one accent, operational status.
"""

import html
import threading
import time
from typing import Optional

import numpy as np
from PyQt6.QtCore import QObject, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ami.core.models import reason_text
from ami.core.paths import get_base_path
from ami.ui.themes import get_stylesheet, palette, resolve_theme, status_color

GITHUB_REPO_URL = "https://github.com/dgiovannetti/AMI"
GITHUB_REPO_API = "https://api.github.com/repos/dgiovannetti/AMI"

# GitHub non espone un URL che metta la star in automatico: serve aprire il repo ed essere loggati.
GITHUB_STAR_TOOLTIP = (
    "Apre il repository su GitHub nel browser. "
    "Se hai effettuato l'accesso, premi il pulsante Star in alto a destra sulla pagina."
)

_matplotlib_canvas = None


class _GitHubStarsBridge(QObject):
    """Carries stargazers_count from worker thread to GUI thread."""

    stars_ready = pyqtSignal(object)


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


class MetricCard(QWidget):
    """Flat metric tile: white fill, 1px border. Status color only via set_accent_color."""

    def __init__(self, title: str, initial_value: str = "—", dark: bool = False, theme: str = "auto"):
        super().__init__()
        self._pal = palette("dark" if dark else "light")
        self.setObjectName("MetricCard")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setMinimumHeight(112)
        self._apply_shell_style()

        lay = QVBoxLayout(self)
        lay.setSpacing(4)
        lay.setContentsMargins(18, 14, 18, 14)

        self.title_lbl = QLabel(title.upper())
        self.title_lbl.setFont(QFont("Helvetica Neue", 9, QFont.Weight.DemiBold))
        self.title_lbl.setStyleSheet(self._lbl_reset() + self._title_style())
        lay.addWidget(self.title_lbl)

        self.value_lbl = QLabel(initial_value)
        self.value_lbl.setWordWrap(True)
        self.value_lbl.setFont(QFont("Helvetica Neue", 26, QFont.Weight.Bold))
        self.value_lbl.setStyleSheet(self._lbl_reset() + f"color: {self._pal.text};")
        lay.addWidget(self.value_lbl)

        self.foot_lbl = QLabel("")
        self.foot_lbl.setFont(QFont("", 11, QFont.Weight.Medium))
        self.foot_lbl.setStyleSheet(self._lbl_reset() + self._foot_style())
        self.foot_lbl.setWordWrap(True)
        lay.addWidget(self.foot_lbl)

    @staticmethod
    def _lbl_reset() -> str:
        return "border: none; outline: none; background: transparent; "

    def _title_style(self) -> str:
        return f"color: {self._pal.muted}; letter-spacing: 1px;"

    def _foot_style(self) -> str:
        return f"color: {self._pal.muted};"

    def _apply_shell_style(self) -> None:
        p = self._pal
        self.setStyleSheet(
            f"""
            QWidget#MetricCard {{
                background-color: {p.surface};
                border: 1px solid {p.border};
                border-radius: 12px;
            }}
            """
        )

    def set_value(self, text: str) -> None:
        self.value_lbl.setText(text)
        size = 16 if len(text) > 18 else 26
        self.value_lbl.setFont(QFont("Helvetica Neue", size, QFont.Weight.Bold))

    def set_accent_color(self, color: str) -> None:
        self.value_lbl.setStyleSheet(self._lbl_reset() + f"color: {color};")

    def set_footnote(self, text: str) -> None:
        self.foot_lbl.setText(text)
        self.foot_lbl.setVisible(bool(text))


StatCard = MetricCard


class EnterpriseDashboard(QMainWindow):
    def __init__(self, config: dict, monitor, tray_icon=None):
        super().__init__()
        self.config = config
        self.monitor = monitor
        self.tray_icon = tray_icon
        self._compact_mode = False
        self._github_stars_last_fetch: Optional[float] = None
        self._github_stars_cached: Optional[int] = None
        self._recording = False
        self._record_handler = None
        theme = config.get("ui", {}).get("theme", "auto")
        self._dark = resolve_theme(theme) == "dark"
        self._pal = palette(theme)
        self.setWindowTitle("AMI — Network Monitor")
        self.setGeometry(120, 80, 1120, 760)
        self.setMinimumSize(920, 620)

        self._github_stars_bridge = _GitHubStarsBridge(self)
        self._github_stars_bridge.stars_ready.connect(self._on_github_stars)

        self.setStyleSheet(get_stylesheet(theme) + self._dashboard_chrome_qss())
        self.setup_ui()

        self._graph_fingerprint = None
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)
        # Started on show; paused while hidden to avoid QtAgg churn on Windows.

        self._github_stars_timer = QTimer()
        self._github_stars_timer.timeout.connect(self._fetch_github_stars)
        self._github_stars_timer.start(10 * 60 * 1000)
        QTimer.singleShot(600, self._fetch_github_stars)

    def _dashboard_chrome_qss(self) -> str:
        p = self._pal
        return f"""
            QMainWindow#EnterpriseDashboard {{
                background: {p.page};
            }}
            QMainWindow#EnterpriseDashboard QLabel {{
                border: none;
                background: transparent;
            }}
        """

    def setup_ui(self) -> None:
        self.setObjectName("EnterpriseDashboard")
        main_widget = QWidget()
        main_widget.setStyleSheet("border: none; background: transparent;")
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.top_bar = QWidget()
        self.top_bar.setObjectName("DashTopBar")
        p = self._pal
        self.top_bar.setObjectName("DashTopBar")
        self.top_bar.setStyleSheet(
            f"QWidget#DashTopBar {{ background-color: {p.surface}; border: none; border-bottom: 1px solid {p.border}; }}"
        )
        top_layout = QHBoxLayout(self.top_bar)
        top_layout.setContentsMargins(28, 16, 28, 16)

        self.logo_label = QLabel()
        logo_path = get_base_path() / "resources" / "ami_logo.png"
        if logo_path.exists():
            pm = QPixmap(str(logo_path))
            if not pm.isNull():
                self.logo_label.setPixmap(pm.scaledToHeight(36, Qt.TransformationMode.SmoothTransformation))
        self.logo_label.setStyleSheet("border: none; background: transparent;")
        top_layout.addWidget(self.logo_label)
        top_layout.addStretch(1)

        brand_col = QVBoxLayout()
        brand_col.setSpacing(2)
        row = QHBoxLayout()
        self.brand_title = QLabel("AMI")
        self.brand_title.setFont(QFont("Helvetica Neue", 22, QFont.Weight.Black))
        self.brand_title.setStyleSheet(
            f"border: none; background: transparent; color: {p.text};"
        )
        row.addWidget(self.brand_title)
        row.addStretch()
        brand_col.addLayout(row)
        self.brand_sub = QLabel("sai se sei davvero online")
        self.brand_sub.setFont(QFont("Helvetica Neue", 12, QFont.Weight.Medium))
        self.brand_sub.setStyleSheet(
            f"border: none; background: transparent; color: {p.muted};"
        )
        brand_col.addWidget(self.brand_sub)
        top_layout.addLayout(brand_col, 0)
        top_layout.addStretch(2)

        self.status_chip = QLabel("—")
        self.status_chip.setFont(QFont("Helvetica Neue", 12, QFont.Weight.DemiBold))
        self.status_chip.setStyleSheet(self._chip_qss(p.muted))
        self.header_reason = QLabel("")
        self.header_reason.setFont(QFont("Helvetica Neue", 12, QFont.Weight.Medium))
        self.header_reason.setStyleSheet(
            f"border: none; background: transparent; color: {p.muted};"
        )
        top_layout.addWidget(self.status_chip, 0, Qt.AlignmentFlag.AlignVCenter)
        top_layout.addSpacing(10)
        top_layout.addWidget(self.header_reason, 0, Qt.AlignmentFlag.AlignVCenter)
        top_layout.addSpacing(14)

        self.stars_label = QLabel()
        self.stars_label.setObjectName("GitHubStarsLabel")
        self.stars_label.setTextFormat(Qt.TextFormat.RichText)
        self.stars_label.setOpenExternalLinks(True)
        self.stars_label.setFont(QFont("Helvetica Neue", 10, QFont.Weight.DemiBold))
        self.stars_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.stars_label.setToolTip(GITHUB_STAR_TOOLTIP)
        top_layout.addWidget(self.stars_label, 0, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
        top_layout.addSpacing(10)

        ver = self.config.get("app", {}).get("version", "")
        self.ver_badge = QLabel(f"v{ver}")
        self.ver_badge.setFont(QFont("Menlo", 10, QFont.Weight.Medium))
        self.ver_badge.setStyleSheet(
            f"""
            QLabel {{
                background-color: {p.page};
                color: {p.muted};
                border: 1px solid {p.border};
                border-radius: 999px;
                padding: 4px 10px;
            }}
            """
        )
        top_layout.addWidget(self.ver_badge, 0, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignVCenter)

        main_layout.addWidget(self.top_bar)

        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("background: transparent; border: none;")
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setSpacing(18)
        content_layout.setContentsMargins(28, 24, 28, 20)

        hero = QHBoxLayout()
        self.main_title = QLabel("Status")
        self.main_title.setFont(QFont("Helvetica Neue", 22, QFont.Weight.Bold))
        self.main_title.setStyleSheet(
            f"border: none; background: transparent; color: {p.text};"
        )
        hero.addWidget(self.main_title)
        hero.addStretch()
        self.hero_hint = QLabel("")
        self.hero_hint.setFont(QFont("Helvetica Neue", 12, QFont.Weight.Medium))
        self.hero_hint.setStyleSheet(
            f"border: none; background: transparent; color: {p.muted};"
        )
        hero.addWidget(self.hero_hint, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)
        content_layout.addLayout(hero)

        self.status_grid = QGridLayout()
        self.status_grid.setHorizontalSpacing(14)
        self.status_grid.setVerticalSpacing(14)

        self.card_status = MetricCard("Link", "—", self._dark)
        self.card_latency = MetricCard("Latency", "—", self._dark)
        self.card_uptime = MetricCard("Uptime", "—", self._dark)
        self.card_success = MetricCard("Ping OK", "—", self._dark)
        self.card_speed = MetricCard("Throughput", "—", self._dark)
        self.card_isp = MetricCard("ISP", "—", self._dark)
        self.card_ip = MetricCard("Public IP", "—", self._dark)
        self.card_vpn = MetricCard("VPN", "—", self._dark)
        self.status_cards = [
            self.card_status,
            self.card_latency,
            self.card_uptime,
            self.card_success,
            self.card_speed,
            self.card_isp,
            self.card_ip,
            self.card_vpn,
        ]
        for i, card in enumerate(self.status_cards):
            self.status_grid.addWidget(card, i // 4, i % 4)
        content_layout.addLayout(self.status_grid)

        chart_wrap = QWidget()
        chart_wrap.setObjectName("ChartShell")
        chart_wrap.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        chart_wrap.setStyleSheet(
            f"QWidget#ChartShell {{ background-color: {p.surface}; border: 1px solid {p.border}; border-radius: 12px; }}"
        )
        cw_lay = QVBoxLayout(chart_wrap)
        cw_lay.setContentsMargins(10, 10, 10, 6)
        cw_lay.addWidget(self._chart_legend())
        Figure, FigureCanvas = _get_figure_canvas()
        self.figure = Figure(figsize=(10.5, 4.35), facecolor=p.surface)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setStyleSheet("background: transparent; border: none;")
        cw_lay.addWidget(self.canvas)
        content_layout.addWidget(chart_wrap, 1)
        self._setup_matplotlib_axes()
        main_layout.addWidget(self.content_widget, 1)

        # —— Compact mode (narrow / short window) ——
        self.compact_widget = QWidget()
        self.compact_widget.setObjectName("CompactDash")
        self.compact_widget.setStyleSheet("QWidget#CompactDash { background: transparent; border: none; }")
        c_lay = QVBoxLayout(self.compact_widget)
        c_lay.setContentsMargins(20, 16, 20, 16)
        c_lay.setSpacing(10)

        crow0 = QHBoxLayout()
        self.compact_brand = QLabel("AMI")
        self.compact_brand.setFont(QFont("Helvetica Neue", 15, QFont.Weight.Black))
        self.compact_brand.setStyleSheet(
            f"border: none; background: transparent; color: {p.text};"
        )
        self.compact_sub = QLabel("compact")
        self.compact_sub.setFont(QFont("Helvetica Neue", 10, QFont.Weight.Medium))
        self.compact_sub.setStyleSheet(
            f"border: none; background: transparent; color: {p.muted};"
        )
        crow0.addWidget(self.compact_brand)
        crow0.addWidget(self.compact_sub)
        crow0.addStretch()
        ver_c = self.config.get("app", {}).get("version", "")
        self.compact_ver = QLabel(f"v{ver_c}")
        self.compact_ver.setFont(QFont("Menlo", 9))
        self.compact_ver.setStyleSheet(
            f"border: none; background: transparent; color: {p.muted};"
        )
        crow0.addWidget(self.compact_ver)
        c_lay.addLayout(crow0)

        self.compact_status_chip = QLabel("—")
        self.compact_status_chip.setFont(QFont("Helvetica Neue", 11, QFont.Weight.Bold))
        self.compact_status_chip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.compact_status_chip.setStyleSheet(self._chip_qss(p.muted))
        c_lay.addWidget(self.compact_status_chip)

        self.compact_ping = QLabel("— ms")
        self.compact_ping.setFont(QFont("Helvetica Neue", 36, QFont.Weight.Black))
        self.compact_ping.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.compact_ping.setStyleSheet(
            f"border: none; background: transparent; color: {p.text};"
        )
        c_lay.addWidget(self.compact_ping)

        self.compact_meta = QLabel("—")
        self.compact_meta.setFont(QFont("Helvetica Neue", 12, QFont.Weight.Medium))
        self.compact_meta.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.compact_meta.setStyleSheet(
            f"border: none; background: transparent; color: {p.muted};"
        )
        self.compact_meta.setWordWrap(True)
        c_lay.addWidget(self.compact_meta)

        self.compact_hint = QLabel("Widen the window for charts & all metrics")
        self.compact_hint.setFont(QFont("", 10))
        self.compact_hint.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.compact_hint.setStyleSheet(
            f"border: none; background: transparent; color: {p.muted};"
        )
        c_lay.addWidget(self.compact_hint)

        self.compact_stars = QLabel()
        self.compact_stars.setTextFormat(Qt.TextFormat.RichText)
        self.compact_stars.setOpenExternalLinks(True)
        self.compact_stars.setFont(QFont("Helvetica Neue", 9))
        self.compact_stars.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.compact_stars.setCursor(Qt.CursorShape.PointingHandCursor)
        self.compact_stars.setToolTip(GITHUB_STAR_TOOLTIP)
        c_lay.addWidget(self.compact_stars)

        self.compact_widget.setVisible(False)

        self.bottom_bar = QWidget()
        self.bottom_bar.setObjectName("DashBottomBar")
        self.bottom_bar.setStyleSheet(
            f"""
            QWidget#DashBottomBar {{
                background-color: {p.surface};
                border: none;
                border-top: 1px solid {p.border};
            }}
            QPushButton {{
                background-color: {p.surface};
                color: {p.text};
                border: 1px solid {p.border};
                border-radius: 8px;
                padding: 6px 14px;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:hover {{ border-color: {p.text}; }}
            QPushButton#PrimaryButton {{
                background-color: {p.accent};
                color: {p.on_accent};
                border: 1px solid {p.accent};
            }}
            QPushButton#PrimaryButton:hover {{
                background-color: {p.accent_hover};
                border-color: {p.accent_hover};
            }}
            """
        )
        bottom_layout = QHBoxLayout(self.bottom_bar)
        bottom_layout.setContentsMargins(28, 12, 28, 12)
        app_cfg = self.config.get("app", {})
        self.footer_copyright = QLabel()
        self.footer_copyright.setTextFormat(Qt.TextFormat.RichText)
        self.footer_copyright.setOpenExternalLinks(True)
        self.footer_copyright.setCursor(Qt.CursorShape.PointingHandCursor)
        self._apply_footer_copyright()
        bottom_layout.addWidget(self.footer_copyright)
        bottom_layout.addStretch()
        self.record_btn = QPushButton("Record for ISP")
        self.record_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.record_btn.clicked.connect(self._on_record_clicked)
        bottom_layout.addWidget(self.record_btn)
        for text, slot, primary in (
            ("Refresh", self.refresh_data, False),
            ("Minimize", self.hide, False),
            ("Close", self.close, True),
        ):
            btn = QPushButton(text)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            if primary:
                btn.setObjectName("PrimaryButton")
            btn.clicked.connect(slot)
            bottom_layout.addWidget(btn)

        main_layout.addWidget(self.compact_widget)
        main_layout.addWidget(self.bottom_bar)

        self._refresh_github_stars_labels()

    def bind_record(self, handler, recording: bool = False) -> None:
        self._record_handler = handler
        self.set_recording(recording)

    def set_recording(self, active: bool) -> None:
        self._recording = bool(active)
        if getattr(self, "record_btn", None) is not None:
            self.record_btn.setText("Stop recording" if self._recording else "Record for ISP")
        if getattr(self, "hero_hint", None) is not None and self._recording:
            self.hero_hint.setText("Recording")

    def _on_record_clicked(self) -> None:
        handler = getattr(self, "_record_handler", None)
        if callable(handler):
            handler()

    def _footer_website_href(self) -> str:
        app_cfg = self.config.get("app", {})
        site = (app_cfg.get("website") or "https://ciaoim.tech/projects/ami").strip()
        if site and not site.startswith(("http://", "https://")):
            site = "https://" + site.lstrip("/")
        return site

    def _apply_footer_copyright(self) -> None:
        if getattr(self, "footer_copyright", None) is None:
            return
        app_cfg = self.config.get("app", {})
        copy_txt = app_cfg.get("copyright", "© 2025–2026 CiaoIM™ by Daniel Giovannetti")
        esc = html.escape(copy_txt)
        href = html.escape(self._footer_website_href(), quote=True)
        ac = self._pal.accent
        mu = self._pal.muted
        self.footer_copyright.setText(
            f'<span style="color:{mu};">{esc}</span>'
            f' · <a href="{href}" style="color:{ac}; text-decoration:none;">ciaoim.tech</a>'
        )
        self.footer_copyright.setToolTip(f"Apri il sito ufficiale ({self._footer_website_href()})")

    def _stars_accent_hex(self) -> str:
        return self._pal.accent

    def _stars_muted_hex(self) -> str:
        return self._pal.muted

    def _refresh_github_stars_labels(self) -> None:
        ac = self._stars_accent_hex()
        if self._github_stars_cached is not None:
            label = f"★ {self._github_stars_cached} · Lascia una stella su GitHub"
        else:
            label = "Lascia una stella su GitHub"
        markup = (
            f'<a href="{GITHUB_REPO_URL}" style="color:{ac}; text-decoration:none;">{html.escape(label)}</a>'
        )
        if getattr(self, "stars_label", None) is not None:
            self.stars_label.setText(markup)
        if getattr(self, "compact_stars", None) is not None:
            self.compact_stars.setText(markup)

    def _on_github_stars(self, count: object) -> None:
        if isinstance(count, int):
            self._github_stars_cached = count
        self._refresh_github_stars_labels()

    def _fetch_github_stars(self) -> None:
        now = time.monotonic()
        if self._github_stars_last_fetch is not None and now - self._github_stars_last_fetch < 45:
            return
        self._github_stars_last_fetch = now
        bridge = self._github_stars_bridge

        def run() -> None:
            try:
                import requests

                r = requests.get(
                    GITHUB_REPO_API,
                    timeout=15,
                    headers={
                        "Accept": "application/vnd.github+json",
                        "X-GitHub-Api-Version": "2022-11-28",
                        "User-Agent": "AMI-ActiveMonitorOfInternet (https://github.com/dgiovannetti/AMI)",
                    },
                )
                if r.status_code == 200:
                    data = r.json()
                    n = data.get("stargazers_count")
                    bridge.stars_ready.emit(n if isinstance(n, int) else None)
                else:
                    bridge.stars_ready.emit(None)
            except Exception:
                bridge.stars_ready.emit(None)

        threading.Thread(target=run, daemon=True).start()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._fetch_github_stars()

    def _chart_legend(self) -> QWidget:
        row = QWidget()
        row.setObjectName("ChartLegend")
        lay = QHBoxLayout(row)
        lay.setContentsMargins(8, 2, 8, 0)
        lay.setSpacing(16)
        items = (
            ("online", "Online"),
            ("unstable", "Unstable"),
            ("captive", "Captive"),
            ("offline", "Offline"),
        )
        for key, label in items:
            color = getattr(self._pal, key)
            swatch = QLabel()
            swatch.setFixedSize(12, 12)
            swatch.setStyleSheet(
                f"background-color: {color}; border: none; border-radius: 2px;"
            )
            text = QLabel(label)
            text.setFont(QFont("Helvetica Neue", 11, QFont.Weight.Medium))
            text.setStyleSheet(
                f"color: {self._pal.muted}; border: none; background: transparent;"
            )
            lay.addWidget(swatch, 0, Qt.AlignmentFlag.AlignVCenter)
            lay.addWidget(text, 0, Qt.AlignmentFlag.AlignVCenter)
        lay.addStretch()
        return row

    def _setup_matplotlib_axes(self) -> None:
        self.figure.clear()
        p = self._pal
        face = p.surface
        tick = p.muted
        grid = p.grid

        # Thin status ribbon on top + latency chart — avoids the dense “barcode” of status dots.
        gs = self.figure.add_gridspec(
            2, 1, height_ratios=[0.32, 1.0], left=0.08, right=0.97, top=0.98, bottom=0.14, hspace=0.22
        )
        self.ax1 = self.figure.add_subplot(gs[0], facecolor=face)
        self.ax2 = self.figure.add_subplot(gs[1], facecolor=face, sharex=self.ax1)

        for ax in (self.ax1, self.ax2):
            for spine in ax.spines.values():
                spine.set_visible(False)

        self.ax1.set_ylim(0, 1)
        self.ax1.set_yticks([])
        self.ax1.tick_params(axis="x", labelbottom=False, length=0)
        self.ax1.set_ylabel("Link", color=tick, fontsize=10, fontweight="600", labelpad=10)
        self.ax1.grid(False)

        self.ax2.tick_params(colors=tick, labelsize=9)
        self.ax2.grid(True, alpha=0.18, color=grid, linestyle="-", linewidth=0.5)
        self.ax2.set_ylabel("Latency (ms)", color=tick, fontsize=10, fontweight="600")

        self._status_bars = []
        self._status_legend = None
        self._line2, = self.ax2.plot([], [], "-", color=p.text, linewidth=1.8, antialiased=True, zorder=3)
        self._fill2 = None
        self._incident_spans = []
        self._chart_colors = {
            "online": p.online,
            "unstable": p.unstable,
            "captive": p.captive,
            "offline": p.offline,
            "line": p.text,
        }

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

    def _chip_qss(self, color: str) -> str:
        return (
            f"QLabel {{ color: {color}; background-color: {self._pal.surface}; "
            f"border: 1px solid {color}; border-radius: 8px; padding: 4px 10px; }}"
        )

    def _update_compact_chips(self, status: str) -> None:
        labels = {"online": "Online", "unstable": "Unstable", "captive": "Captive", "offline": "Offline"}
        txt = labels.get(status, "Unknown")
        fg = status_color(self._pal, status)
        qss = self._chip_qss(fg)
        self.compact_status_chip.setText(txt)
        self.compact_status_chip.setStyleSheet(qss)
        if getattr(self, "status_chip", None) is not None:
            self.status_chip.setText(txt)
            self.status_chip.setStyleSheet(qss)

    def update_data(self, status, statistics: dict) -> None:
        labels = {"online": "Online", "unstable": "Unstable", "captive": "Captive", "offline": "Offline"}
        st_text = labels.get(status.status, "Unknown")
        st_color = status_color(self._pal, status.status)
        reason = getattr(status, "reason", None)
        st_foot = reason_text(reason) if reason else ""
        self.card_status.set_value(st_text)
        self.card_status.set_accent_color(st_color)
        self.card_status.set_footnote(st_foot)
        if getattr(self, "header_reason", None) is not None:
            show_reason = bool(reason and reason != "ok")
            self.header_reason.setText(st_foot if show_reason else "")
            self.header_reason.setVisible(show_reason)
        checked = getattr(status, "timestamp", None)
        if getattr(self, "hero_hint", None) is not None:
            if getattr(self, "_recording", False):
                self.hero_hint.setText("Recording")
            else:
                self.hero_hint.setText(checked.strftime("%H:%M:%S") if checked else "")

        self._update_compact_chips(status.status)

        if getattr(status, "avg_latency_ms", None) is not None:
            ms = status.avg_latency_ms
            self.card_latency.set_value(f"{ms:.0f} ms")
            self.card_latency.set_footnote("Round-trip estimate" if ms < 200 else "Elevated delay")
            self.compact_ping.setText(f"{ms:.0f} ms")
        else:
            self.card_latency.set_value("—")
            self.card_latency.set_footnote("")
            self.compact_ping.setText("— ms")

        uptime_pct = statistics.get("uptime_percentage")
        if uptime_pct is None:
            uptime_pct = getattr(self.monitor, "get_uptime_percentage", lambda: None)()
        self.card_uptime.set_value(f"{uptime_pct:.1f} %" if uptime_pct is not None else "—")
        self.card_uptime.set_footnote("Session availability" if uptime_pct is not None else "")

        success_pct = (status.successful_pings / status.total_pings * 100) if getattr(status, "total_pings", 0) > 0 else None
        self.card_success.set_value(f"{success_pct:.1f} %" if success_pct is not None else "—")
        self.card_success.set_footnote("Last probe window" if success_pct is not None else "")

        speed_mbps = getattr(status, "speed_mbps", None)
        speed_tier = getattr(status, "speed_tier", None)
        speed_compact = "—"
        if speed_tier is not None and speed_mbps is not None:
            if speed_mbps >= 1000:
                self.card_speed.set_value(f"{speed_mbps / 1000:.2f} Gbps")
                speed_compact = f"{speed_mbps / 1000:.2f} Gbps"
            else:
                self.card_speed.set_value(f"{speed_mbps:.0f} Mbps")
                speed_compact = f"{speed_mbps:.0f} Mbps"
            tier_labels = {"fast": "Fast", "medium": "Mid", "slow": "Slow"}
            self.card_speed.set_accent_color(self._pal.text)
            self.card_speed.set_footnote(tier_labels.get(speed_tier, ""))
            speed_compact += f" · {speed_tier.capitalize()}"
        else:
            self.card_speed.set_value("—")
            self.card_speed.set_accent_color(self._pal.text)
            self.card_speed.set_footnote("")

        self._update_network_cards(status)

        up_s = f"{uptime_pct:.1f}% uptime" if uptime_pct is not None else "uptime —"
        ping_s = f"{success_pct:.0f}% probes OK" if success_pct is not None else "probes —"
        net_bits = [up_s, ping_s, speed_compact]
        isp_name = getattr(status, "isp", None)
        if isp_name:
            net_bits.append(str(isp_name))
        vpn_on = getattr(status, "vpn_connected", None)
        if vpn_on is True:
            net_bits.append("VPN on")
        elif vpn_on is False:
            net_bits.append("VPN off")
        self.compact_meta.setText("  ·  ".join(net_bits))

        self.compact_ping.setStyleSheet(
            f"border: none; background: transparent; color: {self._pal.text};"
        )

        self.update_graphs()

    def _update_network_cards(self, status) -> None:
        lookup = bool(getattr(self.monitor, "lookup_public_network", True))
        isp = getattr(status, "isp", None)
        ip = getattr(status, "public_ip", None)
        if not lookup:
            self.card_isp.set_value("—")
            self.card_isp.set_footnote("Enable in Settings")
            self.card_ip.set_value("—")
            self.card_ip.set_footnote("Enable in Settings")
        elif not isp and not ip:
            self.card_isp.set_value("—")
            self.card_isp.set_footnote("Looking up")
            self.card_ip.set_value("—")
            self.card_ip.set_footnote("Looking up")
        else:
            self.card_isp.set_value(str(isp) if isp else "—")
            self.card_isp.set_footnote("")
            self.card_ip.set_value(str(ip) if ip else "—")
            self.card_ip.set_footnote("")
        self.card_isp.set_accent_color(self._pal.text)
        self.card_ip.set_accent_color(self._pal.text)

        vpn_on = getattr(status, "vpn_connected", None)
        provider = getattr(status, "vpn_provider", None) or ""
        if vpn_on is True:
            self.card_vpn.set_value("On")
            self.card_vpn.set_footnote(provider)
        elif vpn_on is False:
            self.card_vpn.set_value("Off")
            self.card_vpn.set_footnote("")
        else:
            self.card_vpn.set_value("—")
            self.card_vpn.set_footnote("")
        self.card_vpn.set_accent_color(self._pal.text)

    @staticmethod
    def _status_runs(statuses: list) -> list:
        """Collapse consecutive identical statuses into (start, length, status) runs."""
        if not statuses:
            return []
        runs = []
        start = 0
        current = statuses[0]
        for i, st in enumerate(statuses[1:], start=1):
            if st != current:
                runs.append((start, i - start, current))
                start = i
                current = st
        runs.append((start, len(statuses) - start, current))
        return runs

    @staticmethod
    def _bucket_statuses(statuses: list, max_buckets: int = 120) -> list:
        """Downsample status history for the ribbon; keep worst status per bucket."""
        n = len(statuses)
        if n <= max_buckets:
            return list(statuses)
        rank = {"online": 0, "unstable": 1, "captive": 2, "offline": 3}
        out = []
        for b in range(max_buckets):
            a = (b * n) // max_buckets
            z = ((b + 1) * n) // max_buckets
            chunk = statuses[a:z] or ["online"]
            out.append(max(chunk, key=lambda s: rank.get(s, 0)))
        return out

    def _set_time_ticks(self, history) -> None:
        n = len(history)
        if n < 2 or getattr(history[-1], "timestamp", None) is None:
            self.ax2.set_xticks([])
            return
        slots = 4 if n >= 4 else n
        indices = [round(i * (n - 1) / (slots - 1)) for i in range(slots)] if slots > 1 else [0]
        labels = []
        for i in indices:
            ts = getattr(history[i], "timestamp", None)
            labels.append(ts.strftime("%H:%M") if ts else "")
        self.ax2.set_xticks(indices)
        self.ax2.set_xticklabels(labels)

    def update_graphs(self) -> None:
        if not self.isVisible():
            return
        history = getattr(self.monitor, "status_history", [])
        if not history:
            return
        statuses = [
            h.status if h.status in ("online", "unstable", "captive", "offline") else "offline" for h in history
        ]
        n = len(history)
        last = history[-1]
        fingerprint = (
            n,
            last.status,
            last.avg_latency_ms,
            getattr(last, "timestamp", None),
        )
        if fingerprint == getattr(self, "_graph_fingerprint", None):
            return
        self._graph_fingerprint = fingerprint
        idx = np.arange(n, dtype=float)
        lat = np.array(
            [h.avg_latency_ms if h.avg_latency_ms is not None else np.nan for h in history],
            dtype=float,
        )

        for artist in getattr(self, "_status_bars", []) or []:
            try:
                artist.remove()
            except Exception:
                pass
        self._status_bars = []
        for artist in getattr(self, "_incident_spans", []) or []:
            try:
                artist.remove()
            except Exception:
                pass
        self._incident_spans = []

        ribbon = self._bucket_statuses(statuses)
        rb = max(len(ribbon), 1)
        for start, width, st in self._status_runs(ribbon):
            color = self._chart_colors.get(st, self._chart_colors["offline"])
            x0 = (start * n / rb) - 0.5
            w = width * n / rb
            bar = self.ax1.barh(
                0.5,
                w,
                left=x0,
                height=0.72,
                color=color,
                alpha=1.0,
                linewidth=0,
                align="center",
                zorder=2,
            )
            self._status_bars.extend(bar)
            if st == "online":
                continue
            span = self.ax2.axvspan(
                x0,
                x0 + w,
                color=color,
                alpha=0.22,
                linewidth=0,
                zorder=1,
            )
            self._incident_spans.append(span)

        self._set_time_ticks(history)

        self._line2.set_data(idx, lat)
        if self._fill2 is not None:
            try:
                self._fill2.remove()
            except Exception:
                pass
        self._fill2 = self.ax2.fill_between(
            idx,
            lat,
            where=np.isfinite(lat),
            alpha=0.14,
            color=self._chart_colors["line"],
            interpolate=False,
            zorder=2,
        )

        x_right = max(n - 1, 1) + 0.5
        self.ax1.set_xlim(-0.5, x_right)
        self.ax2.set_xlim(-0.5, x_right)
        finite = lat[np.isfinite(lat)]
        lat_max = float(np.max(finite)) if finite.size else 0.0
        self.ax2.set_ylim(0, max(lat_max * 1.15, 10.0))
        self.canvas.draw_idle()

    def refresh_data(self) -> None:
        if not self.isVisible():
            return
        if self.monitor.last_status:
            self.update_data(self.monitor.last_status, self.monitor.get_statistics())

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if getattr(self, "refresh_timer", None) is not None and not self.refresh_timer.isActive():
            self.refresh_timer.start(5000)
        # Force a chart refresh when reopened (fingerprint may skip otherwise).
        self._graph_fingerprint = None
        QTimer.singleShot(0, self.refresh_data)

    def hideEvent(self, event) -> None:
        if getattr(self, "refresh_timer", None) is not None:
            self.refresh_timer.stop()
        super().hideEvent(event)

    def closeEvent(self, event) -> None:
        if self.tray_icon and self.tray_icon.isVisible():
            event.ignore()
            self.hide()
        else:
            if getattr(self, "refresh_timer", None) is not None:
                self.refresh_timer.stop()
            event.accept()
