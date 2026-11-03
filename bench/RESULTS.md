# Bench: vi-textmatch vs difflib vs rapidfuzz

Sinh tự động bởi `bench/run_bench.py` — phần số liệu không sửa tay; phần nhận định ở cuối cũng lấy số từ chính lần chạy này.

- Chạy lúc: 2026-11-03 11:12 UTC
- Commit: `b79b647` · Python 3.13.18 · rapidfuzz 3.14.6 · Linux-6.18.44-fc-v230-x86_64-with-glibc2.39
- Dữ liệu: `pairs.jsonl` — **590 cặp bịa hoàn toàn**, 293 cặp bằng nhau / 297 cặp khác nhau (money 115, date 90, id 105, name 103, text 177).

## Phương pháp

- `vi_textmatch`: `compare(a, b, kind=...).match`; TEXT coi `TYPO` (ratio ≥ 0.85) là match, MONEY/DATE ném lỗi khi không ép được kiểu; DATE gọi với `day_first=True` (dữ liệu VN, DD/MM/YYYY); NAME so từng thành phần tên, lệch là KHÁC.
- `difflib`: `SequenceMatcher(None, a, b).ratio() >= 0.9` trên chuỗi **thô**.
- `rapidfuzz`: `fuzz.ratio(a, b) >= 90.0` trên chuỗi **thô**.
- Chuẩn đúng là **nghĩa**, chốt trước khi chạy: cùng một người / cùng một số tiền / cùng một ngày / cùng một định danh → `expected_equal = true`.
- Ném lỗi được ghi `ERR` và tính là **không bằng** (fail-closed) — đúng hướng thư viện mong muốn, và vẫn bị tính vào accuracy.
- accuracy = đoán đúng / tổng; false-equal = đoán BẰNG nhưng thực ra KHÁC; false-diff = đoán KHÁC nhưng thực ra BẰNG.

## Tổng

| matcher | accuracy | đúng | false-equal ⚠ | false-diff | ERR |
|---|---|---|---|---|---|
| `vi_textmatch` | 86.1% | 508/590 | **58** | 24 | 23 |
| `difflib` | 52.9% | 312/590 | **92** | 186 | 0 |
| `rapidfuzz` | 52.9% | 312/590 | **92** | 186 | 0 |
| `difflib+normalize` | 68.0% | 401/590 | **94** | 95 | 0 |
| `rapidfuzz+normalize` | 68.0% | 401/590 | **94** | 95 | 0 |

`+normalize` = cùng thước đo chuỗi nhưng chạy trên `normalize()` (baseline mạnh hơn, để so sánh công bằng).

## Theo nguồn / mẫu biến đổi (`vi_textmatch`)

Cặp sinh tự động được gán nhãn theo phép biến đổi; bảng này cho thấy thư viện mạnh/yếu ở phép nào, tránh để vài mẫu dễ kéo điểm tổng.

| nguồn | ghi chú (phép biến đổi) | nhãn | n | đúng | FE | FD |
|---|---|---|---|---|---|---|
| gen:address | bỏ khoảng trắng sau dấu phẩy | BẰNG | 11 | 11 | 0 | 0 |
| gen:address | khác phường | KHÁC | 10 | 0 | 10 | 0 |
| gen:address | khác số ngõ | KHÁC | 11 | 0 | 11 | 0 |
| gen:address | khác số nhà | KHÁC | 17 | 0 | 17 | 0 |
| gen:address | khác tên đường | KHÁC | 9 | 0 | 9 | 0 |
| gen:address | viết tắt P./Q. — cùng địa chỉ | BẰNG | 6 | 6 | 0 | 0 |
| gen:address | địa chỉ NFC vs NFD | BẰNG | 7 | 7 | 0 | 0 |
| gen:address | địa chỉ thừa khoảng trắng | BẰNG | 10 | 10 | 0 | 0 |
| gen:address | địa chỉ viết HOA | BẰNG | 9 | 9 | 0 | 0 |
| gen:company | khác loại hình (TNHH/CP/MTV/DNTN) | KHÁC | 15 | 8 | 7 | 0 |
| gen:company | khác một từ trong tên | KHÁC | 8 | 6 | 2 | 0 |
| gen:company | tên công ty NFC vs NFD | BẰNG | 12 | 12 | 0 | 0 |
| gen:company | tên công ty thừa khoảng trắng | BẰNG | 11 | 11 | 0 | 0 |
| gen:company | tên công ty viết HOA | BẰNG | 13 | 13 | 0 | 0 |
| gen:company | viết tắt Cty — cùng công ty | BẰNG | 6 | 6 | 0 | 0 |
| gen:company | đảo thứ tự từ trong tên | KHÁC | 15 | 15 | 0 | 0 |
| gen:contract | phụ lục của HĐ ≠ HĐ gốc | KHÁC | 12 | 12 | 0 | 0 |
| gen:contract | số HĐ khác hậu tố đơn vị | KHÁC | 9 | 9 | 0 | 0 |
| gen:contract | số HĐ khác loại hợp đồng | KHÁC | 7 | 7 | 0 | 0 |
| gen:contract | số HĐ khác năm | KHÁC | 6 | 6 | 0 | 0 |
| gen:contract | số HĐ lệch 1 số thứ tự | KHÁC | 8 | 8 | 0 | 0 |
| gen:contract | số HĐ: gạch ngang '–' thay '-' | BẰNG | 14 | 14 | 0 | 0 |
| gen:contract | số HĐ: khoảng trắng quanh '-' | BẰNG | 18 | 18 | 0 | 0 |
| gen:contract | số HĐ: khoảng trắng đầu/cuối | BẰNG | 6 | 6 | 0 | 0 |
| gen:date | cùng ngày, khác định dạng | BẰNG | 19 | 19 | 0 | 0 |
| gen:date | khác năm | KHÁC | 18 | 18 | 0 | 0 |
| gen:date | lệch 1 ngày | KHÁC | 7 | 7 | 0 | 0 |
| gen:date | lệch ~1 tháng | KHÁC | 8 | 8 | 0 | 0 |
| gen:date | ngày viết bằng chữ | BẰNG | 15 | 0 | 0 | 15 |
| gen:date | đảo ngày/tháng — ngày khác | KHÁC | 3 | 3 | 0 | 0 |
| gen:money | cùng số tiền, có phần thập phân ,00 | BẰNG | 17 | 17 | 0 | 0 |
| gen:money | cùng số tiền, khác định dạng/đơn vị VND | BẰNG | 20 | 20 | 0 | 0 |
| gen:money | khác loại tiền (USD vs VND) | KHÁC | 9 | 9 | 0 | 0 |
| gen:money | khác số tiền | KHÁC | 11 | 11 | 0 | 0 |
| gen:money | số tiền viết bằng chữ tỷ/triệu | BẰNG | 6 | 0 | 0 | 6 |
| gen:money | thiếu tiền | KHÁC | 13 | 13 | 0 | 0 |
| gen:money | thừa một số 0 | KHÁC | 14 | 14 | 0 | 0 |
| gen:name | khác họ | KHÁC | 14 | 14 | 0 | 0 |
| gen:name | khác tên | KHÁC | 11 | 11 | 0 | 0 |
| gen:name | khác tên đệm | KHÁC | 11 | 11 | 0 | 0 |
| gen:name | tên NFC vs NFD | BẰNG | 10 | 10 | 0 | 0 |
| gen:name | tên dấu thanh kiểu cũ (oà/uỷ) | BẰNG | 1 | 1 | 0 | 0 |
| gen:name | tên thừa khoảng trắng | BẰNG | 15 | 15 | 0 | 0 |
| gen:name | tên viết HOA | BẰNG | 12 | 12 | 0 | 0 |
| gen:name | đổi 1 dấu → tên hợp lệ khác (người khác) | KHÁC | 6 | 6 | 0 | 0 |

## Theo kiểu dữ liệu — accuracy

| matcher | money | date | id | name | text | total |
|---|---|---|---|---|---|---|
| `vi_textmatch` | 94.8% | 83.3% | 100.0% | 97.1% | 67.2% | 86.1% |
| `difflib` | 49.6% | 42.2% | 74.3% | 48.5% | 50.3% | 52.9% |
| `rapidfuzz` | 49.6% | 42.2% | 74.3% | 48.5% | 50.3% | 52.9% |

## Theo kiểu dữ liệu — false-equal (hướng sai nguy hiểm)

| matcher | money | date | id | name | text | total |
|---|---|---|---|---|---|---|
| `vi_textmatch` | 0 | 0 | 0 | 0 | **58** | **58** |
| `difflib` | **6** | **11** | **24** | **12** | **39** | **92** |
| `rapidfuzz` | **6** | **11** | **24** | **12** | **39** | **92** |

## Theo kiểu dữ liệu — false-diff (hướng sai gây phiền)

| matcher | money | date | id | name | text | total |
|---|---|---|---|---|---|---|
| `vi_textmatch` | 6 | 15 | 0 | 3 | 0 | 24 |
| `difflib` | 52 | 41 | 3 | 41 | 49 | 186 |
| `rapidfuzz` | 52 | 41 | 3 | 41 | 49 | 186 |

## Theo kiểu dữ liệu — ERR (ném lỗi, fail-closed)

| matcher | money | date | id | name | text | total |
|---|---|---|---|---|---|---|
| `vi_textmatch` | 7 | 16 | 0 | 0 | 0 | 23 |
| `difflib` | 0 | 0 | 0 | 0 | 0 | 0 |
| `rapidfuzz` | 0 | 0 | 0 | 0 | 0 | 0 |

## Bằng chứng — từng cặp bị đoán SAI

### `vi_textmatch` — false-equal: 58 cặp

