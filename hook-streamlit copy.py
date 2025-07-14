from PyInstaller.utils.hooks import collect_all, copy_metadata

datas = copy_metadata('streamlit')
binaries, hiddenimports = [], []

# Coleta tudo do Streamlit e dependências críticas
for pkg in ['streamlit', 'altair', 'pyarrow', 'numpy']:
    a, b, c = collect_all(pkg)
    datas += a
    binaries += b
    hiddenimports += c

hiddenimports += [
    'streamlit.web.cli',
    'streamlit.runtime',
    'pandas',
    'plotly'
]