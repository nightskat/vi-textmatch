#!/usr/bin/env python3
"""Generate bench/pairs.jsonl — 100 fabricated Vietnamese comparison pairs.

Every string is invented: generic Vietnamese name shapes, made-up amounts,
made-up identifiers, made-up dates. No real personal data, no real account
numbers.

Ground truth (`expected_equal`) is SEMANTIC, judged before running any
matcher: "do these two strings denote the same entity / value?"

Conventions used to keep the labels unambiguous (this matters — a benchmark
whose truth is arguable only measures the author):
  - name        : person names (compared with Kind.NAME); labels follow the
    text rules below.
  - text, True  : same name/address/org, differing only in encoding (NFC/NFD),
    tone-mark position, whitespace, case — or a mechanical slip that does not
    produce another valid word (doubled letter, truncated final letter).
  - text, False : a different person / different address number / different
    legal form / a one-diacritic change where BOTH spellings are plausible
    names (Khánh vs Kháng). Document verification must re-check those, so the
    strict answer is "not equal".
  - money/date/id, True : same value or same entity after format differences.
  - money/date, False   : a different value — including inputs that are
    malformed or impossible (29/02/2025) where the library is expected to
    raise rather than answer.

This file only builds data; it never imports the library.

Run:  python3 bench/gen_pairs.py
"""

from __future__ import annotations

import json
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent

NBSP = "\u00a0"
ZWSP = "\u200b"


def nfd(s: str) -> str:
    """Decompose to NFD — what macOS writes into filenames."""
    return unicodedata.normalize("NFD", s)


