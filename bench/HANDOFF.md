# Bench vi-textmatch — bàn giao (cập nhật 03/11/2026)
- **Dữ liệu:** `pairs_core.jsonl` (100 cặp viết tay, nhãn kind đã chỉnh ở commit Kind.NAME) +
  `gen_extended.py` (seed 20261103) → `pairs.jsonl`. `gen_pairs.py` là bản gốc 100 cặp, giữ để tham khảo
  (không còn sinh `pairs.jsonl`).
- **Số liệu:** xem `RESULTS.md` (sinh tự động) — không chép số vào đây để khỏi lệch.
- **CI gate:** `run_bench.py --check` so false-equal với `baseline.json` theo TỪNG CẶP. Sửa được FE → chạy
  `--update-baseline` và commit. Thêm FE mới là fail.
- **Chạy lại:** `pip install -r bench/requirements.txt` rồi `python bench/gen_extended.py && python bench/run_bench.py`.
  Thiếu rapidfuzz thì script **thoát mã 2** (không tự bỏ cột).
- **Đừng:** dùng dữ liệu thật; sửa nhãn cho khớp thư viện.
