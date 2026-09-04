from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from app.config import app_data_dir, default_output_dir

DEFAULTS: dict[str, Any] = {
    "open_after_merge": True,
    "remember_output_dir": True,
    "remember_options": True,
    "auto_check_updates": True,
    "last_output_dir": str(default_output_dir()),
    "merge_options": {},
}


class SettingsManager:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or app_data_dir() / "settings.json"
        self._data = deepcopy(DEFAULTS)
        self.load()

    def load(self) -> dict[str, Any]:
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                self._data.update(raw)
        except (OSError, ValueError):
            pass
        return deepcopy(self._data)

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value
        self.save()

    def update(self, values: dict[str, Any]) -> None:
        self._data.update(values)
        self.save()

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix(".tmp")
        temp.write_text(json.dumps(self._data, ensure_ascii=False, indent=2), encoding="utf-8")
        temp.replace(self.path)

    def reset(self) -> None:
        self._data = deepcopy(DEFAULTS)
        self.save()

