"""
AMI 3.0 - Configuration loading, validation (jsonschema), and migration from 2.x.
"""

import json
import shutil
import sys
from pathlib import Path
from typing import Any, Dict

import jsonschema

from .paths import get_base_path, get_user_config_dir


DEFAULT_CONFIG: Dict[str, Any] = {
    "app": {
        "name": "AMI",
        "subtitle": "Active Monitor of Internet",
        "version": "3.1.4",
        "copyright": "© 2025–2026 CiaoIM™ by Daniel Giovannetti",
        "website": "https://ciaoim.tech/projects/ami",
        "tagline": "Crafted logic. Measured force. Front-end vision, compiled systems, and hardcoded ethics.",
        "inspiration": "Intuizione colta insieme a Giovanni Calvario in aliscafo per il 40° Convegno di Capri dei Giovani Imprenditori",
    },
    "monitoring": {
        "ping_hosts": ["8.8.8.8", "1.1.1.1", "github.com"],
        "http_test_url": "https://www.google.com/generate_204",
        "http_test_urls": [],
        "polling_interval": 1,
        "timeout": 5,
        "retry_count": 2,
        "enable_http_test": True,
        "internal_test_mode": False,
    },
    "thresholds": {"unstable_latency_ms": 500, "unstable_loss_percent": 30},
    "notifications": {
        "enabled": True,
        "silent_mode": False,
        "notify_on_disconnect": True,
        "notify_on_reconnect": True,
        "notify_on_unstable": False,
    },
    "logging": {"enabled": True, "log_file": "ami_log.csv", "max_log_size_mb": 1},
    "api": {"enabled": False, "port": 7212, "auth_token": ""},
    "startup": {"auto_start": False},
    "ui": {
        "theme": "auto",
        "show_dashboard_on_start": False,
        "compact_status_window": False,
    },
    "updates": {
        "enabled": True,
        "check_on_startup": True,
        "check_interval_hours": 24,
        "github_repo": "dgiovannetti/AMI",
        "max_postponements": 3,
        "notify_on_update": True,
    },
    "speed_test": {
        "enabled": True,
        "interval_minutes": 30,
        "test_url": "https://fsn1-speed.hetzner.com/100MB.bin",
        "download_size_mb": 10,
        "warmup_mb": 2,
        "timeout_seconds": 30,
        "tier_low_mbps": 100,
        "tier_high_mbps": 1000,
    },
}

_config_path: Path | None = None
_schema: Dict[str, Any] | None = None


def _get_schema() -> Dict[str, Any]:
    global _schema
    if _schema is not None:
        return _schema
    base = get_base_path()
    schema_path = base / "config.schema.json"
    if schema_path.exists():
        with open(schema_path, "r", encoding="utf-8") as f:
            _schema = json.load(f)
    else:
        _schema = {}
    return _schema


def first_run_migration() -> Path:
    """Migrate config from legacy (2.x) location to user dir. Returns path to use."""
    global _config_path
    user_config = get_user_config_dir() / "config.json"
    legacy_config = get_base_path() / "config.json"

    if user_config.exists():
        _config_path = user_config
        return _config_path

    if legacy_config.exists():
        user_config.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(legacy_config, user_config)
        _config_path = user_config
        return _config_path

    user_config.parent.mkdir(parents=True, exist_ok=True)
    _config_path = user_config
    return _config_path


def _get_config_path() -> Path:
    global _config_path
    if _config_path is not None:
        return _config_path
    if not getattr(sys, "frozen", False):
        _config_path = get_base_path() / "config.json"
        return _config_path
    _config_path = first_run_migration()
    return _config_path


def _migrate_from_2x(config: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure 3.0 keys and version; backfill defaults for new keys."""
    out = dict(config)
    app = out.setdefault("app", {})
    ver = app.get("version", "0.0.0")
    try:
        major = int(ver.split(".")[0])
    except (ValueError, IndexError):
        major = 0
    if major < 3:
        app["version"] = "3.1.4"
    if app.get("website") in ("ciaoim.tech", "www.ciaoim.tech"):
        app["website"] = "https://ciaoim.tech/projects/ami"
    if app.get("copyright") == "© 2025 CiaoIM™ by Daniel Giovannetti":
        app["copyright"] = "© 2025–2026 CiaoIM™ by Daniel Giovannetti"
    mon = out.setdefault("monitoring", {})
    mon.setdefault("http_test_urls", [])
    api = out.setdefault("api", {})
    api.setdefault("auth_token", "")
    ui = out.setdefault("ui", {})
    if ui.get("theme") not in ("auto", "light", "dark"):
        ui["theme"] = "auto"
    st = out.setdefault("speed_test", {
        "enabled": True,
        "interval_minutes": 30,
        "test_url": "https://fsn1-speed.hetzner.com/100MB.bin",
        "download_size_mb": 10,
        "warmup_mb": 2,
        "timeout_seconds": 30,
        "tier_low_mbps": 100,
        "tier_high_mbps": 1000,
    })
    st.setdefault("warmup_mb", 2)
    # Old 50 MB Cloudflare URL may be too small for max warmup (20) + download (50)
    _hetzner_fsn1 = "https://fsn1-speed.hetzner.com/100MB.bin"
    if st.get("test_url") == "https://speed.cloudflare.com/__down?bytes=52428800":
        st["test_url"] = _hetzner_fsn1
    # Deprecated global Hetzner host → region-specific (FSN1 default)
    if "speed.hetzner.de" in str(st.get("test_url", "")):
        st["test_url"] = _hetzner_fsn1
    # Old proof.ovh default → Hetzner FSN1; AMI still tries fallbacks if primary fails
    if "proof.ovh" in str(st.get("test_url", "")):
        st["test_url"] = _hetzner_fsn1
        st["download_size_mb"] = 10
        st["timeout_seconds"] = 30
        st.setdefault("warmup_mb", 2)
    return out


def _validate_config(config: Dict[str, Any]) -> None:
    """Validate config; raise jsonschema.ValidationError or ValueError."""
    hosts = config.get("monitoring", {}).get("ping_hosts", [])
    if not hosts or not isinstance(hosts, list):
        raise ValueError("config.monitoring.ping_hosts must be a non-empty list")
    schema = _get_schema()
    if schema:
        jsonschema.validate(config, schema)


def load_config() -> Dict[str, Any]:
    """Load config from resolved path. Migrate 2.x, validate, return defaults if no file."""
    path = _get_config_path()

    if not path.exists():
        return dict(DEFAULT_CONFIG)

    try:
        with open(path, "r", encoding="utf-8") as f:
            config = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        raise RuntimeError(f"Failed to load config from {path}: {e}") from e

    config = _migrate_from_2x(config)
    _validate_config(config)
    return config


def save_config(config: Dict[str, Any]) -> None:
    """Save config to resolved path."""
    path = _get_config_path()
    config = _migrate_from_2x(config)
    _validate_config(config)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except OSError as e:
        raise RuntimeError(f"Failed to save config to {path}: {e}") from e


def get_config_path_for_ui() -> Path:
    """Return config path for display (e.g. error messages)."""
    return _get_config_path()
