from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from app.config import app_data_dir
from app.core.models import MergeResult


class HistoryManager:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or app_data_dir() / "history.db"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS merge_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL,
                output_path TEXT NOT NULL, file_count INTEGER NOT NULL,
                sheet_count INTEGER NOT NULL, status TEXT NOT NULL,
                elapsed_seconds REAL NOT NULL, error TEXT DEFAULT '')""")

    def add_success(self, result: MergeResult) -> None:
        self.add(str(result.output_path), result.file_count, result.sheet_count,
                 "Thành công", result.elapsed_seconds)

    def add(self, output_path: str, file_count: int, sheet_count: int,
            status: str, elapsed: float, error: str = "") -> None:
        with self._connect() as db:
            db.execute("INSERT INTO merge_history(created_at, output_path, file_count, sheet_count, status, elapsed_seconds, error) VALUES(?,?,?,?,?,?,?)",
                       (datetime.now().isoformat(timespec="seconds"), output_path, file_count,
                        sheet_count, status, elapsed, error))

    def list_recent(self, limit: int = 200) -> list[dict]:
        with self._connect() as db:
            rows = db.execute("SELECT * FROM merge_history ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [dict(row) for row in rows]

    def clear(self) -> None:
        with self._connect() as db:
            db.execute("DELETE FROM merge_history")

