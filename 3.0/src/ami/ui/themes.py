"""
AMI 3.0 - Theme support: light (default look), dark, auto (system).
Light-first: paper canvas, one accent, 1px borders. No gradients.
"""

from dataclasses import dataclass
from typing import Literal

ThemeName = Literal["auto", "light", "dark"]


@dataclass(frozen=True)
class Palette:
    page: str
    surface: str
    text: str
    muted: str
    border: str
    accent: str
    accent_hover: str
    on_accent: str
    online: str
    unstable: str
    captive: str
    offline: str
    grid: str


LIGHT = Palette(
    page="#f7f7f5",
    surface="#ffffff",
    text="#141414",
    muted="#5c5c5c",
    border="#e6e6e3",
    accent="#ff6d5a",
    accent_hover="#e85a48",
    on_accent="#ffffff",
    online="#1a7f4b",
    unstable="#d97706",
    captive="#6d28d9",
    offline="#b91c1c",
    grid="#eceae6",
)

DARK = Palette(
    page="#161616",
    surface="#1e1e1e",
    text="#f2f0ea",
    muted="#9a9790",
    border="#2e2e2e",
    accent="#ff6d5a",
    accent_hover="#ff8574",
    on_accent="#141414",
    online="#3ecf8e",
    unstable="#f5a524",
    captive="#c4b5fd",
    offline="#f07167",
    grid="#2a2a2a",
)


def _is_dark_system() -> bool:
    """Guess system dark mode (Qt or env)."""
    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtGui import QPalette
        app = QApplication.instance()
        if app:
            bg = app.palette().color(QPalette.ColorRole.Window)
            gray = (bg.red() + bg.green() + bg.blue()) / 3
            return gray < 128
    except Exception:
        pass
    return False


def resolve_theme(theme: ThemeName) -> Literal["light", "dark"]:
    if theme == "dark":
        return "dark"
    if theme == "light":
        return "light"
    return "dark" if _is_dark_system() else "light"


def palette(theme: ThemeName) -> Palette:
    return DARK if resolve_theme(theme) == "dark" else LIGHT


def status_color(pal: Palette, status: str) -> str:
    if status == "online":
        return pal.online
    if status == "unstable":
        return pal.unstable
    if status == "captive":
        return pal.captive
    return pal.offline


def get_stylesheet(theme: ThemeName) -> str:
    """Return main window/dialog stylesheet for the given theme."""
    p = palette(theme)
    return f"""
        QMainWindow, QDialog, QWidget {{ background-color: {p.page}; color: {p.text}; }}
        QLabel {{ color: {p.text}; background: transparent; border: none; }}
        QFrame {{
            background-color: {p.surface};
            border: 1px solid {p.border};
            border-radius: 12px;
            color: {p.text};
        }}
        QPushButton {{
            background-color: {p.surface};
            color: {p.text};
            border: 1px solid {p.border};
            border-radius: 8px;
            padding: 8px 16px;
            font-size: 13px;
            font-weight: 600;
        }}
        QPushButton:hover {{ border-color: {p.text}; }}
        QPushButton:pressed {{ background-color: {p.page}; }}
        QPushButton:disabled {{ color: {p.muted}; border-color: {p.border}; }}
        QPushButton#PrimaryButton {{
            background-color: {p.accent};
            color: {p.on_accent};
            border: 1px solid {p.accent};
        }}
        QPushButton#PrimaryButton:hover {{ background-color: {p.accent_hover}; border-color: {p.accent_hover}; }}
        QLineEdit, QSpinBox, QDoubleSpinBox, QPlainTextEdit, QComboBox, QTextEdit {{
            background-color: {p.surface};
            border: 1px solid {p.border};
            border-radius: 6px;
            color: {p.text};
            padding: 8px 12px;
        }}
        QTabWidget::pane {{
            background-color: {p.surface};
            border: 1px solid {p.border};
            border-radius: 8px;
            top: -1px;
            padding: 8px;
        }}
        QTabBar::tab {{ background: transparent; color: {p.muted}; padding: 10px 18px; border: none; }}
        QTabBar::tab:selected {{ color: {p.text}; border-bottom: 2px solid {p.accent}; }}
        QCheckBox {{ color: {p.text}; spacing: 8px; }}
        QMenu {{
            background-color: {p.surface};
            color: {p.text};
            border: 1px solid {p.border};
            padding: 4px;
        }}
        QMenu::item {{ padding: 6px 18px; background: transparent; }}
        QMenu::item:disabled {{ color: {p.muted}; }}
        QMenu::separator {{ height: 1px; background: {p.border}; margin: 4px 8px; }}
        QProgressBar {{ background-color: {p.page}; border: 1px solid {p.border}; border-radius: 6px; }}
        QProgressBar::chunk {{ background-color: {p.accent}; border-radius: 5px; }}
    """
