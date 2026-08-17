# BÁO CÁO — CI + py.typed

## File đã tạo / sửa
- `src/vi_textmatch/py.typed` — rỗng (0 byte), đánh dấu PEP 561.
- `pyproject.toml` — thêm `[tool.setuptools.package-data]` → `vi_textmatch = ["py.typed"]`.
- `.github/workflows/test.yml` — push/PR vào `main`; ma trận 3.11/3.12/3.13 trên ubuntu-latest; chỉ `pip install pytest` rồi `pytest tests/ -q`.
- `README.md` — thêm badge Actions ở đầu.

## Chứng minh py.typed nằm trong wheel
Lệnh: `~/.pyenv/versions/3.11.8/bin/python -m pip wheel . --no-deps -w /tmp/vi-wheelbuild`
Output: `Successfully built vi-textmatch`
Liệt kê wheel mới (trích `python -m zipfile -l`):
`vi_textmatch/py.typed   0` ← CÓ trong wheel.
(Wheel cũ trong `dist/` không có dòng này — đúng lỗ hổng cần vá.)

## Test
`~/.pyenv/versions/3.11.8/bin/python -m pytest tests/test_compare.py tests/test_normalize.py -q`
→ `35 passed in 0.02s`

## Điều đáng ngờ
1. Có task CLI chạy song song trong repo (`DE-BAI-CLI.md`): đang thêm `cli.py`, `test_cli.py`, `[project.scripts]`. Lúc viết báo cáo, `pytest tests/ -q` lỗi collection vì `tests/test_cli.py:10` import `vi_textmatch.cli` mà thiếu `sys.path.insert(0, …/src)` như 2 file test cũ → CI sẽ đỏ tới khi task CLI xử lý xong. Tôi không sửa file của task kia.
2. `.ds-ci.err`, `.ds-ci.out` không nằm trong `.gitignore` (khác `.agy*`/`.grok*`/`.codex*`/`.dsh-*`) → làm bẩn `git status`.
3. `python3` mặc định là 3.14.7 (pyenv shim); `__pycache__` có `.cpython-314.pyc` → đã có người chạy bằng 3.14, ngoài ma trận 3.11–3.13.
4. README mục Development ghi `python3 -m unittest discover tests` nhưng lệnh đó đếm 36 test và lỗi 1 (do test_cli); CI lại dùng pytest — nên thống nhất một cách chạy.
