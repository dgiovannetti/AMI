"""
AMI - Active Monitor of Internet
Configuration loading, validation, and migration
"""

import json
import shutil
import sys
from pathlib import Path
from typing import Dict, Any

from .paths import get_base_path, get_user_config_dir


# Default config used when no file exists
DEFAULT_CONFIG: Dict[str, Any] = {
    "app": {
        "name": "AMI",
        "subtitle": "Active Monitor of Internet",
        "version": "2.1.0",
        "copyright": "© 2025 CiaoIM™ by Daniel Giovannetti",
        "website": "ciaoim.tech",
        "tagline": "Crafted logic. Measured force. Front-end vision, compiled systems, and hardcoded ethics.",
        "inspiration": "Intuizione colta insieme a Giovanni Calvario in aliscafo per il 40° Convegno di Capri dei Giovani Imprenditori",
    },
    "monitoring": {
        "ping_hosts": ["8.8.8.8", "1.1.1.1", "github.com"],
        "http_test_url": "https://www.google.com/generate_204",
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
    "api": {"enabled": False, "port": 7212},
    "startup": {"auto_start": False},
    "ui": {
        "theme": "auto",
        "show_dashboard_on_start": True,
        "compact_status_window": True,  # Small always-visible window (useful when menu bar icon is not visible, e.g. macOS)
    },
    "updates": {
        "enabled": True,
        "check_on_startup": True,
        "check_interval_hours": 24,
        "github_repo": "dgiovannetti/AMI",
        "max_postponements": 3,
        "notify_on_update": True,
    },
}

# Resolved config path (set by first_run_migration / load_config)
_config_path: Path | None = None


def first_run_migration() -> Path:
    """
    Migrate config from legacy location to user dir.
    Returns the path to use for config.json.
    Critical for existing users upgrading to the new version.
    """
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

    # User dir, will create default
    user_config.parent.mkdir(parents=True, exist_ok=True)
    _config_path = user_config
    return _config_path


def _get_config_path() -> Path:
    """Get the config path (run migration if needed)."""
    global _config_path
    if _config_path is not None:
        return _config_path

    # Development: use project root. Production (frozen): use user dir with migration.
    if not getattr(sys, "frozen", False):
        _config_path = get_base_path() / "config.json"
        return _config_path

    _config_path = first_run_migration()
    return _config_path


def _validate_config(config: Dict[str, Any]) -> None:
    """Validate minimal schema. Raises ValueError on failure."""
    hosts = config.get("monitoring", {}).get("ping_hosts", [])
    if not hosts or not isinstance(hosts, list):
        raise ValueError("config.monitoring.ping_hosts must be a non-empty list")


def load_config() -> Dict[str, Any]:
    """
    Load config from the resolved path.
    Runs migration on first call.
    Returns default config if file doesn't exist.
    """
    path = _get_config_path()

    if not path.exists():
        return dict(DEFAULT_CONFIG)

    try:
        with open(path, "r", encoding="utf-8") as f:
            config = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        raise RuntimeError(f"Failed to load config from {path}: {e}") from e

    _validate_config(config)
    return config


def save_config(config: Dict[str, Any]) -> None:
    """Save config to the resolved path."""
    path = _get_config_path()
    _validate_config(config)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except OSError as e:
        raise RuntimeError(f"Failed to save config to {path}: {e}") from e


def get_config_path_for_ui() -> Path:
    """Return the config path for display (e.g. in error messages)."""
    return _get_config_path()
