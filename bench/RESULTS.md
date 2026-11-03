# Bench: vi-textmatch vs difflib vs rapidfuzz

Sinh tự động bởi `bench/run_bench.py` — phần số liệu không sửa tay; phần nhận định ở cuối cũng lấy số từ chính lần chạy này.

- Chạy lúc: 2026-11-03 09:37 UTC
- Commit: `e7b00c3` · Python 3.13.18 · rapidfuzz 3.14.6 · Linux-6.18.44-fc-v230-x86_64-with-glibc2.39
- Dữ liệu: `pairs.jsonl` — **100 cặp bịa hoàn toàn**, 55 cặp bằng nhau / 45 cặp khác nhau (money 25, date 20, id 25, name 23, text 7).

## Phương pháp

- `vi_textmatch`: `compare(a, b, kind=...).match`; TEXT coi `TYPO` (ratio ≥ 0.85) là match, MONEY/DATE ném lỗi khi không ép được kiểu.
- `difflib`: `SequenceMatcher(None, a, b).ratio() >= 0.9` trên chuỗi **thô**.
- `rapidfuzz`: `fuzz.ratio(a, b) >= 90.0` trên chuỗi **thô**.
- Chuẩn đúng là **nghĩa**, chốt trước khi chạy: cùng một người / cùng một số tiền / cùng một ngày / cùng một định danh → `expected_equal = true`.
- Ném lỗi được ghi `ERR` và tính là **không bằng** (fail-closed) — đúng hướng thư viện mong muốn, và vẫn bị tính vào accuracy.
- accuracy = đoán đúng / tổng; false-equal = đoán BẰNG nhưng thực ra KHÁC; false-diff = đoán KHÁC nhưng thực ra BẰNG.

## Tổng

| matcher | accuracy | đúng | false-equal ⚠ | false-diff | ERR |
|---|---|---|---|---|---|
| `vi_textmatch` | 95.0% | 95/100 | **2** | 3 | 2 |
| `difflib` | 46.0% | 46/100 | **22** | 32 | 0 |
| `rapidfuzz` | 46.0% | 46/100 | **22** | 32 | 0 |

## Theo kiểu dữ liệu — accuracy

| matcher | money | date | id | name | text | total |
|---|---|---|---|---|---|---|
| `vi_textmatch` | 100.0% | 100.0% | 100.0% | 87.0% | 71.4% | 95.0% |
| `difflib` | 36.0% | 30.0% | 52.0% | 60.9% | 57.1% | 46.0% |
| `rapidfuzz` | 36.0% | 30.0% | 52.0% | 60.9% | 57.1% | 46.0% |

## Theo kiểu dữ liệu — false-equal (hướng sai nguy hiểm)

| matcher | money | date | id | name | text | total |
|---|---|---|---|---|---|---|
| `vi_textmatch` | 0 | 0 | 0 | 0 | **2** | **2** |
| `difflib` | **4** | **5** | **9** | **3** | **1** | **22** |
| `rapidfuzz` | **4** | **5** | **9** | **3** | **1** | **22** |

## Theo kiểu dữ liệu — false-diff (hướng sai gây phiền)

| matcher | money | date | id | name | text | total |
|---|---|---|---|---|---|---|
| `vi_textmatch` | 0 | 0 | 0 | 3 | 0 | 3 |
| `difflib` | 12 | 9 | 3 | 6 | 2 | 32 |
| `rapidfuzz` | 12 | 9 | 3 | 6 | 2 | 32 |

## Theo kiểu dữ liệu — ERR (ném lỗi, fail-closed)

| matcher | money | date | id | name | text | total |
|---|---|---|---|---|---|---|
| `vi_textmatch` | 1 | 1 | 0 | 0 | 0 | 2 |
| `difflib` | 0 | 0 | 0 | 0 | 0 | 0 |
| `rapidfuzz` | 0 | 0 | 0 | 0 | 0 | 0 |

## Bằng chứng — từng cặp bị đoán SAI

### `vi_textmatch` — false-equal: 2 cặp

