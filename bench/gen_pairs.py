#!/usr/bin/env python3
"""Generate bench/pairs.jsonl — fabricated Vietnamese comparison pairs.

All strings are invented (fake names, fake amounts, fake IDs). No real
personal data, no real account numbers.

Ground truth is SEMANTIC, not "what the library says":
  expected_equal = "these two strings denote the same entity/value"

That means a pair like "Phạm Quốc Khánh" vs "Phạm Quốc Kháng" is
expected_equal=False even though every fuzzy matcher scores it >0.95 —
they are two different people who happen to differ by one character.
This is the whole point of the benchmark.

Run:  python3 bench/gen_pairs.py
"""

from __future__ import annotations

import json
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent


def nfd(s: str) -> str:
    """Decompose to NFD (what macOS writes to filenames)."""
    return unicodedata.normalize("NFD", s)


NBSP = "\u00a0"
ZWSP = "\u200b"

# (a, b, kind, expected_equal, note)
PAIRS: list[tuple[str, str, str, bool, str]] = [
    # ------------------------------------------------------------------ TEXT
    ("Nguyễn Thị Hòa", nfd("Nguyễn Thị Hòa"), "text", True,
     "NFC vs NFD, cùng một tên — bẫy byte, không phải bẫy nghĩa"),
    ("Hoà Văn Bình", "Hòa Văn Bình", "text", True,
     "vị trí dấu thanh oà / òa, âm tiết mở"),
    ("Thuỳ Dương", "Thùy Dương", "text", True,
     "uỳ / ùy, âm tiết mở"),
    ("Hoè Thị Lan", "Hòe Thị Lan", "text", True,
     "oè / òe, âm tiết mở"),
    ("Nguyễn Thị Hòa", "Nguyễn  Thị   Hòa", "text", True,
     "khoảng trắng thừa"),
    ("Nguyễn Thị Hòa", f"Nguyễn{NBSP}Thị Hòa", "text", True,
     "nbsp U+00A0 do Word/Excel chèn"),
    ("Nguyễn Thị Hòa", "nguyễn thị hòa", "text", True,
     "khác hoa/thường"),
    ("Nguyễn Thị Hòa", "Nguyễn Thị Hoa", "text", True,
     "thiếu dấu hỏi — lỗi gõ, vẫn cùng người"),
    ("Trần Văn Bình", "Trần Văn Binh", "text", True,
     "mất dấu toàn bộ âm tiết cuối — lỗi OCR/gõ"),
    ("Ngô Thị Kim Ngân", "Ngô Thị Kim Ngan", "text", True,
     "mất dấu 'â' ở tên đệm cuối"),
    ("Bùi Minh Châu", f"Bùi Minh{ZWSP} Châu", "text", True,
     "zero-width space U+200B"),
    ("Vũ Hoàng Nam", "Vũ Hoàng Nam ", "text", True,
     "khoảng trắng cuối"),
    ("Phòng giao dịch Lê Chân", "Phòng Giao Dịch Lê Chân", "text", True,
     "khác hoa/thường từng từ"),
    ("PGBank Hải Phòng", "PG Bank Hải Phòng", "text", True,
     "khoảng trắng trong tên thương hiệu"),
    ("Trường THPT Nguyễn Trãi", "Trường THPT Nguyễn Trải", "text", True,
     "lỗi gõ 1 ký tự trong tên trường"),
    ("Nguyễn Thị Hòa", "Trần Văn Bình", "text", False,
     "hai người khác nhau hoàn toàn"),
    ("Lê Văn Hoàn", "Lê Văn Hòa", "text", False,
     "âm tiết đóng 'hoàn' không được phép đổi thành 'hòa'"),
    ("Phòng giao dịch Lê Chân", "Phòng giao dịch Hồng Bàng", "text", False,
     "cùng mẫu, khác địa danh"),
    ("Công ty TNHH Bình Minh", "Công ty CP Bình Minh", "text", False,
     "khác loại hình doanh nghiệp = khác pháp nhân"),
    ("Phạm Quốc Khánh", "Phạm Quốc Kháng", "text", False,
     "lệch 1 dấu = 2 người khác nhau (ratio rất cao)"),
    ("Nguyễn Văn An", "Nguyễn Văn Ân", "text", False,
     "lệch 1 dấu mũ = 2 người khác nhau"),
    ("Lý Thị Hương", "Lý Thị Hường", "text", False,
     "lệch 1 dấu huyền = 2 người khác nhau"),
    ("Nguyễn Thị Hòa", "Nguyễn Thị Hồng", "text", False,
     "cùng họ + đệm, khác tên gọi"),
    ("Số 12 phố Lạch Tray", "So 12 pho Lach Tray", "text", True,
     "mất toàn bộ dấu — cùng địa chỉ, OCR bỏ dấu"),
    ("Đinh Tiên Hoàng", nfd("Đinh Tiên Hoàng"), "text", True,
     "NFD trên chuỗi địa chỉ"),
    ("Lương Văn Tuấn", "Lương Văn Tuấn", "text", True,
     "giống hệt — kiểm tra dương tính giả"),
    ("Nguyễn Thị Hòa", "Nguyễn Thị Hòaa", "text", True,
     "khoảng trắng/ký tự lặp do gõ"),
    ("Hoàng Thị Thu Hà", "Hoàng Thị Thu Hà", "text", True,
     "giống hệt"),
    ("Trịnh Công Sơn", "Trịnh Công Sơnn", "text", True,
     "lặp 1 ký tự cuối"),
    ("Đỗ Thị Mai Anh", "Đỗ Thị Mai An", "text", False,
     "rơi mất chữ cuối = khác tên"),

    # ----------------------------------------------------------------- MONEY
    ("1.000.000đ", "1,000,000 VND", "money", True,
     "VN có hậu tố vs US không hậu tố — cùng 1 triệu"),
    ("2.500.000.000", "2,500,000,000", "money", True,
     "dấu nghìn VN vs US"),
    ("2.500.000.000", "2.600.000.000", "money", False,
     "lệch 100 triệu, ratio vẫn rất cao"),
    ("2.500.000.000", "2500000000", "money", True,
     "không phân cách"),
    ("1.000.000", "1.000.001", "money", False,
     "lệch đúng 1 chữ số = lệch 1 đồng, vẫn là SAI"),
    ("5.000.000đ", "5.000.000 đồng", "money", True,
     "ký hiệu 'đ' vs 'đồng'"),
    ("5.000.000₫", "5.000.000 VNĐ", "money", True,
     "₫ vs VNĐ"),
    ("1.250.000,50", "1,250,000.50", "money", True,
     "thập phân: phẩy VN vs chấm US"),
    ("1.250.000,50", "1.250.000,5", "money", True,
     "0,50 vs 0,5 — cùng giá trị"),
    ("1.250.000,50", "1.250.000,55", "money", False,
     "lệch 5 xu"),
    ("0", "0đ", "money", True,
     "số 0 có/không hậu tố"),
    ("10.000.000", "10.000.000,00", "money", True,
     "phần thập phân bằng 0"),
    ("100.000", "1.000.000", "money", False,
     "thiếu 1 số 0 = sai 10 lần"),
    ("50.000.000", "50,000,001", "money", False,
     "lệch 1 đồng"),
    ("1.000.000", "1.000.000.000", "money", False,
     "lệch 1000 lần"),
    ("-2.000.000", "-2.000.000đ", "money", True,
     "số âm có hậu tố"),
    ("2.000.000", "-2.000.000", "money", False,
     "khác dấu = ghi có vs ghi nợ"),
    ("1.000.000", "1.000.000đ ", "money", True,
     "khoảng trắng sau hậu tố"),
    (" 1.000.000 ", "1,000,000", "money", True,
     "khoảng trắng hai đầu"),
    ("2.500", "2.500.000", "money", False,
     "2.500 đọc kiểu VN = 2.500 đồng, không phải 2,5 triệu"),
    ("999.999", "999.998", "money", False,
     "lệch 1 đồng"),
    ("1.000.000", "1.000.000 vnđ", "money", True,
     "hậu tố chữ thường"),
    ("3.000.000", "3,000,000.00", "money", True,
     "US + thập phân .00"),
    ("7.500.000", "7.500.000 ", "money", True,
     "khoảng trắng cuối"),
    ("12.000.000", "12.000.00", "money", False,
     "định dạng sai — kỳ vọng ném lỗi, không âm thầm so chuỗi"),
    ("2.000.000,0", "2.000.000", "money", True,
     "đuôi ,0"),
    ("150.000.000", "150.000,000", "money", False,
     "bẫy phẩy thập phân: 150.000,000 = 150.000 đồng, không phải 150 triệu"),
    ("4.500.000", "4.500.001", "money", False,
     "lệch 1 đồng"),

    # ------------------------------------------------------------------ DATE
    ("01/02/2026", "1-2-2026", "date", True,
     "thiếu số 0 + đổi dấu phân cách"),
    ("12/08/2026", "12-8-2026", "date", True,
     "DD/MM/YYYY vs D-M-YYYY"),
    ("12/08/2026", "2026-08-12", "date", True,
     "DD/MM/YYYY vs ISO YYYY-MM-DD"),
    ("2026-01-15", "15/01/2026", "date", True,
     "ISO vs DD/MM"),
    ("12/08/2026", "12/08/2025", "date", False,
     "lệch 1 năm"),
    ("05/06/2026", "05/06/2027", "date", False,
     "lệch 1 năm, chuỗi chỉ khác 1 ký tự — bẫy ngưỡng 0.9"),
    ("10/10/2026", "10-11-2026", "date", False,
     "lệch 1 tháng, chuỗi chỉ khác 1 ký tự"),
    ("01/02/2026", "02/01/2026", "date", False,
     "hoán vị ngày/tháng — cùng tập ký tự, khác ngày"),
    ("1/2/2026", "01/02/2026", "date", True,
     "thiếu số 0 hai vế"),
    ("31/12/2025", "31-12-2025", "date", True,
     "đổi dấu phân cách"),
    ("31/12/2025", "31/12/2024", "date", False,
     "lệch 1 năm"),
    ("2026-01-15", "2026-01-16", "date", False,
     "lệch 1 ngày"),
    ("01.02.2026", "1.2.2026", "date", True,
     "dấu chấm + thiếu số 0"),
    ("01 02 2026", "01/02/2026", "date", True,
     "dấu cách vs dấu gạch chéo"),
    ("29/02/2024", "29-2-2024", "date", True,
     "năm nhuận hợp lệ"),
    ("29/02/2025", "29/02/2025", "date", False,
     "ngày không tồn tại — kỳ vọng ném lỗi, không âm thầm 'bằng'"),
    ("15/07/2026", "15/7/2026 ", "date", True,
     "khoảng trắng cuối"),
    ("15/07/2026", "15/ 07/2026", "date", True,
     "dấu cách sau gạch chéo"),
    ("08/03/2026", "09/03/2026", "date", False,
     "lệch 1 ngày"),
    ("20/11/2026", "20/11/2026", "date", True,
     "giống hệt"),
    ("30/06/2026", "30/07/2026", "date", False,
     "lệch 1 tháng"),
    ("07/09/2026", "7/9/2026", "date", True,
     "thiếu số 0 hai vế"),

    # -------------------------------------------------------------------- ID
    ("031234567890", "0312 3456 7890", "id", True,
     "chỉ khác khoảng trắng"),
    ("031234567890", "031234567891", "id", False,
     "lệch 1 số = 2 người, ratio ~0.92"),
    ("031234567890", "0312-3456-7890", "id", True,
     "gạch nối"),
    ("031234567890", "031 2345 67890", "id", True,
     "nhóm 3 chữ số"),
    ("031234567890 ", "031234567890", "id", True,
     "khoảng trắng cuối"),
    ("031234567890", "03123456789O", "id", False,
     "chữ O thay số 0 — lỗi OCR kinh điển, ratio ~0.92"),
    ("001099012345", "001099012346", "id", False,
     "lệch 1 số cuối"),
    ("0312345678901", "031234567890", "id", False,
     "lệch độ dài"),
    ("0001234567", "1234567", "id", False,
     "số 0 đầu có nghĩa, không được bỏ"),
    ("KH-2026-001", "kh 2026 001", "id", True,
     "gạch nối + hoa/thường"),
    ("KH-2026-001", "KH-2026-002", "id", False,
     "lệch 1 số"),
    ("KH2026 01", "kh2026-01", "id", True,
     "khoảng trắng vs gạch nối"),
    ("HD-2026-0457", "HD20260457", "id", True,
     "bỏ hết dấu phân cách vẫn cùng số"),
    ("HD-2026-0457", "HD-2026-0458", "id", False,
     "lệch 1 số"),
    ("STK-1234567890", "STK 1234 5678 90", "id", True,
     "nhóm số + dấu phân cách"),
    ("1234567890", "1234567891", "id", False,
     "lệch 1 số"),
    ("AB-12-CD", "ab12cd", "id", True,
     "mã chữ + số, khác hoa/thường và gạch nối"),
    ("AB-12-CD", "AB-12-CE", "id", False,
     "lệch 1 ký tự mã"),
    ("MST 0101234567", "0101234567", "id", False,
     "nhãn 'MST' dính vào mã — thư viện không bỏ nhãn (hạn chế đã biết)"),
    ("031234567890", "031234567890\n", "id", True,
     "xuống dòng cuối"),
    ("CC-2026-77", "CC 2026 77", "id", True,
     "dấu phân cách"),
    ("CC-2026-77", "cc-2026-71", "id", False,
     "lệch 1 số"),
]

KINDS = ("money", "date", "text", "id")


def main() -> None:
    assert all(len(p) == 5 for p in PAIRS)
    bad = [p for p in PAIRS if p[2] not in KINDS]
    assert not bad, bad

    out = HERE / "pairs.jsonl"
    with out.open("w", encoding="utf-8") as fh:
        for a, b, kind, expected, note in PAIRS:
            fh.write(
                json.dumps(
                    {"a": a, "b": b, "kind": kind, "expected_equal": expected, "note": note},
                    ensure_ascii=True,
                )
                + "\n"
            )

    counts: dict[str, int] = {}
    for _, _, kind, expected, _ in PAIRS:
        counts[kind] = counts.get(kind, 0) + 1
    eq = sum(1 for p in PAIRS if p[3])
    print(f"wrote {out} — {len(PAIRS)} pairs, {eq} equal / {len(PAIRS) - eq} unequal")
    for kind in KINDS:
        sub = [p for p in PAIRS if p[2] == kind]
        print(f"  {kind:6s} {len(sub):3d}  (equal={sum(1 for p in sub if p[3])})")


if __name__ == "__main__":
    main()
