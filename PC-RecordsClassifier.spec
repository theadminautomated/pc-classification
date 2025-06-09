# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['N:\\IT Ops\\Product_Support_Documentation\\M365 Administration\\Records\\RecordsClassifierGui\\app_gui.py'],
    pathex=[],
    binaries=[],
    datas=[('N:\\IT Ops\\Product_Support_Documentation\\M365 Administration\\Records\\RecordsClassifierGui', 'RecordsClassifierGui'), ('N:\\IT Ops\\Product_Support_Documentation\\M365 Administration\\Records\\pierce-county-records-classifier-phi2', 'pierce-county-records-classifier-phi2'), ('N:\\IT Ops\\Product_Support_Documentation\\M365 Administration\\Records\\installer', 'installer')],
    hiddenimports=[],
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
    name='PC-RecordsClassifier',
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
    icon=['N:\\IT Ops\\Product_Support_Documentation\\M365 Administration\\Records\\RecordsClassifierGui\\app.ico'],
)
