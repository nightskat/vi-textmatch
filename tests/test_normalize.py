"""Unit tests for vi_textmatch.normalize and tone normalization steps."""

import sys
import unicodedata
import unittest
from pathlib import Path

# Add src to sys.path if running tests directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from vi_textmatch.compare import Kind, compare
from vi_textmatch.normalize import (
    normalize,
    normalize_case,
    normalize_tone,
    normalize_unicode,
    normalize_whitespace,
)


class TestNormalize(unittest.TestCase):
    """Test cases for 4-step normalization functions."""

    def test_step1_normalize_unicode(self) -> None:
        """Step 1: Converts NFD decomposed text to NFC precomposed form."""
        nfd_str = unicodedata.normalize("NFD", "Nguyễn Thị Hòa")
        nfc_str = normalize_unicode(nfd_str)
        self.assertEqual(nfc_str, "Nguyễn Thị Hòa")
        self.assertEqual(unicodedata.is_normalized("NFC", nfc_str), True)

    def test_step2_normalize_tone(self) -> None:
        """Step 2: Normalizes second-vowel tone marks to first-vowel placement."""
        self.assertEqual(normalize_tone("hoà"), "hòa")
        self.assertEqual(normalize_tone("hoá"), "hóa")
        self.assertEqual(normalize_tone("hoè"), "hòe")
        self.assertEqual(normalize_tone("huỳ"), "hùy")
        # Protection rule for 'qu' initial consonant
        self.assertEqual(normalize_tone("quý"), "quý")
        self.assertEqual(normalize_tone("quỳ"), "quỳ")
        self.assertEqual(normalize_tone("quỷ"), "quỷ")

    def test_step3_normalize_whitespace(self) -> None:
        """Step 3: Strips U+00A0 (NBSP), U+200B, collapses spaces and trims."""
        raw = "  Nguyễn  Thị\u00a0Hòa\u200b  "
        cleaned = normalize_whitespace(raw)
        self.assertEqual(cleaned, "Nguyễn Thị Hòa")

    def test_step4_normalize_case(self) -> None:
        """Step 4: Converts text to casefolded representation."""
        self.assertEqual(normalize_case("NGUYỄN THỊ HÒA"), "nguyễn thị hòa")

    def test_full_normalize(self) -> None:
        """Full 4-step normalization pipeline integration."""
        nfd_raw = unicodedata.normalize("NFD", "  NGUYỄN  THỊ\u00a0HOÀ\u200b  ")
        expected = "nguyễn thị hòa"
        self.assertEqual(normalize(nfd_raw), expected)


class TestTonePlacementRules(unittest.TestCase):
    """Tone placement rules from research/QUY-TAC.md (open vs closed syllables)."""

    def test_closed_syllables_kept(self) -> None:
        """Closed syllables (a consonant/vowel follows oa/oe/uy) are never rewritten."""
        for word in ["hoàn", "suýt", "huỳnh", "khuỷu", "khuỵu", "nguýt", "huých",
                     "khoét", "tuýt", "khuỳnh"]:
            self.assertEqual(normalize(word), word, word)

    def test_preaccented_vowels_kept(self) -> None:
        """Rhymes with ê/ô/ơ/ă/â/ư already carry the tone in the right place."""
        for word in ["huệ", "thuở", "chuồn", "thuyền", "giường", "mượn"]:
            self.assertEqual(normalize(word), word, word)

    def test_qu_gi_clusters_kept(self) -> None:
        """'qu' and 'gi' initial clusters must never be rewritten."""
        for word in ["quý", "quỳnh", "quán", "quốc", "già", "gió", "giữ"]:
            self.assertEqual(normalize(word), word, word)

    def test_open_syllables_normalize_to_same_form(self) -> None:
        """Open syllables: second-vowel form and first-vowel form are equivalent."""
        pairs = [("hoà", "hòa"), ("hoá", "hóa"), ("hoè", "hòe"),
                 ("thuỷ", "thủy"), ("huỷ", "hủy"), ("tuý", "túy")]
        for second_vowel, first_vowel in pairs:
            self.assertEqual(
                normalize(second_vowel), normalize(first_vowel), second_vowel
            )

    def test_proper_names_kept(self) -> None:
        """Real person names keep their correct spelling after normalization."""
        for name in ["Huỳnh Văn Lương", "Phạm Thị Hoài", "Lê Hoàn",
                     "Trần Khoản", "Võ Khoảng"]:
            self.assertEqual(normalize(name), name.casefold(), name)

    def test_no_false_match_closed_vs_short(self) -> None:
        """Closed syllables must not collapse into unrelated words."""
        verdict = compare("suýt", "sút", kind=Kind.TEXT)
        self.assertFalse(verdict.match)
        self.assertEqual(verdict.level, "DIFFERENT")

        verdict = compare("hoàn", "hòn", kind=Kind.TEXT)
        self.assertFalse(verdict.match)
        self.assertEqual(verdict.level, "DIFFERENT")

    def test_mixed_case_pair_identical(self) -> None:
        """Mixed-case second-vowel forms (e.g. 'HoÀ') normalize identically."""
        verdict = compare("HoÀ", "HOÀ", kind=Kind.TEXT)
        self.assertTrue(verdict.match)
        self.assertEqual(verdict.level, "IDENTICAL")


if __name__ == "__main__":
    unittest.main()


class TestZeroWidthBeforeTone(unittest.TestCase):
    """Regression (hypothesis): ZWSP inside 'oa' must not break idempotence."""

    def test_zwsp_inside_pair(self) -> None:
        from vi_textmatch import normalize

        self.assertEqual(normalize("Ho​à"), "hòa")
        self.assertEqual(normalize(normalize("O​À")), normalize("O​À"))
