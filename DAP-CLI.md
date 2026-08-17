# DAP-CLI
HỎNG 5 CHỖ

`cd ~/Developer/active/vi-textmatch` · `PY=~/.pyenv/versions/3.11.8/bin/python` · `export PYTHONPATH=src`

| # | Mức | Hỏng | Hậu quả người lạ |
|---|-----|------|------------------|
| 1 | 🔴 | `closest --kind` parse rồi nuốt | Tiền/ngày trùng → `[]`, exit 0 |
| 2 | 🔴 | Hai `-` + stdin 1 dòng → so với `""` | CLI bảo KHÁC (exit 1) |
| 3 | 🟠 | Chuỗi dẫn `-` bị coi là cờ | ID/text hợp lệ → exit 2 |
| 4 | 🟠 | `--top 0`/`-1` nổ traceback | exit 1 (spec=2), `--json` vỡ |
| 5 | 🟡 | `closest` rỗng vẫn exit 0 | Spec: 0=khớp · 1=không |

52 test xanh. `test_cli.py` không đụng 5 ca này.

### 1. 🔴 `closest --kind` ≠ thư viện
`cli.py:191` gọi `closest(needle, cands, n=top)` — bỏ `args.kind`.
```
$ $PY -m vi_textmatch.cli closest "2,5" "2.50" "zzz" --kind money --json; echo $?
{"needle": "2,5", "matches": []}
0
$ $PY -c 'from vi_textmatch.compare import compare,Kind; print(compare("2,5","2.50",kind=Kind.MONEY))'
Verdict(match=True, level='IDENTICAL', detail='Monetary values match exactly')
$ $PY -m vi_textmatch.cli closest "01/02/2026" "2026-02-01" "foo" --kind date; echo $?
(stdout rỗng)  0
$ $PY -c 'from vi_textmatch.compare import compare,Kind; print(compare("01/02/2026","2026-02-01",kind=Kind.DATE))'
Verdict(match=True, level='IDENTICAL', ...)
```
`--kind foobar` mới exit 2. Cờ sống, nghiệp vụ chết.

### 2. 🔴 Hai `-`, một dòng stdin → giả "không khớp"
```
$ printf '031234567890\n' | $PY -m vi_textmatch.cli compare - - --kind id --json; echo $?
{"match": false, "level": "DIFFERENT", "detail": "ID values do not match", "kind": "id", "a": "031234567890", "b": ""}
1
$ printf 'Nguyễn Văn A\n' | $PY -m vi_textmatch.cli compare - - --kind text --json; echo $?
{"match": false, ..., "a": "Nguyễn Văn A", "b": ""}  1
```
Thiếu dòng ≠ exit 2. `echo "$id" | vi-textmatch compare - - --kind id` từ chối ID đúng.

### 3. 🟠 Chuỗi dẫn `-` bị argparse nuốt
```
$ $PY -m vi_textmatch.cli compare --kind id --secret1 --secret1; echo $?
error: the following arguments are required: a, b    2
$ $PY -c 'from vi_textmatch.compare import compare,Kind; print(compare("--secret1","--secret1",kind=Kind.ID))'
Verdict(match=True, level='IDENTICAL', ...)
$ $PY -m vi_textmatch.cli compare --kind text -foo bar; echo $?
error: the following arguments are required: b    2
```
`--` cứu được (`compare --kind id --json -- --secret1 --secret1` → match=true $?=0).

### 4. 🟠 `--top<=0` nổ, mã thoát sai
```
$ $PY -m vi_textmatch.cli closest "Hoà" "Hòa" --top 0; echo $?
ValueError: n must be > 0: 0    1
$ $PY -m vi_textmatch.cli closest Hoa Hoa --top 0 --json 2>/dev/null | python3 -m json.tool; echo $pipestatus
Expecting value: line 1 column 1 (char 0)    1 1
```
Stdout 0 byte (đúng luồng). Sai: traceback + exit 1, không phải stderr gọn + exit 2.

### 5. 🟡 `closest` không khớp vẫn 0
```
$ $PY -m vi_textmatch.cli closest zzzz aaaa bbbb --json; echo $?
{"needle": "zzzz", "matches": []}    0
```

### Đã soát — không hỏng
| Hạng | Kết quả |
|------|---------|
| Dep ngoài stdlib | Không. `cli.py` = argparse/json/sys/typing + nội bộ. `dependencies=[]` |
| 3 file lõi + API | `git diff` trống. `__all__` cũ. 35 test cũ xanh |
| compare ↔ thư viện | `1.500.000`/`1,500,000`/`1500000đ` $?=0 · `01/02/2026`=`2026-02-01` $?=0 · ID lệch 1 ký tự $?=1 |
| Exit compare dùng sai | thiếu `--kind`/kind lạ/tiền-ngày hỏng/thiếu-thừa arg/`31/02`/`17/08/26` → **2** |
| `--json` luồng | lỗi: stdout 0 byte · khớp `0 0` · không khớp `1 0` |
| Ác ý khác | rỗng/space/tab/NL/NBSP/ZWSP/emoji/NFD/100k: không crash; NFD `Hoà` $?=0 |
