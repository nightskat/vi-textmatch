# Các Kind

| `Kind` | Cách so | Lệch 1 ký tự nghĩa là |
|---|---|---|
| `TEXT` | `normalize()` rồi tỉ lệ `difflib` | có thể là lỗi gõ — chấm mức `IDENTICAL`/`TYPO`/`DIFFERENT` |
| `NAME` | `normalize()` rồi so **từng thành phần** chính xác (giữ dấu) | **người khác** |
| `ID` | bỏ khoảng trắng, `.`, `-`, `–`, `—` (không bỏ `_`), so **bằng tuyệt đối** | **định danh khác** |
| `MONEY` | ép về `Decimal` + loại tiền | **số tiền khác** |
| `DATE` | ép về `date` | **ngày khác** |

## TEXT

Ngưỡng: ratio = 1.0 → `IDENTICAL`; ≥ 0.85 → `TYPO` (`match=True`); thấp hơn → `DIFFERENT`.

!!! warning "TEXT không an toàn cho địa chỉ / tên pháp nhân"
    Bench cho thấy `TEXT` coi `Số 228 …` và `Số 229 …` (khác số nhà), hay `Công ty TNHH Hòa Lợi Thuận Phát`
    và `Công ty Cổ phần Hòa Lợi Thuận Phát` là `TYPO` → `match=True`. Với các trường này nên tách phần số/loại
    hình ra so bằng `ID`, hoặc coi `TYPO` là "phải soát lại".

## NAME

Chỉ bỏ qua NFC/NFD, vị trí dấu thanh (`hoà`/`hòa`), khoảng trắng, hoa/thường. Mọi khác biệt
khác ở bất kỳ thành phần nào đều là `DIFFERENT`, kể cả lỗi gõ (`Sơnn`) — cố ý để người soát lại.

## ID

`0312.345.678 == 0312345678`; `031234567890 != 031234567891`. Không bỏ nhãn như `MST`.

## MONEY

- Định dạng VN `2.500.000,50`, US `2,500,000.50`, số trơn `2500000`.
- `đ`, `₫`, `VND`, `VNĐ`, `đồng` là cùng một loại tiền; hai loại tiền **khác nhau tường minh**
  (`$` vs `€`) là `DIFFERENT`; không có ký hiệu = chỉ so giá trị.
- Không hiểu chữ (`2900 triệu`, `1,5 tỷ`) → **ném `ValueError`** (fail-closed), không đoán.

## DATE

- `DD/MM/YYYY`, `D/M/YYYY`, `YYYY-MM-DD`, phân cách `/ - . khoảng trắng`; năm phải 4 chữ số.
- Ngày mơ hồ (`02/01/2026`) → `match=False, level="AMBIGUOUS"` trừ khi truyền `day_first`.
- Ngày viết bằng chữ (`ngày 04 tháng 04 năm 2022`) chưa hỗ trợ → `ValueError`.
