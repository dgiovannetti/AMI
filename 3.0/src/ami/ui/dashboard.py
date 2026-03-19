"""
AMI 3.0 — Dashboard: low-chrome UI (minimal borders), rich compact mode.
"""

import html
import threading
import time
from typing import Optional

import numpy as np
from PyQt6.QtCore import QObject, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QGraphicsDropShadowEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ami.core.paths import get_base_path
from ami.ui.themes import get_stylesheet, resolve_theme

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


class _GradientHeaderBar(QWidget):
    """Thin top accent strip — no frame border."""

    def __init__(self, dark: bool, height: int = 4, parent=None):
        super().__init__(parent)
        self._dark = dark
        self.setFixedHeight(height)
        self.setStyleSheet("background: transparent; border: none;")

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        g = QLinearGradient(0, 0, self.width(), 0)
        if self._dark:
            g.setColorAt(0.0, QColor(0, 229, 204, 255))
            g.setColorAt(0.45, QColor(168, 85, 247, 255))
            g.setColorAt(1.0, QColor(56, 189, 248, 255))
        else:
            g.setColorAt(0.0, QColor(13, 148, 136, 255))
            g.setColorAt(0.5, QColor(194, 65, 12, 255))
            g.setColorAt(1.0, QColor(30, 58, 138, 255))
        p.fillRect(self.rect(), g)


