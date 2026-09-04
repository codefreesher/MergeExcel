from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class SheetItem:
    source_path: Path
    source_sheet: str
    output_name: str
    selected: bool = True
    status: str = "Sẵn sàng"
    visible_state: str = "visible"


@dataclass
class MergeOptions:
    preserve_formatting: bool = True
    preserve_formulas: bool = True
    values_only: bool = False
    skip_empty_sheets: bool = False
    trim_leading_empty_rows: bool = False
    auto_resolve_duplicates: bool = True
    open_after_merge: bool = True


@dataclass
class MergeResult:
    output_path: Path
    file_count: int
    sheet_count: int
    elapsed_seconds: float
    warnings: list[str] = field(default_factory=list)

