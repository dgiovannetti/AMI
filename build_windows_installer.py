#!/usr/bin/env python3
"""
Build Windows installer for AMI
Creates both standalone .exe and optional installer
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def build_windows_exe():
    """Build AMI as Windows standalone executable"""
    
    print("=" * 60)
    print("Building AMI for Windows")
    print("=" * 60)
    print()
    
    # Check platform
    if sys.platform != 'win32':
        print("⚠️  This script should be run on Windows")
        print("However, the spec file will be created for cross-platform use")
        print()
    
    # Paths
    root_dir = Path(__file__).parent
    
    # Create PyInstaller spec for Windows
    spec_content = """
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['src\\\\main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('resources', 'resources'),
        ('config.json', '.'),
    ],
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'matplotlib',
        'matplotlib.backends.backend_qt5agg',
        'ping3',
        'requests',
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
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources\\\\ami.ico' if os.path.exists('resources\\\\ami.ico') else None,
    version_file='version_info.txt' if os.path.exists('version_info.txt') else None,
)
"""
    
    spec_file = root_dir / "AMI_windows.spec"
    with open(spec_file, 'w') as f:
        f.write(spec_content)
    
    print(f"✅ Created {spec_file}")
    
    # Create version info file for Windows
    version_info = """
# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(2, 1, 1, 0),
    prodvers=(2, 1, 1, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'CiaoIM™ by Daniel Giovannetti'),
        StringStruct(u'FileDescription', u'AMI - Active Monitor of Internet'),
        StringStruct(u'FileVersion', u'2.1.1'),
        StringStruct(u'InternalName', u'AMI'),
        StringStruct(u'LegalCopyright', u'© 2025 CiaoIM™ by Daniel Giovannetti. Apache 2.0 License'),
        StringStruct(u'OriginalFilename', u'AMI.exe'),
        StringStruct(u'ProductName', u'AMI'),
        StringStruct(u'ProductVersion', u'2.1.1')])
      ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
"""
    
    version_file = root_dir / "version_info.txt"
    with open(version_file, 'w', encoding='utf-8') as f:
        f.write(version_info)
    
    print(f"✅ Created {version_file}")
    
    if sys.platform == 'win32':
        # Run PyInstaller on Windows
        print("\nBuilding with PyInstaller...")
        cmd = [sys.executable, '-m', 'PyInstaller', '--clean', str(spec_file)]
        result = subprocess.run(cmd, cwd=root_dir)
        
        if result.returncode != 0:
            print("\n❌ Build failed!")
            return False
        
        # Check output
        exe_path = root_dir / "dist" / "AMI.exe"
        if not exe_path.exists():
            print("\n❌ AMI.exe was not created!")
            return False
        
        print("\n✅ Build successful!")
        print(f"\nAMI.exe created at: {exe_path}")
        
        # Get size
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"Size: {size_mb:.2f} MB")
        
        # Create installer with NSIS (if available)
        create_installer = input("\nCreate NSIS installer? (requires NSIS installed) (y/n): ").lower() == 'y'
        
        if create_installer:
            create_nsis_installer(root_dir)
        
        # Create ZIP
        print("\nCreating ZIP archive...")
        dist_dir = root_dir / "dist"
        zip_path = dist_dir / "AMI-Windows.zip"
        
        if zip_path.exists():
            zip_path.unlink()
        
        # Create package directory
        package_dir = dist_dir / "AMI-Package"
        if package_dir.exists():
            shutil.rmtree(package_dir)
        package_dir.mkdir()
        
        # Copy files
        shutil.copy(exe_path, package_dir)
        shutil.copy(root_dir / "config.json", package_dir)
        shutil.copy(root_dir / "README.md", package_dir)
        shutil.copytree(root_dir / "resources", package_dir / "resources")
        
        # Create quick start
        with open(package_dir / "QUICK_START.txt", 'w') as f:
            f.write("""AMI - Quick Start Guide
========================

1. Double-click AMI.exe
2. Look for the icon in your system tray (bottom-right)
3. Click the icon to open the dashboard
4. Right-click for settings

For more information, see README.md