| kind | a | b | thước đo | ERR | ghi chú |
|---|---|---|---|---|---|
| text | `Số 12 Ngõ 34 Phố Hoa Ban, Phường 5` | `Số 21 Ngõ 34 Phố Hoa Ban, Phường 5` | TYPO (Match ratio: 0.9706 (typo suspected)) |  | số nhà 12→21, phần còn lại giống hệt |
| text | `Công ty TNHH Bình Minh` | `Công ty CP Bình Minh` | TYPO (Match ratio: 0.8571 (typo suspected)) |  | khác loại hình doanh nghiệp = khác pháp nhân |
| text | `Số 165 ngõ 65 Hoàng Văn Thụ, phường Vĩnh Niệm, quận Hồng Bàng, Cần Thơ` | `Số 165 ngõ 65 Hoàng Văn Thụ, phường Cầu Đất, quận Hồng Bàng, Cần Thơ` | TYPO (Match ratio: 0.8986 (typo suspected)) |  | khác phường |
| text | `Số 28 ngõ 44 Nguyễn Trãi, phường An Biên, quận Lê Chân, Cần Thơ` | `Số 28 ngõ 45 Nguyễn Trãi, phường An Biên, quận Lê Chân, Cần Thơ` | TYPO (Match ratio: 0.9841 (typo suspected)) |  | khác số ngõ |
| text | `Số 215 ngõ 105 Hoàng Văn Thụ, phường Kênh Dương, quận Ngô Quyền, Cần Thơ` | `Số 215 ngõ 106 Hoàng Văn Thụ, phường Kênh Dương, quận Ngô Quyền, Cần Thơ` | TYPO (Match ratio: 0.9861 (typo suspected)) |  | khác số ngõ |
| text | `Số 146 ngõ 111 Hùng Vương, phường Thượng Lý, quận Dương Kinh, Cần Thơ` | `Số 146 ngõ 112 Hùng Vương, phường Thượng Lý, quận Dương Kinh, Cần Thơ` | TYPO (Match ratio: 0.9855 (typo suspected)) |  | khác số ngõ |
| text | `Số 229 ngõ 16 Quang Trung, phường Kênh Dương, quận Kiến An, Đà Nẵng` | `Số 228 ngõ 16 Quang Trung, phường Kênh Dương, quận Kiến An, Đà Nẵng` | TYPO (Match ratio: 0.9851 (typo suspected)) |  | khác số nhà |
| text | `Số 137 ngõ 45 Ngô Quyền, phường Hòa Nghĩa, quận Lê Chân, Đà Nẵng` | `Số 137 ngõ 45 Lý Thường Kiệt, phường Hòa Nghĩa, quận Lê Chân, Đà Nẵng` | TYPO (Match ratio: 0.8722 (typo suspected)) |  | khác tên đường |
| text | `Số 115 ngõ 45 Thủy Nguyên, phường Đằng Giang, quận Hồng Bàng, Cần Thơ` | `Số 117 ngõ 45 Thủy Nguyên, phường Đằng Giang, quận Hồng Bàng, Cần Thơ` | TYPO (Match ratio: 0.9855 (typo suspected)) |  | khác số nhà |
| text | `Số 132 ngõ 96 Trần Hưng Đạo, phường Thượng Lý, quận Hồng Bàng, Hà Nội` | `Số 132 ngõ 96 Phạm Văn Đồng, phường Thượng Lý, quận Hồng Bàng, Hà Nội` | TYPO (Match ratio: 0.8696 (typo suspected)) |  | khác tên đường |
| text | `Số 85 ngõ 1 Quang Trung, phường Cầu Đất, quận Hải An, Đà Nẵng` | `Số 85 ngõ 1 Quang Trung, phường Đông Khê, quận Hải An, Đà Nẵng` | TYPO (Match ratio: 0.8943 (typo suspected)) |  | khác phường |
| text | `Số 217 ngõ 118 Lý Thường Kiệt, phường Đằng Giang, quận Kiến An, Hà Nội` | `Số 216 ngõ 118 Lý Thường Kiệt, phường Đằng Giang, quận Kiến An, Hà Nội` | TYPO (Match ratio: 0.9857 (typo suspected)) |  | khác số nhà |
| text | `Số 183 ngõ 43 Quang Trung, phường Lạc Viên, quận Lê Chân, Cần Thơ` | `Số 182 ngõ 43 Quang Trung, phường Lạc Viên, quận Lê Chân, Cần Thơ` | TYPO (Match ratio: 0.9846 (typo suspected)) |  | khác số nhà |
| text | `Số 12 ngõ 105 Tô Hiệu, phường Cầu Đất, quận Ngô Quyền, Cần Thơ` | `Số 12 ngõ 106 Tô Hiệu, phường Cầu Đất, quận Ngô Quyền, Cần Thơ` | TYPO (Match ratio: 0.9839 (typo suspected)) |  | khác số ngõ |
| text | `Số 95 ngõ 95 Thủy Nguyên, phường Kênh Dương, quận Kiến An, Đà Nẵng` | `Số 95 ngõ 95 Trần Hưng Đạo, phường Kênh Dương, quận Kiến An, Đà Nẵng` | TYPO (Match ratio: 0.8806 (typo suspected)) |  | khác tên đường |
| text | `Số 166 ngõ 66 Lý Thường Kiệt, phường Lạc Viên, quận Kiến An, Cần Thơ` | `Số 165 ngõ 66 Lý Thường Kiệt, phường Lạc Viên, quận Kiến An, Cần Thơ` | TYPO (Match ratio: 0.9853 (typo suspected)) |  | khác số nhà |
| text | `Số 12 ngõ 42 Quang Trung, phường Máy Tơ, quận Kiến An, Hải Phòng` | `Số 13 ngõ 42 Quang Trung, phường Máy Tơ, quận Kiến An, Hải Phòng` | TYPO (Match ratio: 0.9844 (typo suspected)) |  | khác số nhà |
| text | `Số 6 ngõ 74 Thủy Nguyên, phường Vĩnh Niệm, quận Hồng Bàng, Đà Nẵng` | `Số 6 ngõ 74 Hùng Vương, phường Vĩnh Niệm, quận Hồng Bàng, Đà Nẵng` | TYPO (Match ratio: 0.9008 (typo suspected)) |  | khác tên đường |
| text | `Số 173 ngõ 29 Hoàng Văn Thụ, phường An Biên, quận Lê Chân, Đà Nẵng` | `Số 173 ngõ 29 Hoàng Văn Thụ, phường Đằng Giang, quận Lê Chân, Đà Nẵng` | TYPO (Match ratio: 0.9037 (typo suspected)) |  | khác phường |
| text | `Số 1 ngõ 29 Trần Hưng Đạo, phường Đằng Giang, quận Lê Chân, Đà Nẵng` | `Số 1 ngõ 29 Trần Hưng Đạo, phường Kênh Dương, quận Lê Chân, Đà Nẵng` | TYPO (Match ratio: 0.9104 (typo suspected)) |  | khác phường |
| text | `Số 49 ngõ 68 Thủy Nguyên, phường Thượng Lý, quận Ngô Quyền, Đà Nẵng` | `Số 49 ngõ 69 Thủy Nguyên, phường Thượng Lý, quận Ngô Quyền, Đà Nẵng` | TYPO (Match ratio: 0.9851 (typo suspected)) |  | khác số ngõ |
| text | `Số 75 ngõ 49 Hòa Bình, phường Đông Khê, quận Hồng Bàng, Hải Phòng` | `Số 75 ngõ 49 Hòa Bình, phường Máy Tơ, quận Hồng Bàng, Hải Phòng` | TYPO (Match ratio: 0.9062 (typo suspected)) |  | khác phường |
| text | `Số 155 ngõ 4 Lạch Tray, phường Đằng Giang, quận Ngô Quyền, Đà Nẵng` | `Số 155 ngõ 4 Lạch Tray, phường Máy Tơ, quận Ngô Quyền, Đà Nẵng` | TYPO (Match ratio: 0.8906 (typo suspected)) |  | khác phường |
| text | `Số 147 ngõ 39 Lê Lợi, phường Cầu Đất, quận Lê Chân, Cần Thơ` | `Số 147 ngõ 39 Lê Lợi, phường Máy Tơ, quận Lê Chân, Cần Thơ` | TYPO (Match ratio: 0.9231 (typo suspected)) |  | khác phường |
| text | `Số 19 ngõ 37 Văn Cao, phường Đông Khê, quận Hồng Bàng, Cần Thơ` | `Số 19 ngõ 38 Văn Cao, phường Đông Khê, quận Hồng Bàng, Cần Thơ` | TYPO (Match ratio: 0.9839 (typo suspected)) |  | khác số ngõ |
| text | `Số 163 ngõ 5 Trần Hưng Đạo, phường Vĩnh Niệm, quận Kiến An, Hải Phòng` | `Số 165 ngõ 5 Trần Hưng Đạo, phường Vĩnh Niệm, quận Kiến An, Hải Phòng` | TYPO (Match ratio: 0.9855 (typo suspected)) |  | khác số nhà |
| text | `Số 37 ngõ 51 Quang Trung, phường Cầu Đất, quận Ngô Quyền, Cần Thơ` | `Số 37 ngõ 51 Lý Thường Kiệt, phường Cầu Đất, quận Ngô Quyền, Cần Thơ` | TYPO (Match ratio: 0.8722 (typo suspected)) |  | khác tên đường |
| text | `Số 217 ngõ 98 Văn Cao, phường Cầu Đất, quận Kiến An, Đà Nẵng` | `Số 218 ngõ 98 Văn Cao, phường Cầu Đất, quận Kiến An, Đà Nẵng` | TYPO (Match ratio: 0.9833 (typo suspected)) |  | khác số nhà |
| text | `Số 245 ngõ 73 Điện Biên Phủ, phường Cầu Đất, quận Hồng Bàng, Hải Phòng` | `Số 255 ngõ 73 Điện Biên Phủ, phường Cầu Đất, quận Hồng Bàng, Hải Phòng` | TYPO (Match ratio: 0.9857 (typo suspected)) |  | khác số nhà |
| text | `Số 126 ngõ 66 Quang Trung, phường Vĩnh Niệm, quận Lê Chân, Hà Nội` | `Số 126 ngõ 66 Điện Biên Phủ, phường Vĩnh Niệm, quận Lê Chân, Hà Nội` | TYPO (Match ratio: 0.8636 (typo suspected)) |  | khác tên đường |
| text | `Số 237 ngõ 52 Ngô Quyền, phường Vĩnh Niệm, quận Lê Chân, Cần Thơ` | `Số 236 ngõ 52 Ngô Quyền, phường Vĩnh Niệm, quận Lê Chân, Cần Thơ` | TYPO (Match ratio: 0.9844 (typo suspected)) |  | khác số nhà |
| text | `Số 125 ngõ 92 Nguyễn Trãi, phường Cầu Đất, quận Ngô Quyền, Hải Phòng` | `Số 125 ngõ 93 Nguyễn Trãi, phường Cầu Đất, quận Ngô Quyền, Hải Phòng` | TYPO (Match ratio: 0.9853 (typo suspected)) |  | khác số ngõ |
| text | `Số 167 ngõ 75 Văn Cao, phường Vĩnh Niệm, quận Lê Chân, Đà Nẵng` | `Số 168 ngõ 75 Văn Cao, phường Vĩnh Niệm, quận Lê Chân, Đà Nẵng` | TYPO (Match ratio: 0.9839 (typo suspected)) |  | khác số nhà |
| text | `Số 7 ngõ 117 Hoàng Văn Thụ, phường Hòa Nghĩa, quận Hồng Bàng, Hà Nội` | `Số 7 ngõ 117 Trần Hưng Đạo, phường Hòa Nghĩa, quận Hồng Bàng, Hà Nội` | TYPO (Match ratio: 0.8676 (typo suspected)) |  | khác tên đường |
| text | `Số 76 ngõ 102 Hoàng Văn Thụ, phường Cầu Đất, quận Dương Kinh, Hải Phòng` | `Số 76 ngõ 103 Hoàng Văn Thụ, phường Cầu Đất, quận Dương Kinh, Hải Phòng` | TYPO (Match ratio: 0.9859 (typo suspected)) |  | khác số ngõ |
| text | `Số 40 ngõ 107 Quang Trung, phường Lạc Viên, quận Dương Kinh, Hà Nội` | `Số 41 ngõ 107 Quang Trung, phường Lạc Viên, quận Dương Kinh, Hà Nội` | TYPO (Match ratio: 0.9851 (typo suspected)) |  | khác số nhà |
| text | `Số 241 ngõ 96 Quang Trung, phường An Biên, quận Ngô Quyền, Hải Phòng` | `Số 240 ngõ 96 Quang Trung, phường An Biên, quận Ngô Quyền, Hải Phòng` | TYPO (Match ratio: 0.9853 (typo suspected)) |  | khác số nhà |
| text | `Số 61 ngõ 65 Quang Trung, phường Hòa Nghĩa, quận Hồng Bàng, Hà Nội` | `Số 61 ngõ 65 Quang Trung, phường An Biên, quận Hồng Bàng, Hà Nội` | TYPO (Match ratio: 0.9231 (typo suspected)) |  | khác phường |
| text | `Số 220 ngõ 94 Ngô Quyền, phường Cầu Đất, quận Hồng Bàng, Đà Nẵng` | `Số 220 ngõ 94 Lạch Tray, phường Cầu Đất, quận Hồng Bàng, Đà Nẵng` | TYPO (Match ratio: 0.8906 (typo suspected)) |  | khác tên đường |
| text | `Số 138 ngõ 88 Điện Biên Phủ, phường Hòa Nghĩa, quận Ngô Quyền, Hà Nội` | `Số 138 ngõ 89 Điện Biên Phủ, phường Hòa Nghĩa, quận Ngô Quyền, Hà Nội` | TYPO (Match ratio: 0.9855 (typo suspected)) |  | khác số ngõ |
| text | `Số 206 ngõ 22 Lê Lợi, phường Lạc Viên, quận Hồng Bàng, Cần Thơ` | `Số 206 ngõ 22 Lê Lợi, phường An Biên, quận Hồng Bàng, Cần Thơ` | TYPO (Match ratio: 0.9431 (typo suspected)) |  | khác phường |
| text | `Số 26 ngõ 15 Lê Lợi, phường Thượng Lý, quận Lê Chân, Đà Nẵng` | `Số 28 ngõ 15 Lê Lợi, phường Thượng Lý, quận Lê Chân, Đà Nẵng` | TYPO (Match ratio: 0.9833 (typo suspected)) |  | khác số nhà |
| text | `Số 44 ngõ 37 Nguyễn Trãi, phường Đông Khê, quận Dương Kinh, Cần Thơ` | `Số 44 ngõ 37 Lý Thường Kiệt, phường Đông Khê, quận Dương Kinh, Cần Thơ` | TYPO (Match ratio: 0.8759 (typo suspected)) |  | khác tên đường |
| text | `Số 247 ngõ 106 Hòa Bình, phường Kênh Dương, quận Kiến An, Đà Nẵng` | `Số 257 ngõ 106 Hòa Bình, phường Kênh Dương, quận Kiến An, Đà Nẵng` | TYPO (Match ratio: 0.9846 (typo suspected)) |  | khác số nhà |
| text | `Số 240 ngõ 15 Hùng Vương, phường Máy Tơ, quận Dương Kinh, Cần Thơ` | `Số 250 ngõ 15 Hùng Vương, phường Máy Tơ, quận Dương Kinh, Cần Thơ` | TYPO (Match ratio: 0.9846 (typo suspected)) |  | khác số nhà |
| text | `Số 248 ngõ 39 Lê Lợi, phường Đông Khê, quận Dương Kinh, Hải Phòng` | `Số 248 ngõ 40 Lê Lợi, phường Đông Khê, quận Dương Kinh, Hải Phòng` | TYPO (Match ratio: 0.9692 (typo suspected)) |  | khác số ngõ |
| text | `Số 168 ngõ 7 Thủy Nguyên, phường Đằng Giang, quận Dương Kinh, Đà Nẵng` | `Số 168 ngõ 7 Thủy Nguyên, phường An Biên, quận Dương Kinh, Đà Nẵng` | TYPO (Match ratio: 0.9037 (typo suspected)) |  | khác phường |
| text | `Số 121 ngõ 33 Lê Lợi, phường Vĩnh Niệm, quận Ngô Quyền, Cần Thơ` | `Số 131 ngõ 33 Lê Lợi, phường Vĩnh Niệm, quận Ngô Quyền, Cần Thơ` | TYPO (Match ratio: 0.9841 (typo suspected)) |  | khác số nhà |
| text | `Số 106 ngõ 7 Quang Trung, phường Thượng Lý, quận Kiến An, Hải Phòng` | `Số 106 ngõ 8 Quang Trung, phường Thượng Lý, quận Kiến An, Hải Phòng` | TYPO (Match ratio: 0.9851 (typo suspected)) |  | khác số ngõ |
| text | `Công ty TNHH Hòa Lợi Thuận Phát` | `Công ty Cổ phần Hòa Lợi Thuận Phát` | TYPO (Match ratio: 0.8615 (typo suspected)) |  | khác loại hình (TNHH/CP/MTV/DNTN) |
| text | `Công ty Cổ phần Kỹ thuật Xây dựng` | `Công ty TNHH Kỹ thuật Xây dựng` | TYPO (Match ratio: 0.8571 (typo suspected)) |  | khác loại hình (TNHH/CP/MTV/DNTN) |
| text | `Công ty TNHH Xây dựng Vận tải` | `Công ty TNHH MTV Xây dựng Vận tải` | TYPO (Match ratio: 0.9355 (typo suspected)) |  | khác loại hình (TNHH/CP/MTV/DNTN) |
| text | `Công ty TNHH Đầu tư Tân Hòa` | `Công ty TNHH MTV Đầu tư Tân Hòa` | TYPO (Match ratio: 0.9310 (typo suspected)) |  | khác loại hình (TNHH/CP/MTV/DNTN) |
| text | `Doanh nghiệp tư nhân Biển Xanh Xây dựng` | `Doanh nghiệp tư nhân Biển Xanh Tân Hòa` | TYPO (Match ratio: 0.8571 (typo suspected)) |  | khác một từ trong tên |
| text | `Công ty TNHH MTV Hoàng Gia Xây dựng` | `Công ty TNHH Hoàng Gia Xây dựng` | TYPO (Match ratio: 0.9394 (typo suspected)) |  | khác loại hình (TNHH/CP/MTV/DNTN) |
| text | `Công ty TNHH Kỹ thuật Thuận Phát` | `Công ty Cổ phần Kỹ thuật Thuận Phát` | TYPO (Match ratio: 0.8657 (typo suspected)) |  | khác loại hình (TNHH/CP/MTV/DNTN) |
| text | `Công ty TNHH MTV Tân Hòa Vận tải` | `Công ty TNHH MTV Tân Hòa Đầu tư` | TYPO (Match ratio: 0.8571 (typo suspected)) |  | khác một từ trong tên |
| text | `Công ty TNHH An Khánh Minh Khoa` | `Công ty TNHH MTV An Khánh Minh Khoa` | TYPO (Match ratio: 0.9394 (typo suspected)) |  | khác loại hình (TNHH/CP/MTV/DNTN) |

### `vi_textmatch` — false-diff: 24 cặp

| kind | a | b | thước đo | ERR | ghi chú |
|---|---|---|---|---|---|
| name | `Trịnh Công Sơnn` | `Trịnh Công Sơn` | DIFFERENT (Name components differ at position 3) |  | lặp 1 ký tự cuối (gõ/OCR) |
| name | `Lương Thị Ánh Tuyế` | `Lương Thị Ánh Tuyết` | DIFFERENT (Name components differ at position 4) |  | nuốt ký tự cuối (OCR) |
| name | `Hoàng Văn Quag` | `Hoàng Văn Quang` | DIFFERENT (Name components differ at position 3) |  | rơi 1 phụ âm cuối |
| money | `2900000000 đồng` | `2900 triệu` | — | x | số tiền viết bằng chữ tỷ/triệu |
| money | `₫292000000` | `292 triệu` | — | x | số tiền viết bằng chữ tỷ/triệu |
| money | `26,000,000,000 VND` | `26 tỷ` | — | x | số tiền viết bằng chữ tỷ/triệu |
| money | `8.500.000.000 VND` | `8500 triệu` | — | x | số tiền viết bằng chữ tỷ/triệu |
| money | `7,000,000,000` | `7 tỷ` | — | x | số tiền viết bằng chữ tỷ/triệu |
| money | `5.800.000.000 đ` | `5800 triệu` | — | x | số tiền viết bằng chữ tỷ/triệu |
| date | `04-04-2022` | `ngày 04 tháng 04 năm 2022` | — | x | ngày viết bằng chữ |
| date | `14/02/2024` | `ngày 14 tháng 02 năm 2024` | — | x | ngày viết bằng chữ |
| date | `2023-05-01` | `ngày 01 tháng 05 năm 2023` | — | x | ngày viết bằng chữ |
| date | `04-07-2022` | `ngày 04 tháng 07 năm 2022` | — | x | ngày viết bằng chữ |
| date | `27/8/2021` | `ngày 27 tháng 08 năm 2021` | — | x | ngày viết bằng chữ |
| date | `2024-10-31` | `ngày 31 tháng 10 năm 2024` | — | x | ngày viết bằng chữ |
| date | `01/09/2024` | `ngày 01 tháng 09 năm 2024` | — | x | ngày viết bằng chữ |
| date | `13/4/2025` | `ngày 13 tháng 04 năm 2025` | — | x | ngày viết bằng chữ |
| date | `2021-06-10` | `ngày 10 tháng 06 năm 2021` | — | x | ngày viết bằng chữ |
| date | `20/10/2024` | `ngày 20 tháng 10 năm 2024` | — | x | ngày viết bằng chữ |
| date | `21-01-2021` | `ngày 21 tháng 01 năm 2021` | — | x | ngày viết bằng chữ |
| date | `21/3/2023` | `ngày 21 tháng 03 năm 2023` | — | x | ngày viết bằng chữ |
| date | `27.07.2023` | `ngày 27 tháng 07 năm 2023` | — | x | ngày viết bằng chữ |
| date | `18.04.2024` | `ngày 18 tháng 04 năm 2024` | — | x | ngày viết bằng chữ |
| date | `21/04/2021` | `ngày 21 tháng 04 năm 2021` | — | x | ngày viết bằng chữ |

