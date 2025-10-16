"""
AMI Settings Dialog

Provides a compact multi-tab dialog to edit configuration safely and apply at runtime.
"""

from __future__ import annotations

from typing import Dict, List
from copy import deepcopy

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QSpinBox, QCheckBox, QPushButton, QLabel,
    QTabWidget, QPlainTextEdit, QComboBox, QWidget, QDoubleSpinBox
)
from PyQt6.QtCore import Qt


class SettingsDialog(QDialog):
    def __init__(self, config: Dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AMI Settings")
        self.setModal(True)
        self.setMinimumWidth(700)
        self.setMinimumHeight(600)
        self.setStyleSheet("""
            QDialog {
                background-color: #000000;
            }
            QLabel {
                color: #ffffff;
            }
            QTabWidget::pane {
                border: 1px solid #222222;
                border-radius: 4px;
                background-color: #000000;
            }
            QTabBar::tab {
                background-color: #0a0a0a;
                color: #666666;
                padding: 12px 24px;
                border: 1px solid #222222;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                font-weight: 600;
                letter-spacing: 1px;
            }
            QTabBar::tab:selected {
                background-color: #000000;
                color: #ffffff;
                border-bottom: 2px solid #E82127;
            }
            QTabBar::tab:hover {
                background-color: #1a1a1a;
                color: #cccccc;
            }
            QLineEdit, QSpinBox, QDoubleSpinBox, QPlainTextEdit, QComboBox {
                background-color: #0a0a0a;
                border: 1px solid #222222;
                border-radius: 4px;
                color: #ffffff;
                padding: 8px 12px;
                font-size: 12px;
            }
            QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QPlainTextEdit:focus, QComboBox:focus {
                border-color: #E82127;
            }
            QCheckBox {
                color: #ffffff;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 1px solid #222222;
                border-radius: 3px;
                background-color: #0a0a0a;
            }
            QCheckBox::indicator:checked {
                background-color: #E82127;
                border-color: #E82127;
            }
            QPushButton {
                background-color: #0a0a0a;
                color: #ffffff;
                border: 1px solid #222222;
                border-radius: 4px;
                padding: 12px 24px;
                font-size: 13px;
                font-weight: 600;
                letter-spacing: 1px;
            }
            QPushButton:hover {
                background-color: #1a1a1a;
                border-color: #333333;
            }
            QPushButton:pressed {
                background-color: #000000;
            }
        """)
        self._original = deepcopy(config)  # keep original
        self._config = deepcopy(config)    # will be mutated

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(20)

        self.tabs = QTabWidget()
        root.addWidget(self.tabs)

        # Tabs
        self._init_monitoring_tab()
        self._init_thresholds_tab()
        self._init_notifications_tab()
        self._init_logging_tab()
        self._init_ui_tab()

        # Buttons - Tesla style
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.btn_cancel = QPushButton("CANCEL")
        self.btn_save = QPushButton("SAVE SETTINGS")
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_save.clicked.connect(self._on_save)
        
        # Style save button with Tesla red
        self.btn_save.setStyleSheet("""
            QPushButton {
                background-color: #E82127;
                color: #ffffff;
                border: none;
                padding: 14px 32px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #ff3339;
            }
            QPushButton:pressed {
                background-color: #cc1a1f;
            }
        """)
        
        btn_row.addWidget(self.btn_cancel)
        btn_row.addWidget(self.btn_save)
        root.addLayout(btn_row)

    # --- Tabs ---
    def _init_monitoring_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(8)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setFormAlignment(Qt.AlignmentFlag.AlignLeft)

        # Ping hosts (one per line)
        self.hosts_edit = QPlainTextEdit()
        self.hosts_edit.setPlaceholderText("One host per line (IP or hostname)")
        self.hosts_edit.setFixedHeight(110)
        hosts = self._config['monitoring'].get('ping_hosts', [])
        self.hosts_edit.setPlainText("\n".join(hosts))
        form.addRow("Ping hosts:", self.hosts_edit)

        # HTTP URL
        self.http_url = QLineEdit(self._config['monitoring'].get('http_test_url', ''))
        self.http_url.setPlaceholderText("https://www.google.com/generate_204")
        form.addRow("HTTP test URL:", self.http_url)

        # Polling interval (s)
        self.poll_interval = QSpinBox()
        self.poll_interval.setRange(1, 3600)
        self.poll_interval.setValue(int(self._config['monitoring'].get('polling_interval', 10)))
        form.addRow("Polling interval (s):", self.poll_interval)

        # Timeout (s)
        self.timeout = QSpinBox()
        self.timeout.setRange(1, 60)
        self.timeout.setValue(int(self._config['monitoring'].get('timeout', 5)))
        form.addRow("Timeout (s):", self.timeout)

        # Retry count
        self.retry_count = QSpinBox()
        self.retry_count.setRange(0, 10)
        self.retry_count.setValue(int(self._config['monitoring'].get('retry_count', 2)))
        form.addRow("Retry count:", self.retry_count)

        # Enable HTTP test
        self.enable_http = QCheckBox("Enable HTTP connectivity test")
        self.enable_http.setChecked(bool(self._config['monitoring'].get('enable_http_test', True)))
        form.addRow("", self.enable_http)

        layout.addLayout(form)
        layout.addStretch()
        self.tabs.addTab(tab, "Monitoring")

    def _init_thresholds_tab(self):
        tab = QWidget()
        layout = QFormLayout(tab)
        layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.unstable_latency = QSpinBox()
        self.unstable_latency.setRange(50, 10000)
        self.unstable_latency.setSingleStep(10)
        self.unstable_latency.setValue(int(self._config['thresholds'].get('unstable_latency_ms', 500)))
        layout.addRow("Unstable over latency (ms):", self.unstable_latency)

        self.unstable_loss = QSpinBox()
        self.unstable_loss.setRange(0, 100)
        self.unstable_loss.setValue(int(self._config['thresholds'].get('unstable_loss_percent', 30)))
        layout.addRow("Unstable over loss (%):", self.unstable_loss)

        self.tabs.addTab(tab, "Thresholds")

    def _init_notifications_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(4)

        notif_cfg = self._config.get('notifications', {})
        self.notif_enabled = QCheckBox("Enable notifications")
        self.notif_enabled.setChecked(bool(notif_cfg.get('enabled', True)))
        layout.addWidget(self.notif_enabled)

        self.notif_silent = QCheckBox("Silent mode")
        self.notif_silent.setChecked(bool(notif_cfg.get('silent_mode', False)))
        layout.addWidget(self.notif_silent)

        self.notif_disc = QCheckBox("Notify on disconnect")
        self.notif_disc.setChecked(bool(notif_cfg.get('notify_on_disconnect', True)))
        layout.addWidget(self.notif_disc)

        self.notif_reconn = QCheckBox("Notify on reconnect")
        self.notif_reconn.setChecked(bool(notif_cfg.get('notify_on_reconnect', True)))
        layout.addWidget(self.notif_reconn)

        self.notif_unstable = QCheckBox("Notify on unstable connection")
        self.notif_unstable.setChecked(bool(notif_cfg.get('notify_on_unstable', False)))
        layout.addWidget(self.notif_unstable)

        layout.addStretch()
        self.tabs.addTab(tab, "Notifications")

    def _init_logging_tab(self):
        tab = QWidget()
        layout = QFormLayout(tab)
        layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        log_cfg = self._config.get('logging', {})

        self.log_enabled = QCheckBox("Enable logging")
        self.log_enabled.setChecked(bool(log_cfg.get('enabled', True)))
        layout.addRow("", self.log_enabled)

        self.log_file_edit = QLineEdit(log_cfg.get('log_file', 'ami_log.csv'))
        layout.addRow("Log file:", self.log_file_edit)

        self.log_max_mb = QDoubleSpinBox()
        self.log_max_mb.setRange(0.1, 1000.0)
        self.log_max_mb.setDecimals(1)
        self.log_max_mb.setSingleStep(0.1)
        self.log_max_mb.setValue(float(log_cfg.get('max_log_size_mb', 1)))
        layout.addRow("Max log size (MB):", self.log_max_mb)

        self.tabs.addTab(tab, "Logging")

    def _init_ui_tab(self):
        tab = QWidget()
        form = QFormLayout(tab)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        ui_cfg = self._config.get('ui', {})

        self.theme = QComboBox()
        self.theme.addItems(["auto", "light", "dark"])
        self.theme.setCurrentText(ui_cfg.get('theme', 'auto'))
        form.addRow("Theme:", self.theme)

        self.show_dash = QCheckBox("Show dashboard on start")
        self.show_dash.setChecked(bool(ui_cfg.get('show_dashboard_on_start', True)))
        form.addRow("", self.show_dash)

        self.tabs.addTab(tab, "UI")

    # --- Save / Build config ---
    def _on_save(self):
        self._build_config()
        # basic validation
        hosts = [h.strip() for h in self.hosts_edit.toPlainText().splitlines() if h.strip()]
        if not hosts:
            # Require at least one host
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Validation", "Please specify at least one ping host.")
            return
        self.accept()

    def _build_config(self):
        cfg = deepcopy(self._original)

        # Monitoring
        hosts = [h.strip() for h in self.hosts_edit.toPlainText().splitlines() if h.strip()]
        cfg['monitoring']['ping_hosts'] = hosts
        cfg['monitoring']['http_test_url'] = self.http_url.text().strip()
        cfg['monitoring']['polling_interval'] = int(self.poll_interval.value())
        cfg['monitoring']['timeout'] = int(self.timeout.value())
        cfg['monitoring']['retry_count'] = int(self.retry_count.value())
        cfg['monitoring']['enable_http_test'] = bool(self.enable_http.isChecked())

        # Thresholds
        cfg['thresholds']['unstable_latency_ms'] = int(self.unstable_latency.value())
        cfg['thresholds']['unstable_loss_percent'] = int(self.unstable_loss.value())

        # Notifications
        cfg.setdefault('notifications', {})
        cfg['notifications']['enabled'] = bool(self.notif_enabled.isChecked())
        cfg['notifications']['silent_mode'] = bool(self.notif_silent.isChecked())
        cfg['notifications']['notify_on_disconnect'] = bool(self.notif_disc.isChecked())
        cfg['notifications']['notify_on_reconnect'] = bool(self.notif_reconn.isChecked())
        cfg['notifications']['notify_on_unstable'] = bool(self.notif_unstable.isChecked())

        # Logging
        cfg.setdefault('logging', {})
        cfg['logging']['enabled'] = bool(self.log_enabled.isChecked())
        cfg['logging']['log_file'] = self.log_file_edit.text().strip() or 'ami_log.csv'
        cfg['logging']['max_log_size_mb'] = float(self.log_max_mb.value())

        # UI
        cfg.setdefault('ui', {})
        cfg['ui']['theme'] = self.theme.currentText()
        cfg['ui']['show_dashboard_on_start'] = bool(self.show_dash.isChecked())

        self._config = cfg

    def get_config(self) -> Dict:
        return deepcopy(self._config)
