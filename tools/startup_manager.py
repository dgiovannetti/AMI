"""
AMI Startup Manager
Utility to manage Windows auto-start functionality
"""

import os
import sys
import winreg
from pathlib import Path


class StartupManager:
    """
    Manages Windows startup registry entries
    """
    
    # Registry path for startup programs
    STARTUP_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
    APP_NAME = "AMI"
    
    @staticmethod
    def is_autostart_enabled() -> bool:
        """Check if AMI is set to start automatically"""
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                StartupManager.STARTUP_KEY,
                0,
                winreg.KEY_READ
            )
            
            try:
                value, _ = winreg.QueryValueEx(key, StartupManager.APP_NAME)
                winreg.CloseKey(key)
                return True
            except FileNotFoundError:
                winreg.CloseKey(key)
                return False
                
        except Exception as e:
            print(f"Error checking autostart: {e}")
            return False
    
    @staticmethod
    def enable_autostart(executable_path: str = None) -> bool:
        """
        Enable auto-start for AMI
        
        Args:
            executable_path: Path to AMI.exe (auto-detected if None)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if executable_path is None:
                # Try to find AMI.exe
                if getattr(sys, 'frozen', False):
                    # Running as compiled executable
                    executable_path = sys.executable
                else:
                    # Running as script - can't autostart a script
                    print("Error: Cannot enable autostart for Python script")
                    print("Please build the executable first (python build.py)")
                    return False
            
            # Ensure path is absolute
            executable_path = os.path.abspath(executable_path)
            
            # Add quotes to handle spaces in path
            value = f'"{executable_path}"'
            
            # Open registry key
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                StartupManager.STARTUP_KEY,
                0,
                winreg.KEY_SET_VALUE
            )
            
            # Set the value
            winreg.SetValueEx(key, StartupManager.APP_NAME, 0, winreg.REG_SZ, value)
            winreg.CloseKey(key)
            
            print(f"✓ Auto-start enabled for: {executable_path}")
            return True
            
        except Exception as e:
            print(f"✗ Error enabling autostart: {e}")
            return False
    
    @staticmethod
    def disable_autostart() -> bool:
        """
        Disable auto-start for AMI
        
        Returns:
            True if successful, False otherwise
        """
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                StartupManager.STARTUP_KEY,
                0,
                winreg.KEY_SET_VALUE
            )
            
            try:
                winreg.DeleteValue(key, StartupManager.APP_NAME)
                winreg.CloseKey(key)
                print("✓ Auto-start disabled")
                return True
            except FileNotFoundError:
                winreg.CloseKey(key)
                print("ℹ Auto-start was not enabled")
                return True
                
        except Exception as e:
            print(f"✗ Error disabling autostart: {e}")
            return False
    
    @staticmethod
    def toggle_autostart(executable_path: str = None) -> bool:
        """
        Toggle auto-start on/off
        
        Args:
            executable_path: Path to AMI.exe (auto-detected if None)
            
        Returns:
            True if now enabled, False if now disabled
        """
        if StartupManager.is_autostart_enabled():
            StartupManager.disable_autostart()
            return False
        else:
            StartupManager.enable_autostart(executable_path)
            return True


def main():
    """Command-line interface for startup manager"""
    import argparse
    
    parser = argparse.ArgumentParser(description='AMI Startup Manager')
    parser.add_argument(
        'action',
        choices=['status', 'enable', 'disable', 'toggle'],
        help='Action to perform'
    )
    parser.add_argument(
        '--path',
        help='Path to AMI.exe (auto-detected if not specified)'
    )
    
    args = parser.parse_args()
    
    if args.action == 'status':
        enabled = StartupManager.is_autostart_enabled()
        print(f"Auto-start is {'ENABLED' if enabled else 'DISABLED'}")
        
    elif args.action == 'enable':
        StartupManager.enable_autostart(args.path)
        
    elif args.action == 'disable':
        StartupManager.disable_autostart()
        
    elif args.action == 'toggle':
        enabled = StartupManager.toggle_autostart(args.path)
        print(f"Auto-start is now {'ENABLED' if enabled else 'DISABLED'}")


if __name__ == '__main__':
    # Check if running on Windows
    if sys.platform != 'win32':
        print("Error: Startup manager only works on Windows")
        sys.exit(1)
    
    main()
