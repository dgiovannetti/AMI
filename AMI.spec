# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('C:\\Mac\\Home\\Documents\\github\\AMI\\config.json', '.')]
binaries = []
hiddenimports = ['ping3', 'matplotlib', 'numpy', 'requests', 'network_monitor', 'logger', 'notifier', 'api_server', 'dashboard', 'splash_screen', 'animated_button']
tmp_ret = collect_all('matplotlib')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['C:\\Mac\\Home\\Documents\\github\\AMI\\src\\tray_app.py'],
    pathex=['C:\\Mac\\Home\\Documents\\github\\AMI\\src'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
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
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['C:\\Mac\\Home\\Documents\\github\\AMI\\resources\\ami.ico'],
)
