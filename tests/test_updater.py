from app.core.updater import Updater


def test_parse_github_release_finds_installer_and_digest() -> None:
    digest = "a" * 64
    data = {
        "tag_name": "v1.3.0",
        "body": "## Thay đổi\n- Sửa lỗi cập nhật\n[mandatory]",
        "assets": [{
            "name": "ExcelMergerPro-Setup-1.3.0.exe",
            "browser_download_url": "https://example.test/ExcelMergerPro-Setup-1.3.0.exe",
            "digest": f"sha256:{digest}",
        }],
    }

    info = Updater()._parse_github_release(data)

    assert info.version == "1.3.0"
    assert info.sha256 == digest
    assert info.mandatory is True
    assert info.release_notes == ["Sửa lỗi cập nhật"]
