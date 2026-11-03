# Bench: vi-textmatch vs difflib vs rapidfuzz

Chạy lúc: 2026-11-03 16:14 +07  
Bộ dữ liệu: `bench/pairs.jsonl` — **102 cặp bịa hoàn toàn**, 61 cặp bằng nhau / 41 cặp khác nhau.  
Môi trường: Python 3.11.16, rapidfuzz 3.14.6.

## Phương pháp

- `vi_textmatch`: `compare(a, b, kind=...).match` (TEXT dùng ngưỡng 0.85 → TYPO vẫn tính là match).
- `difflib`: `SequenceMatcher(None, a, b).ratio() >= 0.9` trên chuỗi **thô**.
- `rapidfuzz`: `fuzz.ratio(a, b) >= 90.0` trên chuỗi **thô**.
- Ground truth là **nghĩa**, không phải hợp đồng của thư viện: hai chuỗi cùng một người/số tiền/ngày → `expected_equal=true`.
- Kết quả ném lỗi (MONEY/DATE không ép được kiểu) ghi `ERR` và tính là **không bằng** (fail-closed).
- Số cặp trong bảng == số dòng `pairs.jsonl`, không có cặp nào bị bỏ.

## Tổng

| matcher | accuracy | correct | false-equal ⚠ | false-diff | ERR |
|---|---|---|---|---|---|
| `vi_textmatch` | 94.1% | 96/102 | **5** | 1 | 2 |
| `difflib` | 45.1% | 46/102 | **23** | 33 | 0 |
| `rapidfuzz` | 45.1% | 46/102 | **23** | 33 | 0 |

## Theo kiểu dữ liệu — accuracy

| matcher | money | date | id | text |
|---|---|---|---|---|
| `vi_textmatch` | 100.0% (28/28) | 100.0% (22/22) | 100.0% (22/22) | 80.0% (24/30) |
| `difflib` | 42.9% (12/28) | 22.7% (5/22) | 45.5% (10/22) | 63.3% (19/30) |
| `rapidfuzz` | 42.9% (12/28) | 22.7% (5/22) | 45.5% (10/22) | 63.3% (19/30) |

## Theo kiểu dữ liệu — false-equal (sai theo hướng nguy hiểm)

| matcher | money | date | id | text |
|---|---|---|---|---|
| `vi_textmatch` | 0 | 0 | 0 | **5** |
| `difflib` | **5** | **7** | **7** | **4** |
| `rapidfuzz` | **5** | **7** | **7** | **4** |

## Các cặp bị coi là BẰNG NHAU nhưng thực ra KHÁC (chi tiết)

### `vi_textmatch` — 5 cặp

| a | b | kind | ghi chú |
|---|---|---|---|
| `Công ty TNHH Bình Minh` | `Công ty CP Bình Minh` | text | khác loại hình doanh nghiệp = khác pháp nhân |
| `Phạm Quốc Khánh` | `Phạm Quốc Kháng` | text | lệch 1 dấu = 2 người khác nhau (ratio rất cao) |
| `Nguyễn Văn An` | `Nguyễn Văn Ân` | text | lệch 1 dấu mũ = 2 người khác nhau |
| `Lý Thị Hương` | `Lý Thị Hường` | text | lệch 1 dấu huyền = 2 người khác nhau |
| `Đỗ Thị Mai Anh` | `Đỗ Thị Mai An` | text | rơi mất chữ cuối = khác tên |

### `difflib` — 23 cặp