| kind | a | b | thước đo | ERR | ghi chú |
|---|---|---|---|---|---|
| text | `Số 12 Ngõ 34 Phố Hoa Ban, Phường 5` | `Số 21 Ngõ 34 Phố Hoa Ban, Phường 5` | TYPO (Match ratio: 0.9706 (typo suspected)) |  | số nhà 12→21, phần còn lại giống hệt |
| text | `Công ty TNHH Bình Minh` | `Công ty CP Bình Minh` | TYPO (Match ratio: 0.8571 (typo suspected)) |  | khác loại hình doanh nghiệp = khác pháp nhân |

### `vi_textmatch` — false-diff: 3 cặp

| kind | a | b | thước đo | ERR | ghi chú |
|---|---|---|---|---|---|
| name | `Trịnh Công Sơnn` | `Trịnh Công Sơn` | DIFFERENT (Name components differ at position 3) |  | lặp 1 ký tự cuối (gõ/OCR) |
| name | `Lương Thị Ánh Tuyế` | `Lương Thị Ánh Tuyết` | DIFFERENT (Name components differ at position 4) |  | nuốt ký tự cuối (OCR) |
| name | `Hoàng Văn Quag` | `Hoàng Văn Quang` | DIFFERENT (Name components differ at position 3) |  | rơi 1 phụ âm cuối |

### `difflib` — false-equal: 22 cặp

| kind | a | b | thước đo | ERR | ghi chú |
|---|---|---|---|---|---|
| name | `Phạm Quốc Khánh` | `Phạm Quốc Kháng` | ratio 0.9333 |  | lệch 1 dấu, mỗi dạng đều là tên hợp lệ → phải soát lại |
| text | `Số 12 Ngõ 34 Phố Hoa Ban, Phường 5` | `Số 21 Ngõ 34 Phố Hoa Ban, Phường 5` | ratio 0.9706 |  | số nhà 12→21, phần còn lại giống hệt |
| name | `Trần Thị Bích Ngọc` | `Trần Thị Bích Ngà` | ratio 0.9143 |  | tên gọi khác — hai người |
| name | `Vũ Hoàng Nam` | `Vũ Hoàng Nga` | ratio 0.9167 |  | tên gọi khác — hai người |
| money | `2.500.000.000` | `2.600.000.000` | ratio 0.9231 |  | lệch 100 triệu, chuỗi vẫn rất giống |
| money | `2.000.000` | `-2.000.000` | ratio 0.9474 |  | khác dấu = ghi có vs ghi nợ |
| money | `1.250.000,50` | `1.250.000,55` | ratio 0.9167 |  | lệch 5 xu |
| money | `12.000.000` | `12.000.00` | ratio 0.9474 |  | định dạng sai (nhóm 2 chữ số) — kỳ vọng ném lỗi, không âm thầm so chuỗi |
| date | `12/08/2026` | `12/08/2025` | ratio 0.9 |  | lệch 1 năm |
| date | `2026-01-15` | `2026-01-16` | ratio 0.9 |  | lệch 1 ngày |
| date | `31/12/2025` | `31/12/2024` | ratio 0.9 |  | lệch 1 năm |
| date | `30/06/2026` | `30/07/2026` | ratio 0.9 |  | lệch 1 tháng |
| date | `08/03/2026` | `09/03/2026` | ratio 0.9 |  | lệch 1 ngày |
| id | `031234567890` | `031234567891` | ratio 0.9167 |  | CCCD lệch đúng 1 số cuối — hai người |
| id | `031234567890` | `03123456789O` | ratio 0.9167 |  | chữ O thay số 0 — lỗi OCR kinh điển |
| id | `031234567890` | `031234567980` | ratio 0.9167 |  | đảo 2 chữ số — cùng độ dài |
| id | `0312345678901` | `031234567890` | ratio 0.96 |  | lệch độ dài (thêm 1 chữ số) |
| id | `001099012345` | `001099012346` | ratio 0.9167 |  | lệch 1 số cuối |
| id | `KH-2026-001` | `KH-2026-002` | ratio 0.9091 |  | lệch 1 số |
| id | `HD-2026-0457` | `HD-2026-0458` | ratio 0.9167 |  | lệch 1 số |
| id | `012345678901` | `012345678900` | ratio 0.9167 |  | lệch 1 số cuối |
| id | `031234567890` | `041234567890` | ratio 0.9167 |  | lệch chữ số đầu |

