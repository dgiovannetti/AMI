"""
Update Dialog UI
Shows update notification with release notes and install/postpone options
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTextEdit, QProgressBar, QMessageBox, QApplication)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont
from updater import UpdateManager, format_size
import os


class UpdateDownloadThread(QThread):
    """Thread for downloading update in background"""
    
    progress = pyqtSignal(int)  # Download progress percentage
    finished = pyqtSignal(bool)  # Success status
    error = pyqtSignal(str)  # Error message
    
    def __init__(self, updater: UpdateManager, update_info: dict):
        super().__init__()
        self.updater = updater
        self.update_info = update_info
    
    def run(self):
        """Download and install update"""
        try:
            # Download
            package_path = self.updater.download_update(
                self.update_info['download_url'],
                self.update_info.get('checksum')
            )
            
            if not package_path:
                self.error.emit("Failed to download update")
                self.finished.emit(False)
                return
            
            self.progress.emit(100)
            
            # Install
            success = self.updater.install_update(package_path)
            self.finished.emit(success)
            
        except Exception as e:
            self.error.emit(str(e))
            self.finished.emit(False)


class UpdateDialog(QDialog):
    """Dialog to show available update and manage installation"""
    
    def __init__(self, updater: UpdateManager, update_info: dict, parent=None):
        super().__init__(parent)
        self.updater = updater
        self.update_info = update_info
        self.download_thread = None
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI - Brutalist Tech aesthetic"""
        self.setWindowTitle("AMI Update")
        self.setMinimumWidth(650)
        self.setMinimumHeight(550)
        self.setStyleSheet("""
            QDialog {
                background-color: #F5F5F7;
            }
            QLabel {
                color: #000000;
            }
            QTextEdit {
                background-color: #FFFFFF;
                border: 2px solid #000000;
                border-radius: 0px;
                color: #000000;
                padding: 16px;
                font-size: 13px;
            }
            QProgressBar {
                background-color: #E8E8ED;
                border: 2px solid #000000;
                border-radius: 0px;
                height: 12px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #0071E3;
                border-radius: 0px;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(32)
        layout.setContentsMargins(48, 48, 48, 48)
        
        # Title - Brutalist uppercase
        title = QLabel("UPDATE AVAILABLE")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 2)
        title.setFont(title_font)
        title.setStyleSheet("color: #86868B; margin-bottom: 16px;")
        layout.addWidget(title)
        
        # Version number - ultra-light, huge
        version_label = QLabel(f"{self.update_info['version']}")
        version_font = QFont()
        version_font.setPointSize(72)
        version_font.setWeight(QFont.Weight.Thin)
        version_label.setFont(version_font)
        version_label.setStyleSheet("color: #0071E3; margin-bottom: 24px;")
        layout.addWidget(version_label)
        
        # Current version info - clean
        current_version = self.updater.current_version
        info_text = f"CURRENT VERSION: {current_version}"
        if 'size' in self.update_info:
            info_text += f"  •  DOWNLOAD SIZE: {format_size(self.update_info['size'])}"
        
        info_label = QLabel(info_text)
        info_font = QFont()
        info_font.setPointSize(11)
        info_font.setBold(True)
        info_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.5)
        info_label.setFont(info_font)
        info_label.setStyleSheet("color: #86868B; margin-bottom: 24px;")
        layout.addWidget(info_label)
        
        # Release notes header
        notes_label = QLabel("RELEASE NOTES")
        notes_font = QFont()
        notes_font.setPointSize(12)
        notes_font.setBold(True)
        notes_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 2)
        notes_label.setFont(notes_font)
        notes_label.setStyleSheet("color: #000000; margin-top: 8px; margin-bottom: 12px;")
        layout.addWidget(notes_label)
        
        notes_text = QTextEdit()
        notes_text.setReadOnly(True)
        notes_text.setPlainText(self.update_info['release_notes'])
        notes_text.setMinimumHeight(200)
        # Hard shadow
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        from PyQt6.QtGui import QColor
        notes_shadow = QGraphicsDropShadowEffect()
        notes_shadow.setColor(QColor(0, 0, 0, 255))
        notes_shadow.setBlurRadius(0)
        notes_shadow.setOffset(6, 6)
        notes_text.setGraphicsEffect(notes_shadow)
        layout.addWidget(notes_text)
        
        # Postpone warning - Brutalist style
        postpone_count = self.updater.get_postpone_count()
        can_postpone = self.updater.can_postpone()
        
        if postpone_count > 0:
            remaining = self.updater.max_postponements - postpone_count
            if remaining > 0:
                warning = QLabel(f"POSTPONED {postpone_count}× • {remaining} REMAINING")
                warning.setStyleSheet("""
                    background-color: #FFFFFF; 
                    color: #FF9500; 
                    padding: 20px; 
                    border: 3px solid #000000;
                    border-left: 6px solid #FF9500;
                    margin: 16px 0;
                    font-weight: 700;
                    letter-spacing: 2px;
                """)
            else:
                warning = QLabel("⚠ MANDATORY UPDATE • CANNOT POSTPONE")
                warning.setStyleSheet("""
                    background-color: #FFFFFF; 
                    color: #FF3B30; 
                    padding: 20px; 
                    border: 3px solid #000000;
                    border-left: 6px solid #FF3B30;
                    margin: 16px 0; 
                    font-weight: 700;
                    letter-spacing: 2px;
                """)
            # Hard shadow on warning
            from PyQt6.QtWidgets import QGraphicsDropShadowEffect
            from PyQt6.QtGui import QColor
            warn_shadow = QGraphicsDropShadowEffect()
            warn_shadow.setColor(QColor(0, 0, 0, 255))
            warn_shadow.setBlurRadius(0)
            warn_shadow.setOffset(6, 6)
            warning.setGraphicsEffect(warn_shadow)
            layout.addWidget(warning)
        
        # Progress bar (hidden initially)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.postpone_btn = QPushButton("LATER")
        self.postpone_btn.clicked.connect(self.postpone_update)
        self.postpone_btn.setEnabled(can_postpone)
        if not can_postpone:
            self.postpone_btn.setToolTip("Maximum postponements reached")
            self.postpone_btn.setVisible(False)
        
        self.install_btn = QPushButton("INSTALL UPDATE")
        self.install_btn.clicked.connect(self.install_update)
        self.install_btn.setDefault(True)
        
        # Brutalist buttons with hard shadows
        button_base = """
            QPushButton {
                padding: 16px 40px;
                font-size: 13px;
                font-weight: 700;
                border-radius: 2px;
                letter-spacing: 2px;
            }
        """
        
        self.postpone_btn.setStyleSheet(button_base + """
            QPushButton {
                background-color: #FFFFFF;
                color: #000000;
                border: 3px solid #000000;
            }
            QPushButton:hover {
                background-color: #E8E8ED;
            }
            QPushButton:disabled {
                background-color: #F5F5F7;
                color: #C7C7CC;
                border-color: #C7C7CC;
            }
        """)
        
        self.install_btn.setStyleSheet(button_base + """
            QPushButton {
                background-color: #0071E3;
                color: #FFFFFF;
                border: 3px solid #000000;
            }
            QPushButton:hover {
                background-color: #0077ED;
            }
            QPushButton:pressed {
                background-color: #0051A3;
            }
        """)
        
        # Hard shadows on buttons
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        from PyQt6.QtGui import QColor
        postpone_shadow = QGraphicsDropShadowEffect()
        postpone_shadow.setColor(QColor(0, 0, 0, 255))
        postpone_shadow.setBlurRadius(0)
        postpone_shadow.setOffset(4, 4)
        self.postpone_btn.setGraphicsEffect(postpone_shadow)
        
        install_shadow = QGraphicsDropShadowEffect()
        install_shadow.setColor(QColor(0, 0, 0, 255))
        install_shadow.setBlurRadius(0)
        install_shadow.setOffset(4, 4)
        self.install_btn.setGraphicsEffect(install_shadow)
        
        button_layout.addWidget(self.postpone_btn)
        button_layout.addWidget(self.install_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def postpone_update(self):
        """Handle postpone button click"""
        self.updater.increment_postpone_count()
        
        remaining = self.updater.max_postponements - self.updater.get_postpone_count()
        
        if remaining > 0:
            QMessageBox.information(
                self,
                "Update Postponed",
                f"Update postponed. You can postpone {remaining} more time(s) before it becomes mandatory."
            )
        else:
            QMessageBox.warning(
                self,
                "Last Postponement",
                "This was your last postponement. Next time, the update will be mandatory."
            )
        
        self.accept()
    
    def install_update(self):
        """Handle install button click"""
        reply = QMessageBox.question(
            self,
            "Confirm Update",
            "AMI will download and install the update, then restart.\n\n"
            "Do you want to continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Disable buttons
        self.install_btn.setEnabled(False)
        self.postpone_btn.setEnabled(False)
        
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Start download thread
        self.download_thread = UpdateDownloadThread(self.updater, self.update_info)
        self.download_thread.progress.connect(self.on_progress)
        self.download_thread.finished.connect(self.on_finished)
        self.download_thread.error.connect(self.on_error)
        self.download_thread.start()
    
    def on_progress(self, percentage: int):
        """Update progress bar"""
        self.progress_bar.setValue(percentage)
    
    def on_finished(self, success: bool):
        """Handle download/install completion"""
        if success:
            QMessageBox.information(
                self,
                "Update Complete",
                "Update installed successfully. AMI will now restart."
            )
            # Quit the current app so only the new instance remains
            app = QApplication.instance()
            if app is not None:
                app.quit()
                # Forcefully terminate after a short delay to ensure updater script can proceed
                QTimer.singleShot(200, lambda: os._exit(0))
            else:
                import sys
                sys.exit(0)
        else:
            QMessageBox.critical(
                self,
                "Update Failed",
                "Failed to install update. Please try again later or download manually from GitHub."
            )
            self.install_btn.setEnabled(True)
            self.postpone_btn.setEnabled(self.updater.can_postpone())
            self.progress_bar.setVisible(False)
    
    def on_error(self, error_msg: str):
        """Handle download/install error"""
        QMessageBox.critical(
            self,
            "Update Error",
            f"An error occurred during update:\n\n{error_msg}"
        )
        self.install_btn.setEnabled(True)
        self.postpone_btn.setEnabled(self.updater.can_postpone())
        self.progress_bar.setVisible(False)
    
    def closeEvent(self, event):
        """Handle dialog close - block if mandatory; otherwise treat as postpone"""
        if not self.download_thread:
            if not self.updater.can_postpone():
                QMessageBox.warning(
                    self,
                    "Update Required",
                    "This update is mandatory. Please install to continue."
                )
                event.ignore()
                return
            self.postpone_update()
        event.accept()
