from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QComboBox, QFileDialog, QFormLayout, QFrame, QHBoxLayout, QLabel,
    QLineEdit, QMessageBox, QPushButton, QScrollArea, QSpinBox, QStackedWidget,
    QTextEdit, QVBoxLayout, QWidget,
)

from app.core.code_generator import FORMAT_NAMES, GeneratedCode, generate_code


class CodeGeneratorPage(QWidget):
    toast_requested = Signal(str)

    CONTENT_TYPES = ["Trang web", "Văn bản", "Wi-Fi", "Danh thiếp", "File"]

    def __init__(self) -> None:
        super().__init__()
        self.generated: GeneratedCode | None = None
        self.file_path = ""

        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 22, 28, 22)
        outer.setSpacing(14)
        outer.addWidget(QLabel("TẠO MÃ QR VÀ MÃ VẠCH", objectName="pageTitle"))
        subtitle = QLabel("Tạo mã để chia sẻ đường dẫn, văn bản, Wi-Fi, danh thiếp hoặc file.")
        subtitle.setObjectName("mutedText")
        outer.addWidget(subtitle)

        scroll = QScrollArea(widgetResizable=True)
        body = QWidget(objectName="scrollBody")
        content = QHBoxLayout(body)
        content.setContentsMargins(0, 4, 8, 8)
        content.setSpacing(16)
        content.addWidget(self._build_editor(), 3)
        content.addWidget(self._build_preview(), 2)
        scroll.setWidget(body)
        outer.addWidget(scroll)

    def _build_editor(self) -> QFrame:
        card = QFrame(objectName="card")
        box = QVBoxLayout(card)
        box.setContentsMargins(18, 16, 18, 18)
        box.setSpacing(14)
        box.addWidget(QLabel("NỘI DUNG", objectName="sectionTitle"))

        form = QFormLayout()
        form.setSpacing(10)
        self.content_type = QComboBox()
        self.content_type.addItems(self.CONTENT_TYPES)
        self.content_type.currentIndexChanged.connect(self._content_type_changed)
        form.addRow("Loại nội dung", self.content_type)
        self.code_format = QComboBox()
        self.code_format.addItems(FORMAT_NAMES)
        self.code_format.currentTextChanged.connect(self._format_changed)
        form.addRow("Loại mã", self.code_format)
        self.scale = QSpinBox()
        self.scale.setRange(2, 12)
        self.scale.setValue(6)
        self.scale.setSuffix(" px/ô")
        form.addRow("Độ phân giải", self.scale)
        box.addLayout(form)

        self.input_stack = QStackedWidget()
        self.input_stack.addWidget(self._website_input())
        self.input_stack.addWidget(self._text_input())
        self.input_stack.addWidget(self._wifi_input())
        self.input_stack.addWidget(self._contact_input())
        self.input_stack.addWidget(self._file_input())
        box.addWidget(self.input_stack)
        box.addStretch()

        note = QLabel("Mã vạch EAN-13 và UPC-A chỉ nhận chuỗi số đúng độ dài. Các nội dung dài nên dùng QR Code, Data Matrix, Aztec hoặc PDF417.")
        note.setWordWrap(True)
        note.setObjectName("hintText")
        box.addWidget(note)
        self.create_button = QPushButton("TẠO MÃ", objectName="primary")
        self.create_button.setMinimumHeight(44)
        self.create_button.clicked.connect(self.create_code)
        box.addWidget(self.create_button)
        return card

    def _website_input(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.addWidget(QLabel("Địa chỉ trang web"))
        self.website = QLineEdit()
        self.website.setPlaceholderText("https://example.com")
        layout.addWidget(self.website)
        layout.addStretch()
        return page

    def _text_input(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.addWidget(QLabel("Văn bản"))
        self.text = QTextEdit()
        self.text.setPlaceholderText("Nhập nội dung cần mã hóa...")
        self.text.setMinimumHeight(150)
        layout.addWidget(self.text)
        return page

    def _wifi_input(self) -> QWidget:
        page = QWidget()
        form = QFormLayout(page)
        form.setContentsMargins(0, 4, 0, 0)
        self.wifi_name = QLineEdit()
        self.wifi_password = QLineEdit()
        self.wifi_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.wifi_security = QComboBox()
        self.wifi_security.addItems(["WPA/WPA2", "WEP", "Không mật khẩu"])
        form.addRow("Tên mạng (SSID)", self.wifi_name)
        form.addRow("Mật khẩu", self.wifi_password)
        form.addRow("Bảo mật", self.wifi_security)
        return page

    def _contact_input(self) -> QWidget:
        page = QWidget()
        form = QFormLayout(page)
        form.setContentsMargins(0, 4, 0, 0)
        self.contact_name = QLineEdit()
        self.contact_phone = QLineEdit()
        self.contact_email = QLineEdit()
        self.contact_company = QLineEdit()
        form.addRow("Họ và tên", self.contact_name)
        form.addRow("Điện thoại", self.contact_phone)
        form.addRow("Email", self.contact_email)
        form.addRow("Công ty", self.contact_company)
        return page

    def _file_input(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.addWidget(QLabel("File cần liên kết"))
        row = QHBoxLayout()
        self.file_display = QLineEdit()
        self.file_display.setReadOnly(True)
        self.file_display.setPlaceholderText("Chưa chọn file")
        choose = QPushButton("Chọn file")
        choose.clicked.connect(self.choose_file)
        row.addWidget(self.file_display, 1)
        row.addWidget(choose)
        layout.addLayout(row)
        explanation = QLabel("Mã lưu đường dẫn tới file, không nhúng toàn bộ dữ liệu file. Người quét cần có quyền truy cập đường dẫn đó.")
        explanation.setWordWrap(True)
        explanation.setObjectName("hintText")
        layout.addWidget(explanation)
        layout.addStretch()
        return page

    def _build_preview(self) -> QFrame:
        card = QFrame(objectName="card")
        box = QVBoxLayout(card)
        box.setContentsMargins(18, 16, 18, 18)
        box.setSpacing(14)
        box.addWidget(QLabel("KẾT QUẢ", objectName="sectionTitle"))
        self.preview = QLabel("Mã vừa tạo sẽ hiển thị tại đây", objectName="codePreview")
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setMinimumSize(320, 360)
        self.preview.setWordWrap(True)
        box.addWidget(self.preview, 1)
        self.result_info = QLabel("")
        self.result_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_info.setObjectName("mutedText")
        box.addWidget(self.result_info)
        self.save_button = QPushButton("LƯU MÃ...")
        self.save_button.setMinimumHeight(42)
        self.save_button.setEnabled(False)
        self.save_button.clicked.connect(self.save_code)
        box.addWidget(self.save_button)
        return card

    def choose_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Chọn file")
        if path:
            self.file_path = path
            self.file_display.setText(path)

    def _content_type_changed(self, index: int) -> None:
        self.input_stack.setCurrentIndex(index)
        if index in (2, 3, 4) and self.code_format.currentText() in {"Code 128", "EAN-13", "UPC-A"}:
            self.code_format.setCurrentText("QR Code")

    def _format_changed(self, value: str) -> None:
        if value in {"Code 128", "EAN-13", "UPC-A"} and self.content_type.currentIndex() in (2, 3, 4):
            self.content_type.setCurrentIndex(1)

    def _payload(self) -> str:
        kind = self.content_type.currentText()
        if kind == "Trang web":
            value = self.website.text().strip()
            if value and "://" not in value:
                value = "https://" + value
            return value
        if kind == "Văn bản":
            return self.text.toPlainText().strip()
        if kind == "Wi-Fi":
            ssid = self._escape_wifi(self.wifi_name.text())
            password = self._escape_wifi(self.wifi_password.text())
            security = {"WPA/WPA2": "WPA", "WEP": "WEP", "Không mật khẩu": "nopass"}[self.wifi_security.currentText()]
            return f"WIFI:T:{security};S:{ssid};P:{password};;" if ssid else ""
        if kind == "Danh thiếp":
            name = self.contact_name.text().strip()
            if not name:
                return ""
            return "\n".join([
                "BEGIN:VCARD", "VERSION:3.0", f"FN:{name}",
                f"ORG:{self.contact_company.text().strip()}",
                f"TEL:{self.contact_phone.text().strip()}",
                f"EMAIL:{self.contact_email.text().strip()}", "END:VCARD",
            ])
        return Path(self.file_path).resolve().as_uri() if self.file_path else ""

    @staticmethod
    def _escape_wifi(value: str) -> str:
        for char in "\\;,:":
            value = value.replace(char, "\\" + char)
        return value

    def create_code(self) -> None:
        payload = self._payload()
        if not payload:
            QMessageBox.warning(self, "Thiếu nội dung", "Vui lòng nhập nội dung trước khi tạo mã.")
            return
        try:
            self.generated = generate_code(payload, self.code_format.currentText(), self.scale.value())
        except (ValueError, RuntimeError) as exc:
            QMessageBox.warning(self, "Không thể tạo mã", str(exc))
            return
        pixmap = QPixmap()
        pixmap.loadFromData(self.generated.png, "PNG")
        available = QSize(max(100, self.preview.width() - 36), max(100, self.preview.height() - 36))
        self.preview.setPixmap(pixmap.scaled(available, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.result_info.setText(f"{self.generated.format_name} • {len(payload)} ký tự")
        self.save_button.setEnabled(True)
        self.toast_requested.emit("Đã tạo mã thành công")

    def save_code(self) -> None:
        if self.generated is None:
            return
        suggested = f"ma-{self.generated.format_name.lower().replace(' ', '-')}.png"
        path, selected = QFileDialog.getSaveFileName(
            self, "Lưu mã", suggested, "Ảnh PNG (*.png);;Ảnh JPEG (*.jpg *.jpeg);;Vector SVG (*.svg)"
        )
        if not path:
            return
        target = Path(path)
        selected_lower = selected.lower()
        if "svg" in selected_lower and target.suffix.lower() != ".svg":
            target = target.with_suffix(".svg")
        elif "jpeg" in selected_lower and target.suffix.lower() not in {".jpg", ".jpeg"}:
            target = target.with_suffix(".jpg")
        elif not target.suffix:
            target = target.with_suffix(".png")
        try:
            if target.suffix.lower() == ".svg":
                target.write_text(self.generated.svg, encoding="utf-8")
            elif target.suffix.lower() in {".jpg", ".jpeg"}:
                from io import BytesIO
                from PIL import Image
                image = Image.open(BytesIO(self.generated.png)).convert("RGB")
                image.save(target, format="JPEG", quality=95)
            else:
                target.write_bytes(self.generated.png)
        except OSError as exc:
            QMessageBox.critical(self, "Không thể lưu", f"Không thể lưu file:\n{exc}")
            return
        self.toast_requested.emit(f"Đã lưu mã: {target.name}")
