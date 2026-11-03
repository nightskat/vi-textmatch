#!/usr/bin/env python3
"""Build bench/pairs.jsonl = 100 hand-written core pairs + generated pairs.

Every string is FABRICATED from small invented vocabularies (street, ward,
company and person-name parts below). No real person, company, contract or
account. A seeded RNG makes the output byte-identical on every run.

Ground truth is assigned BY CONSTRUCTION, never by running a matcher: each
generated pair comes from a named transformation that either preserves the
meaning (encoding, case, spacing, tone placement, number/date format,
currency alias) or changes it (another digit, another day, another legal
form, another currency, another diacritic that yields another valid name).
This file never imports vi_textmatch, so labels cannot be fitted to it.

Some "equal" transformations are deliberately outside what the library
handles (abbreviations like "P." for "Phường", "1,5 tỷ", dates written in
words). They stay in so the benchmark measures real-world inputs, not the
library's comfort zone; those pairs are expected to show up as false-diff.

Run:  python3 bench/gen_extended.py
"""

from __future__ import annotations

import json
import random
import unicodedata
from collections import Counter
from collections.abc import Callable
from pathlib import Path

HERE = Path(__file__).resolve().parent
SEED = 20261103
PER_KIND = {"address": 90, "company": 80, "contract": 80, "money": 90, "date": 70, "name": 80}

Pair = tuple[str, str, str, bool, str]  # a, b, kind, expected_equal, note


def nfd(s: str) -> str:
    return unicodedata.normalize("NFD", s)


# ------------------------------------------------------------ vocabularies
STREETS = ["Lê Lợi", "Trần Hưng Đạo", "Hoàng Văn Thụ", "Nguyễn Trãi", "Điện Biên Phủ",
           "Lạch Tray", "Văn Cao", "Tô Hiệu", "Hòa Bình", "Thủy Nguyên", "Lý Thường Kiệt",
           "Quang Trung", "Phạm Văn Đồng", "Ngô Quyền", "Hùng Vương"]
WARDS = ["Cầu Đất", "Đông Khê", "Lạc Viên", "Hòa Nghĩa", "Máy Tơ", "Vĩnh Niệm",
         "An Biên", "Thượng Lý", "Kênh Dương", "Đằng Giang"]
DISTRICTS = ["Ngô Quyền", "Lê Chân", "Hồng Bàng", "Hải An", "Kiến An", "Dương Kinh"]
CITIES = ["Hải Phòng", "Hà Nội", "Đà Nẵng", "Cần Thơ"]

CO_FORMS = ["Công ty TNHH", "Công ty Cổ phần", "Công ty TNHH MTV", "Doanh nghiệp tư nhân"]
CO_WORDS = ["Thương mại", "Dịch vụ", "Xây dựng", "Vận tải", "Thủy sản", "Đầu tư",
            "Kỹ thuật", "Hoàng Gia", "Minh Khoa", "Thuận Phát", "Hòa Lợi", "Biển Xanh",
            "Phúc Thịnh", "Đại Dương", "An Khánh", "Tân Hòa"]

SURNAMES = ["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Vũ", "Đặng", "Bùi", "Đỗ", "Ngô", "Khúc"]
MIDDLES = ["Văn", "Thị", "Đức", "Minh", "Quốc", "Thu", "Ngọc", "Hữu", "Thanh"]
GIVENS = ["Hòa", "Thủy", "Khánh", "An", "Bình", "Tuấn", "Lan", "Hùng", "Yến", "Toàn",
          "Thụy", "Hoè", "Nhung", "Phương", "Dũng"]
# pairs where one diacritic change gives ANOTHER valid given name -> different person
NAME_NEAR = [("An", "Ân"), ("Khánh", "Kháng"), ("Lan", "Lân"), ("Hùng", "Hưng"),
             ("Tuấn", "Tuân"), ("Bình", "Bính"), ("Dũng", "Dung"), ("Yến", "Yên"),
             ("Hòa", "Hoa"), ("Toàn", "Toán")]
# old (oà) vs new (òa) tone placement — open syllables only, same word
TONE_SWAP = {"Hòa": "Hoà", "Thủy": "Thuỷ", "Thụy": "Thuỵ", "Hoè": "Hòe"}