### `difflib` — false-equal: 92 cặp

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
| text | `Số 28 ngõ 44 Nguyễn Trãi, phường An Biên, quận Lê Chân, Cần Thơ` | `Số 28 ngõ 45 Nguyễn Trãi, phường An Biên, quận Lê Chân, Cần Thơ` | ratio 0.9841 |  | khác số ngõ |
| text | `Số 215 ngõ 105 Hoàng Văn Thụ, phường Kênh Dương, quận Ngô Quyền, Cần Thơ` | `Số 215 ngõ 106 Hoàng Văn Thụ, phường Kênh Dương, quận Ngô Quyền, Cần Thơ` | ratio 0.9861 |  | khác số ngõ |
| text | `Số 146 ngõ 111 Hùng Vương, phường Thượng Lý, quận Dương Kinh, Cần Thơ` | `Số 146 ngõ 112 Hùng Vương, phường Thượng Lý, quận Dương Kinh, Cần Thơ` | ratio 0.9855 |  | khác số ngõ |
| text | `Số 229 ngõ 16 Quang Trung, phường Kênh Dương, quận Kiến An, Đà Nẵng` | `Số 228 ngõ 16 Quang Trung, phường Kênh Dương, quận Kiến An, Đà Nẵng` | ratio 0.9851 |  | khác số nhà |
| text | `Số 115 ngõ 45 Thủy Nguyên, phường Đằng Giang, quận Hồng Bàng, Cần Thơ` | `Số 117 ngõ 45 Thủy Nguyên, phường Đằng Giang, quận Hồng Bàng, Cần Thơ` | ratio 0.9855 |  | khác số nhà |
| text | `Số 217 ngõ 118 Lý Thường Kiệt, phường Đằng Giang, quận Kiến An, Hà Nội` | `Số 216 ngõ 118 Lý Thường Kiệt, phường Đằng Giang, quận Kiến An, Hà Nội` | ratio 0.9857 |  | khác số nhà |
| text | `Số 183 ngõ 43 Quang Trung, phường Lạc Viên, quận Lê Chân, Cần Thơ` | `Số 182 ngõ 43 Quang Trung, phường Lạc Viên, quận Lê Chân, Cần Thơ` | ratio 0.9846 |  | khác số nhà |
| text | `Số 12 ngõ 105 Tô Hiệu, phường Cầu Đất, quận Ngô Quyền, Cần Thơ` | `Số 12 ngõ 106 Tô Hiệu, phường Cầu Đất, quận Ngô Quyền, Cần Thơ` | ratio 0.9839 |  | khác số ngõ |
| text | `Số 166 ngõ 66 Lý Thường Kiệt, phường Lạc Viên, quận Kiến An, Cần Thơ` | `Số 165 ngõ 66 Lý Thường Kiệt, phường Lạc Viên, quận Kiến An, Cần Thơ` | ratio 0.9853 |  | khác số nhà |
| text | `Số 12 ngõ 42 Quang Trung, phường Máy Tơ, quận Kiến An, Hải Phòng` | `Số 13 ngõ 42 Quang Trung, phường Máy Tơ, quận Kiến An, Hải Phòng` | ratio 0.9844 |  | khác số nhà |
| text | `Số 173 ngõ 29 Hoàng Văn Thụ, phường An Biên, quận Lê Chân, Đà Nẵng` | `Số 173 ngõ 29 Hoàng Văn Thụ, phường Đằng Giang, quận Lê Chân, Đà Nẵng` | ratio 0.9333 |  | khác phường |
| text | `Số 1 ngõ 29 Trần Hưng Đạo, phường Đằng Giang, quận Lê Chân, Đà Nẵng` | `Số 1 ngõ 29 Trần Hưng Đạo, phường Kênh Dương, quận Lê Chân, Đà Nẵng` | ratio 0.9104 |  | khác phường |
| text | `Số 49 ngõ 68 Thủy Nguyên, phường Thượng Lý, quận Ngô Quyền, Đà Nẵng` | `Số 49 ngõ 69 Thủy Nguyên, phường Thượng Lý, quận Ngô Quyền, Đà Nẵng` | ratio 0.9851 |  | khác số ngõ |
| text | `Số 75 ngõ 49 Hòa Bình, phường Đông Khê, quận Hồng Bàng, Hải Phòng` | `Số 75 ngõ 49 Hòa Bình, phường Máy Tơ, quận Hồng Bàng, Hải Phòng` | ratio 0.9062 |  | khác phường |
| text | `Số 147 ngõ 39 Lê Lợi, phường Cầu Đất, quận Lê Chân, Cần Thơ` | `Số 147 ngõ 39 Lê Lợi, phường Máy Tơ, quận Lê Chân, Cần Thơ` | ratio 0.906 |  | khác phường |
| text | `Số 19 ngõ 37 Văn Cao, phường Đông Khê, quận Hồng Bàng, Cần Thơ` | `Số 19 ngõ 38 Văn Cao, phường Đông Khê, quận Hồng Bàng, Cần Thơ` | ratio 0.9839 |  | khác số ngõ |
| text | `Số 163 ngõ 5 Trần Hưng Đạo, phường Vĩnh Niệm, quận Kiến An, Hải Phòng` | `Số 165 ngõ 5 Trần Hưng Đạo, phường Vĩnh Niệm, quận Kiến An, Hải Phòng` | ratio 0.9855 |  | khác số nhà |
| text | `Số 217 ngõ 98 Văn Cao, phường Cầu Đất, quận Kiến An, Đà Nẵng` | `Số 218 ngõ 98 Văn Cao, phường Cầu Đất, quận Kiến An, Đà Nẵng` | ratio 0.9833 |  | khác số nhà |
| text | `Số 245 ngõ 73 Điện Biên Phủ, phường Cầu Đất, quận Hồng Bàng, Hải Phòng` | `Số 255 ngõ 73 Điện Biên Phủ, phường Cầu Đất, quận Hồng Bàng, Hải Phòng` | ratio 0.9857 |  | khác số nhà |
| text | `Số 237 ngõ 52 Ngô Quyền, phường Vĩnh Niệm, quận Lê Chân, Cần Thơ` | `Số 236 ngõ 52 Ngô Quyền, phường Vĩnh Niệm, quận Lê Chân, Cần Thơ` | ratio 0.9844 |  | khác số nhà |
| text | `Số 125 ngõ 92 Nguyễn Trãi, phường Cầu Đất, quận Ngô Quyền, Hải Phòng` | `Số 125 ngõ 93 Nguyễn Trãi, phường Cầu Đất, quận Ngô Quyền, Hải Phòng` | ratio 0.9853 |  | khác số ngõ |
| text | `Số 167 ngõ 75 Văn Cao, phường Vĩnh Niệm, quận Lê Chân, Đà Nẵng` | `Số 168 ngõ 75 Văn Cao, phường Vĩnh Niệm, quận Lê Chân, Đà Nẵng` | ratio 0.9839 |  | khác số nhà |
| text | `Số 76 ngõ 102 Hoàng Văn Thụ, phường Cầu Đất, quận Dương Kinh, Hải Phòng` | `Số 76 ngõ 103 Hoàng Văn Thụ, phường Cầu Đất, quận Dương Kinh, Hải Phòng` | ratio 0.9859 |  | khác số ngõ |
| text | `Số 40 ngõ 107 Quang Trung, phường Lạc Viên, quận Dương Kinh, Hà Nội` | `Số 41 ngõ 107 Quang Trung, phường Lạc Viên, quận Dương Kinh, Hà Nội` | ratio 0.9851 |  | khác số nhà |
| text | `Số 241 ngõ 96 Quang Trung, phường An Biên, quận Ngô Quyền, Hải Phòng` | `Số 240 ngõ 96 Quang Trung, phường An Biên, quận Ngô Quyền, Hải Phòng` | ratio 0.9853 |  | khác số nhà |
| text | `Số 138 ngõ 88 Điện Biên Phủ, phường Hòa Nghĩa, quận Ngô Quyền, Hà Nội` | `Số 138 ngõ 89 Điện Biên Phủ, phường Hòa Nghĩa, quận Ngô Quyền, Hà Nội` | ratio 0.9855 |  | khác số ngõ |
| text | `Số 206 ngõ 22 Lê Lợi, phường Lạc Viên, quận Hồng Bàng, Cần Thơ` | `Số 206 ngõ 22 Lê Lợi, phường An Biên, quận Hồng Bàng, Cần Thơ` | ratio 0.9431 |  | khác phường |
| text | `Số 26 ngõ 15 Lê Lợi, phường Thượng Lý, quận Lê Chân, Đà Nẵng` | `Số 28 ngõ 15 Lê Lợi, phường Thượng Lý, quận Lê Chân, Đà Nẵng` | ratio 0.9833 |  | khác số nhà |
| text | `Số 247 ngõ 106 Hòa Bình, phường Kênh Dương, quận Kiến An, Đà Nẵng` | `Số 257 ngõ 106 Hòa Bình, phường Kênh Dương, quận Kiến An, Đà Nẵng` | ratio 0.9846 |  | khác số nhà |
| text | `Số 240 ngõ 15 Hùng Vương, phường Máy Tơ, quận Dương Kinh, Cần Thơ` | `Số 250 ngõ 15 Hùng Vương, phường Máy Tơ, quận Dương Kinh, Cần Thơ` | ratio 0.9846 |  | khác số nhà |
| text | `Số 248 ngõ 39 Lê Lợi, phường Đông Khê, quận Dương Kinh, Hải Phòng` | `Số 248 ngõ 40 Lê Lợi, phường Đông Khê, quận Dương Kinh, Hải Phòng` | ratio 0.9692 |  | khác số ngõ |
| text | `Số 168 ngõ 7 Thủy Nguyên, phường Đằng Giang, quận Dương Kinh, Đà Nẵng` | `Số 168 ngõ 7 Thủy Nguyên, phường An Biên, quận Dương Kinh, Đà Nẵng` | ratio 0.9333 |  | khác phường |
| text | `Số 121 ngõ 33 Lê Lợi, phường Vĩnh Niệm, quận Ngô Quyền, Cần Thơ` | `Số 131 ngõ 33 Lê Lợi, phường Vĩnh Niệm, quận Ngô Quyền, Cần Thơ` | ratio 0.9841 |  | khác số nhà |
| text | `Số 106 ngõ 7 Quang Trung, phường Thượng Lý, quận Kiến An, Hải Phòng` | `Số 106 ngõ 8 Quang Trung, phường Thượng Lý, quận Kiến An, Hải Phòng` | ratio 0.9851 |  | khác số ngõ |
| text | `Công ty TNHH Xây dựng Vận tải` | `Công ty TNHH MTV Xây dựng Vận tải` | ratio 0.9355 |  | khác loại hình (TNHH/CP/MTV/DNTN) |
| text | `Công ty TNHH Đầu tư Tân Hòa` | `Công ty TNHH MTV Đầu tư Tân Hòa` | ratio 0.931 |  | khác loại hình (TNHH/CP/MTV/DNTN) |
| text | `Công ty TNHH MTV Hoàng Gia Xây dựng` | `Công ty TNHH Hoàng Gia Xây dựng` | ratio 0.9394 |  | khác loại hình (TNHH/CP/MTV/DNTN) |
| text | `Công ty TNHH An Khánh Minh Khoa` | `Công ty TNHH MTV An Khánh Minh Khoa` | ratio 0.9394 |  | khác loại hình (TNHH/CP/MTV/DNTN) |
| id | `422/2026/HĐTC-PGB` | `423/2026/HĐTC-PGB` | ratio 0.9412 |  | số HĐ lệch 1 số thứ tự |
| id | `216/2026/HĐTC-CN.HP` | `216/2025/HĐTC-CN.HP` | ratio 0.9474 |  | số HĐ khác năm |
| id | `378/2024/HĐTC-PGB` | `378/2024/HĐTD-PGB` | ratio 0.9412 |  | số HĐ khác loại hợp đồng |
| id | `774/2025/HĐBĐ-KHCN` | `774/2024/HĐBĐ-KHCN` | ratio 0.9444 |  | số HĐ khác năm |
| id | `332/2026/HĐTD-KHDN` | `332/2025/HĐTD-KHDN` | ratio 0.9444 |  | số HĐ khác năm |
| id | `058/2026/PL-CN.HP` | `059/2026/PL-CN.HP` | ratio 0.9412 |  | số HĐ lệch 1 số thứ tự |
| id | `936/2024/HĐMB-KHDN` | `937/2024/HĐMB-KHDN` | ratio 0.9444 |  | số HĐ lệch 1 số thứ tự |
| id | `894/2026/HĐTD-KHCN` | `894/2025/HĐTD-KHCN` | ratio 0.9444 |  | số HĐ khác năm |
| id | `040/2025/HĐTC-KHCN` | `040/2024/HĐTC-KHCN` | ratio 0.9444 |  | số HĐ khác năm |
| id | `566/2026/HĐBĐ-KHCN` | `567/2026/HĐBĐ-KHCN` | ratio 0.9444 |  | số HĐ lệch 1 số thứ tự |
| id | `742/2024/HĐTD-PGB` | `743/2024/HĐTD-PGB` | ratio 0.9412 |  | số HĐ lệch 1 số thứ tự |
| id | `256/2025/PL-KHDN` | `257/2025/PL-KHDN` | ratio 0.9375 |  | số HĐ lệch 1 số thứ tự |
| id | `688/2026/HĐTD-PGB` | `688/2025/HĐTD-PGB` | ratio 0.9412 |  | số HĐ khác năm |
| id | `330/2025/HĐTC-CN.HP` | `331/2025/HĐTC-CN.HP` | ratio 0.9474 |  | số HĐ lệch 1 số thứ tự |
| id | `401/2026/HĐBĐ-KHDN` | `402/2026/HĐBĐ-KHDN` | ratio 0.9444 |  | số HĐ lệch 1 số thứ tự |
| money | `20,000,000,000đ` | `20,000,000,000$` | ratio 0.9333 |  | khác loại tiền (USD vs VND) |
| money | `92399000` | `923990000` | ratio 0.9412 |  | thừa một số 0 |
| date | `2024-09-28` | `2024-10-28` | ratio 0.9 |  | lệch ~1 tháng |
| date | `19/11/2020` | `19/11/2021` | ratio 0.9 |  | khác năm |
| date | `13/07/2026` | `14/07/2026` | ratio 0.9 |  | lệch 1 ngày |
| date | `19/10/2021` | `19/10/2022` | ratio 0.9 |  | khác năm |
| date | `22.01.2023` | `23.01.2023` | ratio 0.9 |  | lệch 1 ngày |
| date | `04-04-2020` | `04-04-2021` | ratio 0.9 |  | khác năm |
| name | `Vũ Văn Toàn` | `Vũ Văn Toán` | ratio 0.9091 |  | đổi 1 dấu → tên hợp lệ khác (người khác) |
| name | `Lê Ngọc Lan` | `Lê Ngọc Lân` | ratio 0.9091 |  | đổi 1 dấu → tên hợp lệ khác (người khác) |
| name | `Nguyễn Văn Tuấn` | `Nguyễn Văn Tuân` | ratio 0.9333 |  | đổi 1 dấu → tên hợp lệ khác (người khác) |
| name | `Hoàng Thị Dũng` | `Hoàng Thu Dũng` | ratio 0.9286 |  | khác tên đệm |
| name | `Trần Thu Dũng` | `Trần Thị Dũng` | ratio 0.9231 |  | khác tên đệm |
| name | `Vũ Hữu Lan` | `Vũ Hữu Lân` | ratio 0.9 |  | đổi 1 dấu → tên hợp lệ khác (người khác) |
| name | `Hoàng Minh Thụy` | `Hoàng Minh Thủy` | ratio 0.9333 |  | khác tên |
| name | `Đặng Văn An` | `Đặng Văn Ân` | ratio 0.9091 |  | đổi 1 dấu → tên hợp lệ khác (người khác) |
| name | `Ngô Hữu Tuấn` | `Ngô Hữu Tuân` | ratio 0.9167 |  | đổi 1 dấu → tên hợp lệ khác (người khác) |

