#!/usr/bin/env python3
"""
Build macOS .app bundle for AMI
Creates a proper macOS application that can be double-clicked
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def build_app_bundle():
    """Build AMI as a macOS .app bundle"""
    
    print("=" * 60)
    print("Building AMI.app for macOS")
    print("=" * 60)
    print()
    
    # Paths
    root_dir = Path(__file__).parent
    dist_dir = root_dir / "dist"
    app_dir = dist_dir / "AMI.app"
    contents_dir = app_dir / "Contents"
    macos_dir = contents_dir / "MacOS"
    resources_dir = contents_dir / "Resources"
    
    # Clean previous build
    if app_dir.exists():
        print(f"Removing existing {app_dir}")
        shutil.rmtree(app_dir)
    
    # Create .app structure
    print("Creating .app bundle structure...")
    macos_dir.mkdir(parents=True, exist_ok=True)
    resources_dir.mkdir(parents=True, exist_ok=True)
    
    # Build with PyInstaller (windowed mode, .app bundle)
    print("\nBuilding with PyInstaller...")
    
    spec_content = """
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['AMI.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('resources', 'resources'),
        ('config.json', '.'),
        ('src', 'src'),
    ],
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'matplotlib',
        'matplotlib.backends.backend_qt5agg',
        'ping3',
        'requests',
        'src.tray_app',
        'src.dashboard',
        'src.settings_dialog',
        'src.update_dialog',
        'src.network_monitor',
        'src.updater',
        'src.logger',
        'src.config_manager',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='AMI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,  # Let PyInstaller detect automatically
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/ami.icns' if os.path.exists('resources/ami.icns') else None,
)

app = BUNDLE(
    exe,
    name='AMI.app',
    icon='resources/ami.icns' if os.path.exists('resources/ami.icns') else None,
    bundle_identifier='tech.ciaoim.ami',
    info_plist={
        'CFBundleName': 'AMI',
        'CFBundleDisplayName': 'AMI - Active Monitor of Internet',
        'CFBundleVersion': '2.0.0',
        'CFBundleShortVersionString': '2.0.0',
        'NSHighResolutionCapable': True,
        'LSUIElement': False,  # Show in Dock
        'NSRequiresAquaSystemAppearance': False,
    },
)
"""
    
    spec_file = root_dir / "AMI_app.spec"
    with open(spec_file, 'w') as f:
        f.write(spec_content)
    
    # Run PyInstaller
    cmd = [sys.executable, '-m', 'PyInstaller', '--clean', str(spec_file)]
    result = subprocess.run(cmd, cwd=root_dir)
    
    if result.returncode != 0:
        print("\n❌ Build failed!")
        return False
    
    # Verify .app was created
    if not app_dir.exists():
        print("\n❌ AMI.app was not created!")
        return False
    
    print("\n✅ Build successful!")
    print(f"\nAMI.app created at: {app_dir}")
    
    # Get size
    size_bytes = sum(f.stat().st_size for f in app_dir.rglob('*') if f.is_file())
    size_mb = size_bytes / (1024 * 1024)
    print(f"Size: {size_mb:.2f} MB")
    
    # Create DMG (optional)
    create_dmg = input("\nCreate .dmg installer? (y/n): ").lower() == 'y'
    
    if create_dmg:
        print("\nCreating DMG...")
        dmg_path = dist_dir / "AMI-macOS-Installer.dmg"
        
        # Remove old DMG
        if dmg_path.exists():
            dmg_path.unlink()
        
        # Create DMG with hdiutil
        cmd = [
            'hdiutil', 'create',
            '-volname', 'AMI',
            '-srcfolder', str(app_dir),
            '-ov',
            '-format', 'UDZO',
            str(dmg_path)
        ]
        
        result = subprocess.run(cmd)
        
        if result.returncode == 0:
            dmg_size_mb = dmg_path.stat().st_size / (1024 * 1024)
            print(f"\n✅ DMG created: {dmg_path}")
            print(f"Size: {dmg_size_mb:.2f} MB")
        else:
            print("\n⚠️  DMG creation failed (optional)")
    
    # Create ZIP
    print("\nCreating ZIP archive...")
    zip_path = dist_dir / "AMI-macOS-App.zip"
    
    if zip_path.exists():
        zip_path.unlink()
    
    shutil.make_archive(
        str(zip_path.with_suffix('')),
        'zip',
        dist_dir,
        'AMI.app'
    )
    
    zip_size_mb = zip_path.stat().st_size / (1024 * 1024)
    print(f"✅ ZIP created: {zip_path}")
    print(f"Size: {zip_size_mb:.2f} MB")
    
    # Cleanup
    print("\nCleaning up...")
    if spec_file.exists():
        spec_file.unlink()
    
    build_dir = root_dir / "build"
    if build_dir.exists():
        shutil.rmtree(build_dir)
    
    print("\n" + "=" * 60)
    print("✅ Build completed successfully!")
    print("=" * 60)
    print(f"\nYou can now:")
    print(f"1. Double-click {app_dir} to run")
    print(f"2. Drag AMI.app to /Applications")
    print(f"3. Distribute {zip_path}")
    if create_dmg:
        print(f"4. Distribute {dmg_path} (drag-to-install)")
    print()
    
    return True

if __name__ == "__main__":
    success = build_app_bundle()
    sys.exit(0 if success else 1)
