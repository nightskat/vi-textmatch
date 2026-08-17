# ĐỀ BÀI — CLI cho vi-textmatch

Repo: `~/Developer/active/vi-textmatch` (MIT, công khai, đã lên PyPI 0.1.0).
Thư viện so khớp văn bản tiếng Việt **theo kiểu dữ liệu**. Đọc `README.md`, `SPEC.md`, `src/vi_textmatch/` trước khi viết dòng nào.

## Ràng buộc CỨNG — vi phạm là bỏ bài

1. 🔴 **CHỈ dùng thư viện chuẩn Python.** Không `click`, không `typer`, không `rich`. Dùng `argparse`. Lý do sống còn: thư viện này phải chạy được **trong trình duyệt qua Pyodide**; thêm một dependency là mất tính năng đó.
2. 🔴 **Không sửa** `src/vi_textmatch/{normalize,tone,compare}.py`. Chỉ THÊM file mới. 35 test hiện có phải xanh nguyên.
3. Python **3.11+**. Có type hint đầy đủ.
4. Tiếng Việt trong output phải in đúng trên terminal macOS (UTF-8).

## Cần dựng

### File `src/vi_textmatch/cli.py` + entry point trong `pyproject.toml`
```toml
[project.scripts]
vi-textmatch = "vi_textmatch.cli:main"
```

### Ba lệnh con

```
vi-textmatch compare <A> <B> --kind {text,id,money,date} [--json]
vi-textmatch normalize <TEXT> [--json]
vi-textmatch closest <NEEDLE> <CANDIDATE>... [--kind ...] [--top N] [--json]
```

- `--kind` **bắt buộc** với `compare` (thư viện cố tình không có mặc định — so sai kiểu là lỗi nguy hiểm nhất, đừng đoán hộ người dùng).
- Đọc được từ **stdin**: `-` thay cho một tham số nghĩa là đọc stdin.

### Định dạng ra — người đọc (mặc định)
```
$ vi-textmatch compare "suýt" "súyt" --kind text
KHÁC  (DIFFERENT)
Tỉ lệ khớp: 0.5000
```
```
$ vi-textmatch compare "Nguyễn Thị Huệ" "Nguyễn Thị Huệ" --kind text
TRÙNG  (IDENTICAL)
Giống nhau sau khi chuẩn hoá
```
- Ngắn, không màu, không khung, không emoji. Dòng đầu là **phán quyết**.

### Định dạng ra — máy đọc (`--json`)
Một dòng JSON, không thụt lề:
```json
{"match":false,"level":"DIFFERENT","detail":"Match ratio: 0.5000","kind":"text","a":"suýt","b":"súyt"}
```

### Mã thoát (quan trọng — script sẽ dựa vào)
| Mã | Nghĩa |
|---|---|
| `0` | khớp (`match=True`) |
| `1` | không khớp |
| `2` | lỗi dùng sai: thiếu `--kind`, kind lạ, không parse được tiền/ngày |

Lỗi phải ra **stderr**, không ra stdout — để `--json` pipe được sạch.

### Test
Thêm `tests/test_cli.py`, tối thiểu 12 test, dùng `subprocess` hoặc gọi `main([...])` trực tiếp. **Bắt buộc phủ:** cả 3 lệnh · cả 4 kind · `--json` · stdin · cả 3 mã thoát · tiếng Việt có dấu · chuỗi rỗng.

## Cấm
- Cấm thêm dependency. Cấm sửa 3 file lõi. Cấm đổi API công khai hiện có.
- Cấm dùng dữ liệu thật của người dùng — **bịa 100%** (ở đây không có PII, cứ dùng tên bịa).

## Định dạng trả lời
- Viết code vào repo. Chạy `~/.pyenv/versions/3.11.8/bin/python -m pytest tests/ -q` cho tới khi **xanh hết**.
- Rồi ghi tóm tắt ≤40 dòng tiếng Việt vào `BAO-CAO-CLI.md`: đã thêm file nào, lệnh chạy thử thật + output thật, chỗ nào bạn phân vân.
- Không mở bài, không khen.
