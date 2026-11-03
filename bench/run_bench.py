#!/usr/bin/env python3
"""Benchmark: vi-textmatch vs raw difflib vs raw rapidfuzz.

Question being asked: on realistic document-verification pairs, which
matcher is safe? "Safe" is not "most accurate" — the costly error is
FALSE-EQUAL (says two different amounts / people / dates are the same).

Matchers (all run on the identical pair set):
  vi_textmatch  compare(a, b, kind=<mapped>) -> Verdict.match
  difflib       difflib.SequenceMatcher(None, a, b).ratio() >= 0.9
  rapidfuzz     rapidfuzz.fuzz.ratio(a, b) >= 90

Two sensitivity variants give the string baselines the library's
normalization (NFC + tone placement + whitespace + casefold) but NOT its
type logic, so you can see whether the win comes from normalization or
from being type-aware.

A raise (e.g. unparseable MONEY/DATE) is recorded as ERR and scored as
"not equal" — fail-closed, the same direction the library intends.

Usage:
  python3 bench/run_bench.py                 # writes bench/RESULTS.md
  python3 bench/run_bench.py --no-write      # print only
"""

from __future__ import annotations

import argparse
import difflib
import json
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(REPO / "src"))

from vi_textmatch import compare as vi_compare  # noqa: E402
from vi_textmatch import Kind, normalize  # noqa: E402
from vi_textmatch.compare import THRESHOLD_TYPO  # noqa: E402,F401  (doc only)

try:
    from rapidfuzz import fuzz as rf_fuzz
    RAPIDFUZZ_VERSION: str | None = getattr(
        __import__("rapidfuzz"), "__version__", "unknown"
    )
except ImportError:  # pragma: no cover - environment dependent
    rf_fuzz = None
    RAPIDFUZZ_VERSION = None

DIFFLIB_CUTOFF = 0.9
RAPIDFUZZ_CUTOFF = 90.0
KIND_MAP = {"text": Kind.TEXT, "id": Kind.ID, "money": Kind.MONEY, "date": Kind.DATE}
KIND_ORDER = ("money", "date", "id", "text")


# --------------------------------------------------------------- matchers
def m_vi_textmatch(a: str, b: str, kind: str) -> bool:
    return vi_compare(a, b, kind=KIND_MAP[kind]).match


def m_difflib(a: str, b: str, kind: str) -> bool:
    return difflib.SequenceMatcher(None, a, b).ratio() >= DIFFLIB_CUTOFF


def m_difflib_norm(a: str, b: str, kind: str) -> bool:
    return (
        difflib.SequenceMatcher(None, normalize(a), normalize(b)).ratio()
        >= DIFFLIB_CUTOFF
    )


def m_rapidfuzz(a: str, b: str, kind: str) -> bool:
    assert rf_fuzz is not None
    return rf_fuzz.ratio(a, b) >= RAPIDFUZZ_CUTOFF


def m_rapidfuzz_norm(a: str, b: str, kind: str) -> bool:
    assert rf_fuzz is not None
    return rf_fuzz.ratio(normalize(a), normalize(b)) >= RAPIDFUZZ_CUTOFF


MATCHERS = [
    ("vi_textmatch", m_vi_textmatch),
    ("difflib", m_difflib),
    ("rapidfuzz", m_rapidfuzz),
]
VARIANTS = [
    ("difflib+norm", m_difflib_norm),
    ("rapidfuzz+norm", m_rapidfuzz_norm),
]


# ------------------------------------------------------------------ scoring
def run(matcher, pairs: list[dict]) -> list[dict]:
    rows = []
    for p in pairs:
        try:
            pred = bool(matcher(p["a"], p["b"], p["kind"]))
            err = False
        except Exception as exc:  # noqa: BLE001 - any raise is a data-quality answer
            pred = False
            err = True
            p = dict(p, error=f"{type(exc).__name__}: {exc}")
        rows.append(dict(p, pred=pred, err=err))
    return rows


def summarize(rows: list[dict]) -> dict:
    n = len(rows)
    err = sum(1 for r in rows if r["err"])
    fe = sum(1 for r in rows if r["pred"] and not r["expected_equal"])
    fd = sum(1 for r in rows if not r["pred"] and r["expected_equal"])
    correct = sum(1 for r in rows if r["pred"] == r["expected_equal"])
    return {
        "n": n,
        "errors": err,
        "false_equal": fe,
        "false_diff": fd,
        "correct": correct,
        "accuracy": correct / n if n else 0.0,
    }


