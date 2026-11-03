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
import hashlib
import json
import platform
import subprocess
import sys
from collections import Counter
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(REPO / "src"))

from vi_textmatch import Kind, normalize  # noqa: E402
from vi_textmatch import compare as vi_compare

try:
    import rapidfuzz
    from rapidfuzz import fuzz as rf_fuzz

    RF_VERSION = rapidfuzz.__version__
except ImportError:  # pragma: no cover - environment dependent
    # Optional: without rapidfuzz the rapidfuzz columns are dropped, not the run.
    rf_fuzz = None
    RF_VERSION = "không cài (bỏ cột rapidfuzz)"
    sys.stderr.write(
        "rapidfuzz not installed: skipping the rapidfuzz columns. To include them:\n"
        "  python3.11 -m venv .venv && .venv/bin/pip install rapidfuzz\n"
        "  .venv/bin/python bench/run_bench.py\n"
    )

DIFFLIB_CUTOFF = 0.9
RAPIDFUZZ_CUTOFF = 90.0
KIND_MAP = {"text": Kind.TEXT, "name": Kind.NAME, "id": Kind.ID, "money": Kind.MONEY, "date": Kind.DATE}
KIND_ORDER = ("money", "date", "id", "name", "text")

Row = dict[str, Any]
Matcher = Callable[[str, str, str], tuple[bool, dict[str, Any]]]


# --------------------------------------------------------------- matchers
def m_vi_textmatch(a: str, b: str, kind: str) -> tuple[bool, dict[str, Any]]:
    # Bench data is Vietnamese: DD/MM/YYYY, so tell DATE the order (v0.3.0+).
    extra = {"day_first": True} if kind == "date" else {}
    verdict = vi_compare(a, b, kind=KIND_MAP[kind], **extra)
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
if rf_fuzz is None:
    MATCHERS = [m for m in MATCHERS if not m[0].startswith("rapidfuzz")]
