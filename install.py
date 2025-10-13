"""
AMI Installation Script
Handles dependency installation and initial setup
"""

import subprocess
import sys
import os
from pathlib import Path


def check_python_version():
    """Check if Python version is compatible"""
    print("Checking Python version...")
    
    if sys.version_info < (3, 8):
        print("[FAIL] Error: Python 3.8 or higher is required")
        print(f"  Current version: {sys.version}")
        return False
    
    print(f"[OK] Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True


def install_dependencies():
    """Install required dependencies"""
    print("\nInstalling dependencies...")
    
    requirements_file = Path(__file__).parent / 'requirements.txt'
    
    if not requirements_file.exists():
        print("[FAIL] Error: requirements.txt not found")
        return False
    
    try:
        subprocess.check_call([
            sys.executable,
            '-m',
            'pip',
            'install',
            '-r',
            str(requirements_file)
        ])
        print("[OK] Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[FAIL] Error installing dependencies: {e}")
        return False


def install_build_dependencies():
    """Install build-time dependencies (optional)"""
    print("\nInstalling build dependencies (optional)...")
    
    requirements_file = Path(__file__).parent / 'requirements-build.txt'
    
    if not requirements_file.exists():
        print("[WARN] Warning: requirements-build.txt not found, skipping")
        return True
    
    try:
        subprocess.check_call([
            sys.executable,
            '-m',
            'pip',
            'install',
            '-r',
            str(requirements_file)
        ])
        print("[OK] Build dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[WARN] Warning: Could not install build dependencies: {e}")
        print("  (This is optional and only needed if you want to build the .exe)")
        return True  # Don't fail if build deps can't be installed


def generate_icons():
    """Generate application icons"""
    print("\nGenerating application icons...")
    
    tools_dir = Path(__file__).parent / 'tools'
    icon_script = tools_dir / 'generate_icons.py'
    
    if not icon_script.exists():
        print("[WARN] Warning: Icon generator script not found")
        return True
    
    try:
        result = subprocess.run(
            [sys.executable, str(icon_script)],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(result.stdout)
            print("[OK] Icons generated successfully")
            return True
        else:
            print(f"[WARN] Warning: Icon generation failed:\n{result.stderr}")
            return True  # Don't fail installation
    except Exception as e:
        print(f"[WARN] Warning: Could not generate icons: {e}")
        return True  # Don't fail installation


def verify_installation():
    """Verify that the installation was successful"""
    print("\nVerifying installation...")
    
    required_modules = [
        'PyQt6',
        'requests',
        'matplotlib',
        'numpy',
        'ping3',
        'psutil'
    ]
    
    all_ok = True
    for module in required_modules:
        try:
            __import__(module)
            print(f"  [OK] {module}")
        except ImportError:
            print(f"  [FAIL] {module} - FAILED")
            all_ok = False
    
    return all_ok


def create_desktop_shortcut():
    """Offer to create a desktop shortcut (Windows only)"""
    if sys.platform != 'win32':
        return
    
    print("\nWould you like to create a desktop shortcut? (y/n): ", end='')
    response = input().strip().lower()
    
    if response == 'y':
        try:
            import winshell
            from win32com.client import Dispatch
            
            desktop = winshell.desktop()
            path = os.path.join(desktop, "AMI.lnk")
            target = str(Path(__file__).parent / 'AMI.py')
            
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(path)
            shortcut.TargetPath = sys.executable
            shortcut.Arguments = f'"{target}"'
            shortcut.WorkingDirectory = str(Path(__file__).parent)
            shortcut.IconLocation = str(Path(__file__).parent / 'resources' / 'ami.ico')
            shortcut.save()
            
            print(f"[OK] Desktop shortcut created: {path}")
        except Exception as e:
            print(f"[WARN] Could not create desktop shortcut: {e}")
            print("  You can manually create a shortcut to AMI.py")


def main():
    """Main installation process"""
    print("=" * 60)
    print("AMI - Active Monitor of Internet")
    print("Installation Script")
    print("=" * 60)
    print()
    
    # Check Python version
    if not check_python_version():
        return 1
    
    # Install dependencies
    if not install_dependencies():
        print("\n[FAIL] Installation failed")
        return 1
    
    # Install build dependencies (optional)
    install_build_dependencies()
    
    # Generate icons
    generate_icons()
    
    # Verify installation
    if not verify_installation():
        print("\n[WARN] Installation completed with warnings")
        print("Some modules could not be imported. Please check the errors above.")
        return 1
    
    # Desktop shortcut (Windows only)
    create_desktop_shortcut()
    
    print("\n" + "=" * 60)
    print("[OK] Installation completed successfully!")
    print("=" * 60)
    print("\nTo run AMI:")
    print(f"  python {Path(__file__).parent / 'AMI.py'}")
    print("\nOr to build an executable:")
    print(f"  python {Path(__file__).parent / 'build.py'}")
    print()
    
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n[FAIL] Installation cancelled by user")
        sys.exit(1)
