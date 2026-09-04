from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import requests
from packaging.version import InvalidVersion, Version

from app.config import UPDATE_URL, VERSION, app_data_dir


@dataclass
class UpdateInfo:
    version: str
    download_url: str
    sha256: str
    mandatory: bool
    release_notes: list[str]


class UpdateError(Exception):
    pass


class Updater:
    def __init__(self, manifest_url: str = UPDATE_URL) -> None:
        self.manifest_url = manifest_url

    def check(self) -> UpdateInfo | None:
        try:
            response = requests.get(
                self.manifest_url,
                params={"_": int(time.time())},
                headers={"Cache-Control": "no-cache", "Pragma": "no-cache"},
                timeout=(5, 15),
            )
            response.raise_for_status()
            data = response.json()
            info = self._parse_github_release(data) if "tag_name" in data else self._parse_manifest(data)
            return info if Version(info.version) > Version(VERSION) else None
        except (requests.RequestException, KeyError, ValueError, InvalidVersion, json.JSONDecodeError) as exc:
            raise UpdateError(f"Không thể kiểm tra cập nhật: {exc}") from exc

    @staticmethod
    def _parse_manifest(data: dict) -> UpdateInfo:
        return UpdateInfo(
            str(data["version"]), str(data["download_url"]),
            str(data.get("sha256", "")), bool(data.get("mandatory", False)),
            [str(item) for item in data.get("release_notes", [])],
        )

    def _parse_github_release(self, data: dict) -> UpdateInfo:
        version = str(data["tag_name"]).lstrip("vV")
        assets = data.get("assets", [])
        pattern = re.compile(r"^ExcelMergerPro-Setup-.*\.exe$", re.IGNORECASE)
        installer = next((asset for asset in assets if pattern.match(str(asset.get("name", "")))), None)
        if installer is None:
            raise UpdateError(f"Release v{version} chưa có installer ExcelMergerPro-Setup-*.exe.")

        digest = str(installer.get("digest") or "")
        sha256 = digest.removeprefix("sha256:").strip()
        if not re.fullmatch(r"[0-9a-fA-F]{64}", sha256):
            checksum_name = f'{installer["name"]}.sha256'
            checksum = next((asset for asset in assets if asset.get("name") == checksum_name), None)
            if checksum:
                checksum_response = requests.get(
                    str(checksum["browser_download_url"]),
                    headers={"Cache-Control": "no-cache"}, timeout=(5, 15),
                )
                checksum_response.raise_for_status()
                candidate = checksum_response.text.strip().split()[0]
                if re.fullmatch(r"[0-9a-fA-F]{64}", candidate):
                    sha256 = candidate

        body = str(data.get("body") or "")
        notes = []
        for line in body.splitlines():
            cleaned = line.strip().lstrip("-* ").strip()
            if cleaned and not cleaned.startswith("#") and cleaned.lower() != "[mandatory]":
                notes.append(cleaned)
        return UpdateInfo(
            version=version,
            download_url=str(installer["browser_download_url"]),
            sha256=sha256,
            mandatory="[mandatory]" in body.lower(),
            release_notes=notes[:12],
        )

    def download(self, info: UpdateInfo, progress: Callable[[int], None] | None = None) -> Path:
        if not info.sha256 or len(info.sha256) != 64:
            raise UpdateError("Bản cập nhật không có mã SHA-256 hợp lệ.")
        folder = app_data_dir() / "update"
        folder.mkdir(parents=True, exist_ok=True)
        destination = folder / f"ExcelMergerPro-Setup-{info.version}.exe"
        temp = destination.with_suffix(".download")
        digest = hashlib.sha256()
        try:
            with requests.get(info.download_url, stream=True, timeout=(10, 60)) as response:
                response.raise_for_status()
                total = int(response.headers.get("content-length", 0))
                received = 0
                with temp.open("wb") as stream:
                    for chunk in response.iter_content(1024 * 256):
                        if chunk:
                            stream.write(chunk)
                            digest.update(chunk)
                            received += len(chunk)
                            if progress and total:
                                progress(int(received * 100 / total))
            if digest.hexdigest().lower() != info.sha256.lower():
                temp.unlink(missing_ok=True)
                raise UpdateError("Mã SHA-256 không khớp. File tải xuống đã bị loại bỏ.")
            temp.replace(destination)
            return destination
        except requests.RequestException as exc:
            temp.unlink(missing_ok=True)
            raise UpdateError(f"Tải bản cập nhật thất bại: {exc}") from exc

    @staticmethod
    def launch_installer(path: Path) -> None:
        if sys.platform != "win32":
            raise UpdateError("Installer chỉ có thể chạy trên Windows.")
        subprocess.Popen([str(path), "/SILENT", "/CLOSEAPPLICATIONS"], close_fds=True)
