# Bench vi-textmatch — bàn giao (03/11/2026)
- **Làm:** Hermes (opencode-go deepseek) dựng 102 cặp bịa + `run_bench.py`; Claude chạy lại nghiệm thu, khớp số.
- **Kết quả:** vi_textmatch 94,1% (FE 5, FD 1, ERR 2) · difflib 45,1% (FE 23) · rapidfuzz 45,1% (FE 23).
- **Finding:** FE còn lại toàn `text` = tên người lệch 1 dấu (Khánh/Kháng, An/Ân) → đề xuất kind `name` chặt hơn hoặc so thành phần tên. CHƯA SỬA.
- **Chạy lại:** `PYTHONPATH=src <python có rapidfuzz> bench/run_bench.py` (thiếu rapidfuzz thì script tự bỏ cột đó).
- **Đừng:** dùng dữ liệu thật trong pairs.jsonl; push trước khi Tuan duyệt.