### `difflib` — false-diff: 186 cặp

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
| text | `Số 46 ngõ 84 Lạch Tray, phường Cầu Đất, quận Ngô Quyền, Hà Nội` | `Số 46 ngõ 84 Lạch Tray, phường Cầu Đất, quận Ngô Quyền, Hà Nội` | ratio 0.6993 |  | địa chỉ NFC vs NFD |
| text | `Số 51 ngõ 111 Phạm Văn Đồng, phường An Biên, quận Hải An, Hải Phòng` | `SỐ 51 NGÕ 111 PHẠM VĂN ĐỒNG, PHƯỜNG AN BIÊN, QUẬN HẢI AN, HẢI PHÒNG` | ratio 0.4776 |  | địa chỉ viết HOA |
| text | `Số 110 ngõ 55 Thủy Nguyên, phường Kênh Dương, quận Ngô Quyền, Đà Nẵng` | `Số 110 ngõ 55 Thủy Nguyên, P. Kênh Dương, Q. Ngô Quyền, Đà Nẵng` | ratio 0.8939 |  | viết tắt P./Q. — cùng địa chỉ |
| text | `Số 132 ngõ 41 Lý Thường Kiệt, phường Đông Khê, quận Hồng Bàng, Hà Nội` | `SỐ 132 NGÕ 41 LÝ THƯỜNG KIỆT, PHƯỜNG ĐÔNG KHÊ, QUẬN HỒNG BÀNG, HÀ NỘI` | ratio 0.4638 |  | địa chỉ viết HOA |
| text | `Số 246 ngõ 61 Hoàng Văn Thụ, phường Vĩnh Niệm, quận Lê Chân, Đà Nẵng` | `Số 246 ngõ 61 Hoàng Văn Thụ, phường Vĩnh Niệm, quận Lê Chân, Đà Nẵng` | ratio 0.6968 |  | địa chỉ NFC vs NFD |
| text | `Số 181 ngõ 107 Tô Hiệu, phường Lạc Viên, quận Hải An, Cần Thơ` | `SỐ 181 NGÕ 107 TÔ HIỆU, PHƯỜNG LẠC VIÊN, QUẬN HẢI AN, CẦN THƠ` | ratio 0.5082 |  | địa chỉ viết HOA |
| text | `Số 105 ngõ 8 Thủy Nguyên, phường Hòa Nghĩa, quận Hồng Bàng, Đà Nẵng` | `Số 105 ngõ 8 Thủy Nguyên, phường Hòa Nghĩa, quận Hồng Bàng, Đà Nẵng` | ratio 0.7105 |  | địa chỉ NFC vs NFD |
| text | `Số 150 ngõ 102 Thủy Nguyên, phường Máy Tơ, quận Hồng Bàng, Hải Phòng` | `SỐ 150 NGÕ 102 THỦY NGUYÊN, PHƯỜNG MÁY TƠ, QUẬN HỒNG BÀNG, HẢI PHÒNG` | ratio 0.4559 |  | địa chỉ viết HOA |
| text | `Số 58 ngõ 14 Hòa Bình, phường Vĩnh Niệm, quận Lê Chân, Hải Phòng` | `Số 58 ngõ 14 Hòa Bình, P. Vĩnh Niệm, Q. Lê Chân, Hải Phòng` | ratio 0.8852 |  | viết tắt P./Q. — cùng địa chỉ |
| text | `Số 145 ngõ 116 Lạch Tray, phường Kênh Dương, quận Hải An, Cần Thơ` | `SỐ 145 NGÕ 116 LẠCH TRAY, PHƯỜNG KÊNH DƯƠNG, QUẬN HẢI AN, CẦN THƠ` | ratio 0.4769 |  | địa chỉ viết HOA |
| text | `Số 118 ngõ 19 Hoàng Văn Thụ, phường An Biên, quận Hải An, Đà Nẵng` | `SỐ 118 NGÕ 19 HOÀNG VĂN THỤ, PHƯỜNG AN BIÊN, QUẬN HẢI AN, ĐÀ NẴNG` | ratio 0.4923 |  | địa chỉ viết HOA |
| text | `Số 39 ngõ 7 Quang Trung, phường Đằng Giang, quận Kiến An, Cần Thơ` | `Số 39 ngõ 7 Quang Trung, phường Đằng Giang, quận Kiến An, Cần Thơ` | ratio 0.7724 |  | địa chỉ NFC vs NFD |
| text | `Số 70 ngõ 76 Ngô Quyền, phường Cầu Đất, quận Hải An, Cần Thơ` | `Số 70 ngõ 76 Ngô Quyền, phường Cầu Đất, quận Hải An, Cần Thơ` | ratio 0.6906 |  | địa chỉ NFC vs NFD |
| text | `Số 169 ngõ 14 Hòa Bình, phường Kênh Dương, quận Hồng Bàng, Hà Nội` | `SỐ 169 NGÕ 14 HÒA BÌNH, PHƯỜNG KÊNH DƯƠNG, QUẬN HỒNG BÀNG, HÀ NỘI` | ratio 0.4615 |  | địa chỉ viết HOA |
| text | `Số 39 ngõ 98 Điện Biên Phủ, phường Kênh Dương, quận Ngô Quyền, Hà Nội` | `Số 39 ngõ 98 Điện Biên Phủ, P. Kênh Dương, Q. Ngô Quyền, Hà Nội` | ratio 0.8939 |  | viết tắt P./Q. — cùng địa chỉ |
| text | `Số 197 ngõ 70 Điện Biên Phủ, phường Đằng Giang, quận Hồng Bàng, Cần Thơ` | `Số 197 ngõ 70 Điện Biên Phủ, P. Đằng Giang, Q. Hồng Bàng, Cần Thơ` | ratio 0.8971 |  | viết tắt P./Q. — cùng địa chỉ |
| text | `Số 24 ngõ 114 Phạm Văn Đồng, phường Kênh Dương, quận Dương Kinh, Hải Phòng` | `SỐ 24 NGÕ 114 PHẠM VĂN ĐỒNG, PHƯỜNG KÊNH DƯƠNG, QUẬN DƯƠNG KINH, HẢI PHÒNG` | ratio 0.4324 |  | địa chỉ viết HOA |
| text | `Số 79 ngõ 119 Thủy Nguyên, phường Đằng Giang, quận Ngô Quyền, Hải Phòng` | `Số 79 ngõ 119 Thủy Nguyên, P. Đằng Giang, Q. Ngô Quyền, Hải Phòng` | ratio 0.8971 |  | viết tắt P./Q. — cùng địa chỉ |
| text | `Số 191 ngõ 53 Lý Thường Kiệt, phường Thượng Lý, quận Hồng Bàng, Hải Phòng` | `Số 191 ngõ 53 Lý Thường Kiệt, phường Thượng Lý, quận Hồng Bàng, Hải Phòng` | ratio 0.6746 |  | địa chỉ NFC vs NFD |
| text | `Số 64 ngõ 10 Thủy Nguyên, phường Lạc Viên, quận Lê Chân, Hà Nội` | `Số 64 ngõ 10 Thủy Nguyên, P. Lạc Viên, Q. Lê Chân, Hà Nội` | ratio 0.8833 |  | viết tắt P./Q. — cùng địa chỉ |
| text | `Số 47 ngõ 101 Lý Thường Kiệt, phường Hòa Nghĩa, quận Hồng Bàng, Cần Thơ` | `SỐ 47 NGÕ 101 LÝ THƯỜNG KIỆT, PHƯỜNG HÒA NGHĨA, QUẬN HỒNG BÀNG, CẦN THƠ` | ratio 0.4507 |  | địa chỉ viết HOA |
| text | `Số 76 ngõ 13 Trần Hưng Đạo, phường Thượng Lý, quận Ngô Quyền, Hà Nội` | `Số 76 ngõ 13 Trần Hưng Đạo, phường Thượng Lý, quận Ngô Quyền, Hà Nội` | ratio 0.6709 |  | địa chỉ NFC vs NFD |
| text | `Công ty TNHH MTV Biển Xanh Đại Dương` | `CÔNG TY TNHH MTV BIỂN XANH ĐẠI DƯƠNG` | ratio 0.5278 |  | tên công ty viết HOA |
| text | `Doanh nghiệp tư nhân Tân Hòa Kỹ thuật` | `Doanh nghiệp tư nhân Tân Hòa Kỹ thuật` | ratio 0.7229 |  | tên công ty NFC vs NFD |
| text | `Công ty Cổ phần Kỹ thuật Tân Hòa` | `CÔNG TY CỔ PHẦN KỸ THUẬT TÂN HÒA` | ratio 0.3438 |  | tên công ty viết HOA |
| text | `Doanh nghiệp tư nhân Đầu tư Hòa Lợi` | `DOANH NGHIỆP TƯ NHÂN ĐẦU TƯ HÒA LỢI` | ratio 0.3143 |  | tên công ty viết HOA |
| text | `Công ty TNHH Thuận Phát Đầu tư` | `Công ty TNHH Thuận Phát Đầu tư` | ratio 0.7463 |  | tên công ty NFC vs NFD |
| text | `Công ty Cổ phần Thương mại Kỹ thuật` | `Công ty Cổ phần Thương mại Kỹ thuật` | ratio 0.6667 |  | tên công ty NFC vs NFD |
| text | `Công ty TNHH MTV Thủy sản Tân Hòa` | `Công ty TNHH MTV Thủy sản Tân Hòa` | ratio 0.7887 |  | tên công ty NFC vs NFD |
| text | `Công ty Cổ phần Đại Dương Kỹ thuật` | `CÔNG TY CỔ PHẦN ĐẠI DƯƠNG KỸ THUẬT` | ratio 0.3529 |  | tên công ty viết HOA |
| text | `Doanh nghiệp tư nhân Thuận Phát Thương mại` | `DOANH NGHIỆP TƯ NHÂN THUẬN PHÁT THƯƠNG MẠI` | ratio 0.2143 |  | tên công ty viết HOA |
| text | `Doanh nghiệp tư nhân Thương mại Đầu tư` | `DOANH NGHIỆP TƯ NHÂN THƯƠNG MẠI ĐẦU TƯ` | ratio 0.2105 |  | tên công ty viết HOA |
| text | `Doanh nghiệp tư nhân Tân Hòa Thương mại` | `DOANH NGHIỆP TƯ NHÂN TÂN HÒA THƯƠNG MẠI` | ratio 0.2308 |  | tên công ty viết HOA |
| text | `Công ty TNHH MTV Xây dựng Đầu tư` | `CÔNG TY TNHH MTV XÂY DỰNG ĐẦU TƯ` | ratio 0.5312 |  | tên công ty viết HOA |
| text | `Doanh nghiệp tư nhân Đầu tư Biển Xanh` | `DOANH NGHIỆP TƯ NHÂN ĐẦU TƯ BIỂN XANH` | ratio 0.2973 |  | tên công ty viết HOA |
| text | `Công ty Cổ phần Tân Hòa Biển Xanh` | `CÔNG TY CỔ PHẦN TÂN HÒA BIỂN XANH` | ratio 0.3939 |  | tên công ty viết HOA |
| text | `Doanh nghiệp tư nhân Phúc Thịnh Thuận Phát` | `DOANH NGHIỆP TƯ NHÂN PHÚC THỊNH THUẬN PHÁT` | ratio 0.2857 |  | tên công ty viết HOA |
| text | `Doanh nghiệp tư nhân An Khánh Thương mại` | `Doanh nghiệp tư nhân An Khánh Thương mại` | ratio 0.75 |  | tên công ty NFC vs NFD |
| text | `Công ty TNHH Đầu tư Dịch vụ` | `Công ty TNHH Đầu tư Dịch vụ` | ratio 0.7333 |  | tên công ty NFC vs NFD |
| text | `Công ty TNHH MTV Hoàng Gia Biển Xanh` | `Công ty TNHH MTV Hoàng Gia Biển Xanh` | ratio 0.8684 |  | tên công ty NFC vs NFD |
| text | `Công ty Cổ phần Đại Dương Thương mại` | `Công ty Cổ phần Đại Dương Thương mại` | ratio 0.6506 |  | tên công ty NFC vs NFD |
| text | `Công ty TNHH Hoàng Gia Thuận Phát` | `CÔNG TY TNHH HOÀNG GIA THUẬN PHÁT` | ratio 0.4545 |  | tên công ty viết HOA |
| text | `Công ty TNHH MTV Tân Hòa Kỹ thuật` | `Công ty TNHH MTV Tân Hòa Kỹ thuật` | ratio 0.7778 |  | tên công ty NFC vs NFD |
| text | `Doanh nghiệp tư nhân An Khánh Tân Hòa` | `Doanh nghiệp tư nhân An Khánh Tân Hòa` | ratio 0.7654 |  | tên công ty NFC vs NFD |
| text | `Công ty Cổ phần Hoàng Gia Xây dựng` | `CÔNG TY CỔ PHẦN HOÀNG GIA XÂY DỰNG` | ratio 0.3529 |  | tên công ty viết HOA |
| text | `Doanh nghiệp tư nhân Biển Xanh Phúc Thịnh` | `Doanh nghiệp tư nhân Biển Xanh Phúc Thịnh` | ratio 0.7778 |  | tên công ty NFC vs NFD |
| text | `Công ty TNHH Đại Dương Phúc Thịnh` | `Công ty TNHH Đại Dương Phúc Thịnh` | ratio 0.75 |  | tên công ty NFC vs NFD |
| money | `46000000000đ` | `46,000,000,000 đồng` | ratio 0.7742 |  | cùng số tiền, khác định dạng/đơn vị VND |
| money | `22,000,000,000 VNĐ` | `22.000.000.000,00 đ` | ratio 0.4865 |  | cùng số tiền, có phần thập phân ,00 |
| money | `85,619,000 đồng` | `85.619.000` | ratio 0.64 |  | cùng số tiền, khác định dạng/đơn vị VND |
| money | `44000000000đ` | `44.000.000.000,00 đ` | ratio 0.7742 |  | cùng số tiền, có phần thập phân ,00 |
| money | `2900000000 đồng` | `2900 triệu` | ratio 0.4 |  | số tiền viết bằng chữ tỷ/triệu |
| money | `40.362.000 đ` | `40,362,000` | ratio 0.7273 |  | cùng số tiền, khác định dạng/đơn vị VND |
| money | `₫292000000` | `292 triệu` | ratio 0.3158 |  | số tiền viết bằng chữ tỷ/triệu |
| money | `74,000,000đ` | `74.000.000,00 đ` | ratio 0.6923 |  | cùng số tiền, có phần thập phân ,00 |
| money | `26,000,000,000 VND` | `26 tỷ` | ratio 0.2609 |  | số tiền viết bằng chữ tỷ/triệu |
| money | `76,043,000 VNĐ` | `76.043.000 đồng` | ratio 0.6207 |  | cùng số tiền, khác định dạng/đơn vị VND |
| money | `45.000.000.000 đ` | `45,000,000,000 đồng` | ratio 0.7429 |  | cùng số tiền, khác định dạng/đơn vị VND |
| money | `28,000,000,000 đồng` | `28.000.000.000,00 đ` | ratio 0.5263 |  | cùng số tiền, có phần thập phân ,00 |
| money | `39157000 VND` | `39.157.000` | ratio 0.7273 |  | cùng số tiền, khác định dạng/đơn vị VND |
| money | `33,000,000,000 VNĐ` | `33.000.000.000,00 đ` | ratio 0.4865 |  | cùng số tiền, có phần thập phân ,00 |
| money | `7,000,000,000 VNĐ` | `7.000.000.000,00 đ` | ratio 0.4571 |  | cùng số tiền, có phần thập phân ,00 |
| money | `8.500.000.000 VND` | `8500 triệu` | ratio 0.3704 |  | số tiền viết bằng chữ tỷ/triệu |
| money | `800000000` | `800.000.000 đồng` | ratio 0.72 |  | cùng số tiền, khác định dạng/đơn vị VND |
| money | `26.240.000đ` | `26.240.000,00 đ` | ratio 0.8462 |  | cùng số tiền, có phần thập phân ,00 |
| money | `41,000,000,000 VND` | `41.000.000.000,00 đ` | ratio 0.4865 |  | cùng số tiền, có phần thập phân ,00 |
| money | `8200000000` | `8,200,000,000đ` | ratio 0.8333 |  | cùng số tiền, khác định dạng/đơn vị VND |
| money | `8.200.000.000 VNĐ` | `8.200.000.000đ` | ratio 0.8387 |  | cùng số tiền, khác định dạng/đơn vị VND |
| money | `1,400,000,000 đồng` | `1.400.000.000,00 đ` | ratio 0.6667 |  | cùng số tiền, có phần thập phân ,00 |
| money | `416000000 đ` | `416.000.000,00 đ` | ratio 0.8148 |  | cùng số tiền, có phần thập phân ,00 |
| money | `7,000,000,000` | `7 tỷ` | ratio 0.1176 |  | số tiền viết bằng chữ tỷ/triệu |
| money | `16,772,000` | `16772000` | ratio 0.8889 |  | cùng số tiền, khác định dạng/đơn vị VND |
| money | `60.501.000 VNĐ` | `60.501.000,00 đ` | ratio 0.7586 |  | cùng số tiền, có phần thập phân ,00 |
| money | `28094000 đồng` | `28,094,000 VNĐ` | ratio 0.6667 |  | cùng số tiền, khác định dạng/đơn vị VND |
| money | `12.000.000` | `12,000,000 đ` | ratio 0.7273 |  | cùng số tiền, khác định dạng/đơn vị VND |
| money | `7.600.000.000 VNĐ` | `7.600.000.000,00 đ` | ratio 0.8 |  | cùng số tiền, có phần thập phân ,00 |
| money | `5.000.000.000 đ` | `5000000000` | ratio 0.8 |  | cùng số tiền, khác định dạng/đơn vị VND |
| money | `61,022,000` | `61.022.000,00 đ` | ratio 0.64 |  | cùng số tiền, có phần thập phân ,00 |
| money | `34000000000` | `34.000.000.000 VNĐ` | ratio 0.7586 |  | cùng số tiền, khác định dạng/đơn vị VND |
| money | `5.800.000.000 đ` | `5800 triệu` | ratio 0.4 |  | số tiền viết bằng chữ tỷ/triệu |
| money | `503.000.000 VND` | `503.000.000,00 đ` | ratio 0.7742 |  | cùng số tiền, có phần thập phân ,00 |
| money | `56,335,000 đồng` | `56,335,000` | ratio 0.8 |  | cùng số tiền, khác định dạng/đơn vị VND |
| money | `₫9900000000` | `9.900.000.000 đồng` | ratio 0.6897 |  | cùng số tiền, khác định dạng/đơn vị VND |
| money | `6,500,000,000 đ` | `6.500.000.000 đ` | ratio 0.8 |  | cùng số tiền, khác định dạng/đơn vị VND |
| money | `3.000.000.000` | `3.000.000.000,00 đ` | ratio 0.8387 |  | cùng số tiền, có phần thập phân ,00 |
| money | `8.300.000.000 VND` | `8.300.000.000,00 đ` | ratio 0.8 |  | cùng số tiền, có phần thập phân ,00 |
| money | `6.500.000.000 VND` | `6500000000 đồng` | ratio 0.6875 |  | cùng số tiền, khác định dạng/đơn vị VND |
| date | `04-04-2022` | `ngày 04 tháng 04 năm 2022` | ratio 0.4571 |  | ngày viết bằng chữ |
| date | `20/2/2021` | `20.02.2021` | ratio 0.7368 |  | cùng ngày, khác định dạng |
| date | `22/10/2024` | `22-10-2024` | ratio 0.8 |  | cùng ngày, khác định dạng |
| date | `14/02/2024` | `ngày 14 tháng 02 năm 2024` | ratio 0.4571 |  | ngày viết bằng chữ |
| date | `11-09-2022` | `11/9/2022` | ratio 0.7368 |  | cùng ngày, khác định dạng |
| date | `2023-05-01` | `ngày 01 tháng 05 năm 2023` | ratio 0.2286 |  | ngày viết bằng chữ |
| date | `04-07-2022` | `ngày 04 tháng 07 năm 2022` | ratio 0.4571 |  | ngày viết bằng chữ |
| date | `13/9/2026` | `13-09-2026` | ratio 0.7368 |  | cùng ngày, khác định dạng |
| date | `07-08-2022` | `07.08.2022` | ratio 0.8 |  | cùng ngày, khác định dạng |
| date | `27/8/2021` | `ngày 27 tháng 08 năm 2021` | ratio 0.4118 |  | ngày viết bằng chữ |
| date | `2024-10-31` | `ngày 31 tháng 10 năm 2024` | ratio 0.2286 |  | ngày viết bằng chữ |
| date | `01/09/2024` | `ngày 01 tháng 09 năm 2024` | ratio 0.4571 |  | ngày viết bằng chữ |
| date | `26.04.2026` | `2026-04-26` | ratio 0.4 |  | cùng ngày, khác định dạng |
| date | `15.09.2021` | `15/9/2021` | ratio 0.7368 |  | cùng ngày, khác định dạng |
| date | `13/4/2025` | `ngày 13 tháng 04 năm 2025` | ratio 0.4118 |  | ngày viết bằng chữ |
| date | `2021-06-10` | `ngày 10 tháng 06 năm 2021` | ratio 0.2286 |  | ngày viết bằng chữ |
| date | `20/10/2024` | `ngày 20 tháng 10 năm 2024` | ratio 0.4571 |  | ngày viết bằng chữ |
| date | `21-01-2021` | `ngày 21 tháng 01 năm 2021` | ratio 0.4571 |  | ngày viết bằng chữ |
| date | `21/3/2023` | `ngày 21 tháng 03 năm 2023` | ratio 0.4118 |  | ngày viết bằng chữ |
| date | `30-12-2024` | `2024-12-30` | ratio 0.6 |  | cùng ngày, khác định dạng |
| date | `27.07.2023` | `ngày 27 tháng 07 năm 2023` | ratio 0.4571 |  | ngày viết bằng chữ |
| date | `08-04-2021` | `2021-04-08` | ratio 0.6 |  | cùng ngày, khác định dạng |
| date | `29-06-2024` | `29.06.2024` | ratio 0.8 |  | cùng ngày, khác định dạng |
| date | `13-03-2025` | `13/03/2025` | ratio 0.8 |  | cùng ngày, khác định dạng |
| date | `18.04.2024` | `ngày 18 tháng 04 năm 2024` | ratio 0.4571 |  | ngày viết bằng chữ |
| date | `15.04.2026` | `2026-04-15` | ratio 0.4 |  | cùng ngày, khác định dạng |
| date | `23-08-2022` | `23/08/2022` | ratio 0.8 |  | cùng ngày, khác định dạng |
| date | `23/11/2020` | `2020-11-23` | ratio 0.4 |  | cùng ngày, khác định dạng |
| date | `2025-05-03` | `3/5/2025` | ratio 0.4444 |  | cùng ngày, khác định dạng |
| date | `17/10/2024` | `17-10-2024` | ratio 0.8 |  | cùng ngày, khác định dạng |
| date | `21/04/2021` | `ngày 21 tháng 04 năm 2021` | ratio 0.4571 |  | ngày viết bằng chữ |
| date | `24/07/2021` | `24.07.2021` | ratio 0.8 |  | cùng ngày, khác định dạng |
| name | `Đỗ Quốc Toàn` | `ĐỖ QUỐC TOÀN` | ratio 0.4167 |  | tên viết HOA |
| name | `Hoàng Hữu Dũng` | `  Hoàng Hữu  Dũng ` | ratio 0.875 |  | tên thừa khoảng trắng |
| name | `Lê Đức Hòa` | `LÊ ĐỨC HÒA` | ratio 0.5 |  | tên viết HOA |
| name | `Khúc Văn Khánh` | `  Khúc Văn Khánh  ` | ratio 0.875 |  | tên thừa khoảng trắng |
| name | `Vũ Hữu Dũng` | `  Vũ  Hữu Dũng ` | ratio 0.8462 |  | tên thừa khoảng trắng |
| name | `Đỗ Thị Nhung` | `Đỗ Thị Nhung` | ratio 0.7407 |  | tên NFC vs NFD |
| name | `Bùi Văn Khánh` | `  Bùi Văn  Khánh ` | ratio 0.8667 |  | tên thừa khoảng trắng |
| name | `Vũ Thu An` | `  Vũ Thu  An ` | ratio 0.8182 |  | tên thừa khoảng trắng |
| name | `Khúc Văn Hùng` | `Khúc Văn Hùng` | ratio 0.6897 |  | tên NFC vs NFD |
| name | `Đỗ Hữu Tuấn` | `Đỗ Hữu Tuấn` | ratio 0.5714 |  | tên NFC vs NFD |
| name | `Đặng Thị Phương` | `Đặng Thị Phương` | ratio 0.6286 |  | tên NFC vs NFD |
| name | `Trần Minh Lan` | `TRẦN MINH LAN` | ratio 0.3846 |  | tên viết HOA |
| name | `Nguyễn Ngọc Bình` | `Nguyễn Ngọc Bình` | ratio 0.7222 |  | tên NFC vs NFD |
| name | `Vũ Văn Yến` | `VŨ VĂN YẾN` | ratio 0.5 |  | tên viết HOA |
| name | `Đặng Minh Lan` | `  Đặng Minh  Lan ` | ratio 0.8667 |  | tên thừa khoảng trắng |
| name | `Hoàng Văn Nhung` | `Hoàng Văn Nhung` | ratio 0.8125 |  | tên NFC vs NFD |
| name | `Đặng Ngọc Lan` | `Đặng Ngọc Lan` | ratio 0.7586 |  | tên NFC vs NFD |
| name | `Trần Thị Hòa` | `TRẦN THỊ HÒA` | ratio 0.4167 |  | tên viết HOA |
| name | `Nguyễn Thanh Thụy` | `  Nguyễn Thanh Thụy  ` | ratio 0.8947 |  | tên thừa khoảng trắng |
| name | `Nguyễn Văn Hoè` | `NGUYỄN VĂN HOÈ` | ratio 0.3571 |  | tên viết HOA |
| name | `Đỗ Văn Thủy` | `  Đỗ  Văn Thủy ` | ratio 0.8462 |  | tên thừa khoảng trắng |
| name | `Đỗ Thanh Hòa` | `ĐỖ THANH HÒA` | ratio 0.4167 |  | tên viết HOA |
| name | `Đỗ Quốc Hòa` | `Đỗ Quốc Hòa` | ratio 0.5926 |  | tên NFC vs NFD |
| name | `Hoàng Minh Khánh` | `Hoàng Minh Khánh` | ratio 0.8235 |  | tên NFC vs NFD |
| name | `Đỗ Văn Bình` | `  Đỗ  Văn Bình ` | ratio 0.8462 |  | tên thừa khoảng trắng |
| name | `Bùi Quốc Dũng` | `BÙI QUỐC DŨNG` | ratio 0.3846 |  | tên viết HOA |
| name | `Ngô Văn Hòa` | `Ngô Văn Hoà` | ratio 0.8182 |  | tên dấu thanh kiểu cũ (oà/uỷ) |
| name | `Lê Thị Lan` | `LÊ THỊ LAN` | ratio 0.5 |  | tên viết HOA |
| name | `Đặng Quốc Dũng` | `ĐẶNG QUỐC DŨNG` | ratio 0.3571 |  | tên viết HOA |
| name | `Đặng Ngọc Lan` | `  Đặng Ngọc  Lan ` | ratio 0.8667 |  | tên thừa khoảng trắng |
| name | `Bùi Văn Nhung` | `  Bùi  Văn Nhung ` | ratio 0.8667 |  | tên thừa khoảng trắng |
| name | `Đỗ Đức Hòa` | `ĐỖ ĐỨC HÒA` | ratio 0.5 |  | tên viết HOA |
| name | `Phạm Văn An` | `  Phạm Văn An  ` | ratio 0.8462 |  | tên thừa khoảng trắng |
| name | `Ngô Minh Hòa` | `NGÔ MINH HÒA` | ratio 0.4167 |  | tên viết HOA |
| name | `Đặng Minh Bình` | `Đặng Minh Bình` | ratio 0.7742 |  | tên NFC vs NFD |

