# -*- mode: python -*-
from PyInstaller.utils.hooks import collect_all

block_cipher = None

# Coleta TUDO do Streamlit e dependências
streamlit_data = collect_all('streamlit')
altair_data = collect_all('altair')
pyarrow_data = collect_all('pyarrow')

a = Analysis(
    ['wpaut.py'],
    pathex=[],
    binaries=streamlit_data[1] + altair_data[1] + pyarrow_data[1],
    datas=streamlit_data[0] + altair_data[0] + pyarrow_data[0],
    hiddenimports=streamlit_data[2] + altair_data[2] + pyarrow_data[2] + [
        'streamlit.web.cli',
        'streamlit.runtime',
        'streamlit.config'
    ],
    hookspath=[],
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
    name='wpaut',
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
    icon='wp.ico',
)