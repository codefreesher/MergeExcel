from __future__ import annotations

from pathlib import Path

from openpyxl import load_workbook

from app.config import SUPPORTED_EXTENSIONS
from app.core.models import SheetItem


class ExcelReadError(Exception):
    pass


def read_workbook_sheets(path: Path) -> list[SheetItem]:
    path = Path(path)
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ExcelReadError(f"Định dạng {path.suffix or 'không xác định'} không được hỗ trợ.")
    try:
        workbook = load_workbook(path, read_only=True, data_only=False, keep_links=True)
        items = [SheetItem(path, sheet.title, sheet.title, visible_state=sheet.sheet_state)
                 for sheet in workbook.worksheets]
        workbook.close()
        return items
    except PermissionError as exc:
        raise ExcelReadError("Không có quyền đọc file. Hãy đóng file trong Excel rồi thử lại.") from exc
    except Exception as exc:
        raise ExcelReadError(f"Không thể đọc workbook: {exc}") from exc

