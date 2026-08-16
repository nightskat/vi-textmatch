# Quy tắc đặt dấu thanh — bản lập trình được

Nguồn: xem `NGUON.md`. Đây là bản dịch từ quy tắc ngôn ngữ học sang điều kiện code hoá được
cho `tone.py`. Không đưa số liệu/model/giá vào file này (theo luật `~/.claude/rules/routing-summary.md`).

## 1. Khung lý thuyết — cấu trúc âm tiết tiếng Việt

Một âm tiết tiếng Việt đầy đủ có 5 thành phần (nguồn: icanreadvietnamese.com, Wikipedia):

```
Âm đầu (phụ âm đầu) — Âm đệm (o/u, có thể vắng) — Âm chính (bắt buộc, không bao giờ vắng)
— Âm cuối (phụ âm hoặc bán nguyên âm cuối, có thể vắng) — Thanh điệu (bắt buộc, phủ toàn âm tiết)
```

**Luật tối thượng:** dấu thanh LUÔN đặt trên (hoặc dưới) chữ cái biểu diễn ÂM CHÍNH. Âm đệm
(o/u đứng đầu vần) KHÔNG BAO GIỜ mang dấu thanh. Đây là điểm mọi nguồn đồng thuận — kể cả phía
"kiểu cũ" cũng không đặt dấu lên âm đệm khi âm tiết có âm cuối (xem mục 3).

**Âm tiết MỞ** = không có âm cuối (vần kết thúc ngay ở âm chính, hoặc âm chính + bán nguyên âm
cuối i/u/y khi bán nguyên âm đó tạo thành một cụm 2 chữ cái không tách được — trường hợp `oa/oe/uy`
xử lý ở mục 3 CHỈ tính là "mở" khi không có gì theo sau cụm 2 chữ đó trong cùng âm tiết).
**Âm tiết ĐÓNG** = có âm cuối là phụ âm (p, t, c, ch, m, n, ng, nh) hoặc bán nguyên âm cuối
thêm (i, o, u, y) sau âm chính.

## 2. Vai trò của `qu` và `gi`

- `qu` là TỔ HỢP PHỤ ÂM ĐẦU (đọc /kw/), KHÔNG PHẢI phụ âm `q` + âm đệm `u`. Phần vần bắt đầu
  SAU chữ `u`. Do đó trong `quý`, `quỳ`, `quán`, `quả` — nguyên âm đầu tiên của VẦN là `y`/`y`/`á`/`ả`,
  không có âm đệm riêng để tranh chấp dấu. → **không có ambiguity, không có "kiểu cũ/kiểu mới" cho
  `qu` + nguyên âm.** Chỉ có MỘT dạng đúng, dấu luôn ở nguyên âm sau `u`.
  - Đúng: `quý`, `quỳnh`, `quả`, `quốc`. Sai: `qúy`, `qùynh`, `qủa`, `qúôc` (dấu lạc lên `u`).
- `gi` tương tự: phần vần bắt đầu SAU chữ `i` (trừ trường hợp `gì`, `gịa` nơi một `i` bị lược
  theo quy ước chính tả vì `gi` + vần bắt đầu bằng `i` sẽ trùng chữ). Không liên quan trực tiếp
  đến `oa/oe/uy` (không tìm thấy ví dụ `gi` + oa/oe/uy thực tế trong tiếng Việt).

## 3. Vùng THỰC SỰ có tranh chấp: `oa`, `oe`, `uy` — CHỈ KHI ÂM TIẾT MỞ

Đây là nguồn gốc chính xác của bug: `oà→òa` v.v. chỉ đúng khi `oa/oe/uy` là 2 CHỮ CÁI CUỐI CÙNG
của âm tiết (không có gì theo sau). Khi có âm cuối theo sau (âm tiết đóng), CHỈ CÓ MỘT dạng đúng
— dấu luôn ở chữ cái thứ hai (nguyên âm chính) — và **không được đụng vào**, dù dạng đó "trông giống"
kiểu cũ hay kiểu mới.

