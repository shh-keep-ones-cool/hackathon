# Hướng dẫn setup và chạy project (Windows 10/11 + VS Code)

## 0. Cài công cụ

1. Cài **Python 3.11 hoặc 3.12**: https://www.python.org/downloads/ (tick `Add Python to PATH`).
2. Cài **Visual Studio Code**: https://code.visualstudio.com/.
3. Cài **Git** nếu dùng GitHub: https://git-scm.com/downloads.
4. Cài **Node.js 20 LTS** nếu muốn chạy kiểm tra OLS JavaScript ↔ Python: https://nodejs.org/.
5. Cài extension **Python** của Microsoft trong VS Code.

## 1. Mở project và tạo môi trường ảo

Giải nén `pci_dashboard_project.zip`, mở folder `pci_dashboard_project` bằng VS Code. Mở Terminal → New Terminal và chạy PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Nếu PowerShell chặn activate, chạy lệnh sau trong cửa sổ terminal hiện tại, rồi activate lại:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Trên macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 2. Kiểm tra cấu trúc ban đầu

```bash
python analysis/validate_data.py
```

Kỳ vọng: 34 dòng PCI 2025, đủ 9 chỉ số thành phần, 63 dòng crosswalk và tổng `share=1` theo mỗi tỉnh cũ. GeoJSON sẽ hiện cảnh báo cho đến khi bạn tạo file.

## 3. Thu thập PCI 2025

Dữ liệu 34×9 đã được điền trong `data/pci_provinces.csv` theo bảng công bố trên trang VCCI PCI 2025. Để tự cào lại và lưu bản gốc:

```bash
python analysis/scrape_pci_2025.py
```

Script sẽ tải HTML trang và thử tải XLSX chính thức vào `data/raw/pci/`, rồi cập nhật 9 subindices. Nếu cấu trúc HTML thay đổi, script dừng thay vì tự đoán. Kiểm tra đối chiếu 34×9 giá trị với workbook của VCCI trước khi dùng làm kết quả cuối cùng.

BPI nằm riêng trong `data/pci_bpi_2025.csv`; không gộp BPI vào 9 subindices.

**Lưu ý:** `pci_total` cố ý để trống vì dashboard PCI 2.0 công khai không đưa ra điểm tổng có thể so sánh theo cách PCI cũ. Không tự cộng chín chỉ số.

## 4. Tải dữ liệu PCI lịch sử 63 tỉnh

```bash
python analysis/download_pci_archives.py
```

Script tải các workbook tìm thấy ở kho VCCI 2010–2024 vào `data/raw/pci/`. Nếu website đổi cấu trúc, tải thủ công tại https://pcivietnam.vn/en/pci-data rồi đặt tên `PCI_YYYY.xlsx` hoặc `PCI_YYYY.xls`.

**Không dùng một parser chung để đoán header của tất cả năm.** Mỗi workbook có thể có sheet, tên cột và cấu trúc khác nhau. Mở từng file, xác định sheet và cột bằng mắt, sau đó điền `config/pci_historical_column_map_template.csv`:

- `sheet_name`: tên sheet chứa điểm cấp tỉnh.
- `province_column`: cột tên tỉnh.
- `surveyed_firms_column`: cột số doanh nghiệp khảo sát, nếu có.
- `source_col_pci_old_1` … `_10`: tên header thực tế trong workbook cho từng chỉ số legacy.
- `framework_version`: mã phiên bản đã đối chiếu với báo cáo/phương pháp năm đó.

Khi đã điền và kiểm tra mapping:

```bash
python analysis/import_historical_pci.py
```

Script chỉ nhập năm có mapping đủ; không đoán hoặc tự gán chỉ số. Bản import phải được so sánh thủ công với workbook gốc và ghi vào `docs/AI_USE.md`.

## 5. Thu thập outcomes từ NSO/GSO

Nguồn: https://www.nso.gov.vn/so-lieu-thong-ke/ . Các bảng cần lấy gồm:

- Số doanh nghiệp đăng ký thành lập mới phân theo địa phương.
- Số doanh nghiệp đang hoạt động tại thời điểm 31/12 hàng năm phân theo địa phương.
- Dân số trung bình phân theo địa phương.
- GRDP bình quân đầu người phân theo địa phương; nếu cần tổng GRDP, lấy đúng bảng GRDP theo giá hiện hành hoặc giá so sánh.

### Cách an toàn nhất (khuyến nghị)

1. Mở đúng bảng trên NSO/PXWeb.
2. Chọn chỉ tiêu, tỉnh và năm cần thiết.
3. Export Excel/CSV.
4. Giữ file gốc trong `data/raw/gso/`.
5. Chuẩn hóa dữ liệu về template `data/raw/gso/gso_34_2025_template.csv` cho năm 2025 hoặc `data/raw/gso/gso_63_long_template.csv` cho chuỗi 63 tỉnh.
6. Ghi URL, tên/mã bảng, ngày tải, đơn vị và price basis ngay trong CSV/README.

