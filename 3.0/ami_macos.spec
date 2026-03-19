# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec: macOS .app bundle for AMI 3.x.
Avoids Gatekeeper showing "Python" as the app name (proper CFBundleName / bundle).
"""
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_all

# Repo root = directory containing this spec (3.0/)
_sp = SPECPATH
ROOT = Path(_sp[0] if isinstance(_sp, (list, tuple)) else _sp)
SRC = ROOT / "src"
RES = ROOT / "resources"
MAIN = SRC / "ami" / "main.py"
CFG = ROOT / "config.json"
SCHEMA = ROOT / "config.schema.json"

# Version from package (single source)
sys.path.insert(0, str(SRC))
from ami import __version__ as AMI_VERSION  # noqa: E402

matplotlib_datas, matplotlib_binaries, matplotlib_hiddenimports = collect_all("matplotlib")

block_cipher = None

datas = [
    (str(CFG), "."),
]
if SCHEMA.exists():
    datas.append((str(SCHEMA), "."))
if RES.exists():
    datas.append((str(RES), "resources"))
datas += matplotlib_datas

a = Analysis(
    [str(MAIN)],
    pathex=[str(SRC)],
    binaries=matplotlib_binaries,
    datas=datas,
    hiddenimports=[
        "ami",
        "ami.core",
        "ami.core.config",
        "ami.core.models",
        "ami.core.paths",
        "ami.services",
        "ami.services.network_monitor",
        "ami.services.logger",
        "ami.services.notifier",
        "ami.services.api_server",
        "ami.services.updater",
        "ami.services.speed_test",
        "ami.ui",
        "ami.ui.tray_app",
        "ami.ui.dashboard",
        "ami.ui.splash_screen",
        "ami.ui.settings_dialog",
        "ami.ui.update_dialog",
        "ami.ui.compact_status",
        "ami.ui.themes",
        "ping3",
        "matplotlib",
        "numpy",
    ]
    + matplotlib_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # Evita dipendenze pesanti opzionali (riduce .so / warning SDK su CI; matplotlib QtAgg non richiede scipy)
    excludes=["scipy", "pandas", "IPython", "jupyter"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="AMI",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="AMI",
)

app = BUNDLE(
    coll,
    name="AMI.app",
    icon=None,
    bundle_identifier="tech.ciaoim.ami",
    info_plist={
        "CFBundleName": "AMI",
        "CFBundleDisplayName": "AMI — Active Monitor of Internet",
        "CFBundleIdentifier": "tech.ciaoim.ami",
        "CFBundleVersion": AMI_VERSION,
        "CFBundleShortVersionString": AMI_VERSION,
        "CFBundlePackageType": "APPL",
        "NSHighResolutionCapable": True,
        "LSMinimumSystemVersion": "10.14",
        "NSHumanReadableCopyright": "Copyright © 2025–2026 CiaoIM™",
        # Tray + dashboard: show in Dock when windows are used
        "LSUIElement": False,
    },
)
