"""
AMI 3.0 - Settings dialog with validation and theme support.
"""

from copy import deepcopy
from typing import Dict

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ami.ui.themes import get_stylesheet


class SettingsDialog(QDialog):
    def __init__(self, config: Dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AMI Settings")
        self.setModal(True)
        self.setMinimumWidth(650)
        self.setMinimumHeight(550)
        theme = config.get("ui", {}).get("theme", "auto")
        self.setStyleSheet(get_stylesheet(theme))
        self._original = deepcopy(config)
        self._config = deepcopy(config)
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(16)
        self.tabs = QTabWidget()
        root.addWidget(self.tabs)
        self._init_monitoring_tab()
        self._init_thresholds_tab()
        self._init_notifications_tab()
        self._init_logging_tab()
        self._init_api_tab()
        self._init_speed_test_tab()
        self._init_ui_tab()
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.btn_cancel = QPushButton("Cancel")
        self.btn_save = QPushButton("Save Settings")
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_save.clicked.connect(self._on_save)
        btn_row.addWidget(self.btn_cancel)
        btn_row.addWidget(self.btn_save)
        root.addLayout(btn_row)

    def _init_monitoring_tab(self) -> None:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.hosts_edit = QPlainTextEdit()
        self.hosts_edit.setPlaceholderText("One host per line (IP or hostname)")
        self.hosts_edit.setFixedHeight(110)
        hosts = self._config["monitoring"].get("ping_hosts", [])
        self.hosts_edit.setPlainText("\n".join(hosts))
        form.addRow("Ping hosts:", self.hosts_edit)
        self.http_url = QLineEdit(self._config["monitoring"].get("http_test_url", ""))
        self.http_url.setPlaceholderText("https://www.google.com/generate_204")
        form.addRow("HTTP test URL:", self.http_url)
        self.poll_interval = QSpinBox()
        self.poll_interval.setRange(1, 3600)
        self.poll_interval.setValue(int(self._config["monitoring"].get("polling_interval", 1)))
        form.addRow("Polling interval (s):", self.poll_interval)
        self.timeout = QSpinBox()
        self.timeout.setRange(1, 60)
        self.timeout.setValue(int(self._config["monitoring"].get("timeout", 5)))
        form.addRow("Timeout (s):", self.timeout)
        self.retry_count = QSpinBox()
        self.retry_count.setRange(0, 10)
        self.retry_count.setValue(int(self._config["monitoring"].get("retry_count", 2)))
        form.addRow("Retry count:", self.retry_count)
        self.enable_http = QCheckBox("Enable HTTP connectivity test")
        self.enable_http.setChecked(bool(self._config["monitoring"].get("enable_http_test", True)))
        form.addRow("", self.enable_http)
        self.internal_test = QCheckBox("Internal test mode (simulate flapping network)")
        self.internal_test.setChecked(bool(self._config["monitoring"].get("internal_test_mode", False)))
        form.addRow("", self.internal_test)
        layout.addLayout(form)
        layout.addStretch()
        self.tabs.addTab(tab, "Monitoring")

    def _init_thresholds_tab(self) -> None:
        tab = QWidget()
        layout = QFormLayout(tab)
        layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.unstable_latency = QSpinBox()
        self.unstable_latency.setRange(50, 10000)
        self.unstable_latency.setSingleStep(10)
        self.unstable_latency.setValue(int(self._config["thresholds"].get("unstable_latency_ms", 500)))
        layout.addRow("Unstable over latency (ms):", self.unstable_latency)
        self.unstable_loss = QSpinBox()
        self.unstable_loss.setRange(0, 100)
        self.unstable_loss.setValue(int(self._config["thresholds"].get("unstable_loss_percent", 30)))
        layout.addRow("Unstable over loss (%):", self.unstable_loss)
        self.tabs.addTab(tab, "Thresholds")

    def _init_notifications_tab(self) -> None:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        n = self._config.get("notifications", {})
        self.notif_enabled = QCheckBox("Enable notifications")
        self.notif_enabled.setChecked(bool(n.get("enabled", True)))
        layout.addWidget(self.notif_enabled)
        self.notif_silent = QCheckBox("Silent mode")
        self.notif_silent.setChecked(bool(n.get("silent_mode", False)))
        layout.addWidget(self.notif_silent)
        self.notif_disc = QCheckBox("Notify on disconnect")
        self.notif_disc.setChecked(bool(n.get("notify_on_disconnect", True)))
        layout.addWidget(self.notif_disc)
        self.notif_reconn = QCheckBox("Notify on reconnect")
        self.notif_reconn.setChecked(bool(n.get("notify_on_reconnect", True)))
        layout.addWidget(self.notif_reconn)
        self.notif_unstable = QCheckBox("Notify on unstable connection")
        self.notif_unstable.setChecked(bool(n.get("notify_on_unstable", False)))
        layout.addWidget(self.notif_unstable)
        layout.addStretch()
        self.tabs.addTab(tab, "Notifications")

    def _init_logging_tab(self) -> None:
        tab = QWidget()
        layout = QFormLayout(tab)
        layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        log_cfg = self._config.get("logging", {})
        self.log_enabled = QCheckBox("Enable logging")
        self.log_enabled.setChecked(bool(log_cfg.get("enabled", True)))
        layout.addRow("", self.log_enabled)
        self.log_file_edit = QLineEdit(log_cfg.get("log_file", "ami_log.csv"))
        layout.addRow("Log file:", self.log_file_edit)
        self.log_max_mb = QDoubleSpinBox()
        self.log_max_mb.setRange(0.1, 1000.0)
        self.log_max_mb.setDecimals(1)
        self.log_max_mb.setValue(float(log_cfg.get("max_log_size_mb", 1)))
        layout.addRow("Max log size (MB):", self.log_max_mb)
        self.tabs.addTab(tab, "Logging")

    def _init_api_tab(self) -> None:
        tab = QWidget()
        layout = QFormLayout(tab)
        layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        api_cfg = self._config.get("api", {})
        self.api_enabled = QCheckBox("Enable API server")
        self.api_enabled.setChecked(bool(api_cfg.get("enabled", False)))
        layout.addRow("", self.api_enabled)
        self.api_port = QSpinBox()
        self.api_port.setRange(1024, 65535)
        self.api_port.setValue(int(api_cfg.get("port", 7212)))
        layout.addRow("Port:", self.api_port)
        self.api_token = QLineEdit(api_cfg.get("auth_token", ""))
        self.api_token.setPlaceholderText("Optional Bearer token (leave empty for no auth)")
        self.api_token.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addRow("Auth token:", self.api_token)
        self.tabs.addTab(tab, "API")

    def _init_speed_test_tab(self) -> None:
        tab = QWidget()
        layout = QFormLayout(tab)
        layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        st = self._config.get("speed_test", {})
        self.speed_test_enabled = QCheckBox("Enable speed test (download throughput)")
        self.speed_test_enabled.setChecked(bool(st.get("enabled", True)))
        layout.addRow("", self.speed_test_enabled)
        self.speed_test_interval = QSpinBox()
        self.speed_test_interval.setRange(5, 1440)
        self.speed_test_interval.setValue(int(st.get("interval_minutes", 30)))
        self.speed_test_interval.setSuffix(" min")
        layout.addRow("Interval:", self.speed_test_interval)
        self.speed_test_timeout = QSpinBox()
        self.speed_test_timeout.setRange(5, 120)
        self.speed_test_timeout.setValue(int(st.get("timeout_seconds", 30)))
        self.speed_test_timeout.setSuffix(" s")
        layout.addRow("Timeout:", self.speed_test_timeout)
        self.speed_test_url = QLineEdit(st.get("test_url", "https://speed.cloudflare.com/__down?bytes=52428800"))
        self.speed_test_url.setPlaceholderText("e.g. https://speed.cloudflare.com/__down?bytes=52428800")
        layout.addRow("Test URL:", self.speed_test_url)
        self.speed_test_size_mb = QDoubleSpinBox()
        self.speed_test_size_mb.setRange(1, 50)
        self.speed_test_size_mb.setDecimals(1)
        self.speed_test_size_mb.setValue(float(st.get("download_size_mb", 10)))
        self.speed_test_size_mb.setSuffix(" MB")
        layout.addRow("Download size:", self.speed_test_size_mb)
        self.speed_test_tier_low = QSpinBox()
        self.speed_test_tier_low.setRange(1, 10000)
        self.speed_test_tier_low.setValue(int(st.get("tier_low_mbps", 100)))
        self.speed_test_tier_low.setSuffix(" Mbps")
        layout.addRow("Tier low (Slow < this):", self.speed_test_tier_low)
        self.speed_test_tier_high = QSpinBox()
        self.speed_test_tier_high.setRange(1, 100000)
        self.speed_test_tier_high.setValue(int(st.get("tier_high_mbps", 1000)))
        self.speed_test_tier_high.setSuffix(" Mbps")
        layout.addRow("Tier high (Fast ≥ this):", self.speed_test_tier_high)
        self.tabs.addTab(tab, "Speed test")

    def _init_ui_tab(self) -> None:
        tab = QWidget()
        form = QFormLayout(tab)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        ui_cfg = self._config.get("ui", {})
        self.theme = QComboBox()
        self.theme.addItems(["auto", "light", "dark"])
        self.theme.setCurrentText(ui_cfg.get("theme", "auto"))
        form.addRow("Theme:", self.theme)
        self.show_dash = QCheckBox("Show dashboard on start")
        self.show_dash.setChecked(bool(ui_cfg.get("show_dashboard_on_start", False)))
        form.addRow("", self.show_dash)
        self.compact_status = QCheckBox("Compact status window (Dock fallback)")
        self.compact_status.setChecked(bool(ui_cfg.get("compact_status_window", True)))
        form.addRow("", self.compact_status)
        self.tabs.addTab(tab, "UI")

    def _on_save(self) -> None:
        self._build_config()
        hosts = [h.strip() for h in self.hosts_edit.toPlainText().splitlines() if h.strip()]
        if not hosts:
            QMessageBox.warning(self, "Validation", "Please specify at least one ping host.")
            return
        if self.speed_test_enabled.isChecked():
            if not self.speed_test_url.text().strip():
                QMessageBox.warning(self, "Validation", "Speed test enabled: please set a test URL.")
                return
            if self.speed_test_tier_low.value() >= self.speed_test_tier_high.value():
                QMessageBox.warning(self, "Validation", "Tier low (Mbps) must be less than tier high.")
                return
        self.accept()

    def _build_config(self) -> None:
        cfg = deepcopy(self._original)
        cfg["monitoring"]["ping_hosts"] = [h.strip() for h in self.hosts_edit.toPlainText().splitlines() if h.strip()]
        cfg["monitoring"]["http_test_url"] = self.http_url.text().strip()
        cfg["monitoring"]["polling_interval"] = int(self.poll_interval.value())
        cfg["monitoring"]["timeout"] = int(self.timeout.value())
        cfg["monitoring"]["retry_count"] = int(self.retry_count.value())
        cfg["monitoring"]["enable_http_test"] = bool(self.enable_http.isChecked())
        cfg["monitoring"]["internal_test_mode"] = bool(self.internal_test.isChecked())
        cfg["thresholds"]["unstable_latency_ms"] = int(self.unstable_latency.value())
        cfg["thresholds"]["unstable_loss_percent"] = int(self.unstable_loss.value())
        cfg.setdefault("notifications", {})
        cfg["notifications"]["enabled"] = bool(self.notif_enabled.isChecked())
        cfg["notifications"]["silent_mode"] = bool(self.notif_silent.isChecked())
        cfg["notifications"]["notify_on_disconnect"] = bool(self.notif_disc.isChecked())
        cfg["notifications"]["notify_on_reconnect"] = bool(self.notif_reconn.isChecked())
        cfg["notifications"]["notify_on_unstable"] = bool(self.notif_unstable.isChecked())
        cfg.setdefault("logging", {})
        cfg["logging"]["enabled"] = bool(self.log_enabled.isChecked())
        cfg["logging"]["log_file"] = self.log_file_edit.text().strip() or "ami_log.csv"
        cfg["logging"]["max_log_size_mb"] = float(self.log_max_mb.value())
        cfg.setdefault("api", {})
        cfg["api"]["enabled"] = bool(self.api_enabled.isChecked())
        cfg["api"]["port"] = int(self.api_port.value())
        cfg["api"]["auth_token"] = self.api_token.text().strip()
        cfg.setdefault("speed_test", {})
        cfg["speed_test"]["enabled"] = bool(self.speed_test_enabled.isChecked())
        cfg["speed_test"]["interval_minutes"] = int(self.speed_test_interval.value())
        cfg["speed_test"]["timeout_seconds"] = int(self.speed_test_timeout.value())
        cfg["speed_test"]["test_url"] = self.speed_test_url.text().strip()
        cfg["speed_test"]["download_size_mb"] = float(self.speed_test_size_mb.value())
        cfg["speed_test"]["tier_low_mbps"] = int(self.speed_test_tier_low.value())
        cfg["speed_test"]["tier_high_mbps"] = int(self.speed_test_tier_high.value())
        cfg.setdefault("ui", {})
        cfg["ui"]["theme"] = self.theme.currentText()
        cfg["ui"]["show_dashboard_on_start"] = bool(self.show_dash.isChecked())
        cfg["ui"]["compact_status_window"] = bool(self.compact_status.isChecked())
        self._config = cfg

    def get_config(self) -> Dict:
        self._build_config()
        return deepcopy(self._config)
