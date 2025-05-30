# rembg_gui.spec
# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

# Add the source directory to Python path
spec_dir = Path(SPECPATH)
sys.path.insert(0, str(spec_dir))

block_cipher = None

# Define the main script
main_script = 'main.py'

# Data files to include
datas = [
    # Include config files
    ('config/*.py', 'config'),
    # Include any additional data files you might have
    # ('assets/*', 'assets'),  # Uncomment if you have assets
]

# Hidden imports - modules that PyInstaller might miss
hiddenimports = [
    'rembg',
    'PIL',
    'PIL._tkinter_finder',
    'cv2',
    'onnxruntime',
    'psutil',
    'numpy',
    'tkinter',
    'tkinter.ttk',
    'tkinter.filedialog',
    'tkinter.messagebox',
    'tkinter.scrolledtext',
    # Core modules
    'core.processor',
    'core.session_manager', 
    'core.video_handler',
    # GUI modules
    'gui.main_window',
    'gui.components',
    'gui.preview_canvas',
    # Utils modules
    'utils.file_utils',
    'utils.logging_utils',
    'utils.system_utils',
    # Config modules
    'config.models',
    'config.settings',
    # ONNX providers
    'onnxruntime.capi.onnxruntime_providers_shared',
    'onnxruntime.capi.onnxruntime_providers_cuda',
]

# Binaries to exclude (optional, to reduce size)
excludes = [
    'matplotlib',
    'IPython',
    'jupyter',
    'notebook',
    'pytest',
    'sphinx',
]

a = Analysis(
    [main_script],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyi_splash = Splash(
    'splash.png',  # Create a splash screen image (optional)
    binaries=a.binaries,
    datas=a.datas,
    text_pos=None,
    text_size=12,
    minify_script=True,
    always_on_top=True,
)

pyx = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyx,
    a.scripts,
    [],
    exclude_binaries=True,
    name='rembg_gui',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Set to True for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',  # Add your icon file here
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    pyi_splash.binaries if 'pyi_splash' in locals() else [],
    strip=False,
    upx=True,
    upx_exclude=[],
    name='rembg_gui',
)
