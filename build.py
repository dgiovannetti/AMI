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
    
    required = ['PyQt6', 'requests', 'matplotlib', 'numpy', 'ping3', 'psutil', 'PIL', 'platformdirs']
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
    
    root_dir = Path(__file__).parent
    src_dir = root_dir / 'src'
    resources_dir = root_dir / 'resources'
    config_file = root_dir / 'config.json'
    main_script = src_dir / 'main.py'
    icon_file = resources_dir / 'ami.ico'
    spec_file = root_dir / 'AMI_app.spec'
    
    # On macOS: use spec file to create .app bundle with CFBundleName (Dock/menu bar show "AMI")
    if sys.platform == 'darwin' and spec_file.exists():
        print("[macOS] Using AMI_app.spec for .app bundle (Dock/menu bar will show 'AMI')")
        args = ['pyinstaller', '--noconfirm', str(spec_file)]
    else:
        # Windows/Linux or no spec
        args = [
            'pyinstaller',
            '--name=AMI',
            '--windowed',
            '--onefile',
            '--noconsole' if sys.platform == 'win32' else '',
            f'--icon={icon_file}' if icon_file.exists() else '',
            '--add-data', f'{config_file}{os.pathsep}.',
            '--add-data', f'{resources_dir}{os.pathsep}resources',
            f'--paths={src_dir}',
            '--hidden-import=ping3',
            '--hidden-import=matplotlib',
            '--hidden-import=numpy',
            '--hidden-import=requests',
            '--hidden-import=platformdirs',
            '--hidden-import=core',
            '--hidden-import=core.paths',
            '--hidden-import=core.config',
            '--hidden-import=core.models',
            '--hidden-import=services',
            '--hidden-import=services.network_monitor',
            '--hidden-import=services.logger',
            '--hidden-import=services.notifier',
            '--hidden-import=services.api_server',
            '--hidden-import=services.updater',
            '--hidden-import=ui',
            '--hidden-import=ui.tray_app',
            '--hidden-import=ui.dashboard',
            '--hidden-import=ui.splash_screen',
            '--hidden-import=ui.settings_dialog',
            '--hidden-import=ui.update_dialog',
            '--hidden-import=ui.compact_status',
            '--collect-all=matplotlib',
            '--noconfirm',
            str(main_script)
        ]
    
    args = [arg for arg in args if arg]
    print(f"Running: {' '.join(args)}")
    
    try:
        subprocess.run(args, check=True)
        print("\n[OK] Build successful!")
        
        dist_dir = root_dir / 'dist'
        if sys.platform == 'win32':
            exe_path = dist_dir / 'AMI.exe'
        elif sys.platform == 'darwin' and (dist_dir / 'AMI.app').exists():
            exe_path = dist_dir / 'AMI.app'
            print(f"\n.app bundle created: {exe_path}")
            return True
        else:
            exe_path = dist_dir / 'AMI'
        
        if exe_path.exists():
            size = exe_path.stat().st_size / (1024 * 1024)
            print(f"\nExecutable created: {exe_path} ({size:.2f} MB)")
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
    
    # Copy executable (on macOS: AMI.app bundle so Dock/menu bar show "AMI")
    if sys.platform == 'win32':
        exe_name, exe_src = 'AMI.exe', dist_dir / 'AMI.exe'
    elif sys.platform == 'darwin':
        exe_name, exe_src = 'AMI.app', dist_dir / 'AMI.app'
    else:
        exe_name, exe_src = 'AMI', dist_dir / 'AMI'
    if exe_src.exists():
        dst = package_dir / exe_name
        if exe_src.is_dir():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(exe_src, dst)
        else:
            shutil.copy2(exe_src, dst)
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
    
    # Copy MACOS_SECURITY.md (macOS only)
    if sys.platform == 'darwin':
        macos_sec = Path(__file__).parent / 'MACOS_SECURITY.md'
        if macos_sec.exists():
            shutil.copy2(macos_sec, package_dir / 'MACOS_SECURITY.md')
            print("  [OK] Copied MACOS_SECURITY.md")
    
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
    is_macos = sys.platform == 'darwin'
    
    with open(quick_start, 'w', encoding='utf-8') as f:
        if is_macos:
            f.write("""AMI - Active Monitor of Internet
Quick Start Guide (macOS)

1. FIRST RUN:
   - Double-click AMI.app to start
   - AMI will appear in the Dock and menu bar as "AMI"
   - If Gatekeeper blocks: right-click AMI.app → Open → Open
   - See MACOS_SECURITY.md for more details.

2. CONFIGURATION:
   - Right-click the menu bar icon and select "Settings"
   - Or edit config.json manually for advanced options

3. FEATURES:
   - Green icon: Online
   - Yellow icon: Unstable connection
   - Red icon: Offline
   
   Right-click the menu bar icon to:
   - View current status
   - Test connection manually
   - Open dashboard with statistics
   - View connection logs
   - Exit the application

4. TROUBLESHOOTING:
   - Check ami_log.csv for connection history
   - Edit config.json to adjust polling interval or test hosts
   - See MACOS_SECURITY.md for Gatekeeper issues
   - Activity Monitor shows "AMI" if running

For more information, see README.md and MACOS_SECURITY.md

"Sai se sei davvero online."
""")
        else:
            f.write("""AMI - Active Monitor of Internet
Quick Start Guide (Windows)

1. FIRST RUN:
   - Double-click AMI.exe to start
   - The application will run in the system tray
   - Look for the AMI icon in the system tray (bottom-right corner)

2. CONFIGURATION:
   - Right-click the tray icon and select "Settings"
   - Or edit config.json manually for advanced options

3. FEATURES:
   - Green icon: Online
   - Yellow icon: Unstable connection
   - Red icon: Offline
   
   Right-click the tray icon to:
   - View current status
   - Test connection manually
   - Open dashboard with statistics
   - View connection logs
   - Exit the application

4. AUTO-START (Optional):
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
    
    # Create ZIP archive with platform-specific name
    try:
        if sys.platform == 'win32':
            archive_name = dist_dir / 'AMI-Windows'
        elif sys.platform == 'darwin':
            archive_name = dist_dir / 'AMI-macOS'
        else:
            archive_name = dist_dir / 'AMI-Linux'
        shutil.make_archive(str(archive_name), 'zip', package_dir)
        print(f"[OK] ZIP archive created: {archive_name}.zip")
    except Exception as e:
        print(f"Warning: Could not create ZIP archive: {e}")


def clean_build_artifacts():
    """Clean up build artifacts"""
    print("\nCleaning build artifacts...")
    
    root = Path(__file__).parent
    paths_to_remove = [
        root / 'build',
        root / 'AMI.spec',
        root / '__pycache__',
    ]
    # Keep AMI_app.spec (used for macOS .app build)
    
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