# (a, b, kind, expected_equal, note)
PAIRS: list[tuple[str, str, str, bool, str]] = [
    # ================================================================== TEXT
    # -- same record, different encoding / typing -------------------------
    ("Nguyễn Thị Hòa", nfd("Nguyễn Thị Hòa"), "name", True,
     "NFC vs NFD: cùng tên, khác byte"),
    ("Đinh Tiên Hoàng", nfd("Đinh Tiên Hoàng"), "text", True,
     "NFD trên địa danh có ký tự Đ"),
    ("Hoà Văn Bình", "Hòa Văn Bình", "name", True,
     "vị trí dấu thanh oà/òa, âm tiết mở"),
    ("Thuỳ Dương", "Thùy Dương", "name", True,
     "uỳ/ùy, âm tiết mở"),
    ("Hoè Thị Lan", "Hòe Thị Lan", "name", True,
     "oè/òe, âm tiết mở"),
    ("Nguyễn Thị Hòa", "Nguyễn  Thị   Hòa", "name", True,
     "khoảng trắng thừa"),
    (f"Nguyễn{NBSP}Thị Hòa", "Nguyễn Thị Hòa", "name", True,
     "nbsp U+00A0 do Word/Excel chèn"),
    (f"Bùi Minh{ZWSP} Châu", "Bùi Minh Châu", "name", True,
     "zero-width space U+200B"),
    ("Nguyễn Thị Hòa", "nguyễn thị hòa", "name", True,
     "chỉ khác hoa/thường"),
    ("Vũ Hoàng Nam ", "Vũ Hoàng Nam", "name", True,
     "khoảng trắng cuối"),
    ("Lý\tThị\tMai", "Lý Thị Mai", "name", True,
     "tab thay dấu cách"),
    ("CÔNG TY TNHH THƯƠNG MẠI BÌNH AN",
     "Công ty TNHH Thương mại Bình An", "text", True,
     "tên tổ chức, chỉ khác hoa/thường"),
    ("Số 12 Ngõ 34 Phố Hoa Ban, Phường 5",
     "Số 12  Ngõ  34  Phố Hoa Ban,  Phường 5", "text", True,
     "địa chỉ, khoảng trắng thừa"),
    ("Xã Hoà Bình, Huyện Quỳnh Lưu", "Xã Hòa Bình, Huyện Quỳnh Lưu", "text", True,
     "hoà→hòa trong địa danh; quỳnh phải giữ nguyên"),
    # -- mechanical slips (không tạo ra từ khác) ---------------------------
    ("Trịnh Công Sơnn", "Trịnh Công Sơn", "name", True,
     "lặp 1 ký tự cuối (gõ/OCR)"),
    ("Lương Thị Ánh Tuyế", "Lương Thị Ánh Tuyết", "name", True,
     "nuốt ký tự cuối (OCR)"),
    ("Hoàng Văn Quag", "Hoàng Văn Quang", "name", True,
     "rơi 1 phụ âm cuối"),
    # -- different records -------------------------------------------------
    ("Nguyễn Thị Hòa", "Trần Văn Bình", "name", False,
     "hai người khác nhau"),
    ("Lê Văn Hoàn", "Lê Văn Hòa", "name", False,
     "âm tiết đóng 'hoàn' KHÔNG được đổi thành 'hòa' — hai từ khác nhau"),
    ("Phạm Quốc Khánh", "Phạm Quốc Kháng", "name", False,
     "lệch 1 dấu, mỗi dạng đều là tên hợp lệ → phải soát lại"),
    ("Phạm Minh Khôi", "Bùi Minh Khôi", "name", False,
     "họ khác — hai người, chuỗi gần như giống hệt"),
    ("Nguyễn Thị Hòa", "Nguyễn Thị Hồng", "name", False,
     "cùng họ + đệm, khác tên gọi"),
    ("Số 12 Ngõ 34 Phố Hoa Ban, Phường 5",
     "Số 21 Ngõ 34 Phố Hoa Ban, Phường 5", "text", False,
     "số nhà 12→21, phần còn lại giống hệt"),
    ("Công ty TNHH Bình Minh", "Công ty CP Bình Minh", "text", False,
     "khác loại hình doanh nghiệp = khác pháp nhân"),
    ("Phòng giao dịch Lê Chân", "Phòng giao dịch Hồng Bàng", "text", False,
     "cùng mẫu, khác địa danh"),
    ("Nguyễn Hoàng Nam", "Nguyễn Hoàng Ninh", "name", False,
     "tên gọi khác — hai người"),
    ("Trần Thị Bích Ngọc", "Trần Thị Bích Ngà", "name", False,
     "tên gọi khác — hai người"),
    ("Lê Quang Dũng", "Lê Quang Hùng", "name", False,
     "tên gọi khác — hai người"),
    ("Vũ Hoàng Nam", "Vũ Hoàng Nga", "name", False,
     "tên gọi khác — hai người"),
    ("Nguyễn Thị Thu Hà", "Nguyễn Thị Thu Hằng", "name", False,
     "tên gọi khác — hai người, chuỗi gần như giống hệt"),

    # ================================================================= MONEY
    # -- same value --------------------------------------------------------
    ("1.000.000đ", "1,000,000 VND", "money", True,
     "kiểu VN có 'đ' vs kiểu US có 'VND'"),
    ("2.500.000.000", "2,500,000,000", "money", True,
     "dấu phân nghìn VN vs US"),
    ("2.500.000.000", "2500000000", "money", True,
     "có phân cách vs số trơn"),
    ("2.500.000,50", "2,500,000.50", "money", True,
     "thập phân: phẩy VN vs chấm US"),
    ("1.250.000,50", "1.250.000,5", "money", True,
     "0,50 vs 0,5 — cùng giá trị"),
    ("5.000.000đ", "5.000.000 đồng", "money", True,
     "'đ' vs 'đồng'"),
    ("5.000.000₫", "5.000.000 VNĐ", "money", True,
     "'₫' vs 'VNĐ'"),
    ("0", "0đ", "money", True,
     "số 0 có/không hậu tố"),
    ("10.000.000", "10.000.000,00", "money", True,
     "phần thập phân bằng 0"),
    (" 1.000.000 ", "1,000,000", "money", True,
     "khoảng trắng hai đầu"),
    ("1.000.000", "1.000.000 vnđ", "money", True,
     "hậu tố chữ thường"),
    ("-2.000.000", "-2.000.000đ", "money", True,
     "số âm có hậu tố"),
    ("3.000.000", "3,000,000.00", "money", True,
     "US + thập phân .00"),
    ("100.000.000", "100000000", "money", True,
     "số trơn 9 chữ số"),
    ("7.000.000", "7.000.000 VND", "money", True,
     "một bên có hậu tố, một bên không"),
    # -- different value ---------------------------------------------------
    ("1.000.000", "1.000.001", "money", False,
     "lệch đúng 1 đồng"),
    ("2.500.000.000", "2.600.000.000", "money", False,
     "lệch 100 triệu, chuỗi vẫn rất giống"),
    ("50.000.000", "50,000,001", "money", False,
     "lệch 1 đồng"),
    ("100.000", "1.000.000", "money", False,
     "thiếu 1 số 0 = sai 10 lần"),
    ("1.000.000", "1.000.000.000", "money", False,
     "lệch 1000 lần, chỉ thêm 1 nhóm .000"),
    ("2.000.000", "-2.000.000", "money", False,
     "khác dấu = ghi có vs ghi nợ"),
    ("2.500", "2.500.000", "money", False,
     "kiểu VN: 2.500 = 2.500 đồng, không phải 2,5 triệu"),
    ("1.250.000,50", "1.250.000,55", "money", False,
     "lệch 5 xu"),
    ("999.999", "999.998", "money", False,
     "lệch 1 đồng"),
    # -- unparseable: kỳ vọng NÉM LỖI --------------------------------------
    ("12.000.000", "12.000.00", "money", False,
     "định dạng sai (nhóm 2 chữ số) — kỳ vọng ném lỗi, không âm thầm so chuỗi"),

    # ================================================================== DATE
    # -- same date ---------------------------------------------------------
    ("01/02/2026", "1-2-2026", "date", True,
     "thiếu số 0 + đổi dấu phân cách"),
    ("12/08/2026", "12-8-2026", "date", True,
     "DD/MM/YYYY vs D-M-YYYY"),
    ("12/08/2026", "2026-08-12", "date", True,
     "DD/MM/YYYY vs ISO YYYY-MM-DD"),
    ("2026-01-15", "15/01/2026", "date", True,
     "ISO vs DD/MM"),
    ("01.02.2026", "1.2.2026", "date", True,
     "dấu chấm + thiếu số 0"),
    ("01 02 2026", "01/02/2026", "date", True,
     "dấu cách vs dấu gạch chéo"),
    ("29/02/2024", "29-2-2024", "date", True,
     "29/02 năm nhuận hợp lệ"),
    ("15/07/2026", "15/7/2026 ", "date", True,
     "bỏ số 0 + khoảng trắng cuối"),
    ("15/07/2026", "15/ 07/2026", "date", True,
     "dấu cách sau gạch chéo"),
    ("31/12/2025", "31-12-2025", "date", True,
     "đổi dấu phân cách"),
    ("07/09/2026", "7/9/2026", "date", True,
     "thiếu số 0 hai vế"),
    # -- different date ----------------------------------------------------
    ("12/08/2026", "12/08/2025", "date", False,
     "lệch 1 năm"),
    ("01/02/2026", "02/01/2026", "date", False,
     "hoán vị ngày/tháng — cùng tập ký tự, khác ngày"),
    ("05/06/2026", "06/05/2026", "date", False,
     "hoán vị ngày/tháng, chuỗi khác đúng 2 ký tự"),
    ("10/10/2026", "10-11-2026", "date", False,
     "lệch 1 tháng, chuỗi khác 1 ký tự"),
    ("2026-01-15", "2026-01-16", "date", False,
     "lệch 1 ngày"),
    ("31/12/2025", "31/12/2024", "date", False,
     "lệch 1 năm"),
    ("30/06/2026", "30/07/2026", "date", False,
     "lệch 1 tháng"),
    ("08/03/2026", "09/03/2026", "date", False,
     "lệch 1 ngày"),
    # -- impossible date: kỳ vọng NÉM LỖI ----------------------------------
    ("29/02/2025", "29-2-2025", "date", False,
     "ngày không tồn tại (2025 không nhuận) — kỳ vọng ném lỗi"),

    # ==================================================================== ID
    # -- same identifier ---------------------------------------------------
    ("031234567890", "0312 3456 7890", "id", True,
     "chỉ khác khoảng trắng"),
    ("031234567890", "0312-3456-7890", "id", True,
     "gạch nối nhóm 4"),
    ("031234567890", "031 2345 67890", "id", True,
     "nhóm 3 chữ số"),
    ("031234567890", "0312–3456–7890", "id", True,
     "en dash thay gạch nối"),
    (" 031234567890 ", "031234567890", "id", True,
     "khoảng trắng đầu/cuối"),
    ("031234567890\n", "031234567890", "id", True,
     "xuống dòng cuối"),
    ("031234567890", "0312\t3456\t7890", "id", True,
     "tab thay khoảng trắng"),
    ("KH-2026-001", "kh 2026 001", "id", True,
     "gạch nối + hoa/thường"),
    ("HD-2026-0457", "HD20260457", "id", True,
     "bỏ hết dấu phân cách"),
    ("STK-1234567890", "STK 1234 5678 90", "id", True,
     "nhóm số + dấu phân cách"),
    ("AB-12-CD", "ab12cd", "id", True,
     "mã chữ + số, khác case và gạch nối"),
    ("001234567890", "0012 3456 7890", "id", True,
     "số 0 đứng trước được giữ"),
    # -- different identifier ----------------------------------------------
    ("031234567890", "031234567891", "id", False,
     "CCCD lệch đúng 1 số cuối — hai người"),
    ("031234567890", "03123456789O", "id", False,
     "chữ O thay số 0 — lỗi OCR kinh điển"),
    ("031234567890", "031234567980", "id", False,
     "đảo 2 chữ số — cùng độ dài"),
    ("0312345678901", "031234567890", "id", False,
     "lệch độ dài (thêm 1 chữ số)"),
    ("001099012345", "001099012346", "id", False,
     "lệch 1 số cuối"),
    ("0001234567", "1234567", "id", False,
     "số 0 đầu có nghĩa, không được bỏ"),
    ("KH-2026-001", "KH-2026-002", "id", False,
     "lệch 1 số"),
    ("HD-2026-0457", "HD-2026-0458", "id", False,
     "lệch 1 số"),
    ("AB-12-CD", "AB-12-CE", "id", False,
     "lệch 1 ký tự mã"),
    ("MST 0101234567", "0101234567", "id", False,
     "nhãn 'MST' chỉ có ở một bên — thư viện không bỏ nhãn (hạn chế đã biết)"),
    ("031234567890", "031234561290", "id", False,
     "lệch 2 chữ số ở giữa"),
    ("012345678901", "012345678900", "id", False,
     "lệch 1 số cuối"),
    ("031234567890", "041234567890", "id", False,
     "lệch chữ số đầu"),
]

