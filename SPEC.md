# vi-textmatch — SPEC v0.1

Thư viện Python: **chuẩn hoá văn bản tiếng Việt** và **so khớp theo kiểu dữ liệu**, dùng để đối chiếu
tài liệu (hồ sơ, hợp đồng, biểu mẫu). Thuần stdlib, không phụ thuộc ngoài. Không dính PII, không gọi mạng.

## Bài toán
So một văn bản đã soạn với dữ liệu gốc: "khớp hay không, và nếu lệch thì lệch kiểu gì".
Hai chuỗi nhìn giống hệt nhau vẫn có thể khác nhau ở tầng byte; và với một số trường,
"gần giống" là kết luận SAI NGUY HIỂM chứ không phải kết luận yếu.

## Phần 1 — `normalize`: thang chuẩn hoá, ĐÚNG THỨ TỰ

| # | Bước | Vì sao bắt buộc |
|---|---|---|
| 1 | `unicodedata.normalize("NFC", s)` | macOS lưu **NFD**: `à` = `a` + U+0300. Nhìn giống, byte khác, hash khác |
| 2 | **Chuẩn vị trí dấu thanh** | `hoà` (h+o+à) vs `hòa` (h+ò+a) là hai chuỗi khác nhau THẬT. NFC không gộp. Cần bảng ánh xạ kiểu-gõ-cũ → kiểu-mới |
| 3 | Khoảng trắng: bỏ U+00A0 (nbsp), U+200B, gộp trắng liên tiếp, trim | Word/Excel chèn nbsp vô hình |
| 4 | `casefold()` | `VĂN A` → `văn a`. Dùng casefold, KHÔNG dùng lower() |

`normalize(s)` chạy cả 4 bước. Mỗi bước cũng phải là hàm gọi riêng được, để test từng tầng.

### Bảng bước 2 (dấu thanh đặt ở đâu)
Nguyên âm đôi/ba, kiểu cũ đặt dấu ở nguyên âm đầu, kiểu mới ở nguyên âm chính:
`oà↔òa · oá↔óa · oả↔ỏa · oã↔õa · oạ↔ọa · oè↔òe · oé↔óe · oẻ↔ỏe · oẽ↔õe · oẹ↔ọe ·
uỳ↔ùy · uý↔úy · uỷ↔ủy · uỹ↔ũy · uỵ↔ụy`
Chuẩn hoá về **một** dạng nhất quán (chọn dạng nào cũng được, miễn ghi rõ và không đổi).
⚠️ Không được áp mù: `hoà`→`hòa` đúng, nhưng phải kiểm không phá các từ mà `o`/`u` là phụ âm đệm khác.

## Phần 2 — `compare`: phép so do KIỂU DỮ LIỆU quyết định

```
compare(a, b, kind=...) -> Verdict(match: bool, level: str, detail: str)
```

| `kind` | Cách so | Ý nghĩa khi lệch |
|---|---|---|
| `TEXT` (tên người, địa chỉ, diễn giải) | `normalize` rồi `difflib.SequenceMatcher.ratio()` | phân mức, xem dưới |
| `ID` (CCCD, STK, số HĐ, MST, mã KH) | bỏ khoảng trắng/gạch nối rồi **so BẰNG tuyệt đối** | **SAI NGƯỜI / SAI HỒ SƠ** |
| `MONEY` | ép `Decimal`, so **giá trị** | **SAI SỐ LIỆU** |
| `DATE` | ép `date`, so **giá trị** | **SAI NGÀY** |

🔴 **Cấm dùng ratio cho `ID` và `MONEY`.** `031234567890` vs `...891` ra ~0.92 nhưng là hai người,
cả hai đều hợp lệ. `2.500.000.000` vs `2.600.000.000` cũng ~0.9 — lệch 100 triệu.
Đây là lỗi im lặng: chạy trơn, không báo gì, và nói "gần đúng" ở đúng chỗ không được phép gần đúng.

Với `MONEY`/`DATE`, hàm phải **ném lỗi rõ ràng nếu không ép kiểu được** — không được âm thầm rơi về so chuỗi.

### Phân mức cho `TEXT`
| ratio | level | Nghĩa |
|---|---|---|
| 1.0 | `IDENTICAL` | chỉ khác kiểu gõ / đã chuẩn hoá xong |
| 0.85–0.99 | `TYPO` | nghi lỗi gõ hoặc OCR đọc nhầm |
| < 0.85 | `DIFFERENT` | nhiều khả năng nhầm người → dừng, soát lại |

Ngưỡng để ở hằng số đặt tên, sửa được, không rải số trong code.

## Phần 3 — tiện ích
- `explain(a, b)` → dùng `difflib.ndiff`, trả về đúng ký tự thừa/thiếu.
- `closest(s, candidates, n=3)` → `difflib.get_close_matches` trên bản đã normalize.

## Ràng buộc
- **Chỉ thư viện chuẩn Python** (`unicodedata`, `difflib`, `decimal`, `datetime`, `re`, `unittest`).
- Python 3.11+. Không gọi mạng, không đọc file ngoài, không phụ thuộc bên thứ ba.
- Type hints đầy đủ. Docstring tiếng Anh (thư viện công khai), README song ngữ sau.
- Không log nội dung chuỗi đầu vào ở bất kỳ đâu.

## Nghiệm thu — thiếu là chưa xong
Test bằng `unittest`, dữ liệu **hoàn toàn bịa**:
1. NFD vs NFC cùng một tên → `IDENTICAL`
2. `hoà` vs `hòa` → `IDENTICAL`
3. `Nguyễn Thị Hòa` vs `nguyễn thị hòa` → `IDENTICAL`
4. Tên có nbsp/trắng đôi → `IDENTICAL`
5. `Nguyễn Thị Hòa` vs `Nguyễn Thị Hoa` → `TYPO`
6. `Nguyễn Thị Hòa` vs `Trần Văn Bình` → `DIFFERENT`
7. `ID`: `0312 3456 7890` vs `031234567890` → **match** (chỉ khác khoảng trắng)
8. `ID`: `031234567890` vs `031234567891` → **KHÔNG match** (dù ratio cao)
9. `MONEY`: `2.500.000.000` vs `2,500,000,000` vs `2500000000` → match
10. `MONEY`: `2.500.000.000` vs `2.600.000.000` → **KHÔNG match**
11. `DATE`: `12/08/2026` vs `12-8-2026` → match
12. `MONEY` với chuỗi không ép được kiểu → **ném lỗi**, không âm thầm so chuỗi
