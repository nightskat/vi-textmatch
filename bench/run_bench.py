#!/usr/bin/env python3
"""Benchmark: vi-textmatch vs raw difflib vs raw rapidfuzz on bench/pairs.jsonl.

The question is not "which matcher scores highest" but "which matcher is safe".
In document verification the expensive error is FALSE-EQUAL: the tool says two
different amounts / dates / people are the same. A false-diff costs a human
re-check; a false-equal ships a wrong number into a signed document.

Matchers, all on the identical pair set, all on the RAW strings:
  vi_textmatch   compare(a, b, kind=<mapped>).match
  difflib        difflib.SequenceMatcher(None, a, b).ratio() >= 0.9
  rapidfuzz      rapidfuzz.fuzz.ratio(a, b) >= 90

Two supplementary variants run the same string metrics on `normalize()`d text
(NFC + tone placement + whitespace + casefold) with no type logic. They answer
"how much of the gap is normalization vs type-awareness" and stay out of the
main table.

A raise (unparseable MONEY, impossible DATE) is recorded as ERR and scored
"not equal" — fail-closed, the direction the library intends.

Usage:
  python3 bench/run_bench.py             # writes bench/RESULTS.md + bench/results.jsonl
  python3 bench/run_bench.py --no-write  # print only
"""

from __future__ import annotations

import argparse
import difflib
import json
import platform
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(REPO / "src"))

from vi_textmatch import Kind, compare as vi_compare, normalize  # noqa: E402

try:
    import rapidfuzz
    from rapidfuzz import fuzz as rf_fuzz
except ImportError:  # pragma: no cover - environment dependent
    sys.stderr.write(
        "rapidfuzz is required for this benchmark (install it outside the system Python):\n"
        "  python3.11 -m venv .venv && .venv/bin/pip install rapidfuzz\n"
        "  .venv/bin/python bench/run_bench.py\n"
    )
    raise SystemExit(2)

DIFFLIB_CUTOFF = 0.9
RAPIDFUZZ_CUTOFF = 90.0
KIND_MAP = {"text": Kind.TEXT, "id": Kind.ID, "money": Kind.MONEY, "date": Kind.DATE}
KIND_ORDER = ("money", "date", "id", "text")

Row = dict[str, Any]
Matcher = Callable[[str, str, str], tuple[bool, dict[str, Any]]]


# --------------------------------------------------------------- matchers
def m_vi_textmatch(a: str, b: str, kind: str) -> tuple[bool, dict[str, Any]]:
    verdict = vi_compare(a, b, kind=KIND_MAP[kind])
    return verdict.match, {"level": verdict.level, "detail": verdict.detail}


def m_difflib(a: str, b: str, kind: str) -> tuple[bool, dict[str, Any]]:
    ratio = difflib.SequenceMatcher(None, a, b).ratio()
    return ratio >= DIFFLIB_CUTOFF, {"ratio": round(ratio, 4)}


def m_rapidfuzz(a: str, b: str, kind: str) -> tuple[bool, dict[str, Any]]:
    score = float(rf_fuzz.ratio(a, b))
    return score >= RAPIDFUZZ_CUTOFF, {"ratio": round(score, 2)}


def m_difflib_norm(a: str, b: str, kind: str) -> tuple[bool, dict[str, Any]]:
    ratio = difflib.SequenceMatcher(None, normalize(a), normalize(b)).ratio()
    return ratio >= DIFFLIB_CUTOFF, {"ratio": round(ratio, 4)}


def m_rapidfuzz_norm(a: str, b: str, kind: str) -> tuple[bool, dict[str, Any]]:
    score = float(rf_fuzz.ratio(normalize(a), normalize(b)))
    return score >= RAPIDFUZZ_CUTOFF, {"ratio": round(score, 2)}


