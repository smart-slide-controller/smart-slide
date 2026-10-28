# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path

import mediapipe


project_root = Path(SPECPATH)
mediapipe_root = Path(mediapipe.__file__).resolve().parent
datas = []

for asset_directory in ("hand_landmark", "palm_detection"):
    asset_path = mediapipe_root / "modules" / asset_directory
    if not asset_path.is_dir():
        raise FileNotFoundError(
            f"Required MediaPipe model assets were not found: {asset_path}"
        )
    datas.append(
        (str(asset_path), f"mediapipe/modules/{asset_directory}")
    )

a = Analysis(
    [str(project_root / "main.py")],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "mediapipe.python.solutions.hands",
        "mediapipe.python.solutions.hands_connections",
        "mediapipe.python.solutions.drawing_utils",
        "pythoncom",
        "pywintypes",
        "win32com.client",
    ],
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
    name="SmartPresentationController",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=os.environ.get("SPC_CONSOLE") == "1",
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
