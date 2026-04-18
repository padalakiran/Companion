# DesktopCatCompanion.spec

import sys
from pathlib import Path

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('assets', 'assets'),
        ('characters', 'characters'),
    ],
    hiddenimports=[
        'updater',
        'tkinter',
        'tkinter.font',
        'tkinter.ttk',
        'PIL.Image',
        'PIL.ImageTk',
        'PIL.ImageDraw',
        'openpyxl',
        'openpyxl.styles',
        'openpyxl.utils',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'pytest',
        'ruff',
        'setuptools',
        'pip',
    ],
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
    upx=True,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='DesktopCatCompanion',
)
