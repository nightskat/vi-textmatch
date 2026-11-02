"""Property-based tests (hypothesis) for tone normalization and compare().

hypothesis is a dev-only dependency; the module is skipped without it.
"""

import unittest

try:
    from hypothesis import example, given, settings
    from hypothesis import strategies as st
except ImportError as exc:  # pragma: no cover - dev dependency missing
    raise unittest.SkipTest("hypothesis not installed") from exc

from vi_textmatch import Kind, compare, normalize
from vi_textmatch.tone import TONE_PAIRS_SECOND_TO_FIRST, normalize_tone

# Vietnamese-heavy alphabet so the tone rules are actually exercised.
_VI_CHARS = (
    "aăâeêioôơuưyđ"
    "àáảãạèéẻẽẹìíỉĩịòóỏõọùúủũụỳýỷỹỵ"
    "ằắẳẵặầấẩẫậềếểễệồốổỗộờớởỡợừứửữự"
    "bcdghklmnpqrstvx"
    "AĂÂEÊIOÔƠUƯYĐÀÁÈÉÒÓÙÚỲÝ"
    "  ​-.,"
)
vi_text = st.text(alphabet=_VI_CHARS, max_size=40)
any_text = st.text(max_size=40)

# 5 tones on the second vowel of each pair, keyed by pair.
_PAIRS = {
    "oa": "àáảãạ",
    "oe": "èéẻẽẹ",
    "uy": "ỳýỷỹỵ",
}
_INITIALS = ["", "h", "th", "kh", "ng", "x", "t"]


class TestNormalizeIdempotent(unittest.TestCase):
    @settings(max_examples=500)
    @given(vi_text)
    @example("Hoà Thuý Khoẻ")
    def test_normalize_idempotent_vi(self, s: str) -> None:
        once = normalize(s)
        self.assertEqual(normalize(once), once)

    @settings(max_examples=300)
    @given(any_text)
    def test_normalize_idempotent_any(self, s: str) -> None:
        once = normalize(s)
        self.assertEqual(normalize(once), once)

    @settings(max_examples=500)
    @given(vi_text)
    def test_normalize_tone_idempotent(self, s: str) -> None:
        once = normalize_tone(s)
        self.assertEqual(normalize_tone(once), once)


def _ml(v: object) -> tuple[object, object]:
    """(match, level): detail may name a/b in order, so it is not compared."""
    return (v.match, v.level)  # type: ignore[attr-defined]


class TestCompareSymmetric(unittest.TestCase):
    @settings(max_examples=500)
    @given(vi_text, vi_text)
    def test_text_symmetric(self, a: str, b: str) -> None:
        v1 = compare(a, b, kind=Kind.TEXT)
        v2 = compare(b, a, kind=Kind.TEXT)
        self.assertEqual((v1.match, v1.level), (v2.match, v2.level))

    @settings(max_examples=300)
    @given(
        st.text(alphabet="0123456789 .-–—_aB", max_size=20),
        st.text(alphabet="0123456789 .-–—_aB", max_size=20),
    )
    def test_id_symmetric(self, a: str, b: str) -> None:
        self.assertEqual(_ml(compare(a, b, kind=Kind.ID)), _ml(compare(b, a, kind=Kind.ID)))

    @settings(max_examples=300)
    @given(
        st.dates(),
        st.dates(),
        st.sampled_from(["%d/%m/%Y", "%Y-%m-%d", "%d.%m.%Y"]),
        st.sampled_from([None, True, False]),
    )
    def test_date_symmetric(self, d1, d2, fmt: str, day_first) -> None:  # type: ignore[no-untyped-def]
        a, b = d1.strftime(fmt), d2.strftime(fmt)
        if d1.year < 1000 or d2.year < 1000:
            return  # 4-digit years only
        self.assertEqual(
            _ml(compare(a, b, kind=Kind.DATE, day_first=day_first)),
            _ml(compare(b, a, kind=Kind.DATE, day_first=day_first)),
        )

    @settings(max_examples=300)
    @given(
        st.integers(min_value=0, max_value=10**9),
        st.integers(min_value=0, max_value=10**9),
        st.sampled_from(["", "đ", " VND", "$", "€", "¥", "₫"]),
        st.sampled_from(["", "đ", " VND", "$", "€", "¥", "₫"]),
    )
    def test_money_symmetric(self, x: int, y: int, ca: str, cb: str) -> None:
        a, b = f"{x}{ca}", f"{y}{cb}"
        self.assertEqual(
            _ml(compare(a, b, kind=Kind.MONEY)), _ml(compare(b, a, kind=Kind.MONEY))
        )


class TestFiveTonesOaOeUy(unittest.TestCase):
    """Every tone x every pair: second-vowel form == first-vowel form."""

    def test_table_covers_5_tones_x_3_pairs(self) -> None:
        for marks in _PAIRS.values():
            self.assertEqual(len(marks), 5)
            for m in marks:
                self.assertIn(m, TONE_PAIRS_SECOND_TO_FIRST)
        self.assertEqual(len(TONE_PAIRS_SECOND_TO_FIRST), 15)

    @given(st.sampled_from(_INITIALS), st.sampled_from(sorted(_PAIRS)), st.integers(0, 4))
    def test_open_syllable_both_styles_equal(self, initial: str, pair: str, tone: int) -> None:
        second = initial + pair[0] + _PAIRS[pair][tone]
        first_mark, plain = TONE_PAIRS_SECOND_TO_FIRST[_PAIRS[pair][tone]]
        first = initial + first_mark + plain
        self.assertEqual(normalize_tone(second), first)
        self.assertEqual(normalize_tone(first), first)
        self.assertEqual(normalize_tone(second.upper()), first.upper())
        self.assertTrue(compare(second, first, kind=Kind.TEXT).match)
        self.assertEqual(compare(second, first, kind=Kind.TEXT).level, "IDENTICAL")

    @given(
        st.sampled_from(_INITIALS),
        st.sampled_from(sorted(_PAIRS)),
        st.integers(0, 4),
        st.sampled_from(["n", "t", "c", "nh", "ch"]),
    )
    def test_closed_syllable_untouched(
        self, initial: str, pair: str, tone: int, final: str
    ) -> None:
        word = initial + pair[0] + _PAIRS[pair][tone] + final
        self.assertEqual(normalize_tone(word), word)

    @given(st.integers(0, 4))
    def test_qu_never_rewritten(self, tone: int) -> None:
        word = "qu" + _PAIRS["uy"][tone]
        self.assertEqual(normalize_tone(word), word)