### `rapidfuzz` — false-equal: 92 cặp

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
| text | `Số 28 ngõ 44 Nguyễn Trãi, phường An Biên, quận Lê Chân, Cần Thơ` | `Số 28 ngõ 45 Nguyễn Trãi, phường An Biên, quận Lê Chân, Cần Thơ` | ratio 98.41 |  | khác số ngõ |
| text | `Số 215 ngõ 105 Hoàng Văn Thụ, phường Kênh Dương, quận Ngô Quyền, Cần Thơ` | `Số 215 ngõ 106 Hoàng Văn Thụ, phường Kênh Dương, quận Ngô Quyền, Cần Thơ` | ratio 98.61 |  | khác số ngõ |
| text | `Số 146 ngõ 111 Hùng Vương, phường Thượng Lý, quận Dương Kinh, Cần Thơ` | `Số 146 ngõ 112 Hùng Vương, phường Thượng Lý, quận Dương Kinh, Cần Thơ` | ratio 98.55 |  | khác số ngõ |
| text | `Số 229 ngõ 16 Quang Trung, phường Kênh Dương, quận Kiến An, Đà Nẵng` | `Số 228 ngõ 16 Quang Trung, phường Kênh Dương, quận Kiến An, Đà Nẵng` | ratio 98.51 |  | khác số nhà |
| text | `Số 115 ngõ 45 Thủy Nguyên, phường Đằng Giang, quận Hồng Bàng, Cần Thơ` | `Số 117 ngõ 45 Thủy Nguyên, phường Đằng Giang, quận Hồng Bàng, Cần Thơ` | ratio 98.55 |  | khác số nhà |
| text | `Số 217 ngõ 118 Lý Thường Kiệt, phường Đằng Giang, quận Kiến An, Hà Nội` | `Số 216 ngõ 118 Lý Thường Kiệt, phường Đằng Giang, quận Kiến An, Hà Nội` | ratio 98.57 |  | khác số nhà |
| text | `Số 183 ngõ 43 Quang Trung, phường Lạc Viên, quận Lê Chân, Cần Thơ` | `Số 182 ngõ 43 Quang Trung, phường Lạc Viên, quận Lê Chân, Cần Thơ` | ratio 98.46 |  | khác số nhà |
| text | `Số 12 ngõ 105 Tô Hiệu, phường Cầu Đất, quận Ngô Quyền, Cần Thơ` | `Số 12 ngõ 106 Tô Hiệu, phường Cầu Đất, quận Ngô Quyền, Cần Thơ` | ratio 98.39 |  | khác số ngõ |
| text | `Số 166 ngõ 66 Lý Thường Kiệt, phường Lạc Viên, quận Kiến An, Cần Thơ` | `Số 165 ngõ 66 Lý Thường Kiệt, phường Lạc Viên, quận Kiến An, Cần Thơ` | ratio 98.53 |  | khác số nhà |
| text | `Số 12 ngõ 42 Quang Trung, phường Máy Tơ, quận Kiến An, Hải Phòng` | `Số 13 ngõ 42 Quang Trung, phường Máy Tơ, quận Kiến An, Hải Phòng` | ratio 98.44 |  | khác số nhà |
| text | `Số 173 ngõ 29 Hoàng Văn Thụ, phường An Biên, quận Lê Chân, Đà Nẵng` | `Số 173 ngõ 29 Hoàng Văn Thụ, phường Đằng Giang, quận Lê Chân, Đà Nẵng` | ratio 93.33 |  | khác phường |
| text | `Số 1 ngõ 29 Trần Hưng Đạo, phường Đằng Giang, quận Lê Chân, Đà Nẵng` | `Số 1 ngõ 29 Trần Hưng Đạo, phường Kênh Dương, quận Lê Chân, Đà Nẵng` | ratio 91.04 |  | khác phường |
| text | `Số 49 ngõ 68 Thủy Nguyên, phường Thượng Lý, quận Ngô Quyền, Đà Nẵng` | `Số 49 ngõ 69 Thủy Nguyên, phường Thượng Lý, quận Ngô Quyền, Đà Nẵng` | ratio 98.51 |  | khác số ngõ |
| text | `Số 75 ngõ 49 Hòa Bình, phường Đông Khê, quận Hồng Bàng, Hải Phòng` | `Số 75 ngõ 49 Hòa Bình, phường Máy Tơ, quận Hồng Bàng, Hải Phòng` | ratio 90.62 |  | khác phường |
| text | `Số 147 ngõ 39 Lê Lợi, phường Cầu Đất, quận Lê Chân, Cần Thơ` | `Số 147 ngõ 39 Lê Lợi, phường Máy Tơ, quận Lê Chân, Cần Thơ` | ratio 90.6 |  | khác phường |
| text | `Số 19 ngõ 37 Văn Cao, phường Đông Khê, quận Hồng Bàng, Cần Thơ` | `Số 19 ngõ 38 Văn Cao, phường Đông Khê, quận Hồng Bàng, Cần Thơ` | ratio 98.39 |  | khác số ngõ |
| text | `Số 163 ngõ 5 Trần Hưng Đạo, phường Vĩnh Niệm, quận Kiến An, Hải Phòng` | `Số 165 ngõ 5 Trần Hưng Đạo, phường Vĩnh Niệm, quận Kiến An, Hải Phòng` | ratio 98.55 |  | khác số nhà |
| text | `Số 217 ngõ 98 Văn Cao, phường Cầu Đất, quận Kiến An, Đà Nẵng` | `Số 218 ngõ 98 Văn Cao, phường Cầu Đất, quận Kiến An, Đà Nẵng` | ratio 98.33 |  | khác số nhà |
| text | `Số 245 ngõ 73 Điện Biên Phủ, phường Cầu Đất, quận Hồng Bàng, Hải Phòng` | `Số 255 ngõ 73 Điện Biên Phủ, phường Cầu Đất, quận Hồng Bàng, Hải Phòng` | ratio 98.57 |  | khác số nhà |
| text | `Số 237 ngõ 52 Ngô Quyền, phường Vĩnh Niệm, quận Lê Chân, Cần Thơ` | `Số 236 ngõ 52 Ngô Quyền, phường Vĩnh Niệm, quận Lê Chân, Cần Thơ` | ratio 98.44 |  | khác số nhà |
| text | `Số 125 ngõ 92 Nguyễn Trãi, phường Cầu Đất, quận Ngô Quyền, Hải Phòng` | `Số 125 ngõ 93 Nguyễn Trãi, phường Cầu Đất, quận Ngô Quyền, Hải Phòng` | ratio 98.53 |  | khác số ngõ |
| text | `Số 167 ngõ 75 Văn Cao, phường Vĩnh Niệm, quận Lê Chân, Đà Nẵng` | `Số 168 ngõ 75 Văn Cao, phường Vĩnh Niệm, quận Lê Chân, Đà Nẵng` | ratio 98.39 |  | khác số nhà |
| text | `Số 76 ngõ 102 Hoàng Văn Thụ, phường Cầu Đất, quận Dương Kinh, Hải Phòng` | `Số 76 ngõ 103 Hoàng Văn Thụ, phường Cầu Đất, quận Dương Kinh, Hải Phòng` | ratio 98.59 |  | khác số ngõ |
| text | `Số 40 ngõ 107 Quang Trung, phường Lạc Viên, quận Dương Kinh, Hà Nội` | `Số 41 ngõ 107 Quang Trung, phường Lạc Viên, quận Dương Kinh, Hà Nội` | ratio 98.51 |  | khác số nhà |
| text | `Số 241 ngõ 96 Quang Trung, phường An Biên, quận Ngô Quyền, Hải Phòng` | `Số 240 ngõ 96 Quang Trung, phường An Biên, quận Ngô Quyền, Hải Phòng` | ratio 98.53 |  | khác số nhà |
| text | `Số 138 ngõ 88 Điện Biên Phủ, phường Hòa Nghĩa, quận Ngô Quyền, Hà Nội` | `Số 138 ngõ 89 Điện Biên Phủ, phường Hòa Nghĩa, quận Ngô Quyền, Hà Nội` | ratio 98.55 |  | khác số ngõ |
| text | `Số 206 ngõ 22 Lê Lợi, phường Lạc Viên, quận Hồng Bàng, Cần Thơ` | `Số 206 ngõ 22 Lê Lợi, phường An Biên, quận Hồng Bàng, Cần Thơ` | ratio 94.31 |  | khác phường |
| text | `Số 26 ngõ 15 Lê Lợi, phường Thượng Lý, quận Lê Chân, Đà Nẵng` | `Số 28 ngõ 15 Lê Lợi, phường Thượng Lý, quận Lê Chân, Đà Nẵng` | ratio 98.33 |  | khác số nhà |
| text | `Số 247 ngõ 106 Hòa Bình, phường Kênh Dương, quận Kiến An, Đà Nẵng` | `Số 257 ngõ 106 Hòa Bình, phường Kênh Dương, quận Kiến An, Đà Nẵng` | ratio 98.46 |  | khác số nhà |
| text | `Số 240 ngõ 15 Hùng Vương, phường Máy Tơ, quận Dương Kinh, Cần Thơ` | `Số 250 ngõ 15 Hùng Vương, phường Máy Tơ, quận Dương Kinh, Cần Thơ` | ratio 98.46 |  | khác số nhà |
| text | `Số 248 ngõ 39 Lê Lợi, phường Đông Khê, quận Dương Kinh, Hải Phòng` | `Số 248 ngõ 40 Lê Lợi, phường Đông Khê, quận Dương Kinh, Hải Phòng` | ratio 96.92 |  | khác số ngõ |
| text | `Số 168 ngõ 7 Thủy Nguyên, phường Đằng Giang, quận Dương Kinh, Đà Nẵng` | `Số 168 ngõ 7 Thủy Nguyên, phường An Biên, quận Dương Kinh, Đà Nẵng` | ratio 93.33 |  | khác phường |
| text | `Số 121 ngõ 33 Lê Lợi, phường Vĩnh Niệm, quận Ngô Quyền, Cần Thơ` | `Số 131 ngõ 33 Lê Lợi, phường Vĩnh Niệm, quận Ngô Quyền, Cần Thơ` | ratio 98.41 |  | khác số nhà |
| text | `Số 106 ngõ 7 Quang Trung, phường Thượng Lý, quận Kiến An, Hải Phòng` | `Số 106 ngõ 8 Quang Trung, phường Thượng Lý, quận Kiến An, Hải Phòng` | ratio 98.51 |  | khác số ngõ |
| text | `Công ty TNHH Xây dựng Vận tải` | `Công ty TNHH MTV Xây dựng Vận tải` | ratio 93.55 |  | khác loại hình (TNHH/CP/MTV/DNTN) |
| text | `Công ty TNHH Đầu tư Tân Hòa` | `Công ty TNHH MTV Đầu tư Tân Hòa` | ratio 93.1 |  | khác loại hình (TNHH/CP/MTV/DNTN) |
| text | `Công ty TNHH MTV Hoàng Gia Xây dựng` | `Công ty TNHH Hoàng Gia Xây dựng` | ratio 93.94 |  | khác loại hình (TNHH/CP/MTV/DNTN) |
| text | `Công ty TNHH An Khánh Minh Khoa` | `Công ty TNHH MTV An Khánh Minh Khoa` | ratio 93.94 |  | khác loại hình (TNHH/CP/MTV/DNTN) |
| id | `422/2026/HĐTC-PGB` | `423/2026/HĐTC-PGB` | ratio 94.12 |  | số HĐ lệch 1 số thứ tự |
| id | `216/2026/HĐTC-CN.HP` | `216/2025/HĐTC-CN.HP` | ratio 94.74 |  | số HĐ khác năm |
| id | `378/2024/HĐTC-PGB` | `378/2024/HĐTD-PGB` | ratio 94.12 |  | số HĐ khác loại hợp đồng |
| id | `774/2025/HĐBĐ-KHCN` | `774/2024/HĐBĐ-KHCN` | ratio 94.44 |  | số HĐ khác năm |
| id | `332/2026/HĐTD-KHDN` | `332/2025/HĐTD-KHDN` | ratio 94.44 |  | số HĐ khác năm |
| id | `058/2026/PL-CN.HP` | `059/2026/PL-CN.HP` | ratio 94.12 |  | số HĐ lệch 1 số thứ tự |
| id | `936/2024/HĐMB-KHDN` | `937/2024/HĐMB-KHDN` | ratio 94.44 |  | số HĐ lệch 1 số thứ tự |
| id | `894/2026/HĐTD-KHCN` | `894/2025/HĐTD-KHCN` | ratio 94.44 |  | số HĐ khác năm |
| id | `040/2025/HĐTC-KHCN` | `040/2024/HĐTC-KHCN` | ratio 94.44 |  | số HĐ khác năm |
| id | `566/2026/HĐBĐ-KHCN` | `567/2026/HĐBĐ-KHCN` | ratio 94.44 |  | số HĐ lệch 1 số thứ tự |
| id | `742/2024/HĐTD-PGB` | `743/2024/HĐTD-PGB` | ratio 94.12 |  | số HĐ lệch 1 số thứ tự |
| id | `256/2025/PL-KHDN` | `257/2025/PL-KHDN` | ratio 93.75 |  | số HĐ lệch 1 số thứ tự |
| id | `688/2026/HĐTD-PGB` | `688/2025/HĐTD-PGB` | ratio 94.12 |  | số HĐ khác năm |
| id | `330/2025/HĐTC-CN.HP` | `331/2025/HĐTC-CN.HP` | ratio 94.74 |  | số HĐ lệch 1 số thứ tự |
| id | `401/2026/HĐBĐ-KHDN` | `402/2026/HĐBĐ-KHDN` | ratio 94.44 |  | số HĐ lệch 1 số thứ tự |
| money | `20,000,000,000đ` | `20,000,000,000$` | ratio 93.33 |  | khác loại tiền (USD vs VND) |
| money | `92399000` | `923990000` | ratio 94.12 |  | thừa một số 0 |
| date | `2024-09-28` | `2024-10-28` | ratio 90.0 |  | lệch ~1 tháng |
| date | `19/11/2020` | `19/11/2021` | ratio 90.0 |  | khác năm |
| date | `13/07/2026` | `14/07/2026` | ratio 90.0 |  | lệch 1 ngày |
| date | `19/10/2021` | `19/10/2022` | ratio 90.0 |  | khác năm |
| date | `22.01.2023` | `23.01.2023` | ratio 90.0 |  | lệch 1 ngày |
| date | `04-04-2020` | `04-04-2021` | ratio 90.0 |  | khác năm |
| name | `Vũ Văn Toàn` | `Vũ Văn Toán` | ratio 90.91 |  | đổi 1 dấu → tên hợp lệ khác (người khác) |
| name | `Lê Ngọc Lan` | `Lê Ngọc Lân` | ratio 90.91 |  | đổi 1 dấu → tên hợp lệ khác (người khác) |
| name | `Nguyễn Văn Tuấn` | `Nguyễn Văn Tuân` | ratio 93.33 |  | đổi 1 dấu → tên hợp lệ khác (người khác) |
| name | `Hoàng Thị Dũng` | `Hoàng Thu Dũng` | ratio 92.86 |  | khác tên đệm |
| name | `Trần Thu Dũng` | `Trần Thị Dũng` | ratio 92.31 |  | khác tên đệm |
| name | `Vũ Hữu Lan` | `Vũ Hữu Lân` | ratio 90.0 |  | đổi 1 dấu → tên hợp lệ khác (người khác) |
| name | `Hoàng Minh Thụy` | `Hoàng Minh Thủy` | ratio 93.33 |  | khác tên |
| name | `Đặng Văn An` | `Đặng Văn Ân` | ratio 90.91 |  | đổi 1 dấu → tên hợp lệ khác (người khác) |
| name | `Ngô Hữu Tuấn` | `Ngô Hữu Tuân` | ratio 91.67 |  | đổi 1 dấu → tên hợp lệ khác (người khác) |