### 3a. Âm tiết ĐÓNG (`oa/oe/uy` + phụ âm cuối hoặc bán nguyên âm cuối) — LUẬT CỐ ĐỊNH, KHÔNG NORMALIZE

| Cụm | Vị trí dấu bắt buộc | Ví dụ ĐÚNG | Ví dụ SAI (bug hiện tại tạo ra) |
|---|---|---|---|
| `oa` + cuối | chữ cái thứ 2 (`a`) | `hoàn`, `khoản`, `ngoạn`, `xoạc` | `hòan`, `khỏan`, `ngòan`, `xòac` |
| `oe` + cuối | chữ cái thứ 2 (`e`) — hiếm, đa phần `oe` là mở | (không có ví dụ phổ biến — `oe` gần như luôn mở trong từ vựng thực tế; giữ luật đối xứng cho an toàn) | — |
| `uy` + cuối | chữ cái thứ 2 (`y`) | `suýt`, `huỳnh`, `quỳnh` (qua `qu`, xem mục 2), `khuỷu`, `nguyễn`→ không áp dụng (đây là `uyê`, xem 3c) | `súyt`, `hùynh`, `khủyu` |

**Điều kiện code hoá:** áp dụng transform CHỈ KHI ký tự ngay sau cụm 2-chữ `oa/oe/uy` (trong cùng
token/âm tiết) là **ranh giới từ** (khoảng trắng, dấu câu, hết chuỗi) — KHÔNG PHẢI một chữ cái
tiếng Việt khác. Nếu có bất kỳ chữ cái nào theo sau (kể cả nguyên âm, như trong `khuỷu` nơi `uỷ`
theo sau bởi `u`) → GIỮ NGUYÊN, không transform.

```python
# Điều kiện lookahead cần thêm (giả mã):
# match "oà" CHỈ KHI theo sau là non-letter hoặc hết chuỗi
r"oà(?=[^A-Za-zÀ-ỹ]|$)"
```
(`[^A-Za-zÀ-ỹ]` là xấp xỉ thô cho "không phải chữ cái Latin/Việt" — cần review kỹ range Unicode
thật khi implement, đừng copy thẳng vào code mà không kiểm tra biên.)

### 3b. Âm tiết MỞ (`oa/oe/uy` là 2 chữ cuối cùng) — ĐÂY LÀ CHỖ CÓ 2 KIỂU CẠNH TRANH

| Cụm | Kiểu "dấu ở chữ cái 1" (o/u) | Kiểu "dấu ở chữ cái 2" (a/e/y) | Ví dụ |
|---|---|---|---|
| `oa` | `hòa, tòa, xòa` | `hoà, toà, xoà` | `hòa` ↔ `hoà` |
| `oe` | `khỏe, lòe, xòe` | `khoẻ, loè, xoè` | `khỏe` ↔ `khoẻ` |
| `uy` (không sau `qu`) | `thúy, lũy, ủy` | `thuý, luỹ, uỷ` | `thúy` ↔ `thuý` |

⚠️ **Nhãn "cũ"/"mới" KHÔNG THỐNG NHẤT giữa các nguồn** — xem mục 4. `tone.py` KHÔNG cần chọn lại
nhãn đúng-sai; SPEC.md v0.1 đã tự chọn chuẩn hoá về MỘT dạng nhất quán, không quan trọng chọn dạng
nào miễn nhất quán và có ghi chú. Cái BẮT BUỘC phải sửa là: chỉ áp dụng khi mở (mục 3a), không phải
hướng chuyển đổi.

### 3c. Trường hợp KHÔNG thuộc bug này — nguyên âm có dấu phụ sẵn (ă, â, ê, ô, ơ, ư)