### `difflib` — false-diff: 32 cặp

| kind | a | b | thước đo | ERR | ghi chú |
|---|---|---|---|---|---|
| name | `Nguyễn Thị Hòa` | `Nguyễn Thị Hòa` | ratio 0.6875 |  | NFC vs NFD: cùng tên, khác byte |
| text | `Đinh Tiên Hoàng` | `Đinh Tiên Hoàng` | ratio 0.8125 |  | NFD trên địa danh có ký tự Đ |
| name | `Hoà Văn Bình` | `Hòa Văn Bình` | ratio 0.8333 |  | vị trí dấu thanh oà/òa, âm tiết mở |
| name | `Thuỳ Dương` | `Thùy Dương` | ratio 0.8 |  | uỳ/ùy, âm tiết mở |
| name | `Hoè Thị Lan` | `Hòe Thị Lan` | ratio 0.8182 |  | oè/òe, âm tiết mở |
| name | `Nguyễn Thị Hòa` | `nguyễn thị hòa` | ratio 0.7857 |  | chỉ khác hoa/thường |
| name | `Lý	Thị	Mai` | `Lý Thị Mai` | ratio 0.8 |  | tab thay dấu cách |
| text | `CÔNG TY TNHH THƯƠNG MẠI BÌNH AN` | `Công ty TNHH Thương mại Bình An` | ratio 0.4516 |  | tên tổ chức, chỉ khác hoa/thường |
| money | `1.000.000đ` | `1,000,000 VND` | ratio 0.6087 |  | kiểu VN có 'đ' vs kiểu US có 'VND' |
| money | `2.500.000.000` | `2,500,000,000` | ratio 0.7692 |  | dấu phân nghìn VN vs US |
| money | `2.500.000.000` | `2500000000` | ratio 0.8696 |  | có phân cách vs số trơn |
| money | `2.500.000,50` | `2,500,000.50` | ratio 0.3333 |  | thập phân: phẩy VN vs chấm US |
| money | `5.000.000đ` | `5.000.000 đồng` | ratio 0.8333 |  | 'đ' vs 'đồng' |
| money | `5.000.000₫` | `5.000.000 VNĐ` | ratio 0.7826 |  | '₫' vs 'VNĐ' |
| money | `0` | `0đ` | ratio 0.6667 |  | số 0 có/không hậu tố |
| money | `10.000.000` | `10.000.000,00` | ratio 0.8696 |  | phần thập phân bằng 0 |
| money | ` 1.000.000 ` | `1,000,000` | ratio 0.7 |  | khoảng trắng hai đầu |
| money | `1.000.000` | `1.000.000 vnđ` | ratio 0.8182 |  | hậu tố chữ thường |
| money | `3.000.000` | `3,000,000.00` | ratio 0.6667 |  | US + thập phân .00 |
| money | `7.000.000` | `7.000.000 VND` | ratio 0.8182 |  | một bên có hậu tố, một bên không |
| date | `01/02/2026` | `1-2-2026` | ratio 0.6667 |  | thiếu số 0 + đổi dấu phân cách |
| date | `12/08/2026` | `12-8-2026` | ratio 0.7368 |  | DD/MM/YYYY vs D-M-YYYY |
| date | `12/08/2026` | `2026-08-12` | ratio 0.4 |  | DD/MM/YYYY vs ISO YYYY-MM-DD |
| date | `2026-01-15` | `15/01/2026` | ratio 0.4 |  | ISO vs DD/MM |
| date | `01.02.2026` | `1.2.2026` | ratio 0.8889 |  | dấu chấm + thiếu số 0 |
| date | `01 02 2026` | `01/02/2026` | ratio 0.8 |  | dấu cách vs dấu gạch chéo |
| date | `29/02/2024` | `29-2-2024` | ratio 0.7368 |  | 29/02 năm nhuận hợp lệ |
| date | `31/12/2025` | `31-12-2025` | ratio 0.8 |  | đổi dấu phân cách |
| date | `07/09/2026` | `7/9/2026` | ratio 0.8889 |  | thiếu số 0 hai vế |
| id | `KH-2026-001` | `kh 2026 001` | ratio 0.6364 |  | gạch nối + hoa/thường |
| id | `STK-1234567890` | `STK 1234 5678 90` | ratio 0.8667 |  | nhóm số + dấu phân cách |
| id | `AB-12-CD` | `ab12cd` | ratio 0.2857 |  | mã chữ + số, khác case và gạch nối |