class MetricCard(QWidget):
    """
    Metric tile: no stroke — depth from soft shadow + fill only.
    QWidget avoids global QFrame { border } from theme leaking onto cards.
    """

    def __init__(self, title: str, accent_hex: str, initial_value: str = "—", dark: bool = False):
        super().__init__()
        self._dark = dark
        self._accent = accent_hex
        self.setObjectName("MetricCard")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setMinimumHeight(124)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(36 if dark else 26)
        shadow.setOffset(0, 14)
        shadow.setColor(QColor(0, 0, 0, 42 if dark else 18))
        self.setGraphicsEffect(shadow)
        self._apply_shell_style()

        lay = QVBoxLayout(self)
        lay.setSpacing(4)
        lay.setContentsMargins(20, 16, 20, 16)

        top = QHBoxLayout()
        top.setSpacing(8)
        self.badge = QLabel("●")
        self.badge.setStyleSheet(self._lbl_reset() + f"color: {accent_hex}; font-size: 9px;")
        self.title_lbl = QLabel(title.upper())
        self.title_lbl.setFont(QFont("Helvetica Neue", 9, QFont.Weight.DemiBold))
        self.title_lbl.setStyleSheet(self._lbl_reset() + self._title_style())
        self.title_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        top.addWidget(self.badge)
        top.addWidget(self.title_lbl, 1)
        lay.addLayout(top)

        self.value_lbl = QLabel(initial_value)
        self.value_lbl.setFont(QFont("Helvetica Neue", 28, QFont.Weight.Black))
        self.value_lbl.setStyleSheet(self._lbl_reset() + f"color: {accent_hex}; letter-spacing: -0.5px;")
        lay.addWidget(self.value_lbl)

        self.foot_lbl = QLabel("")
        self.foot_lbl.setFont(QFont("", 10, QFont.Weight.Medium))
        self.foot_lbl.setStyleSheet(self._lbl_reset() + self._foot_style())
        lay.addWidget(self.foot_lbl)

    @staticmethod
    def _lbl_reset() -> str:
        return "border: none; outline: none; background: transparent; "

    def _title_style(self) -> str:
        c = "#64748b" if self._dark else "#78716c"
        return f"color: {c}; letter-spacing: 2px;"

    def _foot_style(self) -> str:
        c = "#475569" if self._dark else "#57534e"
        return f"color: {c};"

    def _apply_shell_style(self) -> None:
        if self._dark:
            self.setStyleSheet(
                """
                QWidget#MetricCard {
                    background-color: rgba(255, 255, 255, 0.055);
                    border: none;
                    border-radius: 20px;
                }
                """
            )
        else:
            self.setStyleSheet(
                """
                QWidget#MetricCard {
                    background-color: rgba(255, 255, 255, 0.72);
                    border: none;
                    border-radius: 20px;
                }
                """
            )

    def set_value(self, text: str) -> None:
        self.value_lbl.setText(text)

    def set_accent_color(self, color: str) -> None:
        self._accent = color
        self.badge.setStyleSheet(self._lbl_reset() + f"color: {color}; font-size: 9px;")
        self.value_lbl.setStyleSheet(self._lbl_reset() + f"color: {color}; letter-spacing: -0.5px;")

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
        theme = config.get("ui", {}).get("theme", "auto")
        self._dark = resolve_theme(theme) == "dark"
        self.setWindowTitle("AMI — Network Monitor")
        self.setGeometry(120, 80, 1120, 760)
        self.setMinimumSize(920, 620)

        self._github_stars_bridge = _GitHubStarsBridge(self)
        self._github_stars_bridge.stars_ready.connect(self._on_github_stars)

        self.setStyleSheet(get_stylesheet(theme) + self._dashboard_chrome_qss())
        self.setup_ui()

        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(5000)

        self._github_stars_timer = QTimer()
        self._github_stars_timer.timeout.connect(self._fetch_github_stars)
        self._github_stars_timer.start(10 * 60 * 1000)
        QTimer.singleShot(600, self._fetch_github_stars)

    def _dashboard_chrome_qss(self) -> str:
        # Reset theme QFrame borders inside this window (fixes “double box” on metrics)
        reset = """
            QMainWindow#EnterpriseDashboard QLabel {
                border: none;
                outline: none;
            }
            QMainWindow#EnterpriseDashboard QPushButton {
                outline: none;
            }
        """
        if self._dark:
            return reset + """
                QMainWindow#EnterpriseDashboard {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #06080f, stop:0.5 #0a0f1a, stop:1 #0f172a);
                }
            """
        return reset + """
            QMainWindow#EnterpriseDashboard {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #ebe8e4, stop:0.45 #f5f3f0, stop:1 #e7e2dc);
            }
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
        tb = "#0b0f18" if self._dark else "rgba(255,255,255,0.28)"
        self.top_bar.setStyleSheet(f"QWidget#DashTopBar {{ background-color: {tb}; border: none; }}")
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
            "border: none; background: transparent; color: #f8fafc;"
            if self._dark
            else "border: none; background: transparent; color: #1c1917;"
        )
        self.live_dot = QLabel("  LIVE")
        self.live_dot.setFont(QFont("Menlo", 10, QFont.Weight.Bold))
        self.live_dot.setStyleSheet(
            "border: none; background: transparent; color: #2dd4bf;"
            if self._dark
            else "border: none; background: transparent; color: #0d9488;"
        )
        row.addWidget(self.brand_title)
        row.addWidget(self.live_dot)
        row.addStretch()
        brand_col.addLayout(row)
        self.brand_sub = QLabel("Network pulse · latency · throughput")
        self.brand_sub.setFont(QFont("", 12, QFont.Weight.Medium))
        self.brand_sub.setStyleSheet(
            "border: none; background: transparent; color: #64748b;"
            if self._dark
            else "border: none; background: transparent; color: #78716c;"
        )
        brand_col.addWidget(self.brand_sub)
        top_layout.addLayout(brand_col, 0)
        top_layout.addStretch(2)

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
            """
            QLabel {
                background-color: rgba(168, 85, 247, 0.2);
                color: #e9d5ff;
                border: none;
                border-radius: 999px;
                padding: 6px 14px;
            }
            """
            if self._dark
            else """
            QLabel {
                background-color: rgba(13, 148, 136, 0.14);
                color: #134e4a;
                border: none;
                border-radius: 999px;
                padding: 6px 14px;
            }
            """
        )
        top_layout.addWidget(self.ver_badge, 0, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignVCenter)

        main_layout.addWidget(_GradientHeaderBar(self._dark, height=4))
        main_layout.addWidget(self.top_bar)

        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("background: transparent; border: none;")
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setSpacing(18)
        content_layout.setContentsMargins(28, 24, 28, 20)

        hero = QHBoxLayout()
        self.main_title = QLabel("Operations")
        self.main_title.setFont(QFont("Helvetica Neue", 26, QFont.Weight.Black))
        self.main_title.setStyleSheet(
            "border: none; background: transparent; color: #f1f5f9;"
            if self._dark
            else "border: none; background: transparent; color: #1c1917;"
        )
        hero.addWidget(self.main_title)
        hero.addStretch()
        self.hero_hint = QLabel("Streaming metrics")
        self.hero_hint.setFont(QFont("", 11, QFont.Weight.Medium))
        self.hero_hint.setStyleSheet(
            "border: none; background: transparent; color: #64748b;"
            if self._dark
            else "border: none; background: transparent; color: #a8a29e;"
        )
        hero.addWidget(self.hero_hint, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)
        content_layout.addLayout(hero)

        self.status_grid = QGridLayout()
        self.status_grid.setHorizontalSpacing(14)
        self.status_grid.setVerticalSpacing(14)

        self.card_status = MetricCard("Link", "#2dd4bf", "—", self._dark)
        self.card_latency = MetricCard("Latency", "#38bdf8", "—", self._dark)
        self.card_uptime = MetricCard("Uptime", "#a78bfa", "—", self._dark)
        self.card_success = MetricCard("Ping OK", "#fbbf24", "—", self._dark)
        self.card_speed = MetricCard("Throughput", "#94a3b8", "—", self._dark)
        self.status_cards = [
            self.card_status,
            self.card_latency,
            self.card_uptime,
            self.card_success,
            self.card_speed,
        ]
        for i, card in enumerate(self.status_cards):
            self.status_grid.addWidget(card, i // 4, i % 4)
        content_layout.addLayout(self.status_grid)

        chart_wrap = QWidget()
        chart_wrap.setObjectName("ChartShell")
        chart_wrap.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        cw_bg = "rgba(255,255,255,0.035)" if self._dark else "rgba(255,255,255,0.55)"
        chart_wrap.setStyleSheet(
            f"QWidget#ChartShell {{ background-color: {cw_bg}; border: none; border-radius: 22px; }}"
        )
        cw_lay = QVBoxLayout(chart_wrap)
        cw_lay.setContentsMargins(10, 10, 10, 6)
        Figure, FigureCanvas = _get_figure_canvas()
        self.figure = Figure(figsize=(10.5, 4.35), facecolor="none")
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
        c_lay.setContentsMargins(20, 12, 20, 16)
        c_lay.setSpacing(10)

        c_lay.addWidget(_GradientHeaderBar(self._dark, height=5))

        crow0 = QHBoxLayout()
        self.compact_brand = QLabel("AMI")
        self.compact_brand.setFont(QFont("Helvetica Neue", 15, QFont.Weight.Black))
        self.compact_brand.setStyleSheet(
            "border: none; background: transparent; color: #f8fafc;"
            if self._dark
            else "border: none; background: transparent; color: #1c1917;"
        )
        self.compact_sub = QLabel("compact")
        self.compact_sub.setFont(QFont("Helvetica Neue", 10, QFont.Weight.Medium))
        self.compact_sub.setStyleSheet(
            "border: none; background: transparent; color: #64748b;"
            if self._dark
            else "border: none; background: transparent; color: #a8a29e;"
        )
        crow0.addWidget(self.compact_brand)
        crow0.addWidget(self.compact_sub)
        crow0.addStretch()
        ver_c = self.config.get("app", {}).get("version", "")
        self.compact_ver = QLabel(f"v{ver_c}")
        self.compact_ver.setFont(QFont("Menlo", 9))
        self.compact_ver.setStyleSheet(
            "border: none; background: transparent; color: #64748b;"
            if self._dark
            else "border: none; background: transparent; color: #a8a29e;"
        )
        crow0.addWidget(self.compact_ver)
        c_lay.addLayout(crow0)

        self.compact_status_chip = QLabel("ONLINE")
        self.compact_status_chip.setFont(QFont("Helvetica Neue", 11, QFont.Weight.Bold))
        self.compact_status_chip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.compact_status_chip.setStyleSheet(
            "QLabel { color: #5eead4; background-color: rgba(45,212,191,0.18); border: none; "
            "border-radius: 12px; padding: 8px 16px; }"
            if self._dark
            else "QLabel { color: #0f766e; background-color: rgba(13,148,136,0.12); border: none; "
            "border-radius: 12px; padding: 8px 16px; }"
        )
        c_lay.addWidget(self.compact_status_chip)

        self.compact_ping = QLabel("— ms")
        self.compact_ping.setFont(QFont("Helvetica Neue", 36, QFont.Weight.Black))
        self.compact_ping.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.compact_ping.setStyleSheet(
            "border: none; background: transparent; color: #e2e8f0;"
            if self._dark
            else "border: none; background: transparent; color: #1c1917;"
        )
        c_lay.addWidget(self.compact_ping)

        self.compact_meta = QLabel("—")
        self.compact_meta.setFont(QFont("Helvetica Neue", 12, QFont.Weight.Medium))
        self.compact_meta.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.compact_meta.setStyleSheet(
            "border: none; background: transparent; color: #94a3b8;"
            if self._dark
            else "border: none; background: transparent; color: #78716c;"
        )
        self.compact_meta.setWordWrap(True)
        c_lay.addWidget(self.compact_meta)

        self.compact_hint = QLabel("Widen the window for charts & all metrics")
        self.compact_hint.setFont(QFont("", 10))
        self.compact_hint.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.compact_hint.setStyleSheet(
            "border: none; background: transparent; color: #64748b;"
            if self._dark
            else "border: none; background: transparent; color: #a8a29e;"
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
        bb_bg = "#0b0f18" if self._dark else "rgba(255,255,255,0.32)"
        self.bottom_bar.setStyleSheet(f"QWidget#DashBottomBar {{ background-color: {bb_bg}; border: none; }}")
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
        for text, slot, primary in (
            (" Refresh", self.refresh_data, False),
            (" Minimize", self.hide, False),
            (" Close", self.close, True),
        ):
            btn = QPushButton(text)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(self._btn_style(primary=primary))
            btn.clicked.connect(slot)
            bottom_layout.addWidget(btn)

        main_layout.addWidget(self.compact_widget)
        main_layout.addWidget(self.bottom_bar)

        self._refresh_github_stars_labels()

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
        ac = "#38bdf8" if self._dark else "#2563eb"
        mu = "#64748b" if self._dark else "#78716c"
        self.footer_copyright.setText(
            f'<span style="color:{mu};">{esc}</span>'
            f' · <a href="{href}" style="color:{ac}; text-decoration:none;">ciaoim.tech</a>'
        )
        self.footer_copyright.setToolTip(f"Apri il sito ufficiale ({self._footer_website_href()})")

    def _stars_accent_hex(self) -> str:
        return "#38bdf8" if self._dark else "#2563eb"

    def _stars_muted_hex(self) -> str:
        return "#64748b" if self._dark else "#78716c"

    def _refresh_github_stars_labels(self) -> None:
        ac = self._stars_accent_hex()
        mu = self._stars_muted_hex()
        star_link = (
            f'<a href="{GITHUB_REPO_URL}" style="color:{ac}; text-decoration:none;">Star</a>'
        )
        if self._github_stars_cached is not None:
            n = str(self._github_stars_cached)
            top = (
                f'<a href="{GITHUB_REPO_URL}" style="color:{ac}; text-decoration:none;">★ {n}</a>'
                f' <span style="color:{mu};">GitHub</span>'
                f' <span style="color:{mu};">·</span> {star_link}'
            )
            compact = (
                f'<a href="{GITHUB_REPO_URL}" style="color:{ac}; text-decoration:none;">★ {n}</a>'
                f'<span style="color:{mu};"> · </span>'
                f'<a href="{GITHUB_REPO_URL}" style="color:{ac}; text-decoration:none;">GitHub</a>'
                f'<span style="color:{mu};"> · </span>'
                f'<a href="{GITHUB_REPO_URL}" style="color:{ac}; text-decoration:none;">Star</a>'
            )
        else:
            top = (
                f'<a href="{GITHUB_REPO_URL}" style="color:{ac}; text-decoration:none;">GitHub</a>'
                f' <span style="color:{mu};">★ …</span>'
                f' <span style="color:{mu};">·</span> {star_link}'
            )
            compact = (
                f'<a href="{GITHUB_REPO_URL}" style="color:{ac}; text-decoration:none;">GitHub</a>'
                f'<span style="color:{mu};"> · ★… · </span>'
                f'<a href="{GITHUB_REPO_URL}" style="color:{ac}; text-decoration:none;">Star</a>'
            )
        if getattr(self, "stars_label", None) is not None:
            self.stars_label.setText(top)
        if getattr(self, "compact_stars", None) is not None:
            self.compact_stars.setText(compact)

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

    def _btn_style(self, primary: bool) -> str:
        if self._dark:
            if primary:
                return """
                    QPushButton {
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                            stop:0 #a855f7, stop:1 #6366f1);
                        color: #fafafa; border: none; border-radius: 12px;
                        padding: 10px 22px; font-weight: 700; font-size: 13px;
                    }
                    QPushButton:hover { background: #7c3aed; }
                """
            return """
                QPushButton {
                    background-color: rgba(255,255,255,0.07);
                    color: #e2e8f0; border: none;
                    border-radius: 12px; padding: 10px 20px; font-weight: 600; font-size: 13px;
                }
                QPushButton:hover { background-color: rgba(255,255,255,0.12); }
            """
        if primary:
            return """
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #0d9488, stop:1 #1e3a8a);
                    color: #fff; border: none; border-radius: 12px;
                    padding: 10px 22px; font-weight: 700; font-size: 13px;
                }
                QPushButton:hover { background: #0f766e; }
            """
        return """
            QPushButton {
                background-color: rgba(255,255,255,0.75);
                color: #44403c; border: none;
                border-radius: 12px; padding: 10px 20px; font-weight: 600; font-size: 13px;
            }
            QPushButton:hover { background-color: rgba(255,255,255,0.95); }
        """

    def _setup_matplotlib_axes(self) -> None:
        self.figure.clear()
        self.figure.subplots_adjust(left=0.08, right=0.97, top=0.92, bottom=0.14, hspace=0.42)
        face = "#0c1220" if self._dark else "#faf8f6"
        tick = "#94a3b8" if self._dark else "#57534e"
        grid = "#1e293b" if self._dark else "#e7e5e4"

        self.ax1 = self.figure.add_subplot(211, facecolor=face)
        self.ax2 = self.figure.add_subplot(212, facecolor=face)
        for ax in (self.ax1, self.ax2):
            ax.tick_params(colors=tick, labelsize=9)
            for spine in ax.spines.values():
                spine.set_visible(False)
            ax.grid(True, alpha=0.18, color=grid, linestyle="-", linewidth=0.5)

        self.ax1.set_ylim(-0.5, 2.5)
        self.ax1.set_yticks([0, 1, 2])
        self.ax1.set_yticklabels(["Off", "Unstable", "On"])
        self.ax1.set_ylabel("Status", color=tick, fontsize=10, fontweight="600")
        self.ax2.set_ylabel("Latency (ms)", color=tick, fontsize=10, fontweight="600")

        c_on = "#2dd4bf" if self._dark else "#0d9488"
        line_c = "#38bdf8" if self._dark else "#2563eb"
        self._scatter1 = self.ax1.scatter([], [], s=68, alpha=0.92, edgecolors="none", linewidths=0, zorder=3)
        self._line1, = self.ax1.plot([], [], "-", color="#64748b", alpha=0.28, linewidth=2, zorder=2)
        self._line2, = self.ax2.plot([], [], "-", color=line_c, linewidth=2.2, antialiased=True, zorder=3)
        self._fill2 = None
        self._chart_colors = {"on": c_on, "unstable": "#fbbf24", "off": "#f43f5e", "line": line_c}

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

    def _update_compact_chips(self, status: str) -> None:
        labels = {"online": "ONLINE", "unstable": "UNSTABLE", "offline": "OFFLINE"}
        txt = labels.get(status, "UNKNOWN")
        self.compact_status_chip.setText(txt)
        if self._dark:
            if status == "online":
                bg, fg = "rgba(45,212,191,0.18)", "#5eead4"
            elif status == "unstable":
                bg, fg = "rgba(251,191,36,0.18)", "#fcd34d"
            else:
                bg, fg = "rgba(244,63,94,0.18)", "#fda4af"
        else:
            if status == "online":
                bg, fg = "rgba(13,148,136,0.12)", "#0f766e"
            elif status == "unstable":
                bg, fg = "rgba(245,158,11,0.15)", "#b45309"
            else:
                bg, fg = "rgba(244,63,94,0.12)", "#be123c"
        self.compact_status_chip.setStyleSheet(
            f"QLabel {{ color: {fg}; background-color: {bg}; border: none; border-radius: 12px; padding: 8px 16px; }}"
        )

    def update_data(self, status, statistics: dict) -> None:
        status_map = {
            "online": ("Online", "#2dd4bf", "Live · stable route"),
            "unstable": ("Unstable", "#fbbf24", "Degraded · watch"),
            "offline": ("Offline", "#fb7185", "No route"),
        }
        st_text, st_color, st_foot = status_map.get(status.status, ("Unknown", "#94a3b8", ""))
        self.card_status.set_value(st_text)
        self.card_status.set_accent_color(st_color)
        self.card_status.set_footnote(st_foot)

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
            tier_colors = {"fast": "#2dd4bf", "medium": "#fbbf24", "slow": "#fb7185"}
            tier_labels = {"fast": "Fast tier", "medium": "Mid tier", "slow": "Slow tier"}
            self.card_speed.set_accent_color(tier_colors.get(speed_tier, "#94a3b8"))
            self.card_speed.set_footnote(tier_labels.get(speed_tier, ""))
            speed_compact += f" · {speed_tier.capitalize()}"
        else:
            self.card_speed.set_value("—")
            self.card_speed.set_accent_color("#94a3b8" if self._dark else "#78716c")
            self.card_speed.set_footnote("Run speed test from tray")

        up_s = f"{uptime_pct:.1f}% uptime" if uptime_pct is not None else "uptime —"
        ping_s = f"{success_pct:.0f}% probes OK" if success_pct is not None else "probes —"
        self.compact_meta.setText(f"{up_s}  ·  {ping_s}  ·  {speed_compact}")

        super_ping_color = "#e2e8f0" if self._dark else "#1c1917"
        self.compact_ping.setStyleSheet(
            f"border: none; background: transparent; color: {super_ping_color};"
        )

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
        c_on = self._chart_colors["on"]
        colors = [
            c_on if v == 2 else self._chart_colors["unstable"] if v == 1 else self._chart_colors["off"]
            for v in status_values
        ]
        self._scatter1.set_offsets(np.c_[idx, sv])
        self._scatter1.set_facecolors(colors)
        self._line1.set_data(idx, sv)
        self._line2.set_data(idx, lat)
        if self._fill2 is not None:
            try:
                self._fill2.remove()
            except Exception:
                pass
        lc = self._chart_colors["line"]
        self._fill2 = self.ax2.fill_between(idx, lat, alpha=0.18, color=lc, zorder=2)
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