| a | b | kind | ghi chú |
|---|---|---|---|
| `Phạm Quốc Khánh` | `Phạm Quốc Kháng` | text | lệch 1 dấu = 2 người khác nhau (ratio rất cao) |
| `Nguyễn Văn An` | `Nguyễn Văn Ân` | text | lệch 1 dấu mũ = 2 người khác nhau |
| `Lý Thị Hương` | `Lý Thị Hường` | text | lệch 1 dấu huyền = 2 người khác nhau |
| `Đỗ Thị Mai Anh` | `Đỗ Thị Mai An` | text | rơi mất chữ cuối = khác tên |
| `2.500.000.000` | `2.600.000.000` | money | lệch 100 triệu, ratio vẫn rất cao |
| `1.250.000,50` | `1.250.000,55` | money | lệch 5 xu |
| `2.000.000` | `-2.000.000` | money | khác dấu = ghi có vs ghi nợ |
| `12.000.000` | `12.000.00` | money | định dạng sai — kỳ vọng ném lỗi, không âm thầm so chuỗi |
| `150.000.000` | `150.000,000` | money | bẫy phẩy thập phân: 150.000,000 = 150.000 đồng, không phải 150 triệu |
| `12/08/2026` | `12/08/2025` | date | lệch 1 năm |
| `05/06/2026` | `05/06/2027` | date | lệch 1 năm, chuỗi chỉ khác 1 ký tự — bẫy ngưỡng 0.9 |
| `31/12/2025` | `31/12/2024` | date | lệch 1 năm |
| `2026-01-15` | `2026-01-16` | date | lệch 1 ngày |
| `29/02/2025` | `29/02/2025` | date | ngày không tồn tại — kỳ vọng ném lỗi, không âm thầm 'bằng' |
| `08/03/2026` | `09/03/2026` | date | lệch 1 ngày |
| `30/06/2026` | `30/07/2026` | date | lệch 1 tháng |
| `031234567890` | `031234567891` | id | lệch 1 số = 2 người, ratio ~0.92 |
| `031234567890` | `03123456789O` | id | chữ O thay số 0 — lỗi OCR kinh điển, ratio ~0.92 |
| `001099012345` | `001099012346` | id | lệch 1 số cuối |
| `0312345678901` | `031234567890` | id | lệch độ dài |
| `KH-2026-001` | `KH-2026-002` | id | lệch 1 số |
| `HD-2026-0457` | `HD-2026-0458` | id | lệch 1 số |
| `1234567890` | `1234567891` | id | lệch 1 số |

### `rapidfuzz` — 23 cặp

| a | b | kind | ghi chú |
|---|---|---|---|
| `Phạm Quốc Khánh` | `Phạm Quốc Kháng` | text | lệch 1 dấu = 2 người khác nhau (ratio rất cao) |
| `Nguyễn Văn An` | `Nguyễn Văn Ân` | text | lệch 1 dấu mũ = 2 người khác nhau |
| `Lý Thị Hương` | `Lý Thị Hường` | text | lệch 1 dấu huyền = 2 người khác nhau |
| `Đỗ Thị Mai Anh` | `Đỗ Thị Mai An` | text | rơi mất chữ cuối = khác tên |
| `2.500.000.000` | `2.600.000.000` | money | lệch 100 triệu, ratio vẫn rất cao |
| `1.250.000,50` | `1.250.000,55` | money | lệch 5 xu |
| `2.000.000` | `-2.000.000` | money | khác dấu = ghi có vs ghi nợ |
| `12.000.000` | `12.000.00` | money | định dạng sai — kỳ vọng ném lỗi, không âm thầm so chuỗi |
| `150.000.000` | `150.000,000` | money | bẫy phẩy thập phân: 150.000,000 = 150.000 đồng, không phải 150 triệu |
| `12/08/2026` | `12/08/2025` | date | lệch 1 năm |
| `05/06/2026` | `05/06/2027` | date | lệch 1 năm, chuỗi chỉ khác 1 ký tự — bẫy ngưỡng 0.9 |
| `31/12/2025` | `31/12/2024` | date | lệch 1 năm |
| `2026-01-15` | `2026-01-16` | date | lệch 1 ngày |
| `29/02/2025` | `29/02/2025` | date | ngày không tồn tại — kỳ vọng ném lỗi, không âm thầm 'bằng' |
| `08/03/2026` | `09/03/2026` | date | lệch 1 ngày |
| `30/06/2026` | `30/07/2026` | date | lệch 1 tháng |
| `031234567890` | `031234567891` | id | lệch 1 số = 2 người, ratio ~0.92 |
| `031234567890` | `03123456789O` | id | chữ O thay số 0 — lỗi OCR kinh điển, ratio ~0.92 |
| `001099012345` | `001099012346` | id | lệch 1 số cuối |
| `0312345678901` | `031234567890` | id | lệch độ dài |
| `KH-2026-001` | `KH-2026-002` | id | lệch 1 số |
| `HD-2026-0457` | `HD-2026-0458` | id | lệch 1 số |
| `1234567890` | `1234567891` | id | lệch 1 số |

