# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[('C:\\Users\\satya\\AppData\\Local\\Programs\\Python\\Python312\\Lib\\site-packages\\PyQt5\\Qt5\\bin\\Qt5Core.dll', '.'), ('C:\\Users\\satya\\AppData\\Local\\Programs\\Python\\Python312\\Lib\\site-packages\\PyQt5\\Qt5\\bin\\Qt5Gui.dll', '.'), ('C:\\Users\\satya\\AppData\\Local\\Programs\\Python\\Python312\\Lib\\site-packages\\PyQt5\\Qt5\\bin\\Qt5Widgets.dll', '.'), ('C:\\Users\\satya\\AppData\\Local\\Programs\\Python\\Python312\\Lib\\site-packages\\PyQt5\\Qt5\\bin\\Qt5Network.dll', '.'), ('C:\\Users\\satya\\AppData\\Local\\Programs\\Python\\Python312\\Lib\\site-packages\\PyQt5\\Qt5\\bin\\msvcp140.dll', '.'), ('C:\\Users\\satya\\AppData\\Local\\Programs\\Python\\Python312\\Lib\\site-packages\\PyQt5\\Qt5\\bin\\vcruntime140.dll', '.'), ('C:\\Users\\satya\\AppData\\Local\\Programs\\Python\\Python312\\Lib\\site-packages\\PyQt5\\Qt5\\bin\\vcruntime140_1.dll', '.')],
    datas=[('browser_extensions', 'browser_extensions')],
    hiddenimports=['PyQt5.QtCore', 'PyQt5.QtGui', 'PyQt5.QtWidgets', 'PyQt5.sip'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='PyDownloadManager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['browser_extensions\\chrome\\icons\\icon128.png'],
)