### `rapidfuzz` — false-diff: 186 cặp

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
| text | `Số 46 ngõ 84 Lạch Tray, phường Cầu Đất, quận Ngô Quyền, Hà Nội` | `Số 46 ngõ 84 Lạch Tray, phường Cầu Đất, quận Ngô Quyền, Hà Nội` | ratio 69.93 |  | địa chỉ NFC vs NFD |
| text | `Số 51 ngõ 111 Phạm Văn Đồng, phường An Biên, quận Hải An, Hải Phòng` | `SỐ 51 NGÕ 111 PHẠM VĂN ĐỒNG, PHƯỜNG AN BIÊN, QUẬN HẢI AN, HẢI PHÒNG` | ratio 47.76 |  | địa chỉ viết HOA |
| text | `Số 110 ngõ 55 Thủy Nguyên, phường Kênh Dương, quận Ngô Quyền, Đà Nẵng` | `Số 110 ngõ 55 Thủy Nguyên, P. Kênh Dương, Q. Ngô Quyền, Đà Nẵng` | ratio 89.39 |  | viết tắt P./Q. — cùng địa chỉ |
| text | `Số 132 ngõ 41 Lý Thường Kiệt, phường Đông Khê, quận Hồng Bàng, Hà Nội` | `SỐ 132 NGÕ 41 LÝ THƯỜNG KIỆT, PHƯỜNG ĐÔNG KHÊ, QUẬN HỒNG BÀNG, HÀ NỘI` | ratio 46.38 |  | địa chỉ viết HOA |
| text | `Số 246 ngõ 61 Hoàng Văn Thụ, phường Vĩnh Niệm, quận Lê Chân, Đà Nẵng` | `Số 246 ngõ 61 Hoàng Văn Thụ, phường Vĩnh Niệm, quận Lê Chân, Đà Nẵng` | ratio 69.68 |  | địa chỉ NFC vs NFD |
| text | `Số 181 ngõ 107 Tô Hiệu, phường Lạc Viên, quận Hải An, Cần Thơ` | `SỐ 181 NGÕ 107 TÔ HIỆU, PHƯỜNG LẠC VIÊN, QUẬN HẢI AN, CẦN THƠ` | ratio 50.82 |  | địa chỉ viết HOA |
| text | `Số 105 ngõ 8 Thủy Nguyên, phường Hòa Nghĩa, quận Hồng Bàng, Đà Nẵng` | `Số 105 ngõ 8 Thủy Nguyên, phường Hòa Nghĩa, quận Hồng Bàng, Đà Nẵng` | ratio 71.05 |  | địa chỉ NFC vs NFD |
| text | `Số 150 ngõ 102 Thủy Nguyên, phường Máy Tơ, quận Hồng Bàng, Hải Phòng` | `SỐ 150 NGÕ 102 THỦY NGUYÊN, PHƯỜNG MÁY TƠ, QUẬN HỒNG BÀNG, HẢI PHÒNG` | ratio 45.59 |  | địa chỉ viết HOA |
| text | `Số 58 ngõ 14 Hòa Bình, phường Vĩnh Niệm, quận Lê Chân, Hải Phòng` | `Số 58 ngõ 14 Hòa Bình, P. Vĩnh Niệm, Q. Lê Chân, Hải Phòng` | ratio 88.52 |  | viết tắt P./Q. — cùng địa chỉ |
| text | `Số 145 ngõ 116 Lạch Tray, phường Kênh Dương, quận Hải An, Cần Thơ` | `SỐ 145 NGÕ 116 LẠCH TRAY, PHƯỜNG KÊNH DƯƠNG, QUẬN HẢI AN, CẦN THƠ` | ratio 47.69 |  | địa chỉ viết HOA |
| text | `Số 118 ngõ 19 Hoàng Văn Thụ, phường An Biên, quận Hải An, Đà Nẵng` | `SỐ 118 NGÕ 19 HOÀNG VĂN THỤ, PHƯỜNG AN BIÊN, QUẬN HẢI AN, ĐÀ NẴNG` | ratio 49.23 |  | địa chỉ viết HOA |
| text | `Số 39 ngõ 7 Quang Trung, phường Đằng Giang, quận Kiến An, Cần Thơ` | `Số 39 ngõ 7 Quang Trung, phường Đằng Giang, quận Kiến An, Cần Thơ` | ratio 77.24 |  | địa chỉ NFC vs NFD |
| text | `Số 70 ngõ 76 Ngô Quyền, phường Cầu Đất, quận Hải An, Cần Thơ` | `Số 70 ngõ 76 Ngô Quyền, phường Cầu Đất, quận Hải An, Cần Thơ` | ratio 69.06 |  | địa chỉ NFC vs NFD |
| text | `Số 169 ngõ 14 Hòa Bình, phường Kênh Dương, quận Hồng Bàng, Hà Nội` | `SỐ 169 NGÕ 14 HÒA BÌNH, PHƯỜNG KÊNH DƯƠNG, QUẬN HỒNG BÀNG, HÀ NỘI` | ratio 46.15 |  | địa chỉ viết HOA |
| text | `Số 39 ngõ 98 Điện Biên Phủ, phường Kênh Dương, quận Ngô Quyền, Hà Nội` | `Số 39 ngõ 98 Điện Biên Phủ, P. Kênh Dương, Q. Ngô Quyền, Hà Nội` | ratio 89.39 |  | viết tắt P./Q. — cùng địa chỉ |
| text | `Số 197 ngõ 70 Điện Biên Phủ, phường Đằng Giang, quận Hồng Bàng, Cần Thơ` | `Số 197 ngõ 70 Điện Biên Phủ, P. Đằng Giang, Q. Hồng Bàng, Cần Thơ` | ratio 89.71 |  | viết tắt P./Q. — cùng địa chỉ |
| text | `Số 24 ngõ 114 Phạm Văn Đồng, phường Kênh Dương, quận Dương Kinh, Hải Phòng` | `SỐ 24 NGÕ 114 PHẠM VĂN ĐỒNG, PHƯỜNG KÊNH DƯƠNG, QUẬN DƯƠNG KINH, HẢI PHÒNG` | ratio 43.24 |  | địa chỉ viết HOA |
| text | `Số 79 ngõ 119 Thủy Nguyên, phường Đằng Giang, quận Ngô Quyền, Hải Phòng` | `Số 79 ngõ 119 Thủy Nguyên, P. Đằng Giang, Q. Ngô Quyền, Hải Phòng` | ratio 89.71 |  | viết tắt P./Q. — cùng địa chỉ |
| text | `Số 191 ngõ 53 Lý Thường Kiệt, phường Thượng Lý, quận Hồng Bàng, Hải Phòng` | `Số 191 ngõ 53 Lý Thường Kiệt, phường Thượng Lý, quận Hồng Bàng, Hải Phòng` | ratio 67.46 |  | địa chỉ NFC vs NFD |
| text | `Số 64 ngõ 10 Thủy Nguyên, phường Lạc Viên, quận Lê Chân, Hà Nội` | `Số 64 ngõ 10 Thủy Nguyên, P. Lạc Viên, Q. Lê Chân, Hà Nội` | ratio 88.33 |  | viết tắt P./Q. — cùng địa chỉ |
| text | `Số 47 ngõ 101 Lý Thường Kiệt, phường Hòa Nghĩa, quận Hồng Bàng, Cần Thơ` | `SỐ 47 NGÕ 101 LÝ THƯỜNG KIỆT, PHƯỜNG HÒA NGHĨA, QUẬN HỒNG BÀNG, CẦN THƠ` | ratio 45.07 |  | địa chỉ viết HOA |
| text | `Số 76 ngõ 13 Trần Hưng Đạo, phường Thượng Lý, quận Ngô Quyền, Hà Nội` | `Số 76 ngõ 13 Trần Hưng Đạo, phường Thượng Lý, quận Ngô Quyền, Hà Nội` | ratio 67.09 |  | địa chỉ NFC vs NFD |
| text | `Công ty TNHH MTV Biển Xanh Đại Dương` | `CÔNG TY TNHH MTV BIỂN XANH ĐẠI DƯƠNG` | ratio 52.78 |  | tên công ty viết HOA |
| text | `Doanh nghiệp tư nhân Tân Hòa Kỹ thuật` | `Doanh nghiệp tư nhân Tân Hòa Kỹ thuật` | ratio 72.29 |  | tên công ty NFC vs NFD |
| text | `Công ty Cổ phần Kỹ thuật Tân Hòa` | `CÔNG TY CỔ PHẦN KỸ THUẬT TÂN HÒA` | ratio 37.5 |  | tên công ty viết HOA |
| text | `Doanh nghiệp tư nhân Đầu tư Hòa Lợi` | `DOANH NGHIỆP TƯ NHÂN ĐẦU TƯ HÒA LỢI` | ratio 31.43 |  | tên công ty viết HOA |
| text | `Công ty TNHH Thuận Phát Đầu tư` | `Công ty TNHH Thuận Phát Đầu tư` | ratio 74.63 |  | tên công ty NFC vs NFD |
| text | `Công ty Cổ phần Thương mại Kỹ thuật` | `Công ty Cổ phần Thương mại Kỹ thuật` | ratio 66.67 |  | tên công ty NFC vs NFD |
| text | `Công ty TNHH MTV Thủy sản Tân Hòa` | `Công ty TNHH MTV Thủy sản Tân Hòa` | ratio 78.87 |  | tên công ty NFC vs NFD |
| text | `Công ty Cổ phần Đại Dương Kỹ thuật` | `CÔNG TY CỔ PHẦN ĐẠI DƯƠNG KỸ THUẬT` | ratio 35.29 |  | tên công ty viết HOA |
| text | `Doanh nghiệp tư nhân Thuận Phát Thương mại` | `DOANH NGHIỆP TƯ NHÂN THUẬN PHÁT THƯƠNG MẠI` | ratio 26.19 |  | tên công ty viết HOA |
| text | `Doanh nghiệp tư nhân Thương mại Đầu tư` | `DOANH NGHIỆP TƯ NHÂN THƯƠNG MẠI ĐẦU TƯ` | ratio 26.32 |  | tên công ty viết HOA |
| text | `Doanh nghiệp tư nhân Tân Hòa Thương mại` | `DOANH NGHIỆP TƯ NHÂN TÂN HÒA THƯƠNG MẠI` | ratio 28.21 |  | tên công ty viết HOA |
| text | `Công ty TNHH MTV Xây dựng Đầu tư` | `CÔNG TY TNHH MTV XÂY DỰNG ĐẦU TƯ` | ratio 53.12 |  | tên công ty viết HOA |
| text | `Doanh nghiệp tư nhân Đầu tư Biển Xanh` | `DOANH NGHIỆP TƯ NHÂN ĐẦU TƯ BIỂN XANH` | ratio 29.73 |  | tên công ty viết HOA |
| text | `Công ty Cổ phần Tân Hòa Biển Xanh` | `CÔNG TY CỔ PHẦN TÂN HÒA BIỂN XANH` | ratio 39.39 |  | tên công ty viết HOA |
| text | `Doanh nghiệp tư nhân Phúc Thịnh Thuận Phát` | `DOANH NGHIỆP TƯ NHÂN PHÚC THỊNH THUẬN PHÁT` | ratio 28.57 |  | tên công ty viết HOA |
| text | `Doanh nghiệp tư nhân An Khánh Thương mại` | `Doanh nghiệp tư nhân An Khánh Thương mại` | ratio 75.0 |  | tên công ty NFC vs NFD |
| text | `Công ty TNHH Đầu tư Dịch vụ` | `Công ty TNHH Đầu tư Dịch vụ` | ratio 73.33 |  | tên công ty NFC vs NFD |
| text | `Công ty TNHH MTV Hoàng Gia Biển Xanh` | `Công ty TNHH MTV Hoàng Gia Biển Xanh` | ratio 86.84 |  | tên công ty NFC vs NFD |
| text | `Công ty Cổ phần Đại Dương Thương mại` | `Công ty Cổ phần Đại Dương Thương mại` | ratio 65.06 |  | tên công ty NFC vs NFD |
| text | `Công ty TNHH Hoàng Gia Thuận Phát` | `CÔNG TY TNHH HOÀNG GIA THUẬN PHÁT` | ratio 45.45 |  | tên công ty viết HOA |
| text | `Công ty TNHH MTV Tân Hòa Kỹ thuật` | `Công ty TNHH MTV Tân Hòa Kỹ thuật` | ratio 77.78 |  | tên công ty NFC vs NFD |
| text | `Doanh nghiệp tư nhân An Khánh Tân Hòa` | `Doanh nghiệp tư nhân An Khánh Tân Hòa` | ratio 76.54 |  | tên công ty NFC vs NFD |
| text | `Công ty Cổ phần Hoàng Gia Xây dựng` | `CÔNG TY CỔ PHẦN HOÀNG GIA XÂY DỰNG` | ratio 35.29 |  | tên công ty viết HOA |
| text | `Doanh nghiệp tư nhân Biển Xanh Phúc Thịnh` | `Doanh nghiệp tư nhân Biển Xanh Phúc Thịnh` | ratio 77.78 |  | tên công ty NFC vs NFD |
| text | `Công ty TNHH Đại Dương Phúc Thịnh` | `Công ty TNHH Đại Dương Phúc Thịnh` | ratio 75.0 |  | tên công ty NFC vs NFD |
| money | `46000000000đ` | `46,000,000,000 đồng` | ratio 77.42 |  | cùng số tiền, khác định dạng/đơn vị VND |
| money | `22,000,000,000 VNĐ` | `22.000.000.000,00 đ` | ratio 64.86 |  | cùng số tiền, có phần thập phân ,00 |
| money | `85,619,000 đồng` | `85.619.000` | ratio 64.0 |  | cùng số tiền, khác định dạng/đơn vị VND |
| money | `44000000000đ` | `44.000.000.000,00 đ` | ratio 77.42 |  | cùng số tiền, có phần thập phân ,00 |
| money | `2900000000 đồng` | `2900 triệu` | ratio 40.0 |  | số tiền viết bằng chữ tỷ/triệu |
| money | `40.362.000 đ` | `40,362,000` | ratio 72.73 |  | cùng số tiền, khác định dạng/đơn vị VND |
| money | `₫292000000` | `292 triệu` | ratio 31.58 |  | số tiền viết bằng chữ tỷ/triệu |
| money | `74,000,000đ` | `74.000.000,00 đ` | ratio 69.23 |  | cùng số tiền, có phần thập phân ,00 |
| money | `26,000,000,000 VND` | `26 tỷ` | ratio 26.09 |  | số tiền viết bằng chữ tỷ/triệu |
| money | `76,043,000 VNĐ` | `76.043.000 đồng` | ratio 62.07 |  | cùng số tiền, khác định dạng/đơn vị VND |
| money | `45.000.000.000 đ` | `45,000,000,000 đồng` | ratio 74.29 |  | cùng số tiền, khác định dạng/đơn vị VND |
| money | `28,000,000,000 đồng` | `28.000.000.000,00 đ` | ratio 68.42 |  | cùng số tiền, có phần thập phân ,00 |
| money | `39157000 VND` | `39.157.000` | ratio 72.73 |  | cùng số tiền, khác định dạng/đơn vị VND |
| money | `33,000,000,000 VNĐ` | `33.000.000.000,00 đ` | ratio 64.86 |  | cùng số tiền, có phần thập phân ,00 |
| money | `7,000,000,000 VNĐ` | `7.000.000.000,00 đ` | ratio 62.86 |  | cùng số tiền, có phần thập phân ,00 |
| money | `8.500.000.000 VND` | `8500 triệu` | ratio 37.04 |  | số tiền viết bằng chữ tỷ/triệu |
| money | `800000000` | `800.000.000 đồng` | ratio 72.0 |  | cùng số tiền, khác định dạng/đơn vị VND |
| money | `26.240.000đ` | `26.240.000,00 đ` | ratio 84.62 |  | cùng số tiền, có phần thập phân ,00 |
| money | `41,000,000,000 VND` | `41.000.000.000,00 đ` | ratio 64.86 |  | cùng số tiền, có phần thập phân ,00 |
| money | `8200000000` | `8,200,000,000đ` | ratio 83.33 |  | cùng số tiền, khác định dạng/đơn vị VND |
| money | `8.200.000.000 VNĐ` | `8.200.000.000đ` | ratio 83.87 |  | cùng số tiền, khác định dạng/đơn vị VND |
| money | `1,400,000,000 đồng` | `1.400.000.000,00 đ` | ratio 66.67 |  | cùng số tiền, có phần thập phân ,00 |
| money | `416000000 đ` | `416.000.000,00 đ` | ratio 81.48 |  | cùng số tiền, có phần thập phân ,00 |
| money | `7,000,000,000` | `7 tỷ` | ratio 11.76 |  | số tiền viết bằng chữ tỷ/triệu |
| money | `16,772,000` | `16772000` | ratio 88.89 |  | cùng số tiền, khác định dạng/đơn vị VND |
| money | `60.501.000 VNĐ` | `60.501.000,00 đ` | ratio 75.86 |  | cùng số tiền, có phần thập phân ,00 |
| money | `28094000 đồng` | `28,094,000 VNĐ` | ratio 66.67 |  | cùng số tiền, khác định dạng/đơn vị VND |
| money | `12.000.000` | `12,000,000 đ` | ratio 72.73 |  | cùng số tiền, khác định dạng/đơn vị VND |
| money | `7.600.000.000 VNĐ` | `7.600.000.000,00 đ` | ratio 80.0 |  | cùng số tiền, có phần thập phân ,00 |
| money | `5.000.000.000 đ` | `5000000000` | ratio 80.0 |  | cùng số tiền, khác định dạng/đơn vị VND |
| money | `61,022,000` | `61.022.000,00 đ` | ratio 64.0 |  | cùng số tiền, có phần thập phân ,00 |
| money | `34000000000` | `34.000.000.000 VNĐ` | ratio 75.86 |  | cùng số tiền, khác định dạng/đơn vị VND |
| money | `5.800.000.000 đ` | `5800 triệu` | ratio 40.0 |  | số tiền viết bằng chữ tỷ/triệu |
| money | `503.000.000 VND` | `503.000.000,00 đ` | ratio 77.42 |  | cùng số tiền, có phần thập phân ,00 |
| money | `56,335,000 đồng` | `56,335,000` | ratio 80.0 |  | cùng số tiền, khác định dạng/đơn vị VND |
| money | `₫9900000000` | `9.900.000.000 đồng` | ratio 68.97 |  | cùng số tiền, khác định dạng/đơn vị VND |
| money | `6,500,000,000 đ` | `6.500.000.000 đ` | ratio 80.0 |  | cùng số tiền, khác định dạng/đơn vị VND |
| money | `3.000.000.000` | `3.000.000.000,00 đ` | ratio 83.87 |  | cùng số tiền, có phần thập phân ,00 |
| money | `8.300.000.000 VND` | `8.300.000.000,00 đ` | ratio 80.0 |  | cùng số tiền, có phần thập phân ,00 |
| money | `6.500.000.000 VND` | `6500000000 đồng` | ratio 68.75 |  | cùng số tiền, khác định dạng/đơn vị VND |
| date | `04-04-2022` | `ngày 04 tháng 04 năm 2022` | ratio 45.71 |  | ngày viết bằng chữ |
| date | `20/2/2021` | `20.02.2021` | ratio 73.68 |  | cùng ngày, khác định dạng |
| date | `22/10/2024` | `22-10-2024` | ratio 80.0 |  | cùng ngày, khác định dạng |
| date | `14/02/2024` | `ngày 14 tháng 02 năm 2024` | ratio 45.71 |  | ngày viết bằng chữ |
| date | `11-09-2022` | `11/9/2022` | ratio 73.68 |  | cùng ngày, khác định dạng |
| date | `2023-05-01` | `ngày 01 tháng 05 năm 2023` | ratio 22.86 |  | ngày viết bằng chữ |
| date | `04-07-2022` | `ngày 04 tháng 07 năm 2022` | ratio 45.71 |  | ngày viết bằng chữ |
| date | `13/9/2026` | `13-09-2026` | ratio 73.68 |  | cùng ngày, khác định dạng |
| date | `07-08-2022` | `07.08.2022` | ratio 80.0 |  | cùng ngày, khác định dạng |
| date | `27/8/2021` | `ngày 27 tháng 08 năm 2021` | ratio 41.18 |  | ngày viết bằng chữ |
| date | `2024-10-31` | `ngày 31 tháng 10 năm 2024` | ratio 22.86 |  | ngày viết bằng chữ |
| date | `01/09/2024` | `ngày 01 tháng 09 năm 2024` | ratio 45.71 |  | ngày viết bằng chữ |
| date | `26.04.2026` | `2026-04-26` | ratio 60.0 |  | cùng ngày, khác định dạng |
| date | `15.09.2021` | `15/9/2021` | ratio 73.68 |  | cùng ngày, khác định dạng |
| date | `13/4/2025` | `ngày 13 tháng 04 năm 2025` | ratio 41.18 |  | ngày viết bằng chữ |
| date | `2021-06-10` | `ngày 10 tháng 06 năm 2021` | ratio 22.86 |  | ngày viết bằng chữ |
| date | `20/10/2024` | `ngày 20 tháng 10 năm 2024` | ratio 45.71 |  | ngày viết bằng chữ |
| date | `21-01-2021` | `ngày 21 tháng 01 năm 2021` | ratio 45.71 |  | ngày viết bằng chữ |
| date | `21/3/2023` | `ngày 21 tháng 03 năm 2023` | ratio 41.18 |  | ngày viết bằng chữ |
| date | `30-12-2024` | `2024-12-30` | ratio 60.0 |  | cùng ngày, khác định dạng |
| date | `27.07.2023` | `ngày 27 tháng 07 năm 2023` | ratio 45.71 |  | ngày viết bằng chữ |
| date | `08-04-2021` | `2021-04-08` | ratio 60.0 |  | cùng ngày, khác định dạng |
| date | `29-06-2024` | `29.06.2024` | ratio 80.0 |  | cùng ngày, khác định dạng |
| date | `13-03-2025` | `13/03/2025` | ratio 80.0 |  | cùng ngày, khác định dạng |
| date | `18.04.2024` | `ngày 18 tháng 04 năm 2024` | ratio 45.71 |  | ngày viết bằng chữ |
| date | `15.04.2026` | `2026-04-15` | ratio 40.0 |  | cùng ngày, khác định dạng |
| date | `23-08-2022` | `23/08/2022` | ratio 80.0 |  | cùng ngày, khác định dạng |
| date | `23/11/2020` | `2020-11-23` | ratio 40.0 |  | cùng ngày, khác định dạng |
| date | `2025-05-03` | `3/5/2025` | ratio 44.44 |  | cùng ngày, khác định dạng |
| date | `17/10/2024` | `17-10-2024` | ratio 80.0 |  | cùng ngày, khác định dạng |
| date | `21/04/2021` | `ngày 21 tháng 04 năm 2021` | ratio 45.71 |  | ngày viết bằng chữ |
| date | `24/07/2021` | `24.07.2021` | ratio 80.0 |  | cùng ngày, khác định dạng |
| name | `Đỗ Quốc Toàn` | `ĐỖ QUỐC TOÀN` | ratio 41.67 |  | tên viết HOA |
| name | `Hoàng Hữu Dũng` | `  Hoàng Hữu  Dũng ` | ratio 87.5 |  | tên thừa khoảng trắng |
| name | `Lê Đức Hòa` | `LÊ ĐỨC HÒA` | ratio 50.0 |  | tên viết HOA |
| name | `Khúc Văn Khánh` | `  Khúc Văn Khánh  ` | ratio 87.5 |  | tên thừa khoảng trắng |
| name | `Vũ Hữu Dũng` | `  Vũ  Hữu Dũng ` | ratio 84.62 |  | tên thừa khoảng trắng |
| name | `Đỗ Thị Nhung` | `Đỗ Thị Nhung` | ratio 74.07 |  | tên NFC vs NFD |
| name | `Bùi Văn Khánh` | `  Bùi Văn  Khánh ` | ratio 86.67 |  | tên thừa khoảng trắng |
| name | `Vũ Thu An` | `  Vũ Thu  An ` | ratio 81.82 |  | tên thừa khoảng trắng |
| name | `Khúc Văn Hùng` | `Khúc Văn Hùng` | ratio 68.97 |  | tên NFC vs NFD |
| name | `Đỗ Hữu Tuấn` | `Đỗ Hữu Tuấn` | ratio 57.14 |  | tên NFC vs NFD |
| name | `Đặng Thị Phương` | `Đặng Thị Phương` | ratio 62.86 |  | tên NFC vs NFD |
| name | `Trần Minh Lan` | `TRẦN MINH LAN` | ratio 38.46 |  | tên viết HOA |
| name | `Nguyễn Ngọc Bình` | `Nguyễn Ngọc Bình` | ratio 72.22 |  | tên NFC vs NFD |
| name | `Vũ Văn Yến` | `VŨ VĂN YẾN` | ratio 50.0 |  | tên viết HOA |
| name | `Đặng Minh Lan` | `  Đặng Minh  Lan ` | ratio 86.67 |  | tên thừa khoảng trắng |
| name | `Hoàng Văn Nhung` | `Hoàng Văn Nhung` | ratio 81.25 |  | tên NFC vs NFD |
| name | `Đặng Ngọc Lan` | `Đặng Ngọc Lan` | ratio 75.86 |  | tên NFC vs NFD |
| name | `Trần Thị Hòa` | `TRẦN THỊ HÒA` | ratio 41.67 |  | tên viết HOA |
| name | `Nguyễn Thanh Thụy` | `  Nguyễn Thanh Thụy  ` | ratio 89.47 |  | tên thừa khoảng trắng |
| name | `Nguyễn Văn Hoè` | `NGUYỄN VĂN HOÈ` | ratio 35.71 |  | tên viết HOA |
| name | `Đỗ Văn Thủy` | `  Đỗ  Văn Thủy ` | ratio 84.62 |  | tên thừa khoảng trắng |
| name | `Đỗ Thanh Hòa` | `ĐỖ THANH HÒA` | ratio 41.67 |  | tên viết HOA |
| name | `Đỗ Quốc Hòa` | `Đỗ Quốc Hòa` | ratio 59.26 |  | tên NFC vs NFD |
| name | `Hoàng Minh Khánh` | `Hoàng Minh Khánh` | ratio 82.35 |  | tên NFC vs NFD |
| name | `Đỗ Văn Bình` | `  Đỗ  Văn Bình ` | ratio 84.62 |  | tên thừa khoảng trắng |
| name | `Bùi Quốc Dũng` | `BÙI QUỐC DŨNG` | ratio 38.46 |  | tên viết HOA |
| name | `Ngô Văn Hòa` | `Ngô Văn Hoà` | ratio 81.82 |  | tên dấu thanh kiểu cũ (oà/uỷ) |
| name | `Lê Thị Lan` | `LÊ THỊ LAN` | ratio 50.0 |  | tên viết HOA |
| name | `Đặng Quốc Dũng` | `ĐẶNG QUỐC DŨNG` | ratio 35.71 |  | tên viết HOA |
| name | `Đặng Ngọc Lan` | `  Đặng Ngọc  Lan ` | ratio 86.67 |  | tên thừa khoảng trắng |
| name | `Bùi Văn Nhung` | `  Bùi  Văn Nhung ` | ratio 86.67 |  | tên thừa khoảng trắng |
| name | `Đỗ Đức Hòa` | `ĐỖ ĐỨC HÒA` | ratio 50.0 |  | tên viết HOA |
| name | `Phạm Văn An` | `  Phạm Văn An  ` | ratio 84.62 |  | tên thừa khoảng trắng |
| name | `Ngô Minh Hòa` | `NGÔ MINH HÒA` | ratio 41.67 |  | tên viết HOA |
| name | `Đặng Minh Bình` | `Đặng Minh Bình` | ratio 77.42 |  | tên NFC vs NFD |