## Các cặp bị coi là KHÁC nhưng thực ra BẰNG (chi tiết)

### `vi_textmatch` — 1 cặp

| a | b | kind | ERR | ghi chú |
|---|---|---|---|---|
| `Số 12 phố Lạch Tray` | `So 12 pho Lach Tray` | text |  | mất toàn bộ dấu — cùng địa chỉ, OCR bỏ dấu |

### `difflib` — 33 cặp

| a | b | kind | ERR | ghi chú |
|---|---|---|---|---|
| `Nguyễn Thị Hòa` | `Nguyễn Thị Hòa` | text |  | NFC vs NFD, cùng một tên — bẫy byte, không phải bẫy nghĩa |
| `Hoà Văn Bình` | `Hòa Văn Bình` | text |  | vị trí dấu thanh oà / òa, âm tiết mở |
| `Thuỳ Dương` | `Thùy Dương` | text |  | uỳ / ùy, âm tiết mở |
| `Hoè Thị Lan` | `Hòe Thị Lan` | text |  | oè / òe, âm tiết mở |
| `Nguyễn Thị Hòa` | `nguyễn thị hòa` | text |  | khác hoa/thường |
| `Số 12 phố Lạch Tray` | `So 12 pho Lach Tray` | text |  | mất toàn bộ dấu — cùng địa chỉ, OCR bỏ dấu |
| `Đinh Tiên Hoàng` | `Đinh Tiên Hoàng` | text |  | NFD trên chuỗi địa chỉ |
| `1.000.000đ` | `1,000,000 VND` | money |  | VN có hậu tố vs US không hậu tố — cùng 1 triệu |
| `2.500.000.000` | `2,500,000,000` | money |  | dấu nghìn VN vs US |
| `2.500.000.000` | `2500000000` | money |  | không phân cách |
| `5.000.000đ` | `5.000.000 đồng` | money |  | ký hiệu 'đ' vs 'đồng' |
| `5.000.000₫` | `5.000.000 VNĐ` | money |  | ₫ vs VNĐ |
| `1.250.000,50` | `1,250,000.50` | money |  | thập phân: phẩy VN vs chấm US |
| `0` | `0đ` | money |  | số 0 có/không hậu tố |
| `10.000.000` | `10.000.000,00` | money |  | phần thập phân bằng 0 |
| ` 1.000.000 ` | `1,000,000` | money |  | khoảng trắng hai đầu |
| `1.000.000` | `1.000.000 vnđ` | money |  | hậu tố chữ thường |
| `3.000.000` | `3,000,000.00` | money |  | US + thập phân .00 |
| `01/02/2026` | `1-2-2026` | date |  | thiếu số 0 + đổi dấu phân cách |
| `12/08/2026` | `12-8-2026` | date |  | DD/MM/YYYY vs D-M-YYYY |
| `12/08/2026` | `2026-08-12` | date |  | DD/MM/YYYY vs ISO YYYY-MM-DD |
| `2026-01-15` | `15/01/2026` | date |  | ISO vs DD/MM |
| `1/2/2026` | `01/02/2026` | date |  | thiếu số 0 hai vế |
| `31/12/2025` | `31-12-2025` | date |  | đổi dấu phân cách |
| `01.02.2026` | `1.2.2026` | date |  | dấu chấm + thiếu số 0 |
| `01 02 2026` | `01/02/2026` | date |  | dấu cách vs dấu gạch chéo |
| `29/02/2024` | `29-2-2024` | date |  | năm nhuận hợp lệ |
| `07/09/2026` | `7/9/2026` | date |  | thiếu số 0 hai vế |
| `KH-2026-001` | `kh 2026 001` | id |  | gạch nối + hoa/thường |
| `KH2026 01` | `kh2026-01` | id |  | khoảng trắng vs gạch nối |
| `STK-1234567890` | `STK 1234 5678 90` | id |  | nhóm số + dấu phân cách |
| `AB-12-CD` | `ab12cd` | id |  | mã chữ + số, khác hoa/thường và gạch nối |
| `CC-2026-77` | `CC 2026 77` | id |  | dấu phân cách |

