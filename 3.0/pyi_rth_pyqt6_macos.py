# PyInstaller runtime hook — runs before ami.main; cannot import ami (not on path yet).
# Mirrors ami._macos_qt_env logic (keep in sync).
import os
import sys
from pathlib import Path


def _search_plugins_under(root: Path):
    if not root.is_dir():
        return None
    for rel in (("PyQt6", "Qt6", "plugins"), ("PyQt6", "Qt", "plugins")):
        p = root.joinpath(*rel)
        if (p / "platforms").is_dir():
            return p
    try:
        for p in root.rglob("plugins"):
            if p.is_dir() and (p / "platforms").is_dir() and "PyQt6" in p.parts:
                return p
    except OSError:
        pass
    return None


if getattr(sys, "frozen", False) and sys.platform == "darwin":
    base = getattr(sys, "_MEIPASS", None)
    if base:
        roots = [Path(base)]
        macos_dir = Path(sys.executable).resolve().parent
        if macos_dir.name == "MacOS":
            fw = macos_dir.parent / "Frameworks"
            if fw.is_dir() and fw not in roots:
                roots.insert(0, fw)
        plugins_root = None
        for r in roots:
            plugins_root = _search_plugins_under(r)
            if plugins_root is not None:
                break
        if plugins_root is not None:
            platforms = plugins_root / "platforms"
            os.environ.setdefault("QT_PLUGIN_PATH", os.fspath(plugins_root))
            if platforms.is_dir():
                os.environ.setdefault(
                    "QT_QPA_PLATFORM_PLUGIN_PATH", os.fspath(platforms)
                )
            os.environ.setdefault("QT_QPA_PLATFORM", "cocoa")