### `rapidfuzz` — false-equal: 22 cặp

| kind | a | b | thước đo | ERR | ghi chú |
|---|---|---|---|---|---|
| name | `Phạm Quốc Khánh` | `Phạm Quốc Kháng` | ratio 93.33 |  | lệch 1 dấu, mỗi dạng đều là tên hợp lệ → phải soát lại |
| text | `Số 12 Ngõ 34 Phố Hoa Ban, Phường 5` | `Số 21 Ngõ 34 Phố Hoa Ban, Phường 5` | ratio 97.06 |  | số nhà 12→21, phần còn lại giống hệt |
| name | `Trần Thị Bích Ngọc` | `Trần Thị Bích Ngà` | ratio 91.43 |  | tên gọi khác — hai người |
| name | `Vũ Hoàng Nam` | `Vũ Hoàng Nga` | ratio 91.67 |  | tên gọi khác — hai người |
| money | `2.500.000.000` | `2.600.000.000` | ratio 92.31 |  | lệch 100 triệu, chuỗi vẫn rất giống |
| money | `2.000.000` | `-2.000.000` | ratio 94.74 |  | khác dấu = ghi có vs ghi nợ |
| money | `1.250.000,50` | `1.250.000,55` | ratio 91.67 |  | lệch 5 xu |
| money | `12.000.000` | `12.000.00` | ratio 94.74 |  | định dạng sai (nhóm 2 chữ số) — kỳ vọng ném lỗi, không âm thầm so chuỗi |
| date | `12/08/2026` | `12/08/2025` | ratio 90.0 |  | lệch 1 năm |
| date | `2026-01-15` | `2026-01-16` | ratio 90.0 |  | lệch 1 ngày |
| date | `31/12/2025` | `31/12/2024` | ratio 90.0 |  | lệch 1 năm |
| date | `30/06/2026` | `30/07/2026` | ratio 90.0 |  | lệch 1 tháng |
| date | `08/03/2026` | `09/03/2026` | ratio 90.0 |  | lệch 1 ngày |
| id | `031234567890` | `031234567891` | ratio 91.67 |  | CCCD lệch đúng 1 số cuối — hai người |
| id | `031234567890` | `03123456789O` | ratio 91.67 |  | chữ O thay số 0 — lỗi OCR kinh điển |
| id | `031234567890` | `031234567980` | ratio 91.67 |  | đảo 2 chữ số — cùng độ dài |
| id | `0312345678901` | `031234567890` | ratio 96.0 |  | lệch độ dài (thêm 1 chữ số) |
| id | `001099012345` | `001099012346` | ratio 91.67 |  | lệch 1 số cuối |
| id | `KH-2026-001` | `KH-2026-002` | ratio 90.91 |  | lệch 1 số |
| id | `HD-2026-0457` | `HD-2026-0458` | ratio 91.67 |  | lệch 1 số |
| id | `012345678901` | `012345678900` | ratio 91.67 |  | lệch 1 số cuối |
| id | `031234567890` | `041234567890` | ratio 91.67 |  | lệch chữ số đầu |

### `rapidfuzz` — false-diff: 32 cặp

