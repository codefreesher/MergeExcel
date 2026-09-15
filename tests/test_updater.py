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


def test_release_list_chooses_highest_stable_version_with_installer() -> None:
    digest = "b" * 64

    def release(version: str, *, draft: bool = False, prerelease: bool = False,
                with_installer: bool = True) -> dict:
        assets = []
        if with_installer:
            assets.append({
                "name": f"ExcelMergerPro-Setup-{version}.exe",
                "browser_download_url": f"https://example.test/{version}.exe",
                "digest": f"sha256:{digest}",
            })
        return {
            "tag_name": f"v{version}", "body": "", "assets": assets,
            "draft": draft, "prerelease": prerelease,
        }

    info = Updater()._parse_github_releases([
        release("1.2.4"),
        release("2.0.0", draft=True),
        release("1.4.0", prerelease=True),
        release("1.3.1", with_installer=False),
        release("1.3.0"),
    ])

    assert info.version == "1.3.0"