## Kiểm tra độ nhạy: baseline có được chuẩn hoá thì sao?

Cùng hai thước đo chuỗi nhưng chạy trên `normalize()` của vi-textmatch (NFC + vị trí dấu thanh + khoảng trắng + casefold), **không** có logic theo kiểu. Mục đích: tách xem chênh lệch đến từ chuẩn hoá hay từ việc hiểu kiểu dữ liệu.

| matcher | accuracy | false-equal ⚠ | false-diff | ERR |
|---|---|---|---|---|
| `difflib+normalize` | 68.0% | **94** | 95 | 0 |
| `rapidfuzz+normalize` | 68.0% | **94** | 95 | 0 |

## Nhận định (số liệu lấy từ lần chạy này)

1. **Lỗi nguy hiểm tập trung ở baseline.** `vi_textmatch` có 58 false-equal; difflib 92, rapidfuzz 92. Baseline coi hai số tiền/ngày/định danh khác nhau là "gần đúng" đúng ở chỗ SPEC cấm dùng ratio: money 6, date 11, id 24, text 39.
2. **False-equal của `vi_textmatch` theo kiểu:** money 0, date 0, id 0, name 0, text 58. Ở text, ngưỡng TYPO 0.85 gộp hai chuỗi gần giống nhưng khác nghĩa (địa chỉ khác số nhà, công ty khác loại hình) — TEXT không phải kiểu an toàn cho địa chỉ/pháp nhân.
3. **Ngưỡng 0.9 là con dao sắc.** 18/590 cặp có ratio difflib đúng bằng 0.90 (±0.005): `Nguyễn Thị Hòa` vs `Nguyễn  Thị   Hòa` → BẰNG, `100.000.000` vs `100000000` → BẰNG, `15/07/2026` vs `15/7/2026 ` → BẰNG. Cặp khác nhau thật nằm ngay trên ngưỡng thì không nâng ngưỡng được, chỉ đổi cặp nào sai.
4. **False-diff của `vi_textmatch`** = 24 cặp, phân theo kiểu: money 6, date 15, id 0, name 3, text 0. False-diff ở name là cố ý: tên lệch 1 chữ do gõ/OCR bị đẩy về KHÁC để người soát lại, thay vì đoán là cùng người.
5. **ERR (23 cặp)** rơi vào input không ép được kiểu / ngày không tồn tại; 2/23 trong số đó là cặp vốn khác nhau, nên fail-closed không gây hại — điểm money/date có một phần công của việc ném lỗi thay vì đoán.
6. **Chuẩn hoá không phải nguồn gốc của an toàn.** Cho difflib dùng `normalize()` của thư viện: accuracy 52.9% → 68.0%, false-equal 92 → 94. Giá trị nằm ở type-aware, không phải ở NFC.
7. **difflib và rapidfuzz** lệch dự đoán ở 0/590 cặp — trên chuỗi ngắn, hai thuật toán khác nhau cho kết quả gần như trùng. rapidfuzz nhanh hơn, không an toàn hơn cho bài toán này.

## Giới hạn

- 100 cặp viết tay + 490 cặp sinh tự động (`gen_extended.py`, seed cố định, nhãn theo phép biến đổi); vẫn là dữ liệu bịa, do một người đặt nhãn; nhãn text phụ thuộc quan điểm "hai tên lệch 1 dấu có phải cùng người không". Cách chốt ở đây là **chặt**: phải soát lại.
- Mọi chuỗi đều bịa; không có PII, không suy ra hành vi trên dữ liệu thật.
- Chưa đo tốc độ và chưa đo trường hợp chuỗi rất dài (difflib có `autojunk`).

## Chạy lại

```bash
python3 bench/gen_extended.py  # sinh lại bench/pairs.jsonl từ pairs_core.jsonl (tất định)
python3 bench/run_bench.py    # ghi bench/RESULTS.md + bench/results.jsonl
```

Nếu `rapidfuzz` chưa có (Python hệ thống trên macOS bị PEP 668 chặn `pip`):

```bash
python3.11 -m venv .venv && .venv/bin/pip install rapidfuzz
.venv/bin/python bench/run_bench.py
```

`rapidfuzz` chỉ là dependency **của benchmark**; thư viện vẫn zero-dependency.
