"""
AMI - Active Monitor of Internet
Splash Screen

Beautiful animated splash screen shown during app initialization
"""

from PyQt6.QtWidgets import QSplashScreen, QLabel, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont, QLinearGradient, QPen, QRadialGradient
import sys


class ModernSplashScreen(QSplashScreen):
    """
    Modern, elegant splash screen with gradient and animations
    """
    
    def __init__(self):
        # Create a pixmap for the splash screen - professional size
        pixmap = QPixmap(600, 400)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        super().__init__(pixmap)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Animation opacity
        self._opacity = 0.0
        
        # Draw the splash screen
        self.draw_splash()
        
        # Setup fade-in animation
        self.animation = QPropertyAnimation(self, b"opacity")
        self.animation.setDuration(800)
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.animation.start()
    
    def draw_splash(self):
        """Draw professional splash screen with modern design"""
        pixmap = self.pixmap()
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        # Professional gradient background
        gradient = QLinearGradient(0, 0, 0, 400)
        gradient.setColorAt(0, QColor(15, 23, 42))     # Slate-900
        gradient.setColorAt(0.5, QColor(30, 41, 59))   # Slate-800
        gradient.setColorAt(1, QColor(15, 23, 42))     # Slate-900
        painter.setBrush(gradient)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(0, 0, 600, 400, 16, 16)
        
        # Subtle outer shadow/border with gradient
        for i in range(3):
            opacity = 100 - (i * 30)
            painter.setPen(QPen(QColor(52, 211, 153, opacity), 1))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(i, i, 600-(i*2), 400-(i*2), 16-i, 16-i)
        
        # Professional WiFi icon with glow effect
        center_x, center_y = 300, 120
        
        # Glow effect
        glow_gradient = QRadialGradient(center_x, center_y, 60)
        glow_gradient.setColorAt(0, QColor(52, 211, 153, 40))
        glow_gradient.setColorAt(1, QColor(52, 211, 153, 0))
        painter.setBrush(glow_gradient)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(center_x - 60, center_y - 60, 120, 120)
        
        # WiFi arcs with professional styling
        arcs = [
            (25, 4, 200),
            (40, 5, 160),
            (55, 6, 120)
        ]
        for radius, width, opacity in arcs:
            pen = QPen(QColor(52, 211, 153, opacity), width)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            painter.drawArc(center_x - radius, center_y - radius,
                          radius * 2, radius * 2, 0, 180 * 16)
        
        # WiFi dot with shadow
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(0, 0, 0, 60))
        painter.drawEllipse(center_x - 6, center_y + 1, 12, 12)
        painter.setBrush(QColor(52, 211, 153))
        painter.drawEllipse(center_x - 7, center_y - 2, 14, 14)
        
        # App name with shadow effect
        font = QFont("SF Pro Display", 56, QFont.Weight.Bold) if sys.platform == "darwin" else QFont("Segoe UI", 56, QFont.Weight.Bold)
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 2)
        painter.setFont(font)
        
        # Text shadow
        painter.setPen(QColor(0, 0, 0, 80))
        painter.drawText(2, 192, 600, 70, Qt.AlignmentFlag.AlignCenter, "AMI")
        
        # Main text
        painter.setPen(QColor(52, 211, 153))
        painter.drawText(0, 190, 600, 70, Qt.AlignmentFlag.AlignCenter, "AMI")
        
        # Subtitle with proper spacing
        font = QFont("SF Pro Display", 16) if sys.platform == "darwin" else QFont("Segoe UI", 16)
        font.setWeight(QFont.Weight.Normal)
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        painter.setFont(font)
        painter.setPen(QColor(148, 163, 184, 200))
        painter.drawText(0, 250, 600, 30, Qt.AlignmentFlag.AlignCenter, "Active Monitor of Internet")
        
        # Elegant divider
        gradient_line = QLinearGradient(150, 285, 450, 285)
        gradient_line.setColorAt(0, QColor(52, 211, 153, 0))
        gradient_line.setColorAt(0.5, QColor(52, 211, 153, 120))
        gradient_line.setColorAt(1, QColor(52, 211, 153, 0))
        painter.setPen(QPen(QColor(52, 211, 153, 100), 2))
        painter.drawLine(150, 285, 450, 285)
        
        # Copyright
        font = QFont("SF Pro Display", 10) if sys.platform == "darwin" else QFont("Segoe UI", 10)
        painter.setFont(font)
        painter.setPen(QColor(148, 163, 184))
        painter.drawText(0, 300, 600, 20, Qt.AlignmentFlag.AlignCenter, "© 2025 CiaoIM™ di Daniel Giovannetti")
        
        # Website
        font = QFont("SF Pro Display", 9) if sys.platform == "darwin" else QFont("Segoe UI", 9)
        painter.setFont(font)
        painter.setPen(QColor(52, 211, 153, 180))
        painter.drawText(0, 318, 600, 16, Qt.AlignmentFlag.AlignCenter, "ciaoim.tech")
        
        # Tagline
        font_small = QFont("SF Pro Display", 8) if sys.platform == "darwin" else QFont("Segoe UI", 8)
        font_small.setItalic(True)
        painter.setFont(font_small)
        painter.setPen(QColor(100, 116, 139, 180))
        painter.drawText(50, 340, 500, 20, Qt.AlignmentFlag.AlignCenter, 
                        "Crafted logic. Measured force. Front-end vision, compiled systems, hardcoded ethics.")
        
        # Inspiration
        painter.drawText(40, 360, 520, 20, Qt.AlignmentFlag.AlignCenter,
                        "Intuizione colta insieme a Giovanni C. in aliscafo per il 40° Convegno di Capri dei Giovani Imprenditori")
        
        # Version
        font = QFont("SF Pro Display", 8) if sys.platform == "darwin" else QFont("Segoe UI", 8)
        painter.setFont(font)
        painter.setPen(QColor(71, 85, 105, 150))
        painter.drawText(0, 385, 600, 12, Qt.AlignmentFlag.AlignCenter, "v1.0.0 • 2025")
        
        painter.end()
        self.setPixmap(pixmap)
    
    def get_opacity(self):
        """Get current opacity"""
        return self._opacity
    
    def set_opacity(self, value):
        """Set opacity and update"""
        self._opacity = value
        self.setWindowOpacity(value)
    
    # Property for animation
    opacity = pyqtProperty(float, get_opacity, set_opacity)
    
    def fade_out(self, callback=None):
        """Fade out animation before closing"""
        self.fade_animation = QPropertyAnimation(self, b"opacity")
        self.fade_animation.setDuration(500)
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.InCubic)
        
        if callback:
            self.fade_animation.finished.connect(callback)
        
        self.fade_animation.finished.connect(self.close)
        self.fade_animation.start()
    
    def showMessage(self, message, color=None):
        """Override to show loading messages"""
        if color is None:
            color = QColor(52, 211, 153)  # Emerald green
        
        # Redraw with message
        pixmap = self.pixmap()
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw message at bottom
        font = QFont("SF Pro Display", 10) if sys.platform == "darwin" else QFont("Segoe UI", 10)
        painter.setFont(font)
        painter.setPen(color)
        
        # Clear previous message area
        painter.fillRect(50, 305, 500, 25, QColor(20, 30, 48))
        
        # Draw new message
        painter.drawText(50, 305, 500, 25, Qt.AlignmentFlag.AlignCenter, message)
        
        painter.end()
        self.setPixmap(pixmap)
        
        # Process events to show immediately
        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()