VARIANTS: list[tuple[str, Matcher]] = [
    ("difflib+normalize", m_difflib_norm),
    ("rapidfuzz+normalize", m_rapidfuzz_norm),
]
if rf_fuzz is None:
    VARIANTS = [m for m in VARIANTS if not m[0].startswith("rapidfuzz")]


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
                "source": p.get("source", "core"),
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
        f"rapidfuzz {RF_VERSION} · {platform.platform()}")
    add(f"- Dữ liệu: `{pairs_path.name}` — **{len(pairs)} cặp bịa hoàn toàn**, "
        f"{eq} cặp bằng nhau / {len(pairs) - eq} cặp khác nhau "
        f"(money {kinds_n['money']}, date {kinds_n['date']}, id {kinds_n['id']}, "
        f"name {kinds_n['name']}, text {kinds_n['text']}).")
    add("")
    add("## Phương pháp")
    add("")
    add("- `vi_textmatch`: `compare(a, b, kind=...).match`; TEXT coi `TYPO` (ratio ≥ 0.85) "
        "là match, MONEY/DATE ném lỗi khi không ép được kiểu; DATE gọi với `day_first=True` "
        "(dữ liệu VN, DD/MM/YYYY); NAME so từng thành phần tên, lệch là KHÁC.")
    add(f"- `difflib`: `SequenceMatcher(None, a, b).ratio() >= {DIFFLIB_CUTOFF}` trên chuỗi **thô**.")
    if rf_fuzz is not None:
        add(f"- `rapidfuzz`: `fuzz.ratio(a, b) >= {RAPIDFUZZ_CUTOFF}` trên chuỗi **thô**.")
    else:
        add("- `rapidfuzz`: **CHƯA CHẠY** — gói không có trong môi trường này.")
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
    for name, rows in list(results.items()) + list(variants.items()):
        s = summarize(rows)
        add(f"| `{name}` | {pct(s['accuracy'])} | {s['correct']}/{s['n']} | "
            f"**{s['false_equal']}** | {s['false_diff']} | {s['errors']} |")
    add("")
    add("`+normalize` = cùng thước đo chuỗi nhưng chạy trên `normalize()` (baseline mạnh hơn, "
        "để so sánh công bằng).")
    add("")
    add("## Theo nguồn / mẫu biến đổi (`vi_textmatch`)")
    add("")
    add("Cặp sinh tự động được gán nhãn theo phép biến đổi; bảng này cho thấy thư viện "
        "mạnh/yếu ở phép nào, tránh để vài mẫu dễ kéo điểm tổng.")
    add("")
    add("| nguồn | ghi chú (phép biến đổi) | nhãn | n | đúng | FE | FD |")
    add("|---|---|---|---|---|---|---|")
    groups: dict[tuple[str, str, bool], list[Row]] = {}
    for p, r in zip(pairs, results["vi_textmatch"]):
        if p.get("source", "core") == "core":
            continue
        groups.setdefault((p["source"], p["note"], p["expected_equal"]), []).append(r)
    for (src, note, exp), rows in sorted(groups.items()):
        s = summarize(rows)
        add(f"| {src} | {cell(note)} | {'BẰNG' if exp else 'KHÁC'} | {s['n']} | {s['correct']} | "
            f"{s['false_equal']} | {s['false_diff']} |")
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
    rf = results.get("rapidfuzz")
    s_vi, s_df = summarize(vi), summarize(df)
    rf_fe_total = str(summarize(rf)["false_equal"]) if rf is not None else "CHƯA CHẠY"
    vi_fe = {k: summarize([r for r in vi if r["kind"] == k])["false_equal"] for k in KIND_ORDER}
    df_fe = {k: summarize([r for r in df if r["kind"] == k])["false_equal"] for k in KIND_ORDER}
    vi_fd = {k: summarize([r for r in vi if r["kind"] == k])["false_diff"] for k in KIND_ORDER}
    vi_err = [r for r in vi if r["error"]]
    vi_err_safe = [r for r in vi_err if not r["expected_equal"]]
    df_norm = variants.get("difflib+normalize")
    at_boundary = [
        r for r in df if abs(float(r["ratio"]) - DIFFLIB_CUTOFF) <= 0.005
    ]
    diverge = sum(
        1 for d, f in zip(df, rf) if d["pred"] != f["pred"]
    ) if rf is not None and len(df) == len(rf) else None

    add("## Nhận định (số liệu lấy từ lần chạy này)")
    add("")
    add(f"1. **Lỗi nguy hiểm tập trung ở baseline.** `vi_textmatch` có {s_vi['false_equal']} "
        f"false-equal; difflib {s_df['false_equal']}, rapidfuzz {rf_fe_total}. "
        f"Baseline coi hai số tiền/ngày/định danh khác nhau là \"gần đúng\" đúng ở chỗ SPEC cấm "
        f"dùng ratio: money {df_fe['money']}, date {df_fe['date']}, id {df_fe['id']}, "
        f"text {df_fe['text']}.")
    add(f"2. **False-equal của `vi_textmatch` theo kiểu:** money {vi_fe['money']}, "
        f"date {vi_fe['date']}, id {vi_fe['id']}, name {vi_fe['name']}, text {vi_fe['text']}. "
        f"Ở text, ngưỡng TYPO 0.85 gộp hai chuỗi gần giống nhưng khác nghĩa (địa chỉ khác số "
        f"nhà, công ty khác loại hình) — TEXT không phải kiểu an toàn cho địa chỉ/pháp nhân.")
    if at_boundary:
        add(f"3. **Ngưỡng 0.9 là con dao sắc.** {len(at_boundary)}/{len(df)} cặp có ratio difflib "
            f"đúng bằng 0.90 (±0.005): " +
            ", ".join(f"{code(r['a'])} vs {code(r['b'])} → "
                      f"{'BẰNG' if r['pred'] else 'KHÁC'}" for r in at_boundary[:3]) +
            ". Cặp khác nhau thật nằm ngay trên ngưỡng thì không nâng ngưỡng được, chỉ đổi cặp nào sai.")
    add(f"4. **False-diff của `vi_textmatch`** = {s_vi['false_diff']} cặp, phân theo kiểu: "
        f"money {vi_fd['money']}, date {vi_fd['date']}, id {vi_fd['id']}, name {vi_fd['name']}, "
        f"text {vi_fd['text']}. False-diff ở name là cố ý: tên lệch 1 chữ do gõ/OCR bị đẩy về "
        f"KHÁC để người soát lại, thay vì đoán là cùng người.")
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
    n_core = sum(1 for p in pairs if p.get("source", "core") == "core")
    add(f"- {n_core} cặp viết tay + {len(pairs) - n_core} cặp sinh tự động (`gen_extended.py`, "
        "seed cố định, nhãn theo phép biến đổi); vẫn là dữ liệu bịa, do một người đặt nhãn; nhãn text phụ thuộc quan điểm \"hai tên lệch "
        "1 dấu có phải cùng người không\". Cách chốt ở đây là **chặt**: phải soát lại.")
    add("- Mọi chuỗi đều bịa; không có PII, không suy ra hành vi trên dữ liệu thật.")
    add("- Chưa đo tốc độ và chưa đo trường hợp chuỗi rất dài (difflib có `autojunk`).")
    add("")
    add("## Chạy lại")
    add("")
    add("```bash")
    add("python3 bench/gen_extended.py  # sinh lại bench/pairs.jsonl từ pairs_core.jsonl (tất định)")
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


