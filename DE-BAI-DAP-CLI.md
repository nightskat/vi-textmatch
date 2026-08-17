# ĐỀ BÀI — Đập CLI vi-textmatch

Repo: `~/Developer/active/vi-textmatch`. Vừa có người thêm `src/vi_textmatch/cli.py` + `tests/test_cli.py`.
Spec nó phải tuân: `DE-BAI-CLI.md`. Báo cáo của người viết: `BAO-CAO-CLI.md`.

Đây là **thư viện công khai trên PyPI** — lỗi ở đây người lạ gặp, không phải chỉ tác giả.

## Việc của bạn: chứng minh CLI này hỏng

**Test xanh KHÔNG phải bằng chứng.** Cùng repo này tuần trước có 19 rồi 28 test xanh trong khi thư viện biến `suýt` thành `súyt` — vì test hỏi "hai cách viết có khớp không" thay vì "khớp vào cái gì".

### 1. Mã thoát (ưu tiên cao nhất — script sẽ dựa vào)
Spec: `0` khớp · `1` không khớp · `2` dùng sai.
Thử: thiếu `--kind` · `--kind` lạ · tiền không parse được · ngày không parse được · thiếu tham số · thừa tham số · `--json` kèm lỗi.
Mỗi ca: lệnh thật + mã thoát thật (`echo $?`). Sai spec là lỗi.

### 2. stdout/stderr lẫn lộn
Spec: lỗi ra **stderr**, để `--json` pipe sạch.
Thử `cmd --json 2>/dev/null | python3 -m json.tool` ở **cả ca đúng lẫn ca lỗi**. Có gì rơi nhầm luồng không?

### 3. Đầu vào ác ý
Chuỗi rỗng · chỉ khoảng trắng · chuỗi bắt đầu bằng `-` (bị hiểu thành cờ?) · rất dài (100k ký tự) · xuống dòng bên trong · tab · NBSP · ký tự zero-width · emoji · tiếng Việt NFD (gõ trên Mac) · `--` phân cách · stdin rỗng · stdin nhiều dòng · `-` ở cả hai vị trí cùng lúc.

### 4. Đúng nghiệp vụ — quan trọng hơn cả crash
CLI phải cho **cùng kết quả** với việc gọi thư viện trực tiếp. Đối chiếu:
```python
from vi_textmatch import compare
from vi_textmatch.compare import Kind
```
Tìm ca mà CLI nói khác thư viện. Đặc biệt: `--kind money` với `1.500.000` vs `1,500,000` vs `1500000đ`; `--kind date` với `01/02/2026` vs `2026-02-01`; `--kind id` lệch một ký tự.

### 5. Ràng buộc cứng có bị phá không
- 🔴 Có thêm **dependency ngoài stdlib** không? (`grep -rn "^import\|^from" src/vi_textmatch/cli.py`, đối chiếu `pyproject.toml`). Thêm là **hỏng tính năng chạy trong trình duyệt** — lỗi nặng nhất.
- 3 file lõi `normalize.py`/`tone.py`/`compare.py` có bị sửa không? (`git diff --stat`)
- API công khai cũ có đổi không?
- 35 test cũ còn xanh không?

## Cấm
- Cấm sửa code. Bạn đập, không vá.
- Cấm nhận xét chung chung. Mỗi phát hiện = **lệnh chạy lại được + output thật + mã thoát thật**.
- Cấm dùng file thật trong `~/Work/`, `~/Claude/Projects/`, `~/Data/`, `~/Downloads/`.

## Định dạng
- Tiếng Việt, **tối đa 80 dòng**, bảng phẳng, có emoji.
- Dòng đầu: `HỎNG N CHỖ` / `KHÔNG TÌM RA CHỖ HỎNG`.
- Xếp theo **mức thiệt hại**, nặng nhất lên đầu.
- ⚠️ **Ghi `DAP-CLI.md` NGAY khi có phát hiện đầu tiên**, cập nhật dần. Lượt trước bạn hết lượt trước khi kịp ghi và mất sạch kết quả.
