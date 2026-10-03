from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QRect, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPen, QPixmap
from PySide6.QtPrintSupport import QPrintDialog, QPrinter
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QFileDialog, QFormLayout, QFrame, QHBoxLayout, QLabel,
    QDialog, QLineEdit, QMessageBox, QPushButton, QScrollArea, QSpinBox,
    QStackedWidget, QTextEdit, QVBoxLayout, QWidget,
)

from app.core.code_generator import (
    FORMAT_NAMES,
    GeneratedCode,
    generate_code,
    split_text_items,
)


class CodeGeneratorPage(QWidget):
    toast_requested = Signal(str)

    CONTENT_TYPES = ["Trang web", "Văn bản", "Wi-Fi", "Danh thiếp", "File"]

    def __init__(self) -> None:
        super().__init__()
        self.generated: GeneratedCode | None = None
        self.generated_codes: list[GeneratedCode] = []
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
        self.text.setPlaceholderText("Nhập danh sách, mỗi nội dung trên một dòng...")
        self.text.setMinimumHeight(150)
        layout.addWidget(self.text)
        self.batch_lines = QCheckBox("Mỗi dòng tạo một mã riêng")
        self.batch_lines.setChecked(True)
        self.batch_lines.setToolTip("Bỏ chọn nếu muốn mã hóa toàn bộ đoạn văn thành một mã duy nhất.")
        layout.addWidget(self.batch_lines)
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
        self.preview = QScrollArea(widgetResizable=True, objectName="codePreviewArea")
        self.preview.setMinimumSize(320, 360)
        self.preview_content = QWidget(objectName="codePreviewContent")
        self.preview_layout = QVBoxLayout(self.preview_content)
        self.preview_layout.setContentsMargins(14, 14, 14, 14)
        self.preview_layout.setSpacing(18)
        self.preview_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.preview.setWidget(self.preview_content)
        self._show_preview_placeholder()
        box.addWidget(self.preview, 1)
        self.result_info = QLabel("")
        self.result_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_info.setObjectName("mutedText")
        box.addWidget(self.result_info)
        actions = QHBoxLayout()
        actions.setSpacing(10)
        self.print_button = QPushButton("IN MÃ...")
        self.print_button.setMinimumHeight(42)
        self.print_button.setEnabled(False)
        self.print_button.clicked.connect(self.print_codes)
        actions.addWidget(self.print_button)
        self.save_button = QPushButton("LƯU MÃ...")
        self.save_button.setMinimumHeight(42)
        self.save_button.setEnabled(False)
        self.save_button.clicked.connect(self.save_code)
        actions.addWidget(self.save_button)
        box.addLayout(actions)
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

    def _payloads(self) -> list[str]:
        payload = self._payload()
        if self.content_type.currentText() == "Văn bản" and self.batch_lines.isChecked():
            return split_text_items(payload)
        return [payload] if payload else []

    @staticmethod
    def _escape_wifi(value: str) -> str:
        for char in "\\;,:":
            value = value.replace(char, "\\" + char)
        return value

    def create_code(self) -> None:
        payloads = self._payloads()
        if not payloads:
            QMessageBox.warning(self, "Thiếu nội dung", "Vui lòng nhập nội dung trước khi tạo mã.")
            return
        generated_codes: list[GeneratedCode] = []
        for index, payload in enumerate(payloads, start=1):
            try:
                generated_codes.append(
                    generate_code(payload, self.code_format.currentText(), self.scale.value())
                )
            except (ValueError, RuntimeError) as exc:
                prefix = f"Dòng {index}: " if len(payloads) > 1 else ""
                QMessageBox.warning(self, "Không thể tạo mã", prefix + str(exc))
                return

        self.generated_codes = generated_codes
        self.generated = generated_codes[0]
        self._render_previews()
        total_characters = sum(len(item.content) for item in generated_codes)
        if len(generated_codes) == 1:
            self.result_info.setText(
                f"{self.generated.format_name} • {total_characters} ký tự"
            )
            self.print_button.setText("IN MÃ...")
            self.save_button.setText("LƯU MÃ...")
        else:
            self.result_info.setText(
                f"{self.generated.format_name} • {len(generated_codes)} mã • "
                f"{total_characters} ký tự"
            )
            self.print_button.setText("IN DANH SÁCH...")
            self.save_button.setText("LƯU TẤT CẢ...")
        self.print_button.setEnabled(True)
        self.save_button.setEnabled(True)
        self.toast_requested.emit(f"Đã tạo {len(generated_codes)} mã thành công")

    def _clear_preview(self) -> None:
        self.preview_content.setMinimumHeight(0)
        while self.preview_layout.count():
            item = self.preview_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _show_preview_placeholder(self) -> None:
        self._clear_preview()
        placeholder = QLabel("Mã vừa tạo sẽ hiển thị tại đây", objectName="codePreviewPlaceholder")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setWordWrap(True)
        placeholder.setMinimumHeight(300)
        self.preview_layout.addWidget(placeholder)

    def _render_previews(self) -> None:
        self._clear_preview()
        for index, generated in enumerate(self.generated_codes, start=1):
            item = QFrame(objectName="codePreviewItem")
            item_layout = QVBoxLayout(item)
            item_layout.setContentsMargins(10, 10, 10, 12)
            item_layout.setSpacing(8)

            code_label = (
                "Mã vạch"
                if generated.format_name in {"Code 128", "EAN-13", "UPC-A"}
                else "Mã"
            )
            title = QLabel(
                f"{code_label} {index}: ({generated.content})",
                objectName="codePreviewTitle",
            )
            title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            title.setWordWrap(True)
            title.setTextFormat(Qt.TextFormat.PlainText)
            title.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            item_layout.addWidget(title)

            pixmap = QPixmap()
            pixmap.loadFromData(generated.png, "PNG")
            image = QLabel(objectName="codePreviewImage")
            image.setAlignment(Qt.AlignmentFlag.AlignCenter)
            available = QSize(max(180, self.preview.viewport().width() - 70), 280)
            scaled_pixmap = pixmap.scaled(
                available,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            image.setPixmap(scaled_pixmap)
            image.setMinimumHeight(scaled_pixmap.height())
            item_layout.addWidget(image)
            self.preview_layout.addWidget(item)

        self.preview_layout.addStretch()
        self.preview_layout.activate()
        self.preview_content.setMinimumHeight(self.preview_layout.sizeHint().height())
        self.preview.verticalScrollBar().setValue(0)

    def print_codes(self) -> None:
        if not self.generated_codes:
            return
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setDocName(f"Danh sách {self.generated_codes[0].format_name}")
        dialog = QPrintDialog(printer, self)
        dialog.setWindowTitle("In danh sách mã")
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            self._render_print_job(printer)
        except RuntimeError as exc:
            QMessageBox.critical(self, "Không thể in", str(exc))
            return
        self.toast_requested.emit(f"Đã gửi in {len(self.generated_codes)} mã")

    def _render_print_job(self, printer: QPrinter) -> None:
        """Render the current codes to a printer or PDF output device."""
        printer.setFullPage(True)
        painter = QPainter()
        if not painter.begin(printer):
            raise RuntimeError("Không thể khởi tạo máy in đã chọn.")

        try:
            page_rect = printer.pageLayout().paintRectPixels(printer.resolution())
            if page_rect.width() <= 0 or page_rect.height() <= 0:
                raise RuntimeError("Khổ giấy hoặc vùng in không hợp lệ.")

            codes_per_page = 4
            total_pages = (len(self.generated_codes) + codes_per_page - 1) // codes_per_page
            for page_index in range(total_pages):
                if page_index and not printer.newPage():
                    raise RuntimeError("Không thể tạo trang in tiếp theo.")
                start = page_index * codes_per_page
                page_codes = self.generated_codes[start:start + codes_per_page]
                self._paint_code_page(
                    painter,
                    page_rect,
                    page_codes,
                    start,
                    page_index + 1,
                    total_pages,
                    printer.resolution(),
                )
        finally:
            painter.end()

    @staticmethod
    def _paint_code_page(
        painter: QPainter,
        page_rect: QRect,
        codes: list[GeneratedCode],
        start_index: int,
        page_number: int,
        total_pages: int,
        resolution: int,
    ) -> None:
        margin = max(12, int(resolution * 0.16))
        header_height = max(34, int(resolution * 0.34))
        footer_height = max(24, int(resolution * 0.22))
        content_rect = page_rect.adjusted(margin, margin, -margin, -margin)

        header = QRect(
            content_rect.left(), content_rect.top(), content_rect.width(), header_height
        )
        heading_font = QFont(painter.font())
        heading_font.setPointSize(14)
        heading_font.setBold(True)
        painter.setFont(heading_font)
        painter.setPen(QColor("#182135"))
        format_name = codes[0].format_name if codes else ""
        painter.drawText(
            header,
            Qt.AlignmentFlag.AlignCenter,
            f"DANH SÁCH {format_name.upper()}",
        )

        body_top = header.bottom() + margin
        body_height = content_rect.bottom() - footer_height - body_top
        gap = max(8, int(resolution * 0.08))
        slot_height = (body_height - gap * (len(codes) - 1)) // max(1, len(codes))
        title_font = QFont(painter.font())
        title_font.setPointSize(11)
        title_font.setBold(True)

        for offset, generated in enumerate(codes):
            top = body_top + offset * (slot_height + gap)
            slot = QRect(content_rect.left(), top, content_rect.width(), slot_height)
            painter.setPen(QPen(QColor("#d7dee9"), max(1, resolution // 300)))
            painter.setBrush(QColor("#ffffff"))
            painter.drawRoundedRect(slot, margin // 3, margin // 3)

            caption_height = max(28, min(slot.height() // 5, int(resolution * 0.48)))
            caption = slot.adjusted(margin, margin // 2, -margin, 0)
            caption.setHeight(caption_height)
            code_label = (
                "Mã vạch"
                if generated.format_name in {"Code 128", "EAN-13", "UPC-A"}
                else "Mã"
            )
            painter.setFont(title_font)
            painter.setPen(QColor("#1769e8"))
            painter.drawText(
                caption,
                Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
                f"{code_label} {start_index + offset + 1}: ({generated.content})",
            )

            image = QImage.fromData(generated.png, "PNG")
            if image.isNull():
                continue
            image_area = slot.adjusted(
                margin,
                caption_height + margin,
                -margin,
                -margin,
            )
            target_size = image.size().scaled(
                image_area.size(), Qt.AspectRatioMode.KeepAspectRatio
            )
            target = QRect(
                image_area.center().x() - target_size.width() // 2,
                image_area.center().y() - target_size.height() // 2,
                target_size.width(),
                target_size.height(),
            )
            painter.drawImage(target, image)

        footer = QRect(
            content_rect.left(),
            content_rect.bottom() - footer_height,
            content_rect.width(),
            footer_height,
        )
        footer_font = QFont(painter.font())
        footer_font.setPointSize(9)
        footer_font.setBold(False)
        painter.setFont(footer_font)
        painter.setPen(QColor("#68758a"))
        painter.drawText(
            footer,
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
            f"Trang {page_number}/{total_pages}",
        )

    def save_code(self) -> None:
        if not self.generated_codes:
            return
        if len(self.generated_codes) > 1:
            self._save_code_batch()
            return
        self._save_single_code(self.generated_codes[0])

    def _save_single_code(self, generated: GeneratedCode) -> None:
        suggested = f"ma-{generated.format_name.lower().replace(' ', '-')}.png"
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
                target.write_text(generated.svg, encoding="utf-8")
            elif target.suffix.lower() in {".jpg", ".jpeg"}:
                from io import BytesIO
                from PIL import Image
                image = Image.open(BytesIO(generated.png)).convert("RGB")
                image.save(target, format="JPEG", quality=95)
            else:
                target.write_bytes(generated.png)
        except OSError as exc:
            QMessageBox.critical(self, "Không thể lưu", f"Không thể lưu file:\n{exc}")
            return
        self.toast_requested.emit(f"Đã lưu mã: {target.name}")

    def _save_code_batch(self) -> None:
        parent = QFileDialog.getExistingDirectory(self, "Chọn thư mục lưu danh sách mã")
        if not parent:
            return
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        output_dir = Path(parent) / f"danh-sach-ma-{stamp}"
        counter = 2
        while output_dir.exists():
            output_dir = Path(parent) / f"danh-sach-ma-{stamp}-{counter}"
            counter += 1
        try:
            output_dir.mkdir(parents=True)
            digits = max(3, len(str(len(self.generated_codes))))
            for index, generated in enumerate(self.generated_codes, start=1):
                filename = f"ma-{index:0{digits}d}.png"
                (output_dir / filename).write_bytes(generated.png)
        except OSError as exc:
            QMessageBox.critical(self, "Không thể lưu", f"Không thể lưu danh sách mã:\n{exc}")
            return
        self.toast_requested.emit(
            f"Đã lưu {len(self.generated_codes)} mã vào: {output_dir.name}"
        )
