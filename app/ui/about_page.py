from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QIcon
from pathlib import Path
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from app.config import APP_NAME, VERSION


class AboutPage(QWidget):
    check_update_requested = Signal()

    def __init__(self) -> None:
        super().__init__(); layout = QVBoxLayout(self); layout.setAlignment(Qt.AlignmentFlag.AlignCenter); layout.setSpacing(13)
        logo = QLabel(); logo.setPixmap(QIcon(str(Path(__file__).parent.parent / "resources" / "icons" / "app-logo.svg")).pixmap(78, 78)); logo.setAlignment(Qt.AlignmentFlag.AlignCenter); logo.setFixedSize(82, 82)
        layout.addWidget(logo, alignment=Qt.AlignmentFlag.AlignCenter)
        name = QLabel(APP_NAME); name.setStyleSheet("font-size:26px;font-weight:700"); layout.addWidget(name, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(QLabel(f"Phiên bản {VERSION}"), alignment=Qt.AlignmentFlag.AlignCenter)
        text = QLabel("Công cụ giúp bạn ghép nhiều file Excel\nthành một file duy nhất, nhanh chóng và dễ dàng."); text.setAlignment(Qt.AlignmentFlag.AlignCenter); text.setStyleSheet("color:#657188;font-size:14px"); layout.addWidget(text)
        actions = QHBoxLayout()
        update = QPushButton("Kiểm tra cập nhật")
        update.clicked.connect(self.check_update_requested)
        telegram_icon = Path(__file__).parent.parent / "resources" / "icons" / "telegram.svg"
        contact = QPushButton(QIcon(str(telegram_icon)), "Liên hệ Telegram", objectName="primary")
        contact.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://t.me/PandalamDEV")))
        actions.addWidget(update)
        actions.addWidget(contact)
        layout.addLayout(actions)
        layout.addWidget(QLabel("Copyright 2026 PandalamDEV"), alignment=Qt.AlignmentFlag.AlignCenter)
