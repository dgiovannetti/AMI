"""
AMI 3.0 - Entry point.
"""

import sys

# Frozen macOS .app: set Qt plugin paths before PyQt6 (avoids CFBundleCopyBundleURL crash in QtCore).
if getattr(sys, "frozen", False) and sys.platform == "darwin":
    from ami._macos_qt_env import apply_if_needed

    apply_if_needed()

from ami.ui.qt_safe import install_exception_handlers
from ami.ui.tray_app import main as tray_main


def main() -> None:
    install_exception_handlers()
    tray_main()


if __name__ == "__main__":
    main()