### `rapidfuzz` — 33 cặp

| a | b | kind | ERR | ghi chú |
|---|---|---|---|---|
| `Nguyễn Thị Hòa` | `Nguyễn Thị Hòa` | text |  | NFC vs NFD, cùng một tên — bẫy byte, không phải bẫy nghĩa |
| `Hoà Văn Bình` | `Hòa Văn Bình` | text |  | vị trí dấu thanh oà / òa, âm tiết mở |
| `Thuỳ Dương` | `Thùy Dương` | text |  | uỳ / ùy, âm tiết mở |
| `Hoè Thị Lan` | `Hòe Thị Lan` | text |  | oè / òe, âm tiết mở |
| `Nguyễn Thị Hòa` | `nguyễn thị hòa` | text |  | khác hoa/thường |
| `Số 12 phố Lạch Tray` | `So 12 pho Lach Tray` | text |  | mất toàn bộ dấu — cùng địa chỉ, OCR bỏ dấu |
| `Đinh Tiên Hoàng` | `Đinh Tiên Hoàng` | text |  | NFD trên chuỗi địa chỉ |
| `1.000.000đ` | `1,000,000 VND` | money |  | VN có hậu tố vs US không hậu tố — cùng 1 triệu |
| `2.500.000.000` | `2,500,000,000` | money |  | dấu nghìn VN vs US |
| `2.500.000.000` | `2500000000` | money |  | không phân cách |
| `5.000.000đ` | `5.000.000 đồng` | money |  | ký hiệu 'đ' vs 'đồng' |
| `5.000.000₫` | `5.000.000 VNĐ` | money |  | ₫ vs VNĐ |
| `1.250.000,50` | `1,250,000.50` | money |  | thập phân: phẩy VN vs chấm US |
| `0` | `0đ` | money |  | số 0 có/không hậu tố |
| `10.000.000` | `10.000.000,00` | money |  | phần thập phân bằng 0 |
| ` 1.000.000 ` | `1,000,000` | money |  | khoảng trắng hai đầu |
| `1.000.000` | `1.000.000 vnđ` | money |  | hậu tố chữ thường |
| `3.000.000` | `3,000,000.00` | money |  | US + thập phân .00 |
| `01/02/2026` | `1-2-2026` | date |  | thiếu số 0 + đổi dấu phân cách |
| `12/08/2026` | `12-8-2026` | date |  | DD/MM/YYYY vs D-M-YYYY |
| `12/08/2026` | `2026-08-12` | date |  | DD/MM/YYYY vs ISO YYYY-MM-DD |
| `2026-01-15` | `15/01/2026` | date |  | ISO vs DD/MM |
| `1/2/2026` | `01/02/2026` | date |  | thiếu số 0 hai vế |
| `31/12/2025` | `31-12-2025` | date |  | đổi dấu phân cách |
| `01.02.2026` | `1.2.2026` | date |  | dấu chấm + thiếu số 0 |
| `01 02 2026` | `01/02/2026` | date |  | dấu cách vs dấu gạch chéo |
| `29/02/2024` | `29-2-2024` | date |  | năm nhuận hợp lệ |
| `07/09/2026` | `7/9/2026` | date |  | thiếu số 0 hai vế |
| `KH-2026-001` | `kh 2026 001` | id |  | gạch nối + hoa/thường |
| `KH2026 01` | `kh2026-01` | id |  | khoảng trắng vs gạch nối |
| `STK-1234567890` | `STK 1234 5678 90` | id |  | nhóm số + dấu phân cách |
| `AB-12-CD` | `ab12cd` | id |  | mã chữ + số, khác hoa/thường và gạch nối |
| `CC-2026-77` | `CC 2026 77` | id |  | dấu phân cách |

## Kiểm tra độ nhạy: baseline có được chuẩn hoá?

Baseline chạy trên `normalize()` của vi-textmatch (NFC + dấu thanh + trắng + casefold) nhưng **không** có logic theo kiểu dữ liệu — để tách xem lợi thế đến từ chuẩn hoá hay từ type-aware.

