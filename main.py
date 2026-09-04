from __future__ import annotations

import logging
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMessageBox

from app.config import APP_NAME, VERSION
from app.core.logging_config import configure_logging
from app.ui.main_window import MainWindow


def main() -> int:
    configure_logging(); logging.info("Starting %s %s", APP_NAME, VERSION)
    app = QApplication(sys.argv); app.setApplicationName(APP_NAME); app.setApplicationVersion(VERSION); app.setOrganizationName("ExcelMergerPro")
    stylesheet = Path(__file__).parent / "app" / "resources" / "styles" / "app.qss"
    app.setStyleSheet(stylesheet.read_text(encoding="utf-8"))
    try:
        window = MainWindow(); window.show(); return app.exec()
    except Exception as exc:
        logging.exception("Fatal startup error"); QMessageBox.critical(None, APP_NAME, f"Không thể khởi động ứng dụng:\n{exc}"); return 1


if __name__ == "__main__":
    raise SystemExit(main())

