from PySide6.QtCore import QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QCheckBox, QFrame, QHBoxLayout, QLabel, QMessageBox, QPushButton, QVBoxLayout, QWidget

from app.config import VERSION, app_data_dir


class SettingsPage(QWidget):
    check_update_requested = Signal()
    history_clear_requested = Signal()

    def __init__(self, settings) -> None:
        super().__init__(); self.settings = settings
        layout = QVBoxLayout(self); layout.setContentsMargins(28, 22, 28, 22); layout.setSpacing(14)
        layout.addWidget(QLabel("CÀI ĐẶT", objectName="pageTitle"))
        general = QFrame(objectName="card"); box = QVBoxLayout(general); box.addWidget(QLabel("Chung", objectName="sectionTitle"))
        self.checks = {}
        for key, label in (("open_after_merge", "Mở file sau khi ghép thành công"),
                           ("remember_output_dir", "Ghi nhớ thư mục output gần nhất"),
                           ("remember_options", "Ghi nhớ các tùy chọn merge")):
            check = QCheckBox(label); check.setChecked(settings.get(key, True)); check.toggled.connect(lambda value, k=key: settings.set(k, value)); box.addWidget(check); self.checks[key] = check
        layout.addWidget(general)
        update = QFrame(objectName="card"); box = QVBoxLayout(update); box.addWidget(QLabel("Cập nhật", objectName="sectionTitle"))
        auto = QCheckBox("Tự động kiểm tra cập nhật khi mở ứng dụng"); auto.setChecked(settings.get("auto_check_updates", True)); auto.toggled.connect(lambda value: settings.set("auto_check_updates", value)); box.addWidget(auto)
        self.version_label = QLabel(f"Phiên bản hiện tại: {VERSION}\nPhiên bản mới nhất: Chưa kiểm tra"); box.addWidget(self.version_label)
        check = QPushButton("Kiểm tra cập nhật"); check.clicked.connect(self.check_update_requested); box.addWidget(check); layout.addWidget(update)
        data = QFrame(objectName="card"); row = QHBoxLayout(data); row.addWidget(QLabel("Dữ liệu ứng dụng", objectName="sectionTitle")); row.addStretch()
        open_data = QPushButton("Mở thư mục dữ liệu"); open_data.clicked.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(app_data_dir())))); row.addWidget(open_data)
        clear = QPushButton("Xóa lịch sử"); clear.clicked.connect(self.history_clear_requested); row.addWidget(clear)
        reset = QPushButton("Khôi phục mặc định", objectName="danger"); reset.clicked.connect(self.reset); row.addWidget(reset); layout.addWidget(data); layout.addStretch()

    def reset(self) -> None:
        if QMessageBox.question(self, "Khôi phục mặc định", "Khôi phục toàn bộ cài đặt mặc định?") == QMessageBox.StandardButton.Yes:
            self.settings.reset()
            for key, check in self.checks.items(): check.setChecked(self.settings.get(key, True))

