"""
macOS + PyInstaller: Qt 6's QLibraryInfo uses CFBundle APIs during QtCore.abi3.so init.
If plugin paths are unset, Qt can pass an invalid bundle ref → EXC_BAD_ACCESS in CFBundleCopyBundleURL.

Call apply_if_needed() before any PyQt6 import when frozen (see ami.main).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _search_plugins_under(root: Path) -> Path | None:
    """Find .../plugins that contains platforms/ (libqcocoa.dylib)."""
    if not root.is_dir():
        return None
    direct = root / "PyQt6" / "Qt6" / "plugins"
    if (direct / "platforms").is_dir():
        return direct
    alt = root / "PyQt6" / "Qt" / "plugins"
    if (alt / "platforms").is_dir():
        return alt
    try:
        for p in root.rglob("plugins"):
            if p.is_dir() and (p / "platforms").is_dir() and "PyQt6" in p.parts:
                return p
    except OSError:
        pass
    return None


def apply_if_needed() -> None:
    if not getattr(sys, "frozen", False) or sys.platform != "darwin":
        return
    base = getattr(sys, "_MEIPASS", None)
    if not base:
        return

    roots: list[Path] = [Path(base)]
    # BUNDLE: executable in MacOS/, payload often in Frameworks/
    macos_dir = Path(sys.executable).resolve().parent
    if macos_dir.name == "MacOS":
        fw = macos_dir.parent / "Frameworks"
        if fw.is_dir() and fw not in roots:
            roots.insert(0, fw)

    plugins_root: Path | None = None
    for r in roots:
        plugins_root = _search_plugins_under(r)
        if plugins_root is not None:
            break
    if plugins_root is None:
        return

    platforms = plugins_root / "platforms"
    pr = os.fspath(plugins_root)
    os.environ.setdefault("QT_PLUGIN_PATH", pr)
    if platforms.is_dir():
        os.environ.setdefault("QT_QPA_PLATFORM_PLUGIN_PATH", os.fspath(platforms))
    os.environ.setdefault("QT_QPA_PLATFORM", "cocoa")