def fe_key(r: Row) -> str:
    return f"{r['kind']}\t{r['a']}\t{r['b']}"


def gate_check(pairs_path: Path, vi_rows: list[Row], baseline: Path, update: bool) -> int:
    """CI gate: fail on any vi_textmatch false-equal that is not already known.

    Keyed by the pair itself (not a count), so adding pairs never trips it by
    accident, and fixing a known false-equal is allowed (it is just reported).
    """
    current = sorted(fe_key(r) for r in vi_rows if r["pred"] and not r["expected_equal"])
    digest = hashlib.sha256(pairs_path.read_bytes()).hexdigest()
    if update:
        baseline.write_text(json.dumps({"pairs_sha256": digest, "false_equal": current},
                                       ensure_ascii=False, indent=1) + "\n", "utf-8")
        print(f"\nbaseline updated: {len(current)} known false-equal")
        return 0
    if not baseline.exists():
        print(f"\nno baseline at {baseline}")
        return 1
    base = json.loads(baseline.read_text("utf-8"))
    known = set(base["false_equal"])
    new = [k for k in current if k not in known]
    fixed = [k for k in known if k not in set(current)]
    print(f"\ngate: {len(current)} false-equal, {len(known)} in baseline, "
          f"{len(new)} NEW, {len(fixed)} fixed")
    if base.get("pairs_sha256") != digest:
        print("  note: pairs.jsonl changed since baseline — run --update-baseline if intended")
    for k in new:
        print("  NEW false-equal:", k.replace("\t", " | "))
    return 1 if new else 0


def build_summary(pairs: list[Row], results: dict[str, list[Row]],
                  variants: dict[str, list[Row]]) -> str:
    lines = ["<!-- generated by bench/run_bench.py --summary; do not edit -->",
             f"Pairs: **{len(pairs)}** (fabricated) · commit `{git_commit()}` · "
             f"rapidfuzz {rapidfuzz.__version__}", "",
             "| matcher | accuracy | false-equal ⚠ | false-diff | ERR |", "|---|---|---|---|---|"]
    for name, rows in list(results.items()) + list(variants.items()):
        s = summarize(rows)
        lines.append(f"| `{name}` | {pct(s['accuracy'])} | **{s['false_equal']}** | "
                     f"{s['false_diff']} | {s['errors']} |")
    lines += ["", "| matcher | " + " | ".join(KIND_ORDER) + " |",
              "|" + "---|" * (len(KIND_ORDER) + 1)]
    for name, rows in results.items():
        vals = [summarize([r for r in rows if r["kind"] == k]) for k in KIND_ORDER]
        lines.append(f"| `{name}` | " + " | ".join(
            f"{pct(v['accuracy'])} (FE {v['false_equal']})" for v in vals) + " |")
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pairs", default=str(HERE / "pairs.jsonl"))
    ap.add_argument("--out", default=str(HERE / "RESULTS.md"))
    ap.add_argument("--json", default=str(HERE / "results.jsonl"))
    ap.add_argument("--no-write", action="store_true")
    ap.add_argument("--baseline", default=str(HERE / "baseline.json"))
    ap.add_argument("--check", action="store_true",
                    help="exit 1 if vi_textmatch has a false-equal not listed in --baseline")
    ap.add_argument("--update-baseline", action="store_true")
    ap.add_argument("--badge", help="write a shields.io endpoint JSON here")
    ap.add_argument("--summary", help="write a short Markdown summary table here (docs)")
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
    print(f"python {sys.version.split()[0]}  rapidfuzz {RF_VERSION}  "
          f"commit {git_commit()}")
    hdr = f"{'matcher':<22}{'acc':>8}{'correct':>10}{'FE':>5}{'FD':>5}{'ERR':>5}"
    print()
    print(hdr)
    print("-" * len(hdr))
    for name, rows in list(results.items()) + list(variants.items()):
        s = summarize(rows)
        print(f"{name:<22}{pct(s['accuracy']):>8}{s['correct']:>6}/{s['n']:<3}"
              f"{s['false_equal']:>5}{s['false_diff']:>5}{s['errors']:>5}")

    gate = gate_check(pairs_path, results["vi_textmatch"], Path(args.baseline),
                      args.update_baseline)
    if args.badge:
        s = summarize(results["vi_textmatch"])
        Path(args.badge).write_text(json.dumps({
            "schemaVersion": 1, "label": f"bench ({s['n']} cặp)",
            "message": f"{pct(s['accuracy'])} · false-equal {s['false_equal']}",
            "color": "green" if gate == 0 else "red"}, ensure_ascii=False) + "\n", "utf-8")
    if args.summary:
        Path(args.summary).write_text(build_summary(pairs, results, variants), "utf-8")
    if args.check and gate:
        return gate

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
