"""
AMI - Active Monitor of Internet
Main Entry Point

This is a convenience launcher that adds the src directory to the path
and starts the application.
"""

import sys
import os
from pathlib import Path

# Add src directory to path
src_dir = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_dir))

# Import and run the application
from tray_app import main

if __name__ == '__main__':
    main()