© 2025 CiaoIM™ by Daniel Giovannetti
""")
        
        # Create ZIP
        shutil.make_archive(
            str(zip_path.with_suffix('')),
            'zip',
            dist_dir,
            'AMI-Package'
        )
        
        zip_size_mb = zip_path.stat().st_size / (1024 * 1024)
        print(f"✅ ZIP created: {zip_path}")
        print(f"Size: {zip_size_mb:.2f} MB")
        
        print("\n" + "=" * 60)
        print("✅ Build completed successfully!")
        print("=" * 60)
        print(f"\nYou can now:")
        print(f"1. Run {exe_path}")
        print(f"2. Distribute {zip_path}")
        print()
        
        return True
    else:
        print("\n✅ Spec files created!")
        print("\nTo build on Windows, run:")
        print("  python build_windows_installer.py")
        print("\nOr manually:")
        print(f"  pyinstaller --clean {spec_file}")
        return True

def create_nsis_installer(root_dir):
    """Create NSIS installer script"""
    
    nsis_script = """
; AMI Installer Script for NSIS
; Nullsoft Scriptable Install System

!define APP_NAME "AMI"
!define APP_VERSION "2.1.1"
!define APP_PUBLISHER "CiaoIM™ by Daniel Giovannetti"
!define APP_URL "https://github.com/dgiovannetti/AMI"
!define APP_EXE "AMI.exe"

Name "${APP_NAME} ${APP_VERSION}"
OutFile "AMI-Setup.exe"
InstallDir "$PROGRAMFILES64\\${APP_NAME}"
InstallDirRegKey HKLM "Software\\${APP_NAME}" "Install_Dir"
RequestExecutionLevel admin

!include "MUI2.nsh"

!define MUI_ABORTWARNING
!define MUI_ICON "resources\\ami.ico"
!define MUI_UNICON "resources\\ami.ico"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"

Section "Install"
  SetOutPath "$INSTDIR"
  
  File "dist\\AMI.exe"
  File "config.json"
  File "README.md"
  File "LICENSE"
  File "NOTICE"
  File /r "resources"
  
  WriteRegStr HKLM "Software\\${APP_NAME}" "Install_Dir" "$INSTDIR"
  WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}" "DisplayName" "${APP_NAME}"
  WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}" "UninstallString" '"$INSTDIR\\uninstall.exe"'
  WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}" "DisplayIcon" "$INSTDIR\\${APP_EXE}"
  WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}" "Publisher" "${APP_PUBLISHER}"
  WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}" "URLInfoAbout" "${APP_URL}"
  WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}" "DisplayVersion" "${APP_VERSION}"
  WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}" "NoModify" 1
  WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}" "NoRepair" 1
  WriteUninstaller "$INSTDIR\\uninstall.exe"
  
  CreateDirectory "$SMPROGRAMS\\${APP_NAME}"
  CreateShortcut "$SMPROGRAMS\\${APP_NAME}\\${APP_NAME}.lnk" "$INSTDIR\\${APP_EXE}"
  CreateShortcut "$SMPROGRAMS\\${APP_NAME}\\Uninstall.lnk" "$INSTDIR\\uninstall.exe"
  CreateShortcut "$DESKTOP\\${APP_NAME}.lnk" "$INSTDIR\\${APP_EXE}"
  
  WriteRegStr HKCU "Software\\Microsoft\\Windows\\CurrentVersion\\Run" "${APP_NAME}" "$INSTDIR\\${APP_EXE}"
SectionEnd

Section "Uninstall"
  DeleteRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}"
  DeleteRegKey HKLM "Software\\${APP_NAME}"
  DeleteRegValue HKCU "Software\\Microsoft\\Windows\\CurrentVersion\\Run" "${APP_NAME}"
  
  Delete "$INSTDIR\\AMI.exe"
  Delete "$INSTDIR\\config.json"
  Delete "$INSTDIR\\README.md"
  Delete "$INSTDIR\\LICENSE"
  Delete "$INSTDIR\\NOTICE"
  Delete "$INSTDIR\\uninstall.exe"
  RMDir /r "$INSTDIR\\resources"
  RMDir "$INSTDIR"
  
  Delete "$SMPROGRAMS\\${APP_NAME}\\*.*"
  RMDir "$SMPROGRAMS\\${APP_NAME}"
  Delete "$DESKTOP\\${APP_NAME}.lnk"
SectionEnd
"""
    
    nsis_file = root_dir / "installer.nsi"
    with open(nsis_file, 'w') as f:
        f.write(nsis_script)
    
    print(f"\n✅ Created {nsis_file}")
    print("\nTo create installer, run:")
    print(f"  makensis {nsis_file}")
    print("\nOr use NSIS GUI to compile the script")

if __name__ == "__main__":
    success = build_windows_exe()
    sys.exit(0 if success else 1)