CONTRACT_TYPES = ["HĐTD", "HĐBĐ", "HĐTC", "HĐMB", "PL"]
CONTRACT_SUFFIX = ["PGB", "CN.HP", "KHCN", "KHDN"]


def tone_swap(s: str) -> str | None:
    out = s
    for old, new in TONE_SWAP.items():
        out = out.replace(old, new)
    return out if out != s else None


def spaces(rng: random.Random, s: str) -> str:
    words = s.split(" ")
    i = rng.randrange(len(words))
    words[i] = words[i] + " "
    return ("  " if rng.random() < 0.5 else "") + " ".join(words) + " "


# ------------------------------------------------------------ TEXT: address
def gen_address(rng: random.Random) -> Pair:
    no, alley = rng.randint(1, 250), rng.randint(1, 120)
    street, ward = rng.choice(STREETS), rng.choice(WARDS)
    dist, city = rng.choice(DISTRICTS), rng.choice(CITIES)
    a = f"Số {no} ngõ {alley} {street}, phường {ward}, quận {dist}, {city}"
    eq: list[tuple[Callable[[], str | None], str]] = [
        (lambda: nfd(a), "địa chỉ NFC vs NFD"),
        (lambda: a.upper(), "địa chỉ viết HOA"),
        (lambda: spaces(rng, a), "địa chỉ thừa khoảng trắng"),
        (lambda: tone_swap(a), "địa chỉ dấu thanh kiểu cũ (oà/uỷ)"),
        (lambda: a.replace("phường ", "P. ").replace("quận ", "Q. "),
         "viết tắt P./Q. — cùng địa chỉ"),
        (lambda: a.replace(", ", ","), "bỏ khoảng trắng sau dấu phẩy"),
    ]
    other_no = no + rng.choice([1, 2, 10, -1]) if no > 2 else no + 3
    other_street = rng.choice([s for s in STREETS if s != street])
    ne: list[tuple[Callable[[], str | None], str]] = [
        (lambda: a.replace(f"Số {no} ", f"Số {other_no} ", 1), "khác số nhà"),
        (lambda: a.replace(f"ngõ {alley} ", f"ngõ {alley + 1} ", 1), "khác số ngõ"),
        (lambda: a.replace(street, other_street, 1), "khác tên đường"),
        (lambda: a.replace(f"phường {ward}",
                           f"phường {rng.choice([w for w in WARDS if w != ward])}"),
         "khác phường"),
    ]
    return pick(rng, a, "text", eq, ne)


# ------------------------------------------------------------ TEXT: company
def gen_company(rng: random.Random) -> Pair:
    form = rng.choice(CO_FORMS)
    w1, w2 = rng.sample(CO_WORDS, 2)
    a = f"{form} {w1} {w2}"
    other_form = rng.choice([f for f in CO_FORMS if f != form])
    other_word = rng.choice([w for w in CO_WORDS if w not in (w1, w2)])
    eq = [
        (lambda: nfd(a), "tên công ty NFC vs NFD"),
        (lambda: a.upper(), "tên công ty viết HOA"),
        (lambda: spaces(rng, a), "tên công ty thừa khoảng trắng"),
        (lambda: tone_swap(a), "tên công ty dấu thanh kiểu cũ"),
        (lambda: a.replace("Công ty", "Cty", 1) if a.startswith("Công ty") else None,
         "viết tắt Cty — cùng công ty"),
    ]
    ne = [
        (lambda: a.replace(form, other_form, 1), "khác loại hình (TNHH/CP/MTV/DNTN)"),
        (lambda: a.replace(w2, other_word), "khác một từ trong tên"),
        (lambda: f"{form} {w2} {w1}", "đảo thứ tự từ trong tên"),
    ]
    return pick(rng, a, "text", eq, ne)


