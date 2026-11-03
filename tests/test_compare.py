"""Unit tests covering all 12 SPEC acceptance criteria and utility functions."""

import sys
import unicodedata
import unittest
from pathlib import Path

# Add src to sys.path if running tests directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from vi_textmatch import Kind, closest, compare, explain


class TestCompareAcceptance(unittest.TestCase):
    """Test suite for the 12 acceptance criteria specified in SPEC v0.1."""

    def test_case_01_nfd_vs_nfc(self) -> None:
        """1. NFD vs NFC cùng một tên -> IDENTICAL"""
        name_nfd = unicodedata.normalize("NFD", "Nguyễn Thị Hòa")
        name_nfc = unicodedata.normalize("NFC", "Nguyễn Thị Hòa")
        verdict = compare(name_nfd, name_nfc, kind=Kind.TEXT)
        self.assertTrue(verdict.match)
        self.assertEqual(verdict.level, "IDENTICAL")

    def test_case_02_tone_mark_placement(self) -> None:
        """2. hoà vs hòa -> IDENTICAL"""
        verdict = compare("hoà", "hòa", kind=Kind.TEXT)
        self.assertTrue(verdict.match)
        self.assertEqual(verdict.level, "IDENTICAL")

    def test_case_03_case_difference(self) -> None:
        """3. Nguyễn Thị Hòa vs nguyễn thị hòa -> IDENTICAL"""
        verdict = compare("Nguyễn Thị Hòa", "nguyễn thị hòa", kind=Kind.TEXT)
        self.assertTrue(verdict.match)
        self.assertEqual(verdict.level, "IDENTICAL")

    def test_case_04_nbsp_and_double_spaces(self) -> None:
        """4. Tên có nbsp/trắng đôi -> IDENTICAL"""
        a = "Nguyễn  Thị\u00a0Hòa"
        b = "Nguyễn Thị Hòa"
        verdict = compare(a, b, kind=Kind.TEXT)
        self.assertTrue(verdict.match)
        self.assertEqual(verdict.level, "IDENTICAL")

    def test_case_05_single_character_typo(self) -> None:
        """5. Nguyễn Thị Hòa vs Nguyễn Thị Hoa -> TYPO"""
        verdict = compare("Nguyễn Thị Hòa", "Nguyễn Thị Hoa", kind=Kind.TEXT)
        self.assertTrue(verdict.match)
        self.assertEqual(verdict.level, "TYPO")

    def test_case_06_completely_different_name(self) -> None:
        """6. Nguyễn Thị Hòa vs Trần Văn Bình -> DIFFERENT"""
        verdict = compare("Nguyễn Thị Hòa", "Trần Văn Bình", kind=Kind.TEXT)
        self.assertFalse(verdict.match)
        self.assertEqual(verdict.level, "DIFFERENT")

    def test_case_07_id_spaces_hyphens(self) -> None:
        """7. ID: 0312 3456 7890 vs 031234567890 -> match"""
        verdict = compare("0312 3456 7890", "031234567890", kind=Kind.ID)
        self.assertTrue(verdict.match)
        self.assertEqual(verdict.level, "IDENTICAL")

    def test_case_08_id_single_digit_difference(self) -> None:
        """8. ID: 031234567890 vs 031234567891 -> KHÔNG match"""
        verdict = compare("031234567890", "031234567891", kind=Kind.ID)
        self.assertFalse(verdict.match)
        self.assertEqual(verdict.level, "DIFFERENT")

    def test_case_09_money_format_variations(self) -> None:
        """9. MONEY: 2.500.000.000 vs 2,500,000,000 vs 2500000000 -> match"""
        v1 = compare("2.500.000.000", "2,500,000,000", kind=Kind.MONEY)
        v2 = compare("2.500.000.000", "2500000000", kind=Kind.MONEY)
        self.assertTrue(v1.match)
        self.assertEqual(v1.level, "IDENTICAL")
        self.assertTrue(v2.match)
        self.assertEqual(v2.level, "IDENTICAL")

    def test_case_10_money_different_amounts(self) -> None:
        """10. MONEY: 2.500.000.000 vs 2.600.000.000 -> KHÔNG match"""
        verdict = compare("2.500.000.000", "2.600.000.000", kind=Kind.MONEY)
        self.assertFalse(verdict.match)
        self.assertEqual(verdict.level, "DIFFERENT")

    def test_case_11_date_format_variations(self) -> None:
        """11. DATE: 12/08/2026 vs 12-8-2026 -> match"""
        # 12/08 is ambiguous (Aug 12 or Dec 8): refuse to guess by default.
        verdict = compare("12/08/2026", "12-8-2026", kind=Kind.DATE)
        self.assertFalse(verdict.match)
        self.assertEqual(verdict.level, "AMBIGUOUS")
        verdict = compare("12/08/2026", "12-8-2026", kind=Kind.DATE, day_first=True)
        self.assertTrue(verdict.match)
        self.assertEqual(verdict.level, "IDENTICAL")

    def test_case_12_money_unparseable_raises_error(self) -> None:
        """12. MONEY với chuỗi không ép được kiểu -> ném lỗi, không âm thầm so chuỗi"""
        with self.assertRaises(ValueError):
            compare("2.500.000.000", "invalid_amount_xyz", kind=Kind.MONEY)
        with self.assertRaises(ValueError):
            compare("abc", "1000", kind=Kind.MONEY)
        # Also verify DATE unparseable error
        with self.assertRaises(ValueError):
            compare("12/08/2026", "invalid_date_abc", kind=Kind.DATE)