| kind | a | b | thước đo | ERR | ghi chú |
|---|---|---|---|---|---|
| name | `Nguyễn Thị Hòa` | `Nguyễn Thị Hòa` | ratio 68.75 |  | NFC vs NFD: cùng tên, khác byte |
| text | `Đinh Tiên Hoàng` | `Đinh Tiên Hoàng` | ratio 81.25 |  | NFD trên địa danh có ký tự Đ |
| name | `Hoà Văn Bình` | `Hòa Văn Bình` | ratio 83.33 |  | vị trí dấu thanh oà/òa, âm tiết mở |
| name | `Thuỳ Dương` | `Thùy Dương` | ratio 80.0 |  | uỳ/ùy, âm tiết mở |
| name | `Hoè Thị Lan` | `Hòe Thị Lan` | ratio 81.82 |  | oè/òe, âm tiết mở |
| name | `Nguyễn Thị Hòa` | `nguyễn thị hòa` | ratio 78.57 |  | chỉ khác hoa/thường |
| name | `Lý	Thị	Mai` | `Lý Thị Mai` | ratio 80.0 |  | tab thay dấu cách |
| text | `CÔNG TY TNHH THƯƠNG MẠI BÌNH AN` | `Công ty TNHH Thương mại Bình An` | ratio 45.16 |  | tên tổ chức, chỉ khác hoa/thường |
| money | `1.000.000đ` | `1,000,000 VND` | ratio 60.87 |  | kiểu VN có 'đ' vs kiểu US có 'VND' |
| money | `2.500.000.000` | `2,500,000,000` | ratio 76.92 |  | dấu phân nghìn VN vs US |
| money | `2.500.000.000` | `2500000000` | ratio 86.96 |  | có phân cách vs số trơn |
| money | `2.500.000,50` | `2,500,000.50` | ratio 75.0 |  | thập phân: phẩy VN vs chấm US |
| money | `5.000.000đ` | `5.000.000 đồng` | ratio 83.33 |  | 'đ' vs 'đồng' |
| money | `5.000.000₫` | `5.000.000 VNĐ` | ratio 78.26 |  | '₫' vs 'VNĐ' |
| money | `0` | `0đ` | ratio 66.67 |  | số 0 có/không hậu tố |
| money | `10.000.000` | `10.000.000,00` | ratio 86.96 |  | phần thập phân bằng 0 |
| money | ` 1.000.000 ` | `1,000,000` | ratio 70.0 |  | khoảng trắng hai đầu |
| money | `1.000.000` | `1.000.000 vnđ` | ratio 81.82 |  | hậu tố chữ thường |
| money | `3.000.000` | `3,000,000.00` | ratio 66.67 |  | US + thập phân .00 |
| money | `7.000.000` | `7.000.000 VND` | ratio 81.82 |  | một bên có hậu tố, một bên không |
| date | `01/02/2026` | `1-2-2026` | ratio 66.67 |  | thiếu số 0 + đổi dấu phân cách |
| date | `12/08/2026` | `12-8-2026` | ratio 73.68 |  | DD/MM/YYYY vs D-M-YYYY |
| date | `12/08/2026` | `2026-08-12` | ratio 50.0 |  | DD/MM/YYYY vs ISO YYYY-MM-DD |
| date | `2026-01-15` | `15/01/2026` | ratio 40.0 |  | ISO vs DD/MM |
| date | `01.02.2026` | `1.2.2026` | ratio 88.89 |  | dấu chấm + thiếu số 0 |
| date | `01 02 2026` | `01/02/2026` | ratio 80.0 |  | dấu cách vs dấu gạch chéo |
| date | `29/02/2024` | `29-2-2024` | ratio 73.68 |  | 29/02 năm nhuận hợp lệ |
| date | `31/12/2025` | `31-12-2025` | ratio 80.0 |  | đổi dấu phân cách |
| date | `07/09/2026` | `7/9/2026` | ratio 88.89 |  | thiếu số 0 hai vế |
| id | `KH-2026-001` | `kh 2026 001` | ratio 63.64 |  | gạch nối + hoa/thường |
| id | `STK-1234567890` | `STK 1234 5678 90` | ratio 86.67 |  | nhóm số + dấu phân cách |
| id | `AB-12-CD` | `ab12cd` | ratio 28.57 |  | mã chữ + số, khác case và gạch nối |

