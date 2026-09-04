from __future__ import annotations

import os
import sys
from pathlib import Path

APP_NAME = "Excel Merger Pro"
APP_ID = "ExcelMergerPro"
VERSION = "1.0.0"
UPDATE_URL = "https://raw.githubusercontent.com/codefreesher/MergeExcel/main/update.json"
SUPPORTED_EXTENSIONS = {".xlsx", ".xlsm"}
EXCEL_MAX_SHEET_NAME = 31


def app_data_dir() -> Path:
    if sys.platform == "win32":
        base = Path(os.getenv("LOCALAPPDATA") or os.getenv("APPDATA") or Path.home())
    else:
        base = Path(os.getenv("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    path = base / APP_ID
    path.mkdir(parents=True, exist_ok=True)
    return path


def default_output_dir() -> Path:
    return Path.home() / "Documents" / APP_NAME
