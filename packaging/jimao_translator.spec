# PyInstaller spec for Jimao Translator
# Build: pyinstaller packaging/jimao_translator.spec
#
# Produces a one-folder bundle under `dist/jimao_translator/` containing the
# executable + PySide6 plugins + all collected data files. One-folder is
# preferred over one-file for portability — avoids the startup overhead of
# extracting to a temp dir and plays nicely with antivirus scanners.

# ruff: noqa

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

hidden_imports = []
hidden_imports += collect_submodules("edge_tts")
hidden_imports += collect_submodules("anthropic")
hidden_imports += collect_submodules("speech_recognition")

datas = []
datas += collect_data_files("edge_tts")
datas += collect_data_files("speech_recognition")
datas += collect_data_files("langdetect")


a = Analysis(
    ["../src/jimao_translator/main.py"],
    pathex=["../src"],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "unittest", "pytest"],
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
    name="jimao-translator",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
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
    name="jimao_translator",
)