class TestCompareSignatureAndErrors(unittest.TestCase):
    """Tests for the strict compare() signature and static error messages."""

    def test_compare_requires_keyword_only_kind(self) -> None:
        """compare() requires keyword-only kind; omitting it raises TypeError."""
        with self.assertRaises(TypeError):
            compare("abc", "abc")

    def test_compare_rejects_plain_str_kind(self) -> None:
        """compare() only accepts Kind; a raw str kind raises ValueError."""
        with self.assertRaises(ValueError):
            compare("payload-A", "payload-B", kind="payload-A")

    def test_kind_error_message_is_static(self) -> None:
        """Invalid-kind error must not embed the caller-supplied value."""
        with self.assertRaises(ValueError) as ctx:
            compare("payload-A", "payload-B", kind="payload-A")
        self.assertEqual(str(ctx.exception), "Invalid comparison kind")
        self.assertNotIn("payload-A", str(ctx.exception))

    def test_money_rejects_letters_around_digits(self) -> None:
        """MONEY must reject 'abc1000' instead of silently parsing digits."""
        with self.assertRaises(ValueError):
            compare("abc1000", "1000", kind=Kind.MONEY)

    def test_money_rejects_double_separator(self) -> None:
        """MONEY must reject '1..000' (invalid separator structure)."""
        with self.assertRaises(ValueError):
            compare("1..000", "1000", kind=Kind.MONEY)

    def test_money_error_message_is_static(self) -> None:
        """MONEY parse errors must not embed the input string."""
        with self.assertRaises(ValueError) as ctx:
            compare("abc1000", "1000", kind=Kind.MONEY)
        self.assertNotIn("abc1000", str(ctx.exception))

    def test_date_rejects_two_digit_year(self) -> None:
        """DATE must reject two-digit years like '12/08/26'."""
        with self.assertRaises(ValueError):
            compare("12/08/26", "12/08/2026", kind=Kind.DATE)


