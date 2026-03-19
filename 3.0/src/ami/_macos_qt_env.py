"""
macOS frozen .app: Qt 6's QLibraryInfo hits CFBundleCopyBundleURL during QtCore.abi3.so
static init (qdarwinpermissionplugin). PyInstaller's layout + macOS 26+ → SIGSEGV unless:

1) Contents/Resources/qt.conf exists (written at build time; Prefix → PyQt6/Qt6).
2) QT_PLUGIN_PATH / QT_QPA_PLATFORM_PLUGIN_PATH are set to absolute paths BEFORE import PyQt6.

Use os.environ[...] = (not setdefault): a preset empty/wrong value would block the fix.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def apply_if_needed() -> None:
    if not getattr(sys, "frozen", False) or sys.platform != "darwin":
        return
    exe = Path(sys.executable).resolve()
    if exe.parent.name != "MacOS":
        return
    frameworks = exe.parent.parent / "Frameworks"
    plugins = frameworks / "PyQt6" / "Qt6" / "plugins"
    platforms = plugins / "platforms"
    if not platforms.is_dir():
        return
    # Force: never rely on setdefault — broken presets are common from the shell / launcher.
    os.environ["QT_PLUGIN_PATH"] = os.fspath(plugins)
    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = os.fspath(platforms)
    os.environ["QT_QPA_PLATFORM"] = "cocoa"
    qconf = exe.parent.parent / "Resources" / "qt.conf"
    if qconf.is_file():
        os.environ["QT_CONF"] = os.fspath(qconf)
