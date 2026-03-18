"""
AMI 3.0 - Update dialog: release notes, install/postpone.
"""

import os
from typing import TYPE_CHECKING

from PyQt6.QtCore import QTimer, Qt, pyqtSignal, QThread
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from ami.services.updater import UpdateManager, format_size

if TYPE_CHECKING:
    pass


class UpdateDownloadThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(bool)
    error = pyqtSignal(str)

    def __init__(self, updater: UpdateManager, update_info: dict):
        super().__init__()
        self.updater = updater
        self.update_info = update_info

    def run(self) -> None:
        try:
            path = self.updater.download_update(
                self.update_info["download_url"],
                self.update_info.get("checksum"),
            )
            if not path:
                self.error.emit("Failed to download update")
                self.finished.emit(False)
                return
            self.progress.emit(100)
            success = self.updater.install_update(path)
            self.finished.emit(success)
        except Exception as e:
            self.error.emit(str(e))
            self.finished.emit(False)


class UpdateDialog(QDialog):
    def __init__(self, updater: UpdateManager, update_info: dict, parent=None):
        super().__init__(parent)
        self.updater = updater
        self.update_info = update_info
        self.download_thread = None
        self.init_ui()

    def init_ui(self) -> None:
        self.setWindowTitle("Software Update")
        self.setMinimumWidth(550)
        self.setMinimumHeight(500)
        from ami.ui.themes import get_stylesheet
        theme = self.updater.current_version  # no theme in updater; use default
        self.setStyleSheet(get_stylesheet("light"))
        layout = QVBoxLayout()
        layout.setSpacing(24)
        layout.setContentsMargins(32, 32, 32, 32)
        header = QHBoxLayout()
        icon_label = QLabel("🔄")
        icon_label.setFont(QFont("", 32))
        header.addWidget(icon_label)
        title_col = QVBoxLayout()
        title = QLabel("Update Available")
        title.setFont(QFont("", 20, QFont.Weight.Bold))
        title_col.addWidget(title)
        version_label = QLabel(f"Version {self.update_info['version']}")
        version_label.setFont(QFont("", 14, QFont.Weight.Medium))
        version_label.setStyleSheet("color: #3b82f6;")
        title_col.addWidget(version_label)
        header.addLayout(title_col)
        header.addStretch()
        layout.addLayout(header)
        info_frame = QFrame()
        info_frame.setStyleSheet("QFrame { background-color: #f9fafb; border-radius: 8px; padding: 16px; }")
        info_layout = QVBoxLayout(info_frame)
        info_layout.addWidget(QLabel(f"Current version: {self.updater.current_version}"))
        if "size" in self.update_info:
            info_layout.addWidget(QLabel(f"Download size: {format_size(self.update_info['size'])}"))
        layout.addWidget(info_frame)
        layout.addWidget(QLabel("What's New"))
        notes_text = QTextEdit()
        notes_text.setReadOnly(True)
        notes_text.setPlainText(self.update_info.get("release_notes", ""))
        notes_text.setMinimumHeight(150)
        notes_text.setMaximumHeight(200)
        layout.addWidget(notes_text)
        can_postpone = self.updater.can_postpone()
        postpone_count = self.updater.get_postpone_count()
        if postpone_count > 0:
            remaining = self.updater.max_postponements - postpone_count
            if remaining > 0:
                w = QLabel(f"⚠️ Postponed {postpone_count} time(s). {remaining} remaining.")
                w.setStyleSheet("background-color: #fef3c7; color: #92400e; padding: 12px; border-radius: 8px;")
                layout.addWidget(w)
            else:
                w = QLabel("⚠️ This update is mandatory and cannot be postponed.")
                w.setStyleSheet("background-color: #fee2e2; color: #991b1b; padding: 12px; border-radius: 8px;")
                layout.addWidget(w)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.postpone_btn = QPushButton("Remind Me Later")
        self.postpone_btn.clicked.connect(self.postpone_update)
        self.postpone_btn.setEnabled(can_postpone)
        if not can_postpone:
            self.postpone_btn.setVisible(False)
        self.install_btn = QPushButton("Install Update")
        self.install_btn.clicked.connect(self.install_update)
        self.install_btn.setDefault(True)
        button_layout.addWidget(self.postpone_btn)
        button_layout.addWidget(self.install_btn)
        layout.addLayout(button_layout)
        self.setLayout(layout)

    def postpone_update(self) -> None:
        self.updater.increment_postpone_count()
        remaining = self.updater.max_postponements - self.updater.get_postpone_count()
        if remaining > 0:
            QMessageBox.information(
                self, "Update Postponed",
                f"Update postponed. You can postpone {remaining} more time(s) before it becomes mandatory.",
            )
        else:
            QMessageBox.warning(
                self, "Last Postponement",
                "This was your last postponement. Next time, the update will be mandatory.",
            )
        self.accept()

    def install_update(self) -> None:
        reply = QMessageBox.question(
            self, "Confirm Update",
            "AMI will download and install the update, then restart.\n\nDo you want to continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self.install_btn.setEnabled(False)
        self.postpone_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.download_thread = UpdateDownloadThread(self.updater, self.update_info)
        self.download_thread.progress.connect(self.progress_bar.setValue)
        self.download_thread.finished.connect(self.on_finished)
        self.download_thread.error.connect(self.on_error)
        self.download_thread.start()

    def on_finished(self, success: bool) -> None:
        if success:
            QMessageBox.information(self, "Update Complete", "Update installed. AMI will now restart.")
            app = QApplication.instance()
            if app:
                app.quit()
            QTimer.singleShot(200, lambda: os._exit(0))
        else:
            QMessageBox.critical(
                self, "Update Failed",
                "Failed to install update. Please try again or download manually from GitHub.",
            )
            self.install_btn.setEnabled(True)
            self.postpone_btn.setEnabled(self.updater.can_postpone())
            self.progress_bar.setVisible(False)

    def on_error(self, error_msg: str) -> None:
        QMessageBox.critical(self, "Update Error", f"An error occurred:\n\n{error_msg}")
        self.install_btn.setEnabled(True)
        self.postpone_btn.setEnabled(self.updater.can_postpone())
        self.progress_bar.setVisible(False)

    def closeEvent(self, event) -> None:
        if not self.download_thread:
            if not self.updater.can_postpone():
                QMessageBox.warning(self, "Update Required", "This update is mandatory. Please install to continue.")
                event.ignore()
                return
            self.postpone_update()
        event.accept()
