# PyInstaller runtime hook — runs before ami.main; keep in sync with ami._macos_qt_env.
import os
import sys
from pathlib import Path

if getattr(sys, "frozen", False) and sys.platform == "darwin":
    exe = Path(getattr(sys, "executable", "") or "").resolve()
    if exe.parent.name == "MacOS":
        fw = exe.parent.parent / "Frameworks"
        plugins = fw / "PyQt6" / "Qt6" / "plugins"
        platforms = plugins / "platforms"
        if platforms.is_dir():
            os.environ["QT_PLUGIN_PATH"] = os.fspath(plugins)
            os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = os.fspath(platforms)
            os.environ["QT_QPA_PLATFORM"] = "cocoa"
            qconf = exe.parent.parent / "Resources" / "qt.conf"
            if qconf.is_file():
                os.environ["QT_CONF"] = os.fspath(qconf)
