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

    macOS .app: PyInstaller usa ``Contents/Frameworks`` come ``_MEIPASS``, ma i ``datas``
    (config, ``resources/*.png``, …) stanno spesso in ``Contents/Resources`` — vedi PyInstaller #7884.
    Senza questo accorgimento le icone tray e le PNG in bundle non si trovano.
    """
    if getattr(sys, "frozen", False):
        me = Path(getattr(sys, "_MEIPASS", "")).resolve()
        if sys.platform == "darwin":
            # Bundle .app: cartella sorella "Resources" contiene ``resources/`` e copie di config.
            alt = me.parent / "Resources"
            if (alt / "resources").is_dir():
                return alt
        return me
    # __file__ = …/src/ami/core/paths.py → cartella progetto 3.0/ è parents[3] (non parents[2]=src/)
    return Path(__file__).resolve().parents[3]


def get_config_path() -> Path:
    """Path to config.json in base (bundled or project root)."""
    return get_base_path() / "config.json"


def get_user_data_dir() -> Path:
    """User data directory for logs, cache (XDG-compliant on Linux)."""
    return Path(user_data_dir("AMI", "CiaoIM"))


def get_user_config_dir() -> Path:
    """User config directory for config.json."""
    return Path(user_config_dir("AMI", "CiaoIM"))
