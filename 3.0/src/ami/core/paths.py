"""
AMI 3.0 - Centralized path resolution.
Uses platformdirs for user directories; PyInstaller uses sys._MEIPASS for resources.
"""

import sys
from pathlib import Path

from platformdirs import user_data_dir, user_config_dir


def get_base_path() -> Path:
    """
    Base path for application resources.
    PyInstaller: sys._MEIPASS. Development: 3.0/ (parent of src/ami).
    """
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    # __file__ = 3.0/src/ami/core/paths.py -> parents[2] = 3.0
    return Path(__file__).resolve().parents[2]


def get_config_path() -> Path:
    """Path to config.json in base (bundled or project root)."""
    return get_base_path() / "config.json"


def get_user_data_dir() -> Path:
    """User data directory for logs, cache (XDG-compliant on Linux)."""
    return Path(user_data_dir("AMI", "CiaoIM"))


def get_user_config_dir() -> Path:
    """User config directory for config.json."""
    return Path(user_config_dir("AMI", "CiaoIM"))
