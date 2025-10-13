"""
AMI Build Script
Builds the AMI application into a standalone executable using PyInstaller
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


def check_requirements():
    """Check if all required packages are installed"""
    print("Checking requirements...")
    
    required = ['PyQt6', 'requests', 'matplotlib', 'numpy', 'ping3', 'psutil', 'PIL']
    missing = []
    
    for package in required:
        try:
            if package == 'PIL':
                __import__('PIL')
            else:
                __import__(package)
            print(f"  [OK] {package}")
        except ImportError:
            print(f"  [FAIL] {package} - NOT FOUND")
            missing.append(package)
    
    if missing:
        print(f"\nMissing packages: {', '.join(missing)}")
        print("Install with: pip install -r requirements.txt")
        return False
    
    # Check PyInstaller
    try:
        __import__('PyInstaller')
        print("  [OK] PyInstaller")
    except ImportError:
        print("  [FAIL] PyInstaller - NOT FOUND")
        print("\nInstall PyInstaller with: pip install pyinstaller")
        return False
    
    return True


def generate_icons():
    """Generate application icons"""
    print("\nGenerating icons...")
    
    tools_dir = Path(__file__).parent / 'tools'
    icon_script = tools_dir / 'generate_icons.py'
    
    if icon_script.exists():
        try:
            result = subprocess.run(
                [sys.executable, str(icon_script)],
                capture_output=True,
                text=True
            )
            print(result.stdout)
            if result.returncode != 0:
                print(f"Warning: Icon generation had errors:\n{result.stderr}")
        except Exception as e:
            print(f"Warning: Could not generate icons: {e}")
    else:
        print("Warning: Icon generator not found")


def build_executable():
    """Build the executable using PyInstaller"""
    print("\nBuilding executable...")
    
    # Paths
    src_dir = Path(__file__).parent / 'src'
    resources_dir = Path(__file__).parent / 'resources'
    config_file = Path(__file__).parent / 'config.json'
    main_script = src_dir / 'tray_app.py'
    icon_file = resources_dir / 'ami.ico'
    
    # PyInstaller arguments
    args = [
        'pyinstaller',
        '--name=AMI',
        '--windowed',  # No console window
        '--onefile',  # Single executable
        f'--icon={icon_file}' if icon_file.exists() else '',
        '--add-data', f'{config_file}{os.pathsep}.',  # Include config.json
        f'--paths={src_dir}',  # Add src directory to Python path
        '--hidden-import=ping3',
        '--hidden-import=matplotlib',
        '--hidden-import=numpy',
        '--hidden-import=requests',
        '--hidden-import=network_monitor',  # Our modules
        '--hidden-import=logger',
        '--hidden-import=notifier',
        '--hidden-import=api_server',
        '--hidden-import=dashboard',
        '--hidden-import=splash_screen',
        '--hidden-import=animated_button',
        '--collect-all=matplotlib',
        '--noconfirm',  # Overwrite without asking
        str(main_script)
    ]
    
    # Remove empty arguments
    args = [arg for arg in args if arg]
    
    print(f"Running: {' '.join(args)}")
    
    try:
        result = subprocess.run(args, check=True)
        print("\n[OK] Build successful!")
        
        # Show output location
        dist_dir = Path(__file__).parent / 'dist'
        exe_name = 'AMI.exe' if sys.platform == 'win32' else 'AMI'
        exe_path = dist_dir / exe_name
        
        if exe_path.exists():
            print(f"\nExecutable created: {exe_path}")
            print(f"Size: {exe_path.stat().st_size / (1024*1024):.2f} MB")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n[FAIL] Build failed: {e}")
        return False


def create_installer_package():
    """Create a distributable package"""
    print("\nCreating distribution package...")
    
    dist_dir = Path(__file__).parent / 'dist'
    package_dir = dist_dir / 'AMI-Package'
    
    # Create package directory
    package_dir.mkdir(exist_ok=True)
    
    # Copy executable
    exe_name = 'AMI.exe' if sys.platform == 'win32' else 'AMI'
    exe_src = dist_dir / exe_name
    if exe_src.exists():
        shutil.copy2(exe_src, package_dir / exe_name)
        print(f"  [OK] Copied {exe_name}")
    
    # Copy config.json
    config_src = Path(__file__).parent / 'config.json'
    if config_src.exists():
        shutil.copy2(config_src, package_dir / 'config.json')
        print("  [OK] Copied config.json")
    
    # Copy README
    readme_src = Path(__file__).parent / 'README.md'
    if readme_src.exists():
        shutil.copy2(readme_src, package_dir / 'README.md')
        print("  [OK] Copied README.md")
    
    # Copy icons
    resources_src = Path(__file__).parent / 'resources'
    if resources_src.exists():
        resources_dst = package_dir / 'resources'
        if resources_dst.exists():
            shutil.rmtree(resources_dst)
        shutil.copytree(resources_src, resources_dst)
        print("  [OK] Copied resources/")
    
    # Create a quick start guide
    quick_start = package_dir / 'QUICK_START.txt'
    with open(quick_start, 'w', encoding='utf-8') as f:
        f.write("""
