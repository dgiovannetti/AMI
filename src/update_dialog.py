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
        """Initialize UI - Cyberpunk aesthetic"""
        self.setWindowTitle("[AMI] // UPDATE_AVAILABLE.EXE")
        self.setMinimumWidth(650)
        self.setMinimumHeight(550)
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0D0221, stop:1 #1a0933);
            }
            QLabel {
                color: #00F5FF;
                font-family: 'Courier New';
            }
            QTextEdit {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0D0221, stop:1 #160633);
                border: 2px solid #7209B7;
                border-radius: 0px;
                color: #C77DFF;
                padding: 16px;
                font-family: 'Courier New';
                font-size: 11px;
            }
            QProgressBar {
                background: #0D0221;
                border: 2px solid #00F5FF;
                border-radius: 0px;
                height: 12px;
                text-align: center;
                font-family: 'Courier New';
                color: #00F5FF;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00F5FF, stop:1 #00FF41);
                border-radius: 0px;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(28)
        layout.setContentsMargins(40, 40, 40, 40)
        
        # Cyberpunk header with glitch effect
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: transparent;
                border-bottom: 3px solid #00F5FF;
                padding-bottom: 20px;
                margin-bottom: 20px;
            }
        """)
        header_layout = QVBoxLayout(header_frame)
        header_layout.setSpacing(8)
        
        # Terminal prompt
        prompt = QLabel(">_ SYSTEM.UPDATE")
        prompt_font = QFont("Courier New", 12)
        prompt_font.setBold(True)
        prompt.setFont(prompt_font)
        prompt.setStyleSheet("color: #00FF41;")
        header_layout.addWidget(prompt)
        
        # Version - huge monospace with neon
        version_label = QLabel(f"v{self.update_info['version']}")
        version_font = QFont("Courier New", 48)
        version_font.setBold(True)
        version_label.setFont(version_font)
        version_label.setStyleSheet("""
            color: #00F5FF;
            text-shadow: 0 0 20px #00F5FF, 2px 2px 0px #7209B7;
        """)
        header_layout.addWidget(version_label)
        
        layout.addWidget(header_frame)
        
        # Info grid - cyberpunk style
        info_grid = QFrame()
        info_grid.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0D0221, stop:1 #160633);
                border: 2px solid #7209B7;
                padding: 16px;
            }
        """)
        info_layout = QVBoxLayout(info_grid)
        info_layout.setSpacing(8)
        
        current_version = self.updater.current_version
        
        # Current version
        curr_label = QLabel(f"[CURRENT] {current_version}")
        curr_font = QFont("Courier New", 10)
        curr_font.setBold(True)
        curr_label.setFont(curr_font)
        curr_label.setStyleSheet("color: #FF006E;")
        info_layout.addWidget(curr_label)
        
        # Download size
        if 'size' in self.update_info:
            size_label = QLabel(f"[SIZE] {format_size(self.update_info['size'])}")
            size_font = QFont("Courier New", 10)
            size_label.setFont(size_font)
            size_label.setStyleSheet("color: #C77DFF;")
            info_layout.addWidget(size_label)
        
        layout.addWidget(info_grid)
        
        # Release notes header - terminal style
        notes_label = QLabel("// CHANGELOG.TXT")
        notes_font = QFont("Courier New", 11)
        notes_font.setBold(True)
        notes_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 2)
        notes_label.setFont(notes_font)
        notes_label.setStyleSheet("color: #00F5FF; margin-top: 12px; margin-bottom: 8px;")
        layout.addWidget(notes_label)
        
        notes_text = QTextEdit()
        notes_text.setReadOnly(True)
        notes_text.setPlainText(self.update_info['release_notes'])
        notes_text.setMinimumHeight(180)
        layout.addWidget(notes_text)
        
        # Postpone warning - cyberpunk alert
        postpone_count = self.updater.get_postpone_count()
        can_postpone = self.updater.can_postpone()
        
        if postpone_count > 0:
            remaining = self.updater.max_postponements - postpone_count
            if remaining > 0:
                warning = QLabel(f"[!] POSTPONED: {postpone_count}x | REMAINING: {remaining}")
                warning_font = QFont("Courier New", 11)
                warning_font.setBold(True)
                warning.setFont(warning_font)
                warning.setStyleSheet("""
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #1a0933, stop:1 #0D0221);
                    color: #FFD60A;
                    padding: 18px;
                    border: 2px solid #FFD60A;
                    border-radius: 0px;
                    margin: 16px 0;
                    letter-spacing: 2px;
                """)
            else:
                warning = QLabel("[!!!] CRITICAL: MANDATORY_UPDATE | CANNOT_POSTPONE")
                warning_font = QFont("Courier New", 11)
                warning_font.setBold(True)
                warning.setFont(warning_font)
                warning.setStyleSheet("""
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #1a0000, stop:1 #330000);
                    color: #FF006E;
                    padding: 18px;
                    border: 3px solid #FF006E;
                    border-radius: 0px;
                    margin: 16px 0;
                    letter-spacing: 2px;
                    text-shadow: 0 0 10px #FF006E;
                """)
            layout.addWidget(warning)
        
        # Progress bar (hidden initially)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.postpone_btn = QPushButton("[ESC] POSTPONE")
        self.postpone_btn.clicked.connect(self.postpone_update)
        self.postpone_btn.setEnabled(can_postpone)
        if not can_postpone:
            self.postpone_btn.setToolTip("Maximum postponements reached")
            self.postpone_btn.setVisible(False)
        
        self.install_btn = QPushButton("[ENTER] INSTALL_NOW")
        self.install_btn.clicked.connect(self.install_update)
        self.install_btn.setDefault(True)
        
        # Cyberpunk buttons
        button_base = """
            QPushButton {
                padding: 18px 36px;
                font-family: 'Courier New';
                font-size: 12px;
                font-weight: 700;
                border-radius: 0px;
                letter-spacing: 2px;
            }
        """
        
        self.postpone_btn.setStyleSheet(button_base + """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #160633, stop:1 #0D0221);
                color: #7209B7;
                border: 2px solid #7209B7;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1a0933, stop:1 #160633);
                color: #9D4EDD;
                border-color: #9D4EDD;
            }
            QPushButton:disabled {
                background: #0D0221;
                color: #3a0d5c;
                border-color: #3a0d5c;
            }
        """)
        
        self.install_btn.setStyleSheet(button_base + """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00F5FF, stop:1 #00FF41);
                color: #0D0221;
                border: 3px solid #00F5FF;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00FF41, stop:1 #00F5FF);
                border-color: #00FF41;
                box-shadow: 0 0 30px #00F5FF;
            }
            QPushButton:pressed {
                background: #00F5FF;
                border-color: #00F5FF;
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
