from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot

from app.core.excel_merger import ExcelMerger
from app.core.models import MergeOptions, SheetItem


class MergeWorker(QObject):
    progress = Signal(int, int, str)
    completed = Signal(object)
    failed = Signal(str)
    finished = Signal()

    def __init__(self, items: list[SheetItem], output: Path, options: MergeOptions) -> None:
        super().__init__()
        self.items, self.output, self.options = items, output, options
        self._cancelled = False

    @Slot()
    def run(self) -> None:
        try:
            result = ExcelMerger().merge(self.items, self.output, self.options,
                                         self.progress.emit, lambda: self._cancelled)
            self.completed.emit(result)
        except Exception as exc:
            self.failed.emit(str(exc))
        finally:
            self.finished.emit()

    @Slot()
    def cancel(self) -> None:
        self._cancelled = True