# ------------------------------------------------------------ ID: contract number
def gen_contract(rng: random.Random) -> Pair:
    n, year = rng.randint(1, 999), rng.choice([2024, 2025, 2026])
    typ, suf = rng.choice(CONTRACT_TYPES), rng.choice(CONTRACT_SUFFIX)
    a = f"{n:03d}/{year}/{typ}-{suf}"
    eq = [
        (lambda: f"{n:03d}/{year}/{typ} - {suf}", "số HĐ: khoảng trắng quanh '-'"),
        (lambda: f" {a} ", "số HĐ: khoảng trắng đầu/cuối"),
        (lambda: nfd(a), "số HĐ: NFC vs NFD (chữ Đ không đổi nhưng có thể có dấu)"),
        (lambda: f"{n:03d}/{year}/{typ}–{suf}", "số HĐ: gạch ngang '–' thay '-'"),
    ]
    ne = [
        (lambda: f"{n + 1:03d}/{year}/{typ}-{suf}", "số HĐ lệch 1 số thứ tự"),
        (lambda: f"{n:03d}/{year - 1}/{typ}-{suf}", "số HĐ khác năm"),
        (lambda: f"{n:03d}/{year}/{rng.choice([t for t in CONTRACT_TYPES if t != typ])}-{suf}",
         "số HĐ khác loại hợp đồng"),
        (lambda: f"{n:03d}/{year}/{typ}-{rng.choice([s for s in CONTRACT_SUFFIX if s != suf])}",
         "số HĐ khác hậu tố đơn vị"),
        (lambda: f"{n:03d}/{year}/{typ}-{suf}/PL01", "phụ lục của HĐ ≠ HĐ gốc"),
    ]
    return pick(rng, a, "id", eq, ne)


# ------------------------------------------------------------ MONEY
def vn(x: int) -> str:
    return f"{x:,}".replace(",", ".")


def us(x: int) -> str:
    return f"{x:,}"


