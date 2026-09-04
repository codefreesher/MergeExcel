from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout

from app.config import SUPPORTED_EXTENSIONS


class FileDropArea(QFrame):
    files_dropped = Signal(list)
    browse_requested = Signal()
    rejected = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setAcceptDrops(True)
        self.setMinimumHeight(135)
        self.setStyleSheet("QFrame{border:2px dashed #b7c4d8;border-radius:10px;background:#fbfcfe} QFrame[dragging=true]{border-color:#246bfd;background:#eef5ff}")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title = QLabel("Kéo và thả file Excel vào đây")
        title.setStyleSheet("font-size:15px;font-weight:600;border:0;background:transparent")
        subtitle = QLabel("Hỗ trợ .xlsx và .xlsm")
        subtitle.setStyleSheet("color:#718096;border:0;background:transparent")
        button = QPushButton("Chọn file")
        button.clicked.connect(self.browse_requested)
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(button, alignment=Qt.AlignmentFlag.AlignCenter)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        paths = [Path(url.toLocalFile()) for url in event.mimeData().urls()]
        if paths and any(path.suffix.lower() in SUPPORTED_EXTENSIONS for path in paths):
            event.acceptProposedAction()
            self.setProperty("dragging", True)
            self.style().polish(self)

    def dragLeaveEvent(self, event) -> None:
        self.setProperty("dragging", False)
        self.style().polish(self)
        super().dragLeaveEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:
        self.setProperty("dragging", False)
        self.style().polish(self)
        valid, invalid = [], []
        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())
            (valid if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS else invalid).append(path)
        if invalid:
            self.rejected.emit(f"File {invalid[0].name} không được hỗ trợ.")
        if valid:
            self.files_dropped.emit(valid)
            event.acceptProposedAction()