Nếu muốn gọi PxWeb API, trước hết lấy URL API chính xác của bảng từ trang NSO rồi chạy:

```bash
python analysis/fetch_gso_pxweb.py --endpoint "<PXWEB_API_ENDPOINT>" --metadata
```

Đọc các dimension/item code được lưu trong `data/raw/gso/pxweb_metadata.json`, tự tạo query theo metadata và chạy:

```bash
python analysis/fetch_gso_pxweb.py --endpoint "<PXWEB_API_ENDPOINT>" --query-json config/gso_pxweb_query_template.json --out data/raw/gso/pxweb_export.csv
```

Không đoán API endpoint hoặc mã địa phương. PxWeb query cần dùng đúng code mà metadata của bảng trả về.

### Import 34 tỉnh năm 2025 vào PCI file

Copy template thành `data/raw/gso/gso_34_2025.csv`, điền dữ liệu chuẩn hóa, sau đó:

```bash
python analysis/import_gso_34.py
```

Quy ước: `pop_thousand` = nghìn người; `grdp_billion_vnd` = tỷ đồng; `grdp_price_basis` ghi `current` hoặc `constant_YYYY`; `firms_new` và `firms_active` là số doanh nghiệp (số đếm). Không nhập tỷ lệ doanh nghiệp/1.000 dân, log hoặc z-score vào file raw.

## 6. Tổng hợp outcomes từ 63 xuống 34

Khi `outcomes_panel_63.csv` đã có số liệu:

```bash
python analysis/aggregate_old_to_new.py
```

Kết quả `data/outcomes_panel_34.csv`. Script cộng số đếm và dân số theo `share`; `grdp_pc` được tổng hợp bằng bình quân gia quyền dân số. Không cộng điểm PCI. Script sẽ fail nếu crosswalk thiếu tỉnh hoặc share không bằng 1.

## 7. Tạo GeoJSON 34 tỉnh

Tải GeoJSON admin-1 phiên bản có hiệu lực từ **01/07/2025** (ví dụ bộ OCHA/HDX Viet Nam COD-AB version 02, 34 provinces). Không dùng shapefile 63 tỉnh trước sắp xếp.

Chạy:

```bash
python analysis/build_geojson.py --input "data/raw/gso/vnm_admin1_2025.geojson" --name-field "NAME_1"
```

Bỏ `--name-field` nếu script tự nhận diện được field tên tỉnh. Nếu lỗi tên, đọc danh sách properties và bổ sung alias đã xác minh trong `analysis/build_geojson.py`. Output là `data/vn_provinces.geojson` (EPSG:4326), mỗi feature có `province_id` trùng CSV.

## 8. Tạo biến phân tích và chạy OLS

Sau khi `pci_provinces.csv` đã có `pop` và `firms_new`:

```bash
python analysis/derive_and_model.py --outcome firms_new
```

Script tính `firms_new_per_1000 = firms_new / pop` do `pop` được lưu theo nghìn người. Chạy chín mô hình OLS riêng, mỗi mô hình có một PCI subindex làm biến giải thích. Không chạy một mô hình nhồi 9 chỉ số với n=34. Kết quả: `data/derived_features_2025.csv` và `data/model_results.csv`.

Đây là phân tích tương quan/cross-sectional association, không phải tác động nhân quả. Nếu thiếu GSO outcomes, script sẽ dừng; không tự điền số.

## 9. Kiểm tra dữ liệu và độ nhất quán JS/Python

```bash
python analysis/validate_data.py
python analysis/test_ols_parity.py
```

Lệnh thứ hai cần Node.js. Chỉ chạy sau khi đã tạo `derived_features_2025.csv` và có outcome đủ dữ liệu.

## 10. Xem dashboard và publish GitHub Pages

Để chạy local tránh lỗi CORS, từ thư mục gốc chạy:

```bash
python -m http.server 8000
```

Mở `http://localhost:8000/docs/`.

Để publish:

1. Tạo GitHub repository và push project.
2. Đảm bảo `data/raw/` không được commit (đã gitignore).
3. Mở Settings → Pages → Deploy from a branch → `main` / folder `/docs`.
4. Kiểm tra link CSV trong dashboard hoạt động ở GitHub Pages.
5. Chỉ publish datasets/derived values khi đã rà soát điều khoản VCCI/NSO và ghi nguồn theo đúng yêu cầu.

## 11. Thứ tự workflow đề xuất

`01 PCI 2025 → 02 legacy PCI → 03 GSO outcomes → 04 crosswalk aggregation → 05 GeoJSON → 06 validation → 07 OLS → 08 dashboard`.

Sau mỗi stage: lưu nguồn raw, kiểm tra với tài liệu gốc, cập nhật `docs/AI_USE.md`, cập nhật `README.md` nếu có thay đổi đơn vị/định nghĩa, rồi mới chuyển stage tiếp theo.