class TestCompareIdHyphens(unittest.TestCase):
    """Tests for hyphen handling in ID comparison."""

    def test_id_hyphens_ignored(self) -> None:
        """ID: hyphen, en-dash and em-dash separators are ignored."""
        for spaced in ("0312-3456-7890", "0312–3456–7890", "0312—3456—7890"):
            verdict = compare(spaced, "031234567890", kind=Kind.ID)
            self.assertTrue(verdict.match)
            self.assertEqual(verdict.level, "IDENTICAL")

    def test_id_dots_ignored(self) -> None:
        """ID: dot separators are ignored (0312.345.678 == 0312345678)."""
        for dotted in ("0312.345.678", "0312. 345 .678", "0312.345-678"):
            verdict = compare(dotted, "0312345678", kind=Kind.ID)
            self.assertTrue(verdict.match, dotted)
            self.assertEqual(verdict.level, "IDENTICAL")

    def test_id_dots_do_not_hide_digit_difference(self) -> None:
        """ID: stripping dots must not make different digits match."""
        verdict = compare("0312.345.678", "0312345679", kind=Kind.ID)
        self.assertFalse(verdict.match)

    def test_id_underscore_not_stripped(self) -> None:
        """ID: '_' looks like a separator but must NOT be ignored."""
        verdict = compare("0312_3456_7890", "031234567890", kind=Kind.ID)
        self.assertFalse(verdict.match)
        self.assertEqual(verdict.level, "DIFFERENT")


class TestUtilities(unittest.TestCase):
    """Test suite for explain and closest utility functions."""

    def test_explain(self) -> None:
        """Verify explain returns character difference output."""
        result = explain("Nguyễn Thị Hòa", "Nguyễn Thị Hoa")
        self.assertIsInstance(result, str)
        self.assertIn("ò", result)

    def test_closest(self) -> None:
        """Verify closest matching candidates using normalized matching."""
        candidates = ["Trần Văn Bình", "Nguyễn Thị Hoa", "Lê Văn Cường"]
        matches = closest("Nguyễn Thị Hòa", candidates, n=2)
        self.assertIn("Nguyễn Thị Hoa", matches)



class TestCompareMoneyCurrency(unittest.TestCase):
    """MONEY: explicit, different currencies never match."""

    def test_different_currencies_differ(self) -> None:
        for a, b in (("100$", "100€"), ("100$", "100đ"), ("¥100", "100 VND")):
            verdict = compare(a, b, kind=Kind.MONEY)
            self.assertFalse(verdict.match, (a, b))
            self.assertEqual(verdict.level, "DIFFERENT")
            self.assertIn("Currencies differ", verdict.detail)

    def test_same_currency_aliases_match(self) -> None:
        for a, b in (("100đ", "100 VND"), ("100₫", "100 đồng"), ("VNĐ 100", "100đ")):
            self.assertTrue(compare(a, b, kind=Kind.MONEY).match, (a, b))

    def test_missing_marker_stays_compatible(self) -> None:
        self.assertTrue(compare("100", "100$", kind=Kind.MONEY).match)


class TestCompareDateAmbiguous(unittest.TestCase):
    """DATE: ambiguous day/month order must not be guessed."""

    def test_ambiguous_without_day_first(self) -> None:
        verdict = compare("02/01/2026", "2026-01-02", kind=Kind.DATE)
        self.assertFalse(verdict.match)
        self.assertEqual(verdict.level, "AMBIGUOUS")

    def test_day_first_true(self) -> None:
        self.assertTrue(
            compare("02/01/2026", "2026-01-02", kind=Kind.DATE, day_first=True).match
        )

    def test_day_first_false(self) -> None:
        self.assertTrue(
            compare("02/01/2026", "2026-02-01", kind=Kind.DATE, day_first=False).match
        )
        self.assertFalse(
            compare("02/01/2026", "2026-01-02", kind=Kind.DATE, day_first=False).match
        )

    def test_unambiguous_unchanged(self) -> None:
        # first part > 12 -> must be the day; ISO is never ambiguous
        self.assertEqual(compare("25/12/2026", "2026-12-25", kind=Kind.DATE).level, "IDENTICAL")
        self.assertEqual(compare("2026-01-02", "2026-01-02", kind=Kind.DATE).level, "IDENTICAL")
        # day == month reads the same either way
        self.assertEqual(compare("05/05/2026", "2026-05-05", kind=Kind.DATE).level, "IDENTICAL")
        # day_first does not change unambiguous strings
        self.assertTrue(
            compare("25/12/2026", "2026-12-25", kind=Kind.DATE, day_first=False).match
        )
        with self.assertRaises(ValueError):
            compare("01/13/2026", "2026-01-13", kind=Kind.DATE)


if __name__ == "__main__":
    unittest.main()
