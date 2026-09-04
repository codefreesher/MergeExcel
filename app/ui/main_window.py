from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (QButtonGroup, QFrame, QHBoxLayout, QLabel, QMainWindow,
                               QMessageBox, QPushButton, QStackedWidget, QVBoxLayout, QWidget)

from app.config import APP_NAME, VERSION
from app.core.history_manager import HistoryManager
from app.core.settings_manager import SettingsManager
from app.core.updater import Updater
from app.ui.about_page import AboutPage
from app.ui.history_page import HistoryPage
from app.ui.merge_page import MergePage
from app.ui.settings_page import SettingsPage
from app.ui.update_dialog import UpdateDialog
from app.widgets.toast import Toast


class UpdateCheckThread(QThread):
    found = Signal(object); current = Signal(); failed = Signal(str)
    def __init__(self, updater): super().__init__(); self.updater = updater
    def run(self):
        try:
            info = self.updater.check()
            self.found.emit(info) if info else self.current.emit()
        except Exception as exc: self.failed.emit(str(exc))


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__(); self.settings = SettingsManager(); self.history = HistoryManager(); self.updater = Updater(); self.update_thread = None
        self.setWindowTitle(f"{APP_NAME} {VERSION}"); self.resize(1280, 800); self.setMinimumSize(1050, 680)
        root = QWidget(objectName="content"); self.setCentralWidget(root); main = QHBoxLayout(root); main.setContentsMargins(0, 0, 0, 0); main.setSpacing(0)
        sidebar = QFrame(objectName="sidebar"); sidebar.setFixedWidth(222); side = QVBoxLayout(sidebar); side.setContentsMargins(14, 20, 14, 18); side.setSpacing(7)
        brand_row = QHBoxLayout(); logo = QLabel("X"); logo.setFixedSize(32, 32); logo.setStyleSheet("font-size:18px;font-weight:800;color:white;background:#246bfd;border-radius:7px"); logo.setAlignment(Qt.AlignmentFlag.AlignCenter); brand_row.addWidget(logo); brand_row.addWidget(QLabel(APP_NAME, objectName="brand")); side.addLayout(brand_row); side.addSpacing(22)
        self.stack = QStackedWidget(); self.merge_page = MergePage(self.settings); self.history_page = HistoryPage(self.history); self.settings_page = SettingsPage(self.settings); self.about_page = AboutPage()
        for page in (self.merge_page, self.history_page, self.settings_page, self.about_page): self.stack.addWidget(page)
        names = [("Ghép Excel", "spreadsheet.svg"), ("Lịch sử", "history.svg"), ("Cài đặt", "settings.svg"), ("Giới thiệu", "info.svg")]
        group = QButtonGroup(self); group.setExclusive(True); icon_dir = Path(__file__).parent.parent / "resources" / "icons"
        for index, (name, icon) in enumerate(names):
            button = QPushButton(QIcon(str(icon_dir / icon)), name, objectName="nav"); button.setCheckable(True); button.clicked.connect(lambda _=False, i=index: self.show_page(i)); group.addButton(button); side.addWidget(button)
            if index == 0: button.setChecked(True)
        side.addStretch(); side.addWidget(QLabel(f"{APP_NAME}\nPhiên bản {VERSION}"))
        self.update_status = QLabel("Đang chờ kiểm tra cập nhật"); self.update_status.setWordWrap(True); self.update_status.setStyleSheet("color:#68758a;font-size:11px"); side.addWidget(self.update_status)
        main.addWidget(sidebar); main.addWidget(self.stack, 1); self.toast = Toast(root)
        self.merge_page.toast_requested.connect(self.toast.show_message); self.merge_page.merge_completed.connect(self.merge_finished)
        self.settings_page.check_update_requested.connect(lambda: self.check_updates(True)); self.about_page.check_update_requested.connect(lambda: self.check_updates(True)); self.settings_page.history_clear_requested.connect(self.clear_history)
        if self.settings.get("auto_check_updates", True): self.check_updates(False)

    def show_page(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        if index == 1: self.history_page.refresh()

    def merge_finished(self, result) -> None:
        self.history.add_success(result); self.history_page.refresh(); self.toast.show_message("Ghép file thành công")
        if self.settings.get("remember_output_dir", True): self.settings.set("last_output_dir", str(result.output_path.parent))

    def clear_history(self) -> None:
        if QMessageBox.question(self, "Xóa lịch sử", "Xóa toàn bộ lịch sử xử lý?") == QMessageBox.StandardButton.Yes:
            self.history.clear(); self.history_page.refresh()

    def check_updates(self, interactive: bool = False) -> None:
        if self.update_thread and self.update_thread.isRunning(): return
        self.update_status.setText("Đang kiểm tra cập nhật..."); self.update_thread = UpdateCheckThread(self.updater)
        self.update_thread.found.connect(self.update_found); self.update_thread.current.connect(lambda: self.update_current(interactive)); self.update_thread.failed.connect(lambda message: self.update_failed(message, interactive)); self.update_thread.finished.connect(self.update_thread.deleteLater); self.update_thread.start()

    def update_found(self, info) -> None:
        self.update_status.setText(f"Có phiên bản mới {info.version}"); self.settings_page.version_label.setText(f"Phiên bản hiện tại: {VERSION}\nPhiên bản mới nhất: {info.version}"); self.toast.show_message(f"Có phiên bản mới {info.version}"); UpdateDialog(self.updater, info, self.settings, self).exec()

    def update_current(self, interactive: bool) -> None:
        self.update_status.setText("Ứng dụng đã là phiên bản mới nhất"); self.settings_page.version_label.setText(f"Phiên bản hiện tại: {VERSION}\nPhiên bản mới nhất: {VERSION}")
        if interactive: QMessageBox.information(self, "Cập nhật", "Ứng dụng đã là phiên bản mới nhất.")

    def update_failed(self, message: str, interactive: bool) -> None:
        self.update_status.setText("Không thể kiểm tra cập nhật"); logging.getLogger(__name__).warning(message)
        if interactive: QMessageBox.warning(self, "Kiểm tra cập nhật", message)