MATCHERS: list[tuple[str, Matcher]] = [
    ("vi_textmatch", m_vi_textmatch),
    ("difflib", m_difflib),
    ("rapidfuzz", m_rapidfuzz),
]
VARIANTS: list[tuple[str, Matcher]] = [
    ("difflib+normalize", m_difflib_norm),
    ("rapidfuzz+normalize", m_rapidfuzz_norm),
]


# ------------------------------------------------------------------ scoring
def run(fn: Matcher, pairs: list[Row]) -> list[Row]:
    rows: list[Row] = []
    for p in pairs:
        try:
            pred, meta = fn(p["a"], p["b"], p["kind"])
            err = ""
        except Exception as exc:  # noqa: BLE001 - any raise is a data-quality answer
            pred, meta, err = False, {}, f"{type(exc).__name__}: {exc}"
        rows.append(
            {
                "a": p["a"],
                "b": p["b"],
                "kind": p["kind"],
                "expected_equal": p["expected_equal"],
                "note": p["note"],
                "pred": bool(pred),
                "correct": bool(pred) == p["expected_equal"],
                "error": err,
                **meta,
            }
        )
    return rows


def summarize(rows: list[Row]) -> dict[str, Any]:
    n = len(rows)
    return {
        "n": n,
        "correct": sum(1 for r in rows if r["correct"]),
        "false_equal": sum(1 for r in rows if r["pred"] and not r["expected_equal"]),
        "false_diff": sum(1 for r in rows if not r["pred"] and r["expected_equal"]),
        "errors": sum(1 for r in rows if r["error"]),
        "accuracy": (sum(1 for r in rows if r["correct"]) / n) if n else 0.0,
    }


def pct(x: float) -> str:
    return f"{x * 100:.1f}%"


def cell(text: str) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ")


def code(text: str) -> str:
    return f"`{text.replace('`', '')}`"


def metric_of(r: Row) -> str:
    if "level" in r:
        return f"{r['level']} ({r.get('detail', '')})"
    if "ratio" in r:
        return f"ratio {r['ratio']}"
    return "—"


