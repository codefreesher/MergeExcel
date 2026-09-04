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
    qss = stylesheet.read_text(encoding="utf-8")
    check_icon = Path(__file__).parent / "app" / "resources" / "icons" / "check.svg"
    app.setStyleSheet(qss.replace("app/resources/icons/check.svg", check_icon.as_posix()))
    try:
        window = MainWindow(); window.show(); return app.exec()
    except Exception as exc:
        logging.exception("Fatal startup error"); QMessageBox.critical(None, APP_NAME, f"Không thể khởi động ứng dụng:\n{exc}"); return 1


if __name__ == "__main__":
    raise SystemExit(main())
