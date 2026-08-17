# Báo cáo triển khai CLI cho vi-textmatch

## 1. File đã thêm và sửa
- **Thêm**: `src/vi_textmatch/cli.py` (`compare`, `normalize`, `closest`).
- **Thêm**: `tests/test_cli.py` (17 unit tests phủ 3 lệnh, 4 kind, `--json`, stdin, exit code 0/1/2, tiếng Việt, chuỗi rỗng).
- **Sửa**: `pyproject.toml` (thêm entrypoint `vi-textmatch = "vi_textmatch.cli:main"`).
- **Giữ nguyên**: `src/vi_textmatch/{normalize,tone,compare}.py` (35 test cũ xanh nguyên).

## 2. Kết quả chạy test
`~/.pyenv/versions/3.11.8/bin/python -m pytest tests/ -q` -> `52 passed in 0.13s`

## 3. Lệnh chạy thử thật và output thật
```bash
$ python -m vi_textmatch.cli compare "suýt" "súyt" --kind text
KHÁC  (DIFFERENT)
Tỉ lệ khớp: 0.5000

$ python -m vi_textmatch.cli compare "Nguyễn Thị Huệ" "Nguyễn Thị Huệ" --kind text
TRÙNG  (IDENTICAL)
Giống nhau sau khi chuẩn hoá

$ python -m vi_textmatch.cli compare "suýt" "súyt" --kind text --json
{"match": false, "level": "DIFFERENT", "detail": "Match ratio: 0.5000", "kind": "text", "a": "suýt", "b": "súyt"}

$ python -m vi_textmatch.cli normalize "Nguyễn Thị  Hoà "
nguyễn thị hòa

$ python -m vi_textmatch.cli closest "Hoà" "Hòa" "Hoa" "Bình" --top 2
Hòa
Hoa

$ echo "suýt" | python -m vi_textmatch.cli compare - "súyt" --kind text --json
{"match": false, "level": "DIFFERENT", "detail": "Match ratio: 0.5000", "kind": "text", "a": "suýt", "b": "súyt"}
```

## 4. Chỗ phân vân
- **Detail human vs json**: Human dịch `detail` tiếng Anh sang tiếng Việt (`Match ratio:` -> `Tỉ lệ khớp:`), còn `--json` giữ nguyên `verdict.detail` gốc.
- **Stdin (`-`)**: Hỗ trợ đọc cả stream đơn hoặc từng dòng nếu truyền nhiều tham số `-`.
