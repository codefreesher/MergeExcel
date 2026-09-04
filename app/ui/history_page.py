from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QMessageBox, QPushButton,
                               QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)


class HistoryPage(QWidget):
    def __init__(self, history) -> None:
        super().__init__(); self.history = history
        layout = QVBoxLayout(self); layout.setContentsMargins(28, 22, 28, 22)
        header = QHBoxLayout(); header.addWidget(QLabel("LỊCH SỬ XỬ LÝ", objectName="pageTitle")); header.addStretch()
        clear = QPushButton("Xóa lịch sử", objectName="danger"); clear.clicked.connect(self.clear_history); header.addWidget(clear)
        layout.addLayout(header)
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["Thời gian", "Tên file output", "Số file", "Số sheet", "Trạng thái", "Thời gian", "Thao tác"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table); self.refresh()

    def refresh(self) -> None:
        rows = self.history.list_recent(); self.table.setRowCount(len(rows))
        for index, row in enumerate(rows):
            path = Path(row["output_path"])
            values = [row["created_at"].replace("T", " "), path.name, str(row["file_count"]),
                      str(row["sheet_count"]), row["status"], f'{row["elapsed_seconds"]:.1f}s']
            for column, value in enumerate(values): self.table.setItem(index, column, QTableWidgetItem(value))
            button = QPushButton("Mở file")
            button.setEnabled(path.exists())
            button.clicked.connect(lambda _=False, p=path: QDesktopServices.openUrl(QUrl.fromLocalFile(str(p))))
            self.table.setCellWidget(index, 6, button)

    def clear_history(self) -> None:
        if QMessageBox.question(self, "Xóa lịch sử", "Xóa toàn bộ lịch sử xử lý?") == QMessageBox.StandardButton.Yes:
            self.history.clear(); self.refresh()

