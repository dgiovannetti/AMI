"""
AMI 3.0 - Splash screen (dark theme).
"""

import sys

from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, QTimer, Qt, pyqtProperty
from PyQt6.QtGui import QColor, QFont, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import QApplication, QSplashScreen


class UltraModernSplashScreen(QSplashScreen):
    def __init__(self, version: str = "3.1.4"):
        self._version = version
        pixmap = QPixmap(480, 300)
        pixmap.fill(Qt.GlobalColor.transparent)
        super().__init__(pixmap)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._opacity = 0.0
        self.draw_splash()
        self.animation = QPropertyAnimation(self, b"opacity")
        self.animation.setDuration(500)
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.animation.start()

    def draw_splash(self) -> None:
        pixmap = self.pixmap()
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        painter.fillRect(0, 0, 480, 300, QColor(15, 23, 42))
        painter.setPen(QPen(QColor(31, 41, 55), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(0, 0, 480, 300, 8, 8)
        font = QFont("SF Pro Display", 36, QFont.Weight.Bold) if sys.platform == "darwin" else QFont("Segoe UI", 36, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(QColor(226, 232, 240))
        painter.drawText(0, 80, 480, 50, Qt.AlignmentFlag.AlignCenter, "AMI")
        font = QFont("SF Pro Display", 12) if sys.platform == "darwin" else QFont("Segoe UI", 12)
        painter.setFont(font)
        painter.setPen(QColor(148, 163, 184))
        painter.drawText(0, 130, 480, 20, Qt.AlignmentFlag.AlignCenter, "Active Monitor of Internet")
        painter.fillRect(120, 170, 240, 1, QColor(51, 65, 85))
        font = QFont("SF Pro Display", 10) if sys.platform == "darwin" else QFont("Segoe UI", 10)
        painter.setFont(font)
        painter.setPen(QColor(148, 163, 184))
        painter.drawText(40, 190, 400, 20, Qt.AlignmentFlag.AlignLeft, "CiaoIM™ di Daniel Giovannetti")
        painter.drawText(40, 210, 400, 20, Qt.AlignmentFlag.AlignLeft, f"v{self._version}")
        painter.setPen(QColor(203, 213, 225))
        painter.drawText(280, 190, 160, 20, Qt.AlignmentFlag.AlignRight, "ciaoim.tech")
        painter.end()
        self.setPixmap(pixmap)

    def get_opacity(self) -> float:
        return self._opacity

    def set_opacity(self, value: float) -> None:
        self._opacity = value
        self.setWindowOpacity(value)

    opacity = pyqtProperty(float, get_opacity, set_opacity)

    def fade_out(self, callback=None) -> None:
        self.fade_animation = QPropertyAnimation(self, b"opacity")
        self.fade_animation.setDuration(300)
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.InCubic)
        if callback:
            self.fade_animation.finished.connect(callback)

        def _do_close() -> None:
            QTimer.singleShot(0, self.close)

        self.fade_animation.finished.connect(_do_close)
        self.fade_animation.start()

    def showMessage(self, message: str, color: QColor | None = None) -> None:
        if color is None:
            color = QColor(148, 163, 184)
        pixmap = self.pixmap()
        painter = QPainter(pixmap)
        painter.fillRect(0, 280, 480, 20, QColor(15, 23, 42))
        font = QFont("SF Pro Display", 9) if sys.platform == "darwin" else QFont("Segoe UI", 9)
        painter.setFont(font)
        painter.setPen(color)
        painter.drawText(0, 280, 480, 20, Qt.AlignmentFlag.AlignCenter, message)
        painter.end()
        self.setPixmap(pixmap)
        QApplication.processEvents()
