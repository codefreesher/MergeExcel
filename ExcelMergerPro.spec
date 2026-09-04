# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

root = Path(SPECPATH)
a = Analysis(
    [str(root / "main.py")], pathex=[str(root)],
    binaries=[],
    datas=[(str(root / "app" / "resources"), "app/resources")],
    hiddenimports=["openpyxl", "PIL"], hookspath=[], hooksconfig={}, runtime_hooks=[],
    excludes=[], noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name="ExcelMergerPro",
          debug=False, bootloader_ignore_signals=False, strip=False, upx=True,
          console=False, icon=None)