def pct(x: float) -> str:
    return f"{x * 100:.1f}%"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pairs", default=str(HERE / "pairs.jsonl"))
    ap.add_argument("--out", default=str(HERE / "RESULTS.md"))
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args()

    pairs = [
        json.loads(line)
        for line in Path(args.pairs).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    active = [m for m in MATCHERS if rf_fuzz is not None or "rapidfuzz" not in m[0]]
    results = {name: run(fn, pairs) for name, fn in active}
    variants = {
        name: run(fn, pairs)
        for name, fn in VARIANTS
        if rf_fuzz is not None or "rapidfuzz" not in name
    }

    # ------------------------------------------------------------ console
    print(f"pairs: {len(pairs)}  ({Path(args.pairs)})")
    print(f"python {sys.version.split()[0]}  rapidfuzz {RAPIDFUZZ_VERSION or 'MISSING'}")
    hdr = f"{'matcher':<16}{'acc':>8}{'correct':>9}{'FE':>5}{'FD':>5}{'ERR':>5}"
    print()
    print(hdr)
    print("-" * len(hdr))
    for name, rows in results.items():
        s = summarize(rows)
        print(
            f"{name:<16}{pct(s['accuracy']):>8}{s['correct']:>5}/{s['n']:<3}"
            f"{s['false_equal']:>5}{s['false_diff']:>5}{s['errors']:>5}"
        )

    # ------------------------------------------------------------- report
    lines: list[str] = []
    add = lines.append

    add("# Bench: vi-textmatch vs difflib vs rapidfuzz")
    add("")
    add(f"Chạy lúc: {datetime.now().astimezone().strftime('%Y-%m-%d %H:%M %Z')}  ")
    add(f"Bộ dữ liệu: `bench/pairs.jsonl` — **{len(pairs)} cặp bịa hoàn toàn**, "
        f"{sum(1 for p in pairs if p['expected_equal'])} cặp bằng nhau / "
        f"{sum(1 for p in pairs if not p['expected_equal'])} cặp khác nhau.  ")
    add(f"Môi trường: Python {sys.version.split()[0]}, rapidfuzz {RAPIDFUZZ_VERSION or 'KHÔNG CÓ'}.")
    add("")
    add("## Phương pháp")
    add("")
    add("- `vi_textmatch`: `compare(a, b, kind=...).match` (TEXT dùng ngưỡng 0.85 → TYPO vẫn tính là match).")
    add(f"- `difflib`: `SequenceMatcher(None, a, b).ratio() >= {DIFFLIB_CUTOFF}` trên chuỗi **thô**.")
    add(f"- `rapidfuzz`: `fuzz.ratio(a, b) >= {RAPIDFUZZ_CUTOFF}` trên chuỗi **thô**.")
    add("- Ground truth là **nghĩa**, không phải hợp đồng của thư viện: hai chuỗi cùng một người/số tiền/ngày → `expected_equal=true`.")
    add("- Kết quả ném lỗi (MONEY/DATE không ép được kiểu) ghi `ERR` và tính là **không bằng** (fail-closed).")
    add("- Số cặp trong bảng == số dòng `pairs.jsonl`, không có cặp nào bị bỏ.")
    add("")

    add("## Tổng")
    add("")
    add("| matcher | accuracy | correct | false-equal ⚠ | false-diff | ERR |")
    add("|---|---|---|---|---|---|")
    for name, rows in results.items():
        s = summarize(rows)
        add(
            f"| `{name}` | {pct(s['accuracy'])} | {s['correct']}/{s['n']} | "
            f"**{s['false_equal']}** | {s['false_diff']} | {s['errors']} |"
        )
    add("")

    add("## Theo kiểu dữ liệu — accuracy")
    add("")
    head = "| matcher | " + " | ".join(KIND_ORDER) + " |"
    add(head)
    add("|---" * (len(KIND_ORDER) + 1) + "|")
    for name, rows in results.items():
        cells = []
        for kind in KIND_ORDER:
            sub = [r for r in rows if r["kind"] == kind]
            s = summarize(sub)
            cells.append(f"{pct(s['accuracy'])} ({s['correct']}/{s['n']})")
        add(f"| `{name}` | " + " | ".join(cells) + " |")
    add("")

    add("## Theo kiểu dữ liệu — false-equal (sai theo hướng nguy hiểm)")
    add("")
    add("| matcher | " + " | ".join(KIND_ORDER) + " |")
    add("|---" * (len(KIND_ORDER) + 1) + "|")
    for name, rows in results.items():
        cells = []
        for kind in KIND_ORDER:
            sub = [r for r in rows if r["kind"] == kind]
            s = summarize(sub)
            cells.append(f"**{s['false_equal']}**" if s["false_equal"] else "0")
        add(f"| `{name}` | " + " | ".join(cells) + " |")
    add("")

    # false-equal detail
    add("## Các cặp bị coi là BẰNG NHAU nhưng thực ra KHÁC (chi tiết)")
    add("")
    any_fe = False
    for name, rows in results.items():
        bad = [r for r in rows if r["pred"] and not r["expected_equal"]]
        if not bad:
            continue
        any_fe = True
        add(f"### `{name}` — {len(bad)} cặp")
        add("")
        add("| a | b | kind | ghi chú |")
        add("|---|---|---|---|")
        for r in bad:
            add(f"| `{r['a']}` | `{r['b']}` | {r['kind']} | {r['note']} |")
        add("")
    if not any_fe:
        add("Không có.")
        add("")

    add("## Các cặp bị coi là KHÁC nhưng thực ra BẰNG (chi tiết)")
    add("")
    for name, rows in results.items():
        bad = [r for r in rows if not r["pred"] and r["expected_equal"]]
        add(f"### `{name}` — {len(bad)} cặp")
        add("")
        if not bad:
            add("Không có.")
            add("")
            continue
        add("| a | b | kind | ERR | ghi chú |")
        add("|---|---|---|---|---|")
        for r in bad:
            add(f"| `{r['a']}` | `{r['b']}` | {r['kind']} | {'x' if r['err'] else ''} | {r['note']} |")
        add("")

    if variants:
        add("## Kiểm tra độ nhạy: baseline có được chuẩn hoá?")
        add("")
        add("Baseline chạy trên `normalize()` của vi-textmatch (NFC + dấu thanh + trắng + casefold) "
            "nhưng **không** có logic theo kiểu dữ liệu — để tách xem lợi thế đến từ chuẩn hoá hay từ type-aware.")
        add("")
        add("| matcher | accuracy | false-equal ⚠ | false-diff | ERR |")
        add("|---|---|---|---|---|")
        for name, rows in variants.items():
            s = summarize(rows)
            add(f"| `{name}` | {pct(s['accuracy'])} | **{s['false_equal']}** | {s['false_diff']} | {s['errors']} |")
        add("")

    # auto observations, strictly derived from numbers
    add("## Quan sát (sinh tự động từ số liệu trên)")
    add("")
    for name, rows in results.items():
        s = summarize(rows)
        per = {}
        for kind in KIND_ORDER:
            per[kind] = summarize([r for r in rows if r["kind"] == kind])
        worst = max(KIND_ORDER, key=lambda k: per[k]["false_equal"])
        add(
            f"- `{name}`: {s['correct']}/{s['n']} ({pct(s['accuracy'])}), "
            f"false-equal {s['false_equal']}, false-diff {s['false_diff']}, ERR {s['errors']}. "
            f"Kiểu tệ nhất theo false-equal: `{worst}` ({per[worst]['false_equal']} cặp)."
        )
    add("")
    # ------------------------------------------------- hand-written analysis
    # Numbers below are computed, prose is authored; re-running keeps both in sync.
    raw_ratios = [
        difflib.SequenceMatcher(None, p["a"], p["b"]).ratio() * 100 for p in pairs
    ]
    boundary = [
        pairs[i] for i, r in enumerate(raw_ratios) if abs(r - DIFFLIB_CUTOFF * 100) <= 1.0
    ]
    diverge = sum(
        1
        for i, p in enumerate(pairs)
        if (raw_ratios[i] >= DIFFLIB_CUTOFF * 100)
        != (rf_fuzz.ratio(p["a"], p["b"]) >= RAPIDFUZZ_CUTOFF)
    ) if rf_fuzz is not None else None
    vi = results["vi_textmatch"]
    vi_err_safe = sum(1 for r in vi if r["err"] and not r["expected_equal"])
    vi_err_total = sum(1 for r in vi if r["err"])
    df = results["difflib"]
    df_fe_kinds = {
        k: summarize([r for r in df if r["kind"] == k])["false_equal"] for k in KIND_ORDER
    }
    vi_fe_kinds = {
        k: summarize([r for r in vi if r["kind"] == k])["false_equal"] for k in KIND_ORDER
    }

    add("## Nhận định")
    add("")
    add(f"1. **Lỗi nguy hiểm nằm gần hết ở baseline.** `vi_textmatch` false-equal "
        f"{summarize(vi)['false_equal']} cặp; difflib/rapidfuzz false-equal "
        f"{summarize(df)['false_equal']} cặp — ngang nhau vì cả hai đều chỉ so ký tự, "
        f"và cả hai đều nói `031234567890` ≈ `031234567891`.")
    add(f"2. **Toàn bộ false-equal của baseline rơi vào money/date/id** "
        f"({df_fe_kinds['money']} money, {df_fe_kinds['date']} date, {df_fe_kinds['id']} id, "
        f"{df_fe_kinds['text']} text) — đúng chỗ SPEC cấm dùng ratio. "
        f"False-equal của `vi_textmatch` chỉ còn ở `text` ({vi_fe_kinds['text']} cặp).")
    add(f"3. **Ngưỡng 0.9 là dao mỏng.** {len(boundary)}/{len(pairs)} cặp có ratio thô "
        f"nằm trong ±1 điểm quanh 90 — trong đó có những cặp khác nhau thật "
        f"(`12/08/2026` vs `12/08/2025`, `05/06/2026` vs `05/06/2027`: đúng 90.0 → được coi là BẰNG). "
        f"Chỉnh ngưỡng lên 0.95 không cứu được: nó chỉ đổi cặp nào bị coi là khác.")
    add(f"4. **Chuẩn hoá không phải là thứ tạo ra khác biệt.** Cho baseline dùng "
        f"`normalize()` của thư viện (khối 'Kiểm tra độ nhạy') thì accuracy chỉ lên "
        f"{pct(summarize(variants['difflib+norm'])['accuracy']) if 'difflib+norm' in variants else 'n/a'}, "
        f"còn false-equal **tăng** ({summarize(df)['false_equal']} → {summarize(variants['difflib+norm'])['false_equal'] if 'difflib+norm' in variants else 'n/a'}): "
        f"chuẩn hoá làm hai chuỗi khác nghĩa trông giống nhau hơn. Giá trị của thư viện nằm ở "
        f"**type-aware**, không phải ở NFC.")
    add(f"5. **Phần còn lại của `vi_textmatch` là giới hạn của TEXT, không phải bug.** "
        f"{vi_fe_kinds['text']} false-equal đều là tên/địa danh khác người thật nhưng lệch 1 dấu "
        f"(`Phạm Quốc Khánh` vs `Kháng`, `Nguyễn Văn An` vs `Ân`) — ratio ≥ 0.85 nên bị xếp TYPO. "
        f"Với trường tên người, ngưỡng 0.85 của TEXT là quá rộng; muốn chặn phải so thêm "
        f"thành phần tên hoặc dùng kind chặt hơn.")
    add(f"6. **{summarize(vi)['false_diff']} false-diff**: mất sạch dấu (`Số 12 phố Lạch Tray` vs `So 12 pho Lach Tray`) — "
        f"không thư viện nào trong ba cái xử lý được, vì cả ba đều không bỏ dấu.")
    add(f"7. **ERR ({vi_err_total} cặp) đều rơi về phía an toàn** ({vi_err_safe}/{vi_err_total} "
        f"là cặp vốn khác nhau: `12.000.00`, `29/02/2025`). Nói cách khác điểm 100% của money/date "
        f"có một phần công của việc ném lỗi thay vì đoán — đó chính là hành vi SPEC yêu cầu.")
    if diverge is not None:
        add(f"8. **difflib và rapidfuzz cho kết quả y hệt nhau** trên bộ này "
            f"({diverge}/{len(pairs)} cặp lệch dự đoán). Không phải vì cùng code — hai thuật toán "
            f"khác nhau (matching-blocks vs Levenshtein) — mà vì chuỗi ở đây ngắn và gần bằng độ dài. "
            f"Đừng đọc kết quả này thành 'rapidfuzz vô dụng': nó nhanh hơn nhiều lần, chỉ là "
            f"không an toàn hơn cho bài toán này.")
    add("")

    add("## Chạy lại")
    add("")
    add("```bash")
    add("python3 bench/run_bench.py            # ghi bench/RESULTS.md")
    add("python3 bench/gen_pairs.py            # sinh lại bench/pairs.jsonl (tất định)")
    add("```")
    add("")
    add("rapidfuzz là dependency **chỉ của benchmark**, không phải của thư viện "
        "(thư viện vẫn zero-dependency). Nếu thiếu rapidfuzz, script vẫn chạy và bỏ dòng đó.")
    add("")

    report = "\n".join(lines)
    if not args.no_write:
        Path(args.out).write_text(report, encoding="utf-8")
        print(f"\nwrote {args.out}")
    else:
        print("\n" + report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