KINDS = ("money", "date", "id", "name", "text")
EXPECTED_TOTAL = 100


def main() -> None:
    assert len(PAIRS) == EXPECTED_TOTAL, f"expected {EXPECTED_TOTAL} pairs, got {len(PAIRS)}"
    for a, b, kind, expected, note in PAIRS:
        assert kind in KINDS, kind
        assert isinstance(expected, bool), (a, b)
        assert a and b and note, (a, b)
        assert a != b, f"identical pair tests nothing: {a!r}"
        assert "|" not in note and "\n" not in note, note

    # The encoding traps only test something if the raw strings really differ
    # while being equal once composed.
    for a, b, *_ in PAIRS:
        for raw, composed in ((a, b), (b, a)):
            if unicodedata.normalize("NFC", raw) == unicodedata.normalize("NFC", composed):
                assert raw != composed, f"NFC-equal pair collapsed at source: {a!r} / {b!r}"

    out = HERE / "pairs.jsonl"
    with out.open("w", encoding="utf-8") as fh:
        for a, b, kind, expected, note in PAIRS:
            fh.write(
                json.dumps(
                    {"a": a, "b": b, "kind": kind, "expected_equal": expected, "note": note},
                    ensure_ascii=False,
                )
                + "\n"
            )

    eq = sum(1 for p in PAIRS if p[3])
    print(f"wrote {out} — {len(PAIRS)} pairs, {eq} equal / {len(PAIRS) - eq} unequal")
    for kind in KINDS:
        sub = [p for p in PAIRS if p[2] == kind]
        print(f"  {kind:6s} {len(sub):3d}  (equal={sum(1 for p in sub if p[3])})")


if __name__ == "__main__":
    main()
