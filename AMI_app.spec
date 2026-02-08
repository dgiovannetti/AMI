
# -*- mode: python ; coding: utf-8 -*-
# macOS .app bundle - Dock/menu bar show "AMI" instead of "Python"

import os

# Path for imports (AMI.py adds src to path and imports from main)
root = os.getcwd()
pathex = [root, os.path.join(root, 'src')]

block_cipher = None

a = Analysis(
    ['AMI.py'],
    pathex=pathex,
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
        'platformdirs',
        'core',
        'core.paths',
        'core.config',
        'core.models',
        'services',
        'services.network_monitor',
        'services.logger',
        'services.notifier',
        'services.api_server',
        'services.updater',
        'ui',
        'ui.tray_app',
        'ui.dashboard',
        'ui.splash_screen',
        'ui.settings_dialog',
        'ui.update_dialog',
        'ui.compact_status',
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
    icon='resources/ami.icns' if os.path.exists('resources/ami.icns') else 'resources/ami.png',
)

app = BUNDLE(
    exe,
    name='AMI.app',
    icon='resources/ami.icns' if os.path.exists('resources/ami.icns') else 'resources/ami.png',
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
