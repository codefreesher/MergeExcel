from __future__ import annotations

from io import BytesIO

from PIL import Image
import pytest

from app.core.code_generator import FORMAT_NAMES, generate_code, split_text_items


@pytest.mark.parametrize("format_name,content", [
    ("QR Code", "https://example.com"),
    ("Data Matrix", "Xin chao"),
    ("Aztec", "Xin chao"),
    ("PDF417", "Xin chao"),
    ("Code 128", "ABC-123"),
    ("EAN-13", "893850597419"),
    ("UPC-A", "01234567890"),
])
def test_generate_supported_codes(format_name: str, content: str) -> None:
    result = generate_code(content, format_name, scale=3)

    image = Image.open(BytesIO(result.png))
    assert image.width > 20 and image.height > 20
    assert "<svg" in result.svg
    assert result.format_name == format_name


def test_rejects_empty_and_unknown_content() -> None:
    with pytest.raises(ValueError, match="để trống"):
        generate_code(" ", "QR Code")
    with pytest.raises(ValueError, match="không được hỗ trợ"):
        generate_code("hello", "Khác")


def test_all_formats_have_backend_names() -> None:
    assert set(FORMAT_NAMES) == {
        "QR Code", "Data Matrix", "Aztec", "PDF417", "Code 128", "EAN-13", "UPC-A"
    }


def test_split_text_items_ignores_blank_lines_and_whitespace() -> None:
    assert split_text_items("  ma mot  \n\n ma hai\r\n   \nma ba ") == [
        "ma mot", "ma hai", "ma ba"
    ]
