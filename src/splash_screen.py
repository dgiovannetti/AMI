"""
AMI - Active Monitor of Internet
Splash Screen - DESIGN ULTRA PROFESSIONALE

Clean, minimal, enterprise-grade design
"""

from PyQt6.QtWidgets import QSplashScreen
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont, QPen, QBrush
import sys


class UltraModernSplashScreen(QSplashScreen):
    """Ultra professional enterprise splash screen"""

    def __init__(self):
        pixmap = QPixmap(480, 300)
        pixmap.fill(Qt.GlobalColor.transparent)

        super().__init__(pixmap)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._opacity = 0.0
        self.draw_splash()

        # Quick fade-in
        self.animation = QPropertyAnimation(self, b"opacity")
        self.animation.setDuration(500)
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.animation.start()

    def draw_splash(self):
        """Draw ultra clean professional splash"""
        pixmap = self.pixmap()
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        # Dark background (matches dashboard)
        painter.fillRect(0, 0, 480, 300, QColor(15, 23, 42))  # #0f172a

        # Ultra subtle border
        painter.setPen(QPen(QColor(31, 41, 55), 1))  # #1f2937
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(0, 0, 480, 300, 8, 8)

        # Minimal logo area - just text, no icons
        font = QFont("SF Pro Display", 36, QFont.Weight.Bold) if sys.platform == "darwin" else QFont("Segoe UI", 36, QFont.Weight.Bold)
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        painter.setFont(font)
        painter.setPen(QColor(226, 232, 240))  # #e2e8f0
        painter.drawText(0, 80, 480, 50, Qt.AlignmentFlag.AlignCenter, "AMI")

        # Tagline - very minimal
        font = QFont("SF Pro Display", 12) if sys.platform == "darwin" else QFont("Segoe UI", 12)
        font.setWeight(QFont.Weight.Normal)
        painter.setFont(font)
        painter.setPen(QColor(148, 163, 184))  # #94a3b8
        painter.drawText(0, 130, 480, 20, Qt.AlignmentFlag.AlignCenter, "Active Monitor of Internet")

        # Clean divider - ultra thin
        painter.fillRect(120, 170, 240, 1, QColor(51, 65, 85))  # #334155

        # Enterprise info block
        font = QFont("SF Pro Display", 10) if sys.platform == "darwin" else QFont("Segoe UI", 10)
        painter.setFont(font)
        painter.setPen(QColor(148, 163, 184))  # #94a3b8

        # Company info - left aligned, professional
        painter.drawText(40, 190, 400, 20, Qt.AlignmentFlag.AlignLeft, "CiaoIM™ di Daniel Giovannetti")
        painter.drawText(40, 210, 400, 20, Qt.AlignmentFlag.AlignLeft, "Internet Connection Monitor")
        painter.drawText(40, 230, 400, 20, Qt.AlignmentFlag.AlignLeft, "Enterprise Edition v1.0.0")

        # Right side - website and tagline
        painter.setPen(QColor(203, 213, 225))  # #cbd5e1
        painter.drawText(280, 190, 160, 20, Qt.AlignmentFlag.AlignRight, "ciaoim.tech")

        font_small = QFont("SF Pro Display", 8) if sys.platform == "darwin" else QFont("Segoe UI", 8)
        font_small.setItalic(True)
        painter.setFont(font_small)
        painter.setPen(QColor(203, 213, 225))  # #cbd5e1
        painter.drawText(280, 210, 160, 20, Qt.AlignmentFlag.AlignRight, "Crafted logic. Measured force.")
        painter.drawText(280, 230, 160, 20, Qt.AlignmentFlag.AlignRight, "Front-end vision, compiled systems, and hardcoded ethics.")

        # Bottom - inspiration in very small
        font_tiny = QFont("SF Pro Display", 7) if sys.platform == "darwin" else QFont("Segoe UI", 7)
        font_tiny.setItalic(True)
        painter.setFont(font_tiny)
        painter.setPen(QColor(148, 163, 184))
        painter.drawText(20, 270, 440, 15, Qt.AlignmentFlag.AlignCenter,
                        "Intuizione colta insieme a Giovanni Calvario in aliscafo per il 40° Convegno di Capri dei Giovani Imprenditori")

        painter.end()
        self.setPixmap(pixmap)

    def get_opacity(self):
        return self._opacity

    def set_opacity(self, value):
        self._opacity = value
        self.setWindowOpacity(value)

    opacity = pyqtProperty(float, get_opacity, set_opacity)

    def fade_out(self, callback=None):
        """Quick fade out"""
        self.fade_animation = QPropertyAnimation(self, b"opacity")
        self.fade_animation.setDuration(300)
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.InCubic)

        if callback:
            self.fade_animation.finished.connect(callback)

        self.fade_animation.finished.connect(self.close)
        self.fade_animation.start()

    def showMessage(self, message, color=None):
        """Show message"""
        if color is None:
            color = QColor(148, 163, 184)

        pixmap = self.pixmap()
        painter = QPainter(pixmap)

        # Clear area (dark)
        painter.fillRect(0, 280, 480, 20, QColor(15, 23, 42))

        # Draw message
        font = QFont("SF Pro Display", 9) if sys.platform == "darwin" else QFont("Segoe UI", 9)
        painter.setFont(font)
        painter.setPen(color)
        painter.drawText(0, 280, 480, 20, Qt.AlignmentFlag.AlignCenter, message)

        painter.end()
        self.setPixmap(pixmap)

        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()