## Kiểm tra độ nhạy: baseline có được chuẩn hoá thì sao?

Cùng hai thước đo chuỗi nhưng chạy trên `normalize()` của vi-textmatch (NFC + vị trí dấu thanh + khoảng trắng + casefold), **không** có logic theo kiểu. Mục đích: tách xem chênh lệch đến từ chuẩn hoá hay từ việc hiểu kiểu dữ liệu.

| matcher | accuracy | false-equal ⚠ | false-diff | ERR |
|---|---|---|---|---|
| `difflib+normalize` | 54.0% | **22** | 24 | 0 |
| `rapidfuzz+normalize` | 54.0% | **22** | 24 | 0 |

## Nhận định (số liệu lấy từ lần chạy này)

1. **Lỗi nguy hiểm tập trung ở baseline.** `vi_textmatch` có 2 false-equal; difflib 22, rapidfuzz 22. Baseline coi hai số tiền/ngày/định danh khác nhau là "gần đúng" đúng ở chỗ SPEC cấm dùng ratio: money 4, date 5, id 9, text 1.
2. **`vi_textmatch` không false-equal ở money/date/id** (0/0/0 cặp), name 0 cặp. False-equal còn lại nằm ở text (2 cặp), nơi ngưỡng TYPO 0.85 gộp hai chuỗi gần giống nhưng khác nghĩa.
3. **Ngưỡng 0.9 là con dao sắc.** 8/100 cặp có ratio difflib đúng bằng 0.90 (±0.005): `Nguyễn Thị Hòa` vs `Nguyễn  Thị   Hòa` → BẰNG, `100.000.000` vs `100000000` → BẰNG, `15/07/2026` vs `15/7/2026 ` → BẰNG. Cặp khác nhau thật nằm ngay trên ngưỡng thì không nâng ngưỡng được, chỉ đổi cặp nào sai.
4. **False-diff của `vi_textmatch`** = 3 cặp, phân theo kiểu: money 0, date 0, id 0, name 3, text 0. False-diff ở name là cố ý: tên lệch 1 chữ do gõ/OCR bị đẩy về KHÁC để người soát lại, thay vì đoán là cùng người.
5. **ERR (2 cặp)** rơi vào input không ép được kiểu / ngày không tồn tại; 2/2 trong số đó là cặp vốn khác nhau, nên fail-closed không gây hại — điểm money/date có một phần công của việc ném lỗi thay vì đoán.
6. **Chuẩn hoá không phải nguồn gốc của an toàn.** Cho difflib dùng `normalize()` của thư viện: accuracy 46.0% → 54.0%, false-equal 22 → 22. Giá trị nằm ở type-aware, không phải ở NFC.
7. **difflib và rapidfuzz** lệch dự đoán ở 0/100 cặp — trên chuỗi ngắn, hai thuật toán khác nhau cho kết quả gần như trùng. rapidfuzz nhanh hơn, không an toàn hơn cho bài toán này.

## Giới hạn

- 100 cặp là mẫu nhỏ, do một người đặt nhãn; nhãn text phụ thuộc quan điểm "hai tên lệch 1 dấu có phải cùng người không". Cách chốt ở đây là **chặt**: phải soát lại.
- Mọi chuỗi đều bịa; không có PII, không suy ra hành vi trên dữ liệu thật.
- Chưa đo tốc độ và chưa đo trường hợp chuỗi rất dài (difflib có `autojunk`).

## Chạy lại

```bash
python3 bench/gen_pairs.py     # sinh lại bench/pairs.jsonl (tất định)
python3 bench/run_bench.py    # ghi bench/RESULTS.md + bench/results.jsonl
```

Nếu `rapidfuzz` chưa có (Python hệ thống trên macOS bị PEP 668 chặn `pip`):

```bash
python3.11 -m venv .venv && .venv/bin/pip install rapidfuzz
.venv/bin/python bench/run_bench.py
```

`rapidfuzz` chỉ là dependency **của benchmark**; thư viện vẫn zero-dependency.
