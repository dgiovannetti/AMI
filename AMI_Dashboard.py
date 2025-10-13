#!/usr/bin/env python3
"""
AMI Dashboard Launcher
Opens the dashboard directly without requiring system tray access
"""

import sys
import os
from pathlib import Path

# Add src directory to path
src_dir = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_dir))

# Force dashboard to show on start
os.environ['AMI_FORCE_DASHBOARD'] = '1'

# Import and run the application
from tray_app import main

if __name__ == '__main__':
    main()
