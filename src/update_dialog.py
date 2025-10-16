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
        """Initialize UI - Tesla/SpaceX aesthetic"""
        self.setWindowTitle("AMI Update")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        self.setStyleSheet("""
            QDialog {
                background-color: #000000;
            }
            QLabel {
                color: #ffffff;
            }
            QTextEdit {
                background-color: #0a0a0a;
                border: 1px solid #222222;
                border-radius: 4px;
                color: #cccccc;
                padding: 12px;
                font-size: 12px;
            }
            QProgressBar {
                background-color: #0a0a0a;
                border: 1px solid #222222;
                border-radius: 4px;
                height: 8px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #E82127;
                border-radius: 3px;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(24)
        layout.setContentsMargins(32, 32, 32, 32)
        
        # Title - bold, uppercase, Tesla style
        title = QLabel(f"UPDATE AVAILABLE")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 2)
        title.setFont(title_font)
        title.setStyleSheet("color: #ffffff; margin-bottom: 8px;")
        layout.addWidget(title)
        
        # Version number - large, prominent
        version_label = QLabel(f"Version {self.update_info['version']}")
        version_font = QFont()
        version_font.setPointSize(32)
        version_font.setBold(True)
        version_label.setFont(version_font)
        version_label.setStyleSheet("color: #E82127; margin-bottom: 16px;")
        layout.addWidget(version_label)
        
        # Current version info - minimal, clean
        current_version = self.updater.current_version
        info_text = f"Current: {current_version}"
        if 'size' in self.update_info:
            info_text += f"  •  Size: {format_size(self.update_info['size'])}"
        
        info_label = QLabel(info_text)
        info_font = QFont()
        info_font.setPointSize(10)
        info_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 0.5)
        info_label.setFont(info_font)
        info_label.setStyleSheet("color: #666666; margin-bottom: 16px;")
        layout.addWidget(info_label)
        
        # Release notes header
        notes_label = QLabel("RELEASE NOTES")
        notes_font = QFont()
        notes_font.setPointSize(10)
        notes_font.setBold(True)
        notes_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.5)
        notes_label.setFont(notes_font)
        notes_label.setStyleSheet("color: #666666; margin-top: 8px; margin-bottom: 8px;")
        layout.addWidget(notes_label)
        
        notes_text = QTextEdit()
        notes_text.setReadOnly(True)
        notes_text.setPlainText(self.update_info['release_notes'])
        notes_text.setMinimumHeight(180)
        layout.addWidget(notes_text)
        
        # Postpone warning - Tesla red for critical
        postpone_count = self.updater.get_postpone_count()
        can_postpone = self.updater.can_postpone()
        
        if postpone_count > 0:
            remaining = self.updater.max_postponements - postpone_count
            if remaining > 0:
                warning = QLabel(f"POSTPONED {postpone_count}× • {remaining} REMAINING")
                warning.setStyleSheet("""
                    background-color: #1a1a00; 
                    color: #ffcc00; 
                    padding: 16px; 
                    border-radius: 4px; 
                    border-left: 4px solid #ffcc00;
                    margin: 16px 0;
                    font-weight: 600;
                    letter-spacing: 1px;
                """)
            else:
                warning = QLabel("⚠ MANDATORY UPDATE • CANNOT POSTPONE")
                warning.setStyleSheet("""
                    background-color: #1a0000; 
                    color: #E82127; 
                    padding: 16px; 
                    border-radius: 4px; 
                    border-left: 4px solid #E82127;
                    margin: 16px 0; 
                    font-weight: 700;
                    letter-spacing: 1px;
                """)
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
        
        # Tesla-style buttons
        button_base = """
            QPushButton {
                padding: 16px 32px;
                font-size: 13px;
                font-weight: 700;
                border-radius: 4px;
                letter-spacing: 1.5px;
            }
        """
        
        self.postpone_btn.setStyleSheet(button_base + """
            QPushButton {
                background-color: #0a0a0a;
                color: #666666;
                border: 1px solid #222222;
            }
            QPushButton:hover {
                background-color: #1a1a1a;
                color: #999999;
                border-color: #333333;
            }
            QPushButton:disabled {
                background-color: #000000;
                color: #333333;
                border-color: #111111;
            }
        """)
        
        self.install_btn.setStyleSheet(button_base + """
            QPushButton {
                background-color: #E82127;
                color: #ffffff;
                border: none;
            }
            QPushButton:hover {
                background-color: #ff3339;
            }
            QPushButton:pressed {
                background-color: #cc1a1f;
            }
        """)
        
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