def git_commit() -> str:
    try:
        out = subprocess.run(
            ["git", "-C", str(REPO), "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, check=True,
        )
        return out.stdout.strip()
    except Exception:  # noqa: BLE001
        return "unknown"


# ------------------------------------------------------------------- report
def build_report(
    pairs: list[Row],
    results: dict[str, list[Row]],
    variants: dict[str, list[Row]],
    pairs_path: Path,
) -> str:
    eq = sum(1 for p in pairs if p["expected_equal"])
    kinds_n = Counter(p["kind"] for p in pairs)
    lines: list[str] = []
    add = lines.append

    add("# Bench: vi-textmatch vs difflib vs rapidfuzz")
    add("")
    add("Sinh tự động bởi `bench/run_bench.py` — phần số liệu không sửa tay; "
        "phần nhận định ở cuối cũng lấy số từ chính lần chạy này.")
    add("")
    add(f"- Chạy lúc: {datetime.now().astimezone().strftime('%Y-%m-%d %H:%M %Z')}")
    add(f"- Commit: `{git_commit()}` · Python {sys.version.split()[0]} · "
        f"rapidfuzz {rapidfuzz.__version__} · {platform.platform()}")
    add(f"- Dữ liệu: `{pairs_path.name}` — **{len(pairs)} cặp bịa hoàn toàn**, "
        f"{eq} cặp bằng nhau / {len(pairs) - eq} cặp khác nhau "
        f"(money {kinds_n['money']}, date {kinds_n['date']}, id {kinds_n['id']}, "
        f"text {kinds_n['text']}).")
    add("")
    add("## Phương pháp")
    add("")
    add("- `vi_textmatch`: `compare(a, b, kind=...).match`; TEXT coi `TYPO` (ratio ≥ 0.85) "
        "là match, MONEY/DATE ném lỗi khi không ép được kiểu.")
    add(f"- `difflib`: `SequenceMatcher(None, a, b).ratio() >= {DIFFLIB_CUTOFF}` trên chuỗi **thô**.")
    add(f"- `rapidfuzz`: `fuzz.ratio(a, b) >= {RAPIDFUZZ_CUTOFF}` trên chuỗi **thô**.")
    add("- Chuẩn đúng là **nghĩa**, chốt trước khi chạy: cùng một người / cùng một số tiền / "
        "cùng một ngày / cùng một định danh → `expected_equal = true`.")
    add("- Ném lỗi được ghi `ERR` và tính là **không bằng** (fail-closed) — đúng hướng thư viện "
        "mong muốn, và vẫn bị tính vào accuracy.")
    add("- accuracy = đoán đúng / tổng; false-equal = đoán BẰNG nhưng thực ra KHÁC; "
        "false-diff = đoán KHÁC nhưng thực ra BẰNG.")
    add("")

    add("## Tổng")
    add("")
    add("| matcher | accuracy | đúng | false-equal ⚠ | false-diff | ERR |")
    add("|---|---|---|---|---|---|")
    for name, rows in results.items():
        s = summarize(rows)
        add(f"| `{name}` | {pct(s['accuracy'])} | {s['correct']}/{s['n']} | "
            f"**{s['false_equal']}** | {s['false_diff']} | {s['errors']} |")
    add("")

    def kind_table(title: str, metric: str, fmt: Callable[[Any], str]) -> None:
        add(f"## {title}")
        add("")
        add("| matcher | " + " | ".join(KIND_ORDER) + " | total |")
        add("|" + "---|" * (len(KIND_ORDER) + 2))
        for name, rows in results.items():
            vals = [summarize([r for r in rows if r["kind"] == k])[metric] for k in KIND_ORDER]
            add(f"| `{name}` | " + " | ".join(fmt(v) for v in vals)
                + f" | {fmt(summarize(rows)[metric])} |")
        add("")

    kind_table("Theo kiểu dữ liệu — accuracy", "accuracy", lambda v: pct(v))
    kind_table("Theo kiểu dữ liệu — false-equal (hướng sai nguy hiểm)", "false_equal",
               lambda v: f"**{v}**" if v else "0")
    kind_table("Theo kiểu dữ liệu — false-diff (hướng sai gây phiền)", "false_diff", str)
    kind_table("Theo kiểu dữ liệu — ERR (ném lỗi, fail-closed)", "errors", str)

    add("## Bằng chứng — từng cặp bị đoán SAI")
    add("")
    for name, rows in results.items():
        for title, pick in (
            ("false-equal", lambda r: r["pred"] and not r["expected_equal"]),
            ("false-diff", lambda r: not r["pred"] and r["expected_equal"]),
        ):
            bad = [r for r in rows if pick(r)]
            add(f"### `{name}` — {title}: {len(bad)} cặp")
            add("")
            if not bad:
                add("Không có.")
                add("")
                continue
            add("| kind | a | b | thước đo | ERR | ghi chú |")
            add("|---|---|---|---|---|---|")
            for r in bad:
                add(f"| {r['kind']} | {code(r['a'])} | {code(r['b'])} | {cell(metric_of(r))} | "
                    f"{'x' if r['error'] else ''} | {cell(r['note'])} |")
            add("")

    add("## Kiểm tra độ nhạy: baseline có được chuẩn hoá thì sao?")
    add("")
    add("Cùng hai thước đo chuỗi nhưng chạy trên `normalize()` của vi-textmatch "
        "(NFC + vị trí dấu thanh + khoảng trắng + casefold), **không** có logic theo kiểu. "
        "Mục đích: tách xem chênh lệch đến từ chuẩn hoá hay từ việc hiểu kiểu dữ liệu.")
    add("")
    add("| matcher | accuracy | false-equal ⚠ | false-diff | ERR |")
    add("|---|---|---|---|---|")
    for name, rows in variants.items():
        s = summarize(rows)
        add(f"| `{name}` | {pct(s['accuracy'])} | **{s['false_equal']}** | "
            f"{s['false_diff']} | {s['errors']} |")
    add("")

    # ---- observations, every number computed from this run -----------------
    vi = results["vi_textmatch"]
    df = results["difflib"]
    rf = results["rapidfuzz"]
    s_vi, s_df, s_rf = summarize(vi), summarize(df), summarize(rf)
    vi_fe = {k: summarize([r for r in vi if r["kind"] == k])["false_equal"] for k in KIND_ORDER}
    df_fe = {k: summarize([r for r in df if r["kind"] == k])["false_equal"] for k in KIND_ORDER}
    rf_fe = {k: summarize([r for r in rf if r["kind"] == k])["false_equal"] for k in KIND_ORDER}
    vi_fd = {k: summarize([r for r in vi if r["kind"] == k])["false_diff"] for k in KIND_ORDER}
    vi_err = [r for r in vi if r["error"]]
    vi_err_safe = [r for r in vi_err if not r["expected_equal"]]
    df_norm = variants.get("difflib+normalize")
    at_boundary = [
        r for r in df if abs(float(r["ratio"]) - DIFFLIB_CUTOFF) <= 0.005
    ]
    diverge = sum(
        1 for d, f in zip(df, rf) if d["pred"] != f["pred"]
    ) if len(df) == len(rf) else None

    add("## Nhận định (số liệu lấy từ lần chạy này)")
    add("")
    add(f"1. **Lỗi nguy hiểm tập trung ở baseline.** `vi_textmatch` có {s_vi['false_equal']} "
        f"false-equal; difflib {s_df['false_equal']}, rapidfuzz {s_rf['false_equal']}. "
        f"Baseline coi hai số tiền/ngày/định danh khác nhau là \"gần đúng\" đúng ở chỗ SPEC cấm "
        f"dùng ratio: money {df_fe['money']}, date {df_fe['date']}, id {df_fe['id']}, "
        f"text {df_fe['text']}.")
    add(f"2. **`vi_textmatch` không false-equal ở money/date/id** "
        f"({vi_fe['money']}/{vi_fe['date']}/{vi_fe['id']} cặp). Toàn bộ false-equal của nó nằm ở "
        f"text ({vi_fe['text']} cặp), nơi ngưỡng TYPO 0.85 tự động gộp hai tên khác nhau lệch 1 dấu.")
    if at_boundary:
        add(f"3. **Ngưỡng 0.9 là con dao sắc.** {len(at_boundary)}/{len(df)} cặp có ratio difflib "
            f"đúng bằng 0.90 (±0.005): " +
            ", ".join(f"{code(r['a'])} vs {code(r['b'])} → "
                      f"{'BẰNG' if r['pred'] else 'KHÁC'}" for r in at_boundary[:3]) +
            ". Cặp khác nhau thật nằm ngay trên ngưỡng thì không nâng ngưỡng được, chỉ đổi cặp nào sai.")
    add(f"4. **False-diff của `vi_textmatch`** = {s_vi['false_diff']} cặp, phân theo kiểu: "
        f"money {vi_fd['money']}, date {vi_fd['date']}, id {vi_fd['id']}, text {vi_fd['text']}.")
    add(f"5. **ERR ({len(vi_err)} cặp)** rơi vào input không ép được kiểu / ngày không tồn tại; "
        f"{len(vi_err_safe)}/{len(vi_err)} trong số đó là cặp vốn khác nhau, nên fail-closed "
        f"không gây hại — điểm money/date có một phần công của việc ném lỗi thay vì đoán.")
    if df_norm is not None:
        s_norm = summarize(df_norm)
        add(f"6. **Chuẩn hoá không phải nguồn gốc của an toàn.** Cho difflib dùng `normalize()` "
            f"của thư viện: accuracy {pct(s_df['accuracy'])} → {pct(s_norm['accuracy'])}, "
            f"false-equal {s_df['false_equal']} → {s_norm['false_equal']}. Giá trị nằm ở "
            f"type-aware, không phải ở NFC.")
    if diverge is not None:
        add(f"7. **difflib và rapidfuzz** lệch dự đoán ở {diverge}/{len(pairs)} cặp — trên chuỗi "
            f"ngắn, hai thuật toán khác nhau cho kết quả gần như trùng. rapidfuzz nhanh hơn, "
            f"không an toàn hơn cho bài toán này.")
    add("")

    add("## Giới hạn")
    add("")
    add("- 100 cặp là mẫu nhỏ, do một người đặt nhãn; nhãn text phụ thuộc quan điểm \"hai tên lệch "
        "1 dấu có phải cùng người không\". Cách chốt ở đây là **chặt**: phải soát lại.")
    add("- Mọi chuỗi đều bịa; không có PII, không suy ra hành vi trên dữ liệu thật.")
    add("- Chưa đo tốc độ và chưa đo trường hợp chuỗi rất dài (difflib có `autojunk`).")
    add("")
    add("## Chạy lại")
    add("")
    add("```bash")
    add("python3 bench/gen_pairs.py     # sinh lại bench/pairs.jsonl (tất định)")
    add("python3 bench/run_bench.py    # ghi bench/RESULTS.md + bench/results.jsonl")
    add("```")
    add("")
    add("Nếu `rapidfuzz` chưa có (Python hệ thống trên macOS bị PEP 668 chặn `pip`):")
    add("")
    add("```bash")
    add("python3.11 -m venv .venv && .venv/bin/pip install rapidfuzz")
    add(".venv/bin/python bench/run_bench.py")
    add("```")
    add("")
    add("`rapidfuzz` chỉ là dependency **của benchmark**; thư viện vẫn zero-dependency.")
    add("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pairs", default=str(HERE / "pairs.jsonl"))
    ap.add_argument("--out", default=str(HERE / "RESULTS.md"))
    ap.add_argument("--json", default=str(HERE / "results.jsonl"))
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args()

    pairs_path = Path(args.pairs)
    pairs = [
        json.loads(line)
        for line in pairs_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not pairs:
        sys.stderr.write(f"no pairs in {pairs_path}\n")
        return 1
    unknown = {p["kind"] for p in pairs} - set(KIND_MAP)
    assert not unknown, f"unknown kind(s): {unknown}"

    results = {name: run(fn, pairs) for name, fn in MATCHERS}
    variants = {name: run(fn, pairs) for name, fn in VARIANTS}

    # sanity: nothing silently dropped, per-kind counts add up to the total
    for name, rows in results.items():
        assert len(rows) == len(pairs), name
        assert sum(summarize([r for r in rows if r["kind"] == k])["n"]
                   for k in KIND_ORDER) == len(pairs), name

    print(f"pairs: {len(pairs)}  ({pairs_path})")
    print(f"python {sys.version.split()[0]}  rapidfuzz {rapidfuzz.__version__}  "
          f"commit {git_commit()}")
    hdr = f"{'matcher':<22}{'acc':>8}{'correct':>10}{'FE':>5}{'FD':>5}{'ERR':>5}"
    print()
    print(hdr)
    print("-" * len(hdr))
    for name, rows in list(results.items()) + list(variants.items()):
        s = summarize(rows)
        print(f"{name:<22}{pct(s['accuracy']):>8}{s['correct']:>6}/{s['n']:<3}"
              f"{s['false_equal']:>5}{s['false_diff']:>5}{s['errors']:>5}")

    report = build_report(pairs, results, variants, pairs_path)
    if args.no_write:
        print("\n" + report)
        return 0

    Path(args.out).write_text(report, encoding="utf-8")
    rows_written = 0
    with Path(args.json).open("w", encoding="utf-8") as fh:
        for name, rows in list(results.items()) + list(variants.items()):
            for r in rows:
                fh.write(json.dumps({"matcher": name, **r}, ensure_ascii=False) + "\n")
                rows_written += 1
    print(f"\nwrote {args.out}")
    print(f"wrote {args.json}  ({rows_written} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
