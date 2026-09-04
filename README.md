# Excel Merger Pro

Ứng dụng desktop PySide6 gom các sheet được chọn từ nhiều workbook vào một file `.xlsx`. Mỗi sheet vẫn là một sheet riêng; dữ liệu không bị nối thành một bảng.

## Chức năng

- Kéo thả hoặc chọn nhiều file `.xlsx`, `.xlsm`.
- Hiển thị mọi sheet, chọn/bỏ chọn, đổi tên và sắp xếp thứ tự.
- Kiểm tra giới hạn 31 ký tự và ký tự cấm trong tên sheet; tự xử lý tên trùng.
- Sao chép dữ liệu, công thức hoặc cached value, style, border, alignment, merge cell, kích thước hàng/cột, hàng/cột ẩn, freeze panes, filter, hyperlink, comment, ảnh và thiết lập in ở mức `openpyxl` hỗ trợ.
- Chạy ghép trên `QThread`, có tiến độ và hủy an toàn giữa các sheet.
- Lịch sử SQLite, settings JSON và rotating log nằm ngoài thư mục cài đặt.
- Kiểm tra update nền, download installer và bắt buộc xác minh SHA-256 trước khi chạy.
- Giao diện bốn trang theo phong cách Windows 11, icon SVG, shortcut bàn phím và menu chuột phải.

## Chạy từ source

Yêu cầu Python 3.11–3.13 được khuyến nghị trên Windows.

```powershell
py -3 -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python main.py
```

Dữ liệu người dùng được lưu tại `%LOCALAPPDATA%\ExcelMergerPro\` trên Windows. Trên Linux dùng `$XDG_DATA_HOME/ExcelMergerPro`.

## Kiểm thử

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest tests
```

## Build EXE và installer

1. Cài Python và [Inno Setup 6](https://jrsoftware.org/isinfo.php), thêm `ISCC.exe` vào `PATH`. Bản phát hành dùng Nuitka để biên dịch Python thành native binary, khó dịch ngược hơn bundle PyInstaller thông thường.
2. Đồng bộ `VERSION` trong `app/config.py`, `APP_VERSION` trong `build.bat`, rồi chạy:

```bat
build.bat
```

Kết quả:

- `dist\ExcelMergerPro.exe`
- `installer-output\ExcelMergerPro-Setup-1.0.0.exe`

Installer cài theo user vào `%LOCALAPPDATA%\Programs\Excel Merger Pro`, không yêu cầu quyền Administrator. Cùng `AppId` giúp phiên bản mới nâng cấp đè lên bản cũ; dữ liệu trong `%LOCALAPPDATA%\ExcelMergerPro` không bị gỡ hoặc ghi đè.

Nuitka làm tăng đáng kể chi phí phân tích ngược nhưng không có giải pháp nào bảo vệ tuyệt đối mã chạy trên máy khách. Không đặt private key, token GitHub hoặc bí mật server trong source/binary; các bí mật phải nằm ở server hoặc GitHub Actions Secrets.

## Phát hành cập nhật

1. Ứng dụng đọc release mới nhất trực tiếp từ GitHub Releases API của `codefreesher/MergeExcel`.
2. Workflow tự build installer, tạo SHA-256 và upload cả hai asset khi push tag `v*`.
3. Updater tự tìm asset `ExcelMergerPro-Setup-x.x.x.exe`, đọc version từ tag và xác minh digest trước khi chạy.
4. Muốn bắt buộc cập nhật, thêm dòng `[mandatory]` vào nội dung GitHub Release.

Ứng dụng từ chối chạy installer nếu thiếu SHA-256, digest sai hoặc download lỗi. `mandatory: true` sẽ ẩn nút “Để sau”. Nên ký code-signing cho cả EXE và installer trước khi phát hành.

### Phát hành tự động bằng GitHub Actions

Workflow `.github/workflows/release.yml` chạy kiểm thử, build trên Windows và tạo GitHub Release khi push tag:

```bash
git tag v1.0.0
git push origin v1.0.0
```

Sau khi workflow hoàn tất, ứng dụng tự nhận release và installer mới; không cần sửa `update.json` thủ công.

## Giới hạn định dạng Excel

`openpyxl` không thể bảo toàn tuyệt đối mọi đối tượng Excel độc quyền (một số chart, slicer, macro/VBA project, ActiveX và liên kết ngoài phức tạp). File `.xls` cũ chưa được hỗ trợ; hãy chuyển sang `.xlsx` trước. Output luôn là `.xlsx`, vì vậy macro từ `.xlsm` không được đưa vào output. Với workbook cần độ trung thực tuyệt đối trên Windows, cần một backend Microsoft Excel COM riêng.