AMI - Active Monitor of Internet
Quick Start Guide

1. FIRST RUN:
   - Double-click AMI.exe to start
   - The application will run in the system tray
   - Look for the AMI icon in the system tray (bottom-right corner)

2. CONFIGURATION:
   - Right-click the tray icon and select "Settings"
   - Or edit config.json manually for advanced options
   - Restart AMI after changing settings

3. FEATURES:
   - Green icon 🟢: Online
   - Yellow icon 🟡: Unstable connection
   - Red icon 🔴: Offline
   
   Right-click the tray icon to:
   - View current status
   - Test connection manually
   - Open dashboard with statistics
   - View connection logs
   - Exit the application

4. AUTO-START (Optional):
   - To start AMI automatically with Windows:
   - Open config.json
   - Set "auto_start": true under "startup"
   - Restart AMI

5. TROUBLESHOOTING:
   - If the icon doesn't appear, check Task Manager
   - Check ami_log.csv for connection history
   - Edit config.json to adjust polling interval or test hosts

For more information, see README.md

"Sai se sei davvero online."
""")
    print("  [OK] Created QUICK_START.txt")
    
    print(f"\n[OK] Package created: {package_dir}")
    
    # Create ZIP archive
    try:
        archive_name = dist_dir / 'AMI-Package'
        shutil.make_archive(str(archive_name), 'zip', package_dir)
        print(f"[OK] ZIP archive created: {archive_name}.zip")
    except Exception as e:
        print(f"Warning: Could not create ZIP archive: {e}")


def clean_build_artifacts():
    """Clean up build artifacts"""
    print("\nCleaning build artifacts...")
    
    paths_to_remove = [
        Path(__file__).parent / 'build',
        Path(__file__).parent / 'AMI.spec',
        Path(__file__).parent / '__pycache__',
    ]
    
    for path in paths_to_remove:
        if path.exists():
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
            print(f"  [OK] Removed {path.name}")


def main():
    """Main build process"""
    print("=" * 60)
    print("AMI Build Script")
    print("=" * 60)
    
    # Check requirements
    if not check_requirements():
        print("\n[FAIL] Build aborted due to missing requirements")
        return 1
    
    # Generate icons
    generate_icons()
    
    # Build executable
    if not build_executable():
        print("\n[FAIL] Build failed")
        return 1
    
    # Create package
    create_installer_package()
    
    # Clean up
    clean_build_artifacts()
    
    print("\n" + "=" * 60)
    print("[OK] Build completed successfully!")
    print("=" * 60)
    print("\nYou can find the executable in the 'dist/AMI-Package' directory")
    print("A ZIP archive has also been created for easy distribution")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
