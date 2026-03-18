"""
AMI 3.0 - Theme support: light, dark, auto (system).
"""

from typing import Literal

ThemeName = Literal["auto", "light", "dark"]


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


def get_stylesheet(theme: ThemeName) -> str:
    """Return main window/dialog stylesheet for the given theme."""
    effective = resolve_theme(theme)
    if effective == "dark":
        return """
            QMainWindow, QDialog, QWidget { background-color: #0f172a; }
            QLabel { color: #e2e8f0; }
            QFrame { background-color: #1e293b; border: 1px solid #334155; border-radius: 12px; }
            QPushButton {
                background-color: #3b82f6; color: #ffffff; border: none; border-radius: 8px;
                padding: 10px 20px; font-size: 13px; font-weight: 600;
            }
            QPushButton:hover { background-color: #2563eb; }
            QPushButton:pressed { background-color: #1d4ed8; }
            QPushButton:disabled { background-color: #475569; color: #94a3b8; }
            QLineEdit, QSpinBox, QDoubleSpinBox, QPlainTextEdit, QComboBox, QTextEdit {
                background-color: #1e293b; border: 1px solid #475569; border-radius: 6px;
                color: #e2e8f0; padding: 8px 12px;
            }
            QTabWidget::pane { background-color: #1e293b; border: 1px solid #334155; border-radius: 8px; }
            QTabBar::tab { background: transparent; color: #94a3b8; padding: 10px 20px; }
            QTabBar::tab:selected { color: #f8fafc; border-bottom: 2px solid #3b82f6; }
            QCheckBox { color: #cbd5e1; spacing: 8px; }
            QProgressBar { background-color: #334155; border-radius: 6px; }
            QProgressBar::chunk { background-color: #3b82f6; border-radius: 6px; }
        """
    # light
    return """
        QMainWindow, QDialog, QWidget { background-color: #f9fafb; }
        QLabel { color: #111827; }
        QFrame { background-color: #ffffff; border: 1px solid #e5e7eb; border-radius: 12px; }
        QPushButton {
            background-color: #3b82f6; color: #ffffff; border: none; border-radius: 8px;
            padding: 10px 20px; font-size: 13px; font-weight: 600;
        }
        QPushButton:hover { background-color: #2563eb; }
        QPushButton:pressed { background-color: #1d4ed8; }
        QPushButton:disabled { background-color: #9ca3af; color: #f3f4f6; }
        QLineEdit, QSpinBox, QDoubleSpinBox, QPlainTextEdit, QComboBox, QTextEdit {
            background-color: #ffffff; border: 1px solid #d1d5db; border-radius: 6px;
            color: #111827; padding: 8px 12px;
        }
        QTabWidget::pane { background-color: #ffffff; border: 1px solid #e5e7eb; border-radius: 8px; }
        QTabBar::tab { background: transparent; color: #6b7280; padding: 10px 20px; }
        QTabBar::tab:selected { color: #111827; border-bottom: 2px solid #3b82f6; }
        QCheckBox { color: #374151; spacing: 8px; }
        QProgressBar { background-color: #e5e7eb; border-radius: 6px; }
        QProgressBar::chunk { background-color: #3b82f6; border-radius: 6px; }
    """