def gen_money(rng: random.Random) -> Pair:
    x = rng.choice([rng.randint(1, 999) * 10**6, rng.randint(1, 99) * 10**8,
                    rng.randint(100, 99_999) * 1000, rng.randint(1, 50) * 10**9])
    base_fmt = rng.choice([vn, us, str])
    cur_a = rng.choice(["", " đ", "đ", " VND", " VNĐ", " đồng", "₫"])
    a = f"{base_fmt(x)}{cur_a}".strip() if not cur_a.startswith("₫") else f"₫{base_fmt(x)}"
    def fmt_b(v: int) -> str:
        f = rng.choice([vn, us, str])
        return f"{f(v)}{rng.choice(['', ' đ', ' VND', ' VNĐ', ' đồng', 'đ'])}"
    eq = [
        (lambda: fmt_b(x), "cùng số tiền, khác định dạng/đơn vị VND"),
        (lambda: fmt_b(x), "cùng số tiền, khác định dạng/đơn vị VND"),
        (lambda: f"{vn(x)},00 đ", "cùng số tiền, có phần thập phân ,00"),
        (lambda: (f"{x // 10**9} tỷ" if x % 10**9 == 0 else
                  f"{x // 10**6} triệu" if x % 10**6 == 0 else None),
         "số tiền viết bằng chữ tỷ/triệu"),
    ]
    delta = rng.choice([1000, 10**6, 10**7, x // 10 or 1000])
    ne = [
        (lambda: fmt_b(x + delta), "khác số tiền"),
        (lambda: fmt_b(x * 10), "thừa một số 0"),
        # only when `a` names VND explicitly: a bare number has no currency
        (lambda: f"{us(x)}$" if cur_a else None, "khác loại tiền (USD vs VND)"),
        (lambda: fmt_b(x - delta) if x > delta else None, "thiếu tiền"),
    ]
    return pick(rng, a, "money", eq, ne)


# ------------------------------------------------------------ DATE
def gen_date(rng: random.Random) -> Pair:
    import datetime as dt
    d = dt.date(2020, 1, 1) + dt.timedelta(days=rng.randint(0, 2500))
    def render(x: dt.date, style: int) -> str:
        return [f"{x.day:02d}/{x.month:02d}/{x.year}", f"{x.day}/{x.month}/{x.year}",
                x.isoformat(), f"{x.day:02d}-{x.month:02d}-{x.year}",
                f"{x.day:02d}.{x.month:02d}.{x.year}"][style]
    a = render(d, rng.randrange(5))
    eq = [
        (lambda: render(d, rng.randrange(5)), "cùng ngày, khác định dạng"),
        (lambda: render(d, rng.randrange(5)), "cùng ngày, khác định dạng"),
        (lambda: f"ngày {d.day:02d} tháng {d.month:02d} năm {d.year}", "ngày viết bằng chữ"),
    ]
    ne = [
        (lambda: render(d + dt.timedelta(days=1), rng.randrange(5)), "lệch 1 ngày"),
        (lambda: render(d.replace(year=d.year + 1) if not (d.month == 2 and d.day == 29)
                        else d + dt.timedelta(days=365), rng.randrange(5)), "khác năm"),
        (lambda: (render(dt.date(d.year, d.day, d.month), 0)
                  if d.day <= 12 and d.day != d.month else None),
         "đảo ngày/tháng — ngày khác"),
        (lambda: render(d + dt.timedelta(days=30), rng.randrange(5)), "lệch ~1 tháng"),
    ]
    return pick(rng, a, "date", eq, ne)


# ------------------------------------------------------------ NAME
def gen_name(rng: random.Random) -> Pair:
    s, m, g = rng.choice(SURNAMES), rng.choice(MIDDLES), rng.choice(GIVENS)
    a = f"{s} {m} {g}"
    near = [p for p in NAME_NEAR if p[0] == g]
    eq = [
        (lambda: nfd(a), "tên NFC vs NFD"),
        (lambda: a.upper(), "tên viết HOA"),
        (lambda: spaces(rng, a), "tên thừa khoảng trắng"),
        (lambda: tone_swap(a), "tên dấu thanh kiểu cũ (oà/uỷ)"),
    ]
    ne = [
        (lambda: f"{s} {m} {near[0][1]}" if near else None,
         "đổi 1 dấu → tên hợp lệ khác (người khác)"),
        (lambda: f"{s} {m} {rng.choice([x for x in GIVENS if x != g])}", "khác tên"),
        (lambda: f"{rng.choice([x for x in SURNAMES if x != s])} {m} {g}", "khác họ"),
        (lambda: f"{s} {rng.choice([x for x in MIDDLES if x != m])} {g}", "khác tên đệm"),
    ]
    return pick(rng, a, "name", eq, ne)


def pick(rng: random.Random, a: str, kind: str,
         eq: list[tuple[Callable[[], str | None], str]],
         ne: list[tuple[Callable[[], str | None], str]]) -> Pair:
    want_equal = rng.random() < 0.5
    pool = list(eq if want_equal else ne)
    rng.shuffle(pool)
    for fn, note in pool:
        b = fn()
        if b is not None and b != a:
            return (a, b, kind, want_equal, note)
    raise LookupError  # caller retries with a fresh base string


GENERATORS = {"address": gen_address, "company": gen_company, "contract": gen_contract,
              "money": gen_money, "date": gen_date, "name": gen_name}


def main() -> None:
    rng = random.Random(SEED)
    core = [json.loads(x) for x in (HERE / "pairs_core.jsonl").read_text("utf-8").splitlines()
            if x.strip()]
    seen = {(p["a"], p["b"]) for p in core}
    rows = [dict(p, source="core") for p in core]
    for group, n in PER_KIND.items():
        made = 0
        while made < n:
            try:
                a, b, kind, exp, note = GENERATORS[group](rng)
            except LookupError:
                continue
            if (a, b) in seen or (b, a) in seen:
                continue
            seen.add((a, b))
            rows.append({"a": a, "b": b, "kind": kind, "expected_equal": exp,
                         "note": note, "source": f"gen:{group}"})
            made += 1
    for r in rows:
        assert r["a"] != r["b"] and "|" not in r["note"], r
    out = HERE / "pairs.jsonl"
    with out.open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    eq = sum(r["expected_equal"] for r in rows)
    print(f"wrote {out} — {len(rows)} pairs ({eq} equal / {len(rows) - eq} unequal)")
    print("  ", dict(Counter(r["source"] for r in rows)))
    print("  ", dict(Counter(r["kind"] for r in rows)))


if __name__ == "__main__":
    main()