| matcher | accuracy | false-equal ⚠ | false-diff | ERR |
|---|---|---|---|---|
| `difflib+norm` | 50.0% | **24** | 27 | 0 |
| `rapidfuzz+norm` | 50.0% | **24** | 27 | 0 |

## Quan sát (sinh tự động từ số liệu trên)

- `vi_textmatch`: 96/102 (94.1%), false-equal 5, false-diff 1, ERR 2. Kiểu tệ nhất theo false-equal: `text` (5 cặp).
- `difflib`: 46/102 (45.1%), false-equal 23, false-diff 33, ERR 0. Kiểu tệ nhất theo false-equal: `date` (7 cặp).
- `rapidfuzz`: 46/102 (45.1%), false-equal 23, false-diff 33, ERR 0. Kiểu tệ nhất theo false-equal: `date` (7 cặp).

## Nhận định

1. **Lỗi nguy hiểm nằm gần hết ở baseline.** `vi_textmatch` false-equal 5 cặp; difflib/rapidfuzz false-equal 23 cặp — ngang nhau vì cả hai đều chỉ so ký tự, và cả hai đều nói `031234567890` ≈ `031234567891`.
2. **Toàn bộ false-equal của baseline rơi vào money/date/id** (5 money, 7 date, 7 id, 4 text) — đúng chỗ SPEC cấm dùng ratio. False-equal của `vi_textmatch` chỉ còn ở `text` (5 cặp).
3. **Ngưỡng 0.9 là dao mỏng.** 14/102 cặp có ratio thô nằm trong ±1 điểm quanh 90 — trong đó có những cặp khác nhau thật (`12/08/2026` vs `12/08/2025`, `05/06/2026` vs `05/06/2027`: đúng 90.0 → được coi là BẰNG). Chỉnh ngưỡng lên 0.95 không cứu được: nó chỉ đổi cặp nào bị coi là khác.
4. **Chuẩn hoá không phải là thứ tạo ra khác biệt.** Cho baseline dùng `normalize()` của thư viện (khối 'Kiểm tra độ nhạy') thì accuracy chỉ lên 50.0%, còn false-equal **tăng** (23 → 24): chuẩn hoá làm hai chuỗi khác nghĩa trông giống nhau hơn. Giá trị của thư viện nằm ở **type-aware**, không phải ở NFC.
5. **Phần còn lại của `vi_textmatch` là giới hạn của TEXT, không phải bug.** 5 false-equal đều là tên/địa danh khác người thật nhưng lệch 1 dấu (`Phạm Quốc Khánh` vs `Kháng`, `Nguyễn Văn An` vs `Ân`) — ratio ≥ 0.85 nên bị xếp TYPO. Với trường tên người, ngưỡng 0.85 của TEXT là quá rộng; muốn chặn phải so thêm thành phần tên hoặc dùng kind chặt hơn.
6. **1 false-diff**: mất sạch dấu (`Số 12 phố Lạch Tray` vs `So 12 pho Lach Tray`) — không thư viện nào trong ba cái xử lý được, vì cả ba đều không bỏ dấu.
7. **ERR (2 cặp) đều rơi về phía an toàn** (2/2 là cặp vốn khác nhau: `12.000.00`, `29/02/2025`). Nói cách khác điểm 100% của money/date có một phần công của việc ném lỗi thay vì đoán — đó chính là hành vi SPEC yêu cầu.
8. **difflib và rapidfuzz cho kết quả y hệt nhau** trên bộ này (0/102 cặp lệch dự đoán). Không phải vì cùng code — hai thuật toán khác nhau (matching-blocks vs Levenshtein) — mà vì chuỗi ở đây ngắn và gần bằng độ dài. Đừng đọc kết quả này thành 'rapidfuzz vô dụng': nó nhanh hơn nhiều lần, chỉ là không an toàn hơn cho bài toán này.

## Chạy lại

```bash
python3 bench/run_bench.py            # ghi bench/RESULTS.md
python3 bench/gen_pairs.py            # sinh lại bench/pairs.jsonl (tất định)
```

rapidfuzz là dependency **chỉ của benchmark**, không phải của thư viện (thư viện vẫn zero-dependency). Nếu thiếu rapidfuzz, script vẫn chạy và bỏ dòng đó.
