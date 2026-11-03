# vi-textmatch

So khớp chuỗi tiếng Việt **theo kiểu dữ liệu**. Không phụ thuộc thư viện ngoài (chỉ stdlib).

Dùng cho soát hồ sơ: kiểm tra hợp đồng soạn ra có khớp dữ liệu gốc không — nơi "gần đúng"
chấp nhận được với một câu văn, nhưng là **sai nghiêm trọng** với số tiền hay số định danh.

## Cài đặt

```bash
pip install vi-textmatch
```

Python 3.11+.

## Bắt đầu nhanh

```python
from vi_textmatch import normalize, compare, Kind

normalize("Nguyễn Thị  Hoà ")          # 'nguyễn thị hòa'

compare("Nguyễn Thị Hòa", "nguyễn thị hoà", kind=Kind.NAME).match      # True
compare("Nguyễn Văn An", "Nguyễn Văn Ân", kind=Kind.NAME).match        # False — người khác
compare("2.500.000.000", "2,500,000,000", kind=Kind.MONEY).match       # True
compare("100$", "100€", kind=Kind.MONEY).match                         # False
compare("0312.345.678", "0312345678", kind=Kind.ID).match              # True
compare("02/01/2026", "2026-01-02", kind=Kind.DATE, day_first=True).match  # True
```

`kind` là bắt buộc, không có mặc định: `compare(a, b)` ném `TypeError` thay vì lặng lẽ so mờ.

## Dòng lệnh

```bash
vi-textmatch normalize "Nguyễn Thị Hoà"
vi-textmatch compare "0312.345.678" "0312345678" --kind id
```

Xem [các Kind](kinds.md) và [số liệu so sánh](benchmark.md).
