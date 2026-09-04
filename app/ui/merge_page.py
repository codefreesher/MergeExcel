from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThread, Qt, Signal
from PySide6.QtGui import QAction, QDesktopServices, QKeySequence, QShortcut
from PySide6.QtCore import QUrl
from PySide6.QtWidgets import (QAbstractItemView, QCheckBox, QFileDialog, QFrame,
    QGridLayout, QHBoxLayout, QLabel, QLineEdit, QMenu, QMessageBox, QProgressBar,
    QPushButton, QScrollArea, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

from app.config import default_output_dir
from app.core.excel_merger import unique_sheet_name, validate_sheet_name
from app.core.excel_reader import ExcelReadError, read_workbook_sheets
from app.core.models import MergeOptions, MergeResult, SheetItem
from app.widgets.file_drop_area import FileDropArea
from app.workers.merge_worker import MergeWorker


def card(title: str) -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame(objectName="card")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(16, 13, 16, 15)
    layout.setSpacing(10)
    header = QHBoxLayout()
    number, _, caption = title.partition(".")
    badge = QLabel(number.strip(), objectName="stepBadge")
    badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
    label = QLabel(caption.strip() or title, objectName="sectionTitle")
    header.addWidget(badge); header.addWidget(label); header.addStretch()
    layout.addLayout(header)
    return frame, layout


class MergePage(QWidget):
    toast_requested = Signal(str)
    merge_completed = Signal(object)

    def __init__(self, settings) -> None:
        super().__init__()
        self.settings = settings
        self.items: list[SheetItem] = []
        self._thread: QThread | None = None
        self._worker: MergeWorker | None = None
        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 22, 28, 22)
        outer.addWidget(QLabel("GHÉP CÁC FILE EXCEL THÀNH 1 FILE", objectName="pageTitle"))
        scroll = QScrollArea(widgetResizable=True)
        container = QWidget(objectName="scrollBody")
        self.body = QVBoxLayout(container)
        self.body.setContentsMargins(0, 10, 8, 10)
        self.body.setSpacing(12)
        self.body.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(container)
        outer.addWidget(scroll)

        file_card, file_layout = card("1. Chọn các file Excel cần ghép")
        self.drop_area = FileDropArea()
        self.drop_area.browse_requested.connect(self.browse)
        self.drop_area.files_dropped.connect(self.add_files)
        self.drop_area.rejected.connect(self.toast_requested)
        file_layout.addWidget(self.drop_area)
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Chọn", "Tên file", "Sheet nguồn", "Tên sheet đầu ra", "Trạng thái", "Xóa"])
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.horizontalHeader().setSectionResizeMode(1, self.table.horizontalHeader().ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, self.table.horizontalHeader().ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setMinimumHeight(150)
        self.table.setMaximumHeight(245)
        self.table.verticalHeader().setDefaultSectionSize(34)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.context_menu)
        self.table.itemChanged.connect(self._item_changed)
        file_layout.addWidget(self.table)
        controls = QHBoxLayout()
        for text, callback in (("Thêm file", self.browse), ("Chọn tất cả", lambda: self.select_all(True)),
                               ("Bỏ chọn tất cả", lambda: self.select_all(False)), ("Xóa tất cả", self.clear_all)):
            button = QPushButton(text)
            button.clicked.connect(callback)
            controls.addWidget(button)
        controls.addStretch()
        for text, delta in (("Lên", -1), ("Xuống", 1)):
            button = QPushButton(text)
            button.clicked.connect(lambda _=False, d=delta: self.move_row(d))
            controls.addWidget(button)
        file_layout.addLayout(controls)
        self.body.addWidget(file_card)

        output_card, output_layout = card("2. Tùy chọn đầu ra")
        grid = QGridLayout()
        grid.addWidget(QLabel("Tên file output"), 0, 0)
        self.output_name = QLineEdit("Tong_hop.xlsx")
        grid.addWidget(self.output_name, 0, 1, 1, 2)
        grid.addWidget(QLabel("Thư mục lưu"), 1, 0)
        self.output_dir = QLineEdit(self.settings.get("last_output_dir", str(default_output_dir())))
        grid.addWidget(self.output_dir, 1, 1)
        choose = QPushButton("Chọn thư mục")
        choose.clicked.connect(self.choose_output)
        grid.addWidget(choose, 1, 2)
        output_layout.addLayout(grid)
        self.body.addWidget(output_card)

        advanced_card, advanced = card("3. Tùy chọn nâng cao")
        grid = QGridLayout()
        labels = [
            ("name_from_file", "Đặt tên sheet theo tên file", True),
            ("skip_empty", "Bỏ qua các sheet trống", False),
            ("preserve_format", "Giữ nguyên định dạng", True),
            ("preserve_formula", "Giữ nguyên công thức", True),
            ("values_only", "Chỉ lấy giá trị, không lấy công thức", False),
            ("auto_duplicates", "Tự xử lý tên sheet bị trùng", True),
            ("trim_rows", "Bỏ qua dòng trống ở đầu mỗi sheet", False),
            ("open_after", "Mở file sau khi ghép xong", self.settings.get("open_after_merge", True)),
        ]
        self.options: dict[str, QCheckBox] = {}
        for index, (key, text, checked) in enumerate(labels):
            checkbox = QCheckBox(text)
            checkbox.setChecked(checked)
            self.options[key] = checkbox
            grid.addWidget(checkbox, index // 2, index % 2)
        self.options["preserve_formula"].toggled.connect(lambda checked: self.options["values_only"].setChecked(not checked))
        self.options["values_only"].toggled.connect(lambda checked: self.options["preserve_formula"].setChecked(not checked))
        self.options["name_from_file"].toggled.connect(self.apply_suggested_names)
        advanced.addLayout(grid)
        self.body.addWidget(advanced_card)

        self.progress_label = QLabel()
        self.progress = QProgressBar()
        self.progress.hide(); self.progress_label.hide()
        self.body.addWidget(self.progress_label)
        self.body.addWidget(self.progress)
        actions = QHBoxLayout()
        self.cancel_button = QPushButton("Hủy")
        self.cancel_button.hide()
        self.cancel_button.clicked.connect(self.cancel_merge)
        self.merge_button = QPushButton("GHÉP FILE NGAY", objectName="primary")
        self.merge_button.setMinimumHeight(46)
        self.merge_button.setEnabled(False)
        self.merge_button.clicked.connect(self.start_merge)
        actions.addStretch(); actions.addWidget(self.cancel_button); actions.addWidget(self.merge_button, 3); actions.addStretch()
        self.body.addLayout(actions)
        QShortcut(QKeySequence("Ctrl+O"), self, self.browse)
        QShortcut(QKeySequence("Ctrl+Return"), self, self.start_merge)
        QShortcut(QKeySequence("Delete"), self, self.remove_current)

    def browse(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(self, "Chọn file Excel", "", "Excel (*.xlsx *.xlsm)")
        self.add_files([Path(path) for path in paths])

    def add_files(self, paths: list[Path]) -> None:
        existing = {item.source_path.resolve() for item in self.items}
        added = 0
        for path in paths:
            if path.resolve() in existing:
                continue
            try:
                new_items = read_workbook_sheets(path)
                self.items.extend(new_items); added += 1; existing.add(path.resolve())
            except ExcelReadError as exc:
                QMessageBox.warning(self, "Không thể đọc file", f"{path.name}\n\n{exc}")
        self.apply_suggested_names()
        self.refresh_table()
        if added:
            self.toast_requested.emit(f"Đã thêm {added} file Excel")

    def apply_suggested_names(self) -> None:
        if not self.items:
            return
        used: set[str] = set()
        by_file: dict[Path, list[SheetItem]] = {}
        for item in self.items:
            by_file.setdefault(item.source_path, []).append(item)
        for path, group in by_file.items():
            for item in group:
                proposed = f"{path.stem}_{item.source_sheet}" if len(group) > 1 else path.stem
                if not self.options["name_from_file"].isChecked():
                    proposed = item.source_sheet
                item.output_name = unique_sheet_name(proposed, used)
                used.add(item.output_name)
        self.refresh_table()

    def refresh_table(self) -> None:
        self.table.blockSignals(True)
        self.table.setRowCount(len(self.items))
        for row, item in enumerate(self.items):
            chosen = QTableWidgetItem()
            chosen.setCheckState(Qt.CheckState.Checked if item.selected else Qt.CheckState.Unchecked)
            chosen.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsUserCheckable)
            self.table.setItem(row, 0, chosen)
            for col, text in ((1, item.source_path.name), (2, item.source_sheet), (3, item.output_name), (4, item.status)):
                cell = QTableWidgetItem(text)
                if col != 3: cell.setFlags(cell.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row, col, cell)
            delete = QPushButton("Xóa", objectName="danger")
            delete.clicked.connect(lambda _=False, r=row: self.remove_row(r))
            self.table.setCellWidget(row, 5, delete)
        self.table.blockSignals(False)
        self.merge_button.setEnabled(any(item.selected for item in self.items) and self._thread is None)

    def _item_changed(self, cell: QTableWidgetItem) -> None:
        if cell.row() >= len(self.items): return
        item = self.items[cell.row()]
        if cell.column() == 0:
            item.selected = cell.checkState() == Qt.CheckState.Checked
        elif cell.column() == 3:
            error = validate_sheet_name(cell.text())
            if error:
                cell.setToolTip(error); cell.setBackground(Qt.GlobalColor.red)
            else:
                item.output_name = cell.text().strip(); cell.setToolTip("")
        self.merge_button.setEnabled(any(x.selected for x in self.items))

    def select_all(self, selected: bool) -> None:
        for item in self.items: item.selected = selected
        self.refresh_table()

    def clear_all(self) -> None:
        self.items.clear(); self.refresh_table()

    def remove_current(self) -> None:
        self.remove_row(self.table.currentRow())

    def remove_row(self, row: int) -> None:
        if 0 <= row < len(self.items):
            self.items.pop(row); self.refresh_table(); self.toast_requested.emit("Đã xóa sheet khỏi danh sách")

    def move_row(self, delta: int) -> None:
        row = self.table.currentRow(); target = row + delta
        if 0 <= row < len(self.items) and 0 <= target < len(self.items):
            self.items[row], self.items[target] = self.items[target], self.items[row]
            self.refresh_table(); self.table.selectRow(target)

    def context_menu(self, position) -> None:
        row = self.table.rowAt(position.y())
        if row < 0: return
        menu = QMenu(self)
        open_action = menu.addAction("Mở file")
        folder_action = menu.addAction("Mở thư mục chứa file")
        menu.addSeparator()
        up = menu.addAction("Di chuyển lên"); down = menu.addAction("Di chuyển xuống")
        remove = menu.addAction("Xóa khỏi danh sách")
        action = menu.exec(self.table.viewport().mapToGlobal(position))
        if action == open_action: QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.items[row].source_path)))
        elif action == folder_action: QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.items[row].source_path.parent)))
        elif action == up: self.table.selectRow(row); self.move_row(-1)
        elif action == down: self.table.selectRow(row); self.move_row(1)
        elif action == remove: self.remove_row(row)

    def choose_output(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Chọn thư mục lưu", self.output_dir.text())
        if folder: self.output_dir.setText(folder)

    def start_merge(self) -> None:
        selected = [item for item in self.items if item.selected]
        errors = [(item.output_name, validate_sheet_name(item.output_name)) for item in selected]
        errors = [f"{name}: {error}" for name, error in errors if error]
        if errors:
            QMessageBox.warning(self, "Tên sheet không hợp lệ", "\n".join(errors[:5])); return
        name = self.output_name.text().strip() or "Tong_hop.xlsx"
        if not name.lower().endswith(".xlsx"): name += ".xlsx"
        output = Path(self.output_dir.text().strip()) / name
        options = MergeOptions(self.options["preserve_format"].isChecked(), self.options["preserve_formula"].isChecked(),
            self.options["values_only"].isChecked(), self.options["skip_empty"].isChecked(),
            self.options["trim_rows"].isChecked(), self.options["auto_duplicates"].isChecked(),
            self.options["open_after"].isChecked())
        self._thread = QThread(self)
        self._worker = MergeWorker(list(selected), output, options)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self.on_progress)
        self._worker.completed.connect(self.on_completed)
        self._worker.failed.connect(self.on_failed)
        self._worker.finished.connect(self._thread.quit)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.finished.connect(self._reset_worker)
        self.progress.show(); self.progress_label.show(); self.cancel_button.show()
        self.merge_button.setEnabled(False); self.merge_button.setText("Đang xử lý...")
        self._thread.start()

    def on_progress(self, current: int, total: int, filename: str) -> None:
        self.progress.setValue(int(current * 100 / total))
        self.progress_label.setText(f"Đang xử lý {current}/{total}: {filename}")

    def on_completed(self, result: MergeResult) -> None:
        self.merge_completed.emit(result)
        if self.options["open_after"].isChecked(): QDesktopServices.openUrl(QUrl.fromLocalFile(str(result.output_path)))
        box = QMessageBox(self); box.setWindowTitle("Ghép Excel thành công")
        box.setIcon(QMessageBox.Icon.Information)
        box.setText(f"Đã ghép {result.file_count} file, {result.sheet_count} sheet trong {result.elapsed_seconds:.1f} giây.\n\n{result.output_path}")
        open_file = box.addButton("Mở file", QMessageBox.ButtonRole.ActionRole)
        open_folder = box.addButton("Mở thư mục", QMessageBox.ButtonRole.ActionRole)
        box.addButton("Đóng", QMessageBox.ButtonRole.RejectRole); box.exec()
        if box.clickedButton() == open_file: QDesktopServices.openUrl(QUrl.fromLocalFile(str(result.output_path)))
        elif box.clickedButton() == open_folder: QDesktopServices.openUrl(QUrl.fromLocalFile(str(result.output_path.parent)))

    def on_failed(self, message: str) -> None:
        QMessageBox.critical(self, "Không thể ghép Excel", message)

    def cancel_merge(self) -> None:
        if self._worker: self._worker.cancel(); self.cancel_button.setEnabled(False)

    def _reset_worker(self) -> None:
        self._thread = None; self._worker = None
        self.progress.hide(); self.progress_label.hide(); self.cancel_button.hide(); self.cancel_button.setEnabled(True)
        self.merge_button.setText("GHÉP FILE NGAY"); self.refresh_table()
