from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO

from PIL import Image


FORMAT_NAMES = {
    "QR Code": "QRCode",
    "Data Matrix": "DataMatrix",
    "Aztec": "Aztec",
    "PDF417": "PDF417",
    "Code 128": "Code128",
    "EAN-13": "EAN13",
    "UPC-A": "UPCA",
}


@dataclass(frozen=True)
class GeneratedCode:
    png: bytes
    svg: str
    format_name: str
    content: str


def generate_code(content: str, format_name: str, scale: int = 6) -> GeneratedCode:
    """Generate a scannable code as both PNG and SVG."""
    if not content.strip():
        raise ValueError("Nội dung không được để trống.")
    if format_name not in FORMAT_NAMES:
        raise ValueError(f"Định dạng không được hỗ trợ: {format_name}")

    try:
        import zxingcpp
    except ImportError as exc:  # pragma: no cover - only occurs in incomplete installs
        raise RuntimeError(
            "Thiếu thư viện tạo mã. Hãy chạy: pip install -r requirements.txt"
        ) from exc

    barcode_format = getattr(zxingcpp.BarcodeFormat, FORMAT_NAMES[format_name])
    try:
        barcode = zxingcpp.create_barcode(content, barcode_format)
        bitmap = barcode.to_image(scale=scale, add_hrt=format_name in {"Code 128", "EAN-13", "UPC-A"})
        image = Image.fromarray(bitmap).convert("RGB")
        output = BytesIO()
        image.save(output, format="PNG")
        svg = barcode.to_svg(
            scale=scale,
            add_hrt=format_name in {"Code 128", "EAN-13", "UPC-A"},
        )
    except Exception as exc:
        raise ValueError(_friendly_generation_error(format_name, exc)) from exc
    return GeneratedCode(output.getvalue(), svg, format_name, content)


def _friendly_generation_error(format_name: str, error: Exception) -> str:
    hints = {
        "EAN-13": "EAN-13 cần 12 hoặc 13 chữ số hợp lệ.",
        "UPC-A": "UPC-A cần 11 hoặc 12 chữ số hợp lệ.",
    }
    return hints.get(format_name, f"Không thể tạo {format_name}: {error}")
