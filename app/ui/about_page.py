from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from app.config import APP_NAME, VERSION


class AboutPage(QWidget):
    check_update_requested = Signal()

    def __init__(self) -> None:
        super().__init__(); layout = QVBoxLayout(self); layout.setAlignment(Qt.AlignmentFlag.AlignCenter); layout.setSpacing(13)
        logo = QLabel("X"); logo.setAlignment(Qt.AlignmentFlag.AlignCenter); logo.setFixedSize(74, 74); logo.setStyleSheet("font-size:38px;font-weight:800;color:white;background:#246bfd;border-radius:16px")
        layout.addWidget(logo, alignment=Qt.AlignmentFlag.AlignCenter)
        name = QLabel(APP_NAME); name.setStyleSheet("font-size:26px;font-weight:700"); layout.addWidget(name, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(QLabel(f"Phiên bản {VERSION}"), alignment=Qt.AlignmentFlag.AlignCenter)
        text = QLabel("Công cụ giúp bạn ghép nhiều file Excel\nthành một file duy nhất, nhanh chóng và dễ dàng."); text.setAlignment(Qt.AlignmentFlag.AlignCenter); text.setStyleSheet("color:#657188;font-size:14px"); layout.addWidget(text)
        update = QPushButton("Kiểm tra cập nhật"); update.clicked.connect(self.check_update_requested); layout.addWidget(update, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(QLabel("Copyright 2026 Excel Merger Pro"), alignment=Qt.AlignmentFlag.AlignCenter)

