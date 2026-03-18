"""
AMI 3.0 - Entry point.
"""

import sys

from ami.ui.tray_app import main as tray_main


def main() -> None:
    tray_main()


if __name__ == "__main__":
    main()
    sys.exit(0)
