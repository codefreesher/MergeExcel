from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QApplication, QCheckBox, QDialog, QDialogButtonBox, QLabel, QMessageBox, QProgressBar, QPushButton, QVBoxLayout

from app.core.updater import UpdateInfo, Updater


class DownloadThread(QThread):
    progress = Signal(int); downloaded = Signal(object); failed = Signal(str)
    def __init__(self, updater, info): super().__init__(); self.updater, self.info = updater, info
    def run(self):
        try: self.downloaded.emit(self.updater.download(self.info, self.progress.emit))
        except Exception as exc: self.failed.emit(str(exc))


class UpdateDialog(QDialog):
    def __init__(self, updater: Updater, info: UpdateInfo, settings, parent=None) -> None:
        super().__init__(parent); self.updater, self.info, self.settings = updater, info
        self.setWindowTitle("Cập nhật ứng dụng"); self.setMinimumWidth(470)
        layout = QVBoxLayout(self); title = QLabel("Đã có phiên bản mới!"); title.setStyleSheet("font-size:20px;font-weight:700"); layout.addWidget(title)
        layout.addWidget(QLabel(f"Phiên bản {info.version} đã sẵn sàng để cài đặt."))
        notes = "\n".join(f"• {note}" for note in info.release_notes) or "Cải thiện hiệu năng và độ ổn định."
        layout.addWidget(QLabel(f"Những thay đổi trong phiên bản mới:\n\n{notes}"))
        if info.mandatory: layout.addWidget(QLabel("Phiên bản này bắt buộc phải cập nhật để tiếp tục sử dụng."))
        self.progress = QProgressBar(); self.progress.hide(); layout.addWidget(self.progress)
        self.auto = QCheckBox("Tự động kiểm tra cập nhật"); self.auto.setChecked(settings.get("auto_check_updates", True)); self.auto.toggled.connect(lambda value: settings.set("auto_check_updates", value)); layout.addWidget(self.auto)
        buttons = QDialogButtonBox(); self.later = buttons.addButton("Để sau", QDialogButtonBox.ButtonRole.RejectRole); self.install = buttons.addButton("Cập nhật ngay", QDialogButtonBox.ButtonRole.AcceptRole)
        self.later.setVisible(not info.mandatory); self.install.clicked.connect(self.download); self.later.clicked.connect(self.reject); layout.addWidget(buttons)

    def reject(self) -> None:
        if not self.info.mandatory: super().reject()

    def download(self) -> None:
        self.install.setEnabled(False); self.progress.show(); self.thread = DownloadThread(self.updater, self.info)
        self.thread.progress.connect(self.progress.setValue); self.thread.downloaded.connect(self.launch); self.thread.failed.connect(self.failed); self.thread.start()

    def launch(self, path) -> None:
        try:
            self.updater.launch_installer(path); self.accept(); QApplication.quit()
        except Exception as exc: self.failed(str(exc))

    def failed(self, message: str) -> None:
        self.install.setEnabled(True); QMessageBox.critical(self, "Cập nhật thất bại", message)
