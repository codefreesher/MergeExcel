from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QDialog, QDialogButtonBox, QLabel, QMessageBox,
    QProgressBar, QVBoxLayout,
)

from app.core.updater import UpdateInfo, Updater


class DownloadThread(QThread):
    progress = Signal(int); downloaded = Signal(object); failed = Signal(str)
    def __init__(self, updater, info): super().__init__(); self.updater, self.info = updater, info
    def run(self):
        try: self.downloaded.emit(self.updater.download(self.info, self.progress.emit))
        except Exception as exc: self.failed.emit(str(exc))


class UpdateDialog(QDialog):
    def __init__(self, updater: Updater, info: UpdateInfo, settings, parent=None) -> None:
        super().__init__(parent); self.updater, self.info, self.settings = updater, info, settings; self.installing = False; self.thread = None
        self.setWindowTitle("Cập nhật ứng dụng"); self.setMinimumWidth(470)
        layout = QVBoxLayout(self); self.title = QLabel("Đã có phiên bản mới!"); self.title.setStyleSheet("font-size:20px;font-weight:700"); layout.addWidget(self.title)
        self.version_label = QLabel(f"Phiên bản {info.version} đã sẵn sàng để cài đặt."); layout.addWidget(self.version_label)
        notes = "\n".join(f"• {note}" for note in info.release_notes) or "Cải thiện hiệu năng và độ ổn định."
        self.notes_label = QLabel(f"Những thay đổi trong phiên bản mới:\n\n{notes}"); self.notes_label.setWordWrap(True); layout.addWidget(self.notes_label)
        self.mandatory_label = QLabel("Phiên bản này bắt buộc phải cập nhật để tiếp tục sử dụng.")
        self.mandatory_label.setVisible(info.mandatory); layout.addWidget(self.mandatory_label)
        self.status_label = QLabel(""); self.status_label.setWordWrap(True); self.status_label.hide(); layout.addWidget(self.status_label)
        self.progress = QProgressBar(); self.progress.setRange(0, 100); self.progress.hide(); layout.addWidget(self.progress)
        self.auto = QCheckBox("Tự động kiểm tra cập nhật"); self.auto.setChecked(settings.get("auto_check_updates", True)); self.auto.toggled.connect(lambda value: settings.set("auto_check_updates", value)); layout.addWidget(self.auto)
        self.buttons = QDialogButtonBox(); self.later = self.buttons.addButton("Để sau", QDialogButtonBox.ButtonRole.RejectRole); self.install = self.buttons.addButton("Tải và cài đặt", QDialogButtonBox.ButtonRole.AcceptRole)
        self.install.setObjectName("primary"); self.later.setVisible(not info.mandatory); self.install.clicked.connect(self.download); self.later.clicked.connect(self.reject); layout.addWidget(self.buttons)

    def reject(self) -> None:
        if not self.installing and not self.info.mandatory: super().reject()

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.installing or self.info.mandatory:
            event.ignore()
        else:
            event.accept()

    def download(self) -> None:
        if self.installing:
            return
        self.installing = True
        self.title.setText("Đang tải bản cập nhật...")
        self.version_label.hide(); self.notes_label.hide(); self.mandatory_label.hide(); self.auto.hide(); self.buttons.hide()
        self.status_label.setText(f"Đang tải Excel Merger Pro {self.info.version}. Vui lòng không đóng ứng dụng.")
        self.status_label.show(); self.progress.setValue(0); self.progress.show()
        self.thread = DownloadThread(self.updater, self.info)
        self.thread.progress.connect(self.on_progress)
        self.thread.downloaded.connect(self.launch)
        self.thread.failed.connect(self.failed)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def on_progress(self, value: int) -> None:
        self.progress.setValue(value)
        self.status_label.setText(f"Đang tải bản cập nhật... {value}%")

    def launch(self, path) -> None:
        self.progress.setValue(100); self.title.setText("Đang cài đặt bản cập nhật...")
        self.status_label.setText("Đã tải và xác minh thành công. Trình cài đặt đang được khởi chạy tự động.")
        QApplication.processEvents()
        try:
            self.updater.launch_installer(path); self.accept(); QApplication.quit()
        except Exception as exc: self.failed(str(exc))

    def failed(self, message: str) -> None:
        self.installing = False
        self.title.setText("Không thể cập nhật")
        self.status_label.setText("Quá trình cập nhật đã dừng. Bạn có thể thử lại.")
        self.progress.hide(); self.buttons.show(); self.install.setEnabled(True)
        self.install.setText("Thử tải và cài đặt lại")
        if not self.info.mandatory:
            self.later.show()
        QMessageBox.critical(self, "Cập nhật thất bại", message)
