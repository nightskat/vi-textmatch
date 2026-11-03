# So sánh với difflib / rapidfuzz

Số liệu dưới đây **sinh tự động** bởi `bench/run_bench.py` trong CI ở mỗi lần build docs —
không gõ tay. Báo cáo đầy đủ từng cặp: [`bench/RESULTS.md`](https://github.com/nightskat/vi-textmatch/blob/main/bench/RESULTS.md).

--8<-- "bench-summary.md"

## Phương pháp

- Toàn bộ dữ liệu là **bịa**: 100 cặp viết tay + cặp sinh bằng `bench/gen_extended.py`
  (seed cố định) cho địa chỉ, tên công ty, số hợp đồng, số tiền nhiều định dạng, ngày, tên người.
- Nhãn gán **theo phép biến đổi** (giữ nghĩa hay đổi nghĩa), không chạy thư viện để gán.
  Có cả phép giữ nghĩa mà thư viện chưa xử lý (`P.`/`phường`, `2900 triệu`, ngày bằng chữ) —
  chúng hiện thành false-diff, không bị loại ra.
- `difflib`/`rapidfuzz`: ngưỡng 0.9 trên chuỗi thô; dòng `+normalize` chạy trên `normalize()`.
- **false-equal** (nói BẰNG nhưng thực ra KHÁC) là lỗi nguy hiểm; CI fail nếu `vi_textmatch`
  có false-equal **mới** so với `bench/baseline.json`.

## Hạn chế đã biết

`TEXT` vẫn false-equal ở địa chỉ/tên công ty gần giống nhau — xem [Các Kind](kinds.md#text).
