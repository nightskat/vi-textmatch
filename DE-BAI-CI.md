# ĐỀ BÀI — CI + py.typed cho vi-textmatch

Repo: `~/Developer/active/vi-textmatch` — thư viện Python thuần stdlib, MIT, đã lên PyPI 0.1.0.
Remote: `github.com/nightskat/vi-textmatch` (công khai).

## Việc 1 — `py.typed`
Tạo `src/vi_textmatch/py.typed` (**file rỗng**) và khai báo trong `pyproject.toml` để nó được đóng gói vào wheel.
Lý do: thư viện có type hint đầy đủ nhưng thiếu file đánh dấu này thì **mọi IDE và mypy của người dùng bỏ qua sạch** (PEP 561).
Kiểm chứng: build lại rồi liệt kê nội dung wheel, chứng minh `py.typed` **có trong đó**.

## Việc 2 — GitHub Actions
Tạo `.github/workflows/test.yml`:
- Kích hoạt: `push` và `pull_request` vào nhánh mặc định.
- Ma trận: Python **3.11, 3.12, 3.13**, chạy trên `ubuntu-latest`.
- Bước: checkout → cài Python → cài `pytest` → chạy `pytest tests/ -q`.
- **Không** cài dependency nào khác — thư viện thuần stdlib, và CI phải chứng minh điều đó. Nếu phải cài thêm gì để test chạy được thì đó là **phát hiện đáng báo cáo**, đừng lặng lẽ thêm vào.
- Thêm badge trạng thái vào đầu `README.md`.

## Ràng buộc
- 🔴 **Không sửa** `src/vi_textmatch/{normalize,tone,compare}.py` và không đổi API công khai.
- 🔴 **Không thêm dependency runtime.** Thư viện phải chạy được trong trình duyệt qua Pyodide — thêm một gói là mất tính năng đó.
- Không `git push`, không tạo tag, không publish. Chỉ tạo file, để lại cho người khác duyệt.
- 35 test hiện có phải xanh nguyên: `~/.pyenv/versions/3.11.8/bin/python -m pytest tests/ -q`.

## Trả lời
Ghi ≤30 dòng tiếng Việt vào `BAO-CAO-CI.md`: file đã tạo, **lệnh đã chạy + output thật** chứng minh `py.typed` nằm trong wheel, và bất cứ điều gì bạn thấy đáng ngờ trong repo.
Không mở bài, không khen, không tổng kết lại đề bài.