Khi vần chứa một nguyên âm có sẵn dấu phụ (trăng/mũ: ă, â, ê, ô, ơ, ư), dấu THANH luôn đè lên
nguyên âm đó, không tranh chấp gì cả — vì đây là quy tắc ưu tiên số 1 trong mọi nguồn tìm được.
Ví dụ: `cuối, Huế, thuở, luận, xoắn, thuế, quế` — chỉ có MỘT cách viết đúng, không cần map bảng.
**Không đưa các cụm này vào `TONE_MAP_OLD_TO_NEW`** — chúng không có ambiguity, thêm vào chỉ tạo
rủi ro sai không cần thiết.

## 4. Ghi chú KHÔNG chắc chắn — đọc trước khi code

1. **Nhãn "kiểu cũ" vs "kiểu mới" bị đảo ngược giữa các nguồn.** Một nguồn (search snippet tổng hợp
   từ Wikipedia + thảo luận) nói `hòa` = kiểu CŨ (dấu ở âm đệm, quy ước thẩm mỹ tiền-1980), `hoà` =
   kiểu MỚI (dấu ở âm chính theo ngữ âm học, do QĐ 240/1984 đề xuất). Docstring hiện tại trong
   `tone.py:5-6` viết NGƯỢC LẠI (`hoà` = cũ, `hòa` = mới). Thực tế đời sống: `hòa` (dấu ở âm đệm)
   mới là dạng THƯỜNG GẶP trong văn bản hiện hành/báo chí/OCR hôm nay, dù theo nhãn ngôn ngữ học
   1984 nó bị gọi là "cũ". → Khuyến nghị: **bỏ nhãn "cũ/mới" khỏi code và comment**, chỉ mô tả
   bằng vị trí ("dấu ở âm đệm" / "dấu ở âm chính") để tránh gây hiểu nhầm ngược.
2. Không xác nhận được quy định 2018 (SGK mới) có áp dụng luật khác cho riêng `oa/oe/uy` hay không
   — bài tìm được (HoaTieu, ZNews) chỉ nói rõ về cặp `ia/ua/ưa` ↔ `iê/yê/uô/ươ`, đây là bộ nguyên
   âm KHÁC hoàn toàn, đừng nhầm lẫn hai quy tắc.
3. Chưa kiểm chứng được `oe` có ví dụ âm tiết ĐÓNG thực tế phổ biến nào trong tiếng Việt hay không
   — nếu không có, luật 3a cho `oe` mang tính lý thuyết/phòng thủ, không có test case thật để đối chiếu.
4. Danh sách âm tiết hợp lệ để làm oracle kiểm thử: CHƯA có nguồn tải-được, có-giấy-phép nào đầy đủ
   (xem mục "Chưa tìm được nguồn tin cậy" trong `NGUON.md`). Gợi ý thực dụng: dùng
   `vietnamese-wordlist` (Viet74K.txt, GPL-2.0), lọc ra các token 1 âm tiết (không chứa khoảng
   trắng), làm tập kiểm thử "output normalize phải nằm trong tập này" — đây là tập THỰC TẾ dùng
   được chứ không phải tập LÝ THUYẾT đầy đủ, nên false negative (âm tiết đúng nhưng hiếm, không có
   trong wordlist) vẫn có thể xảy ra khi dùng làm assert cứng.

## 5. Tóm tắt sửa `tone.py`

Bug gốc: transform `oà→òa` (và tương tự cho oe/uy) áp dụng bằng khớp CHUỖI CON mù, không kiểm tra
gì theo sau. Cách sửa tối thiểu: thêm lookahead "theo sau là ranh giới từ, không phải chữ cái" vào
mọi pattern trong `_OA_OE_PATTERNS` và `_UY_TONE_PATTERNS` (mục 3a). Lookbehind chặn `qu` hiện có
cho `uy` là ĐÚNG, giữ nguyên (mục 2). Không cần thêm luật cho `ă/â/ê/ô/ơ/ư` (mục 3c) — chúng vốn
không nằm trong bảng map và không nên thêm vào.
