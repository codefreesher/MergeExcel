from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QLabel, QWidget


class Toast(QLabel):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setStyleSheet("background:#182230;color:white;border-radius:7px;padding:10px 16px")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hide()

    def show_message(self, message: str, duration: int = 2600) -> None:
        self.setText(message)
        self.adjustSize()
        self.move(self.parent().width() - self.width() - 24, self.parent().height() - self.height() - 24)
        self.raise_()
        self.show()
        QTimer.singleShot(duration, self.hide)

