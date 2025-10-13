"""
AMI - Active Monitor of Internet
Animated Button Widget

Custom QPushButton with hover animations and effects
"""

from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, pyqtProperty, QSize
from PyQt6.QtGui import QColor


class AnimatedButton(QPushButton):
    """
    Enhanced QPushButton with smooth animations
    """
    
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        
        # Animation properties
        self._glow_intensity = 0.0
        
        # Setup animations
        self.glow_animation = QPropertyAnimation(self, b"glow_intensity")
        self.glow_animation.setDuration(300)
        self.glow_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Connect hover events
        self.setMouseTracking(True)
    
    def enterEvent(self, event):
        """Mouse enter - start glow animation"""
        self.glow_animation.stop()
        self.glow_animation.setStartValue(self._glow_intensity)
        self.glow_animation.setEndValue(1.0)
        self.glow_animation.start()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Mouse leave - fade glow"""
        self.glow_animation.stop()
        self.glow_animation.setStartValue(self._glow_intensity)
        self.glow_animation.setEndValue(0.0)
        self.glow_animation.start()
        super().leaveEvent(event)
    
    def get_glow_intensity(self):
        return self._glow_intensity
    
    def set_glow_intensity(self, value):
        self._glow_intensity = value
        self.update()
    
    glow_intensity = pyqtProperty(float, get_glow_intensity, set_glow_intensity)


class PulsingButton(QPushButton):
    """
    Button that pulses when active/important
    """
    
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        
        self._pulse_value = 0.0
        self._pulsing = False
        
        # Pulse animation
        self.pulse_animation = QPropertyAnimation(self, b"pulse_value")
        self.pulse_animation.setDuration(1500)
        self.pulse_animation.setStartValue(0.0)
        self.pulse_animation.setEndValue(1.0)
        self.pulse_animation.setEasingCurve(QEasingCurve.Type.InOutSine)
        self.pulse_animation.setLoopCount(-1)  # Infinite loop
    
    def start_pulsing(self):
        """Start the pulsing animation"""
        if not self._pulsing:
            self._pulsing = True
            self.pulse_animation.start()
    
    def stop_pulsing(self):
        """Stop the pulsing animation"""
        if self._pulsing:
            self._pulsing = False
            self.pulse_animation.stop()
            self._pulse_value = 0.0
            self.update()
    
    def get_pulse_value(self):
        return self._pulse_value
    
    def set_pulse_value(self, value):
        self._pulse_value = value
        # Update opacity or glow based on pulse value
        opacity = 0.7 + (value * 0.3)
        self.setWindowOpacity(opacity)
    
    pulse_value = pyqtProperty(float, get_pulse_value, set_pulse_value)
