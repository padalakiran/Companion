# DesktopCatCompanion.spec
# PyInstaller spec file — controls exactly what goes into the .exe bundle
#
# Run with:  pyinstaller DesktopCatCompanion.spec
# Or use the build.bat / build command from the README

import sys
from pathlib import Path

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    # Bundle the assets/ and characters/ folders into the package
    datas=[
        ('assets',     'assets'),
        ('characters', 'characters'),
    ],
    hiddenimports=[
        'updater',
        # tkinter sub-modules PyInstaller sometimes misses
        'tkinter',
        'tkinter.font',
        'tkinter.ttk',
        # PIL sub-modules
        'PIL.Image',
        'PIL.ImageTk',
        'PIL.ImageDraw',
        # openpyxl internals
        'openpyxl',
        'openpyxl.styles',
        'openpyxl.utils',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude heavy unused packages to keep .exe smaller
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'pytest',
        'ruff',
        'setuptools',
        'pip',
    ],
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
    name='DesktopCatCompanion',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,                          # compress if UPX available — smaller .exe
    console=False,                     # --windowed: no console window on launch
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='version_info.txt',        # embeds Windows .exe metadata
    # icon='icon.ico',                 # uncomment when icon.ico is ready
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='DesktopCatCompanion',        # output folder name in dist/
)
