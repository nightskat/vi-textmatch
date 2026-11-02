"""Vietnamese tone mark placement normalization.

In Vietnamese, the diphthongs/glides 'oa', 'oe', 'uy' can be written with the
tone mark on either vowel:

- TONE_ON_FIRST_VOWEL: the mark sits on the first vowel (e.g. 'hòa', 'hòe', 'hùy').
- TONE_ON_SECOND_VOWEL: the mark sits on the second vowel (e.g. 'hoà', 'hoè', 'huỳ').

This module rewrites the second-vowel form to the first-vowel form so spelling
variants normalize to a single consistent form for matching.

Placement rules (see research/QUY-TAC.md):
1. The rewrite is applied ONLY when 'oa'/'oe'/'uy' are the two last letters of
   the syllable — an OPEN syllable. That means the character immediately after
   the pair must be a word boundary: a non-letter, or the end of the string.
2. If any consonant or vowel follows the pair (a CLOSED syllable), the text is
   never rewritten. Kept as-is: 'hoàn', 'suýt', 'huỳnh', 'khuỷu', 'khoét', 'huých'.
3. Rhymes whose vowel already carries a diacritic (ê, ô, ơ, ă, â, ư) never
   appear in the mapping: 'huệ', 'thuở', 'chuồn', 'thuyền' are already final.
4. 'qu' is an initial consonant cluster (/kw/), not 'q' + a glide 'u'; the
   negative lookbehind `(?<![qQ])` protects 'quý', 'quỳnh', 'quỷ', ... from
   being rewritten (the vowel that carries the tone starts AFTER the 'u').
"""

import re

# Style labels are position-based, never "old"/"new": published sources use
# those labels in opposite directions, so naming by position avoids confusion.
TONE_ON_FIRST_VOWEL: str = "tone mark on the first vowel (e.g. hòa, hòe, hùy)"
TONE_ON_SECOND_VOWEL: str = "tone mark on the second vowel (e.g. hoà, hoè, huỳ)"

# Second-vowel tone form (lowercase) -> (first-vowel tone form, plain second
# vowel). Only the 5 Vietnamese tones exist on these vowels; both character
# cases are handled at substitution time, so no per-case table is needed.
TONE_PAIRS_SECOND_TO_FIRST: dict[str, tuple[str, str]] = {
    # oa
    "à": ("ò", "a"),
    "á": ("ó", "a"),
    "ả": ("ỏ", "a"),
    "ã": ("õ", "a"),
    "ạ": ("ọ", "a"),
    # oe
    "è": ("ò", "e"),
    "é": ("ó", "e"),
    "ẻ": ("ỏ", "e"),
    "ẽ": ("õ", "e"),
    "ẹ": ("ọ", "e"),
    # uy
    "ỳ": ("ù", "y"),
    "ý": ("ú", "y"),
    "ỷ": ("ủ", "y"),
    "ỹ": ("ũ", "y"),
    "ỵ": ("ụ", "y"),
}

# 'oa'/'oe': plain o/O followed by a tone-marked a/e (either case). The
# lookahead captures the character right after the pair (without consuming it):
# if it is a letter, the syllable is CLOSED and must not be rewritten.
_OA_OE_PATTERN: re.Pattern[str] = re.compile(
    r"[oO](?:[àáảãạÀÁẢÃẠ]|[èéẻẽẹÈÉẺẼẸ])(?=([\s\S])|$)"
)

# 'uy': same rule, plus a negative lookbehind so 'qu' is never rewritten.
_UY_PATTERN: re.Pattern[str] = re.compile(
    r"(?<![qQ])[uU][ỳýỷỹỵỲÝỶỸỴ](?=([\s\S])|$)"
)


def _to_first_vowel(match: re.Match[str]) -> str:
    """Rewrite 'hoà' -> 'hòa' when the pair ends an OPEN syllable."""
    pair = match.group(0)
    following = match.group(1)
    # A letter right after the pair means a CLOSED syllable: never rewrite.
    if following is not None and following.isalpha():
        return pair
    first, second = pair[0], pair[1]
    first_tone, plain_second = TONE_PAIRS_SECOND_TO_FIRST[second.casefold()]
    new_first = first_tone if first.islower() else first_tone.upper()
    new_second = plain_second if second.islower() else plain_second.upper()
    return new_first + new_second


def normalize_tone(text: str) -> str:
    """Normalize Vietnamese tone mark placement (Step 2 of the pipeline).

    Rewrites open syllables written with the mark on the second vowel of
    'oa'/'oe'/'uy' to the first-vowel form ('hoà' -> 'hòa'). Closed syllables
    and rhymes with a pre-accented vowel (ê/ô/ơ/ă/â/ư) are left untouched.

    Args:
        text: Input string.

    Returns:
        String with normalized tone mark placement.
    """
    if not text:
        return text

    text = _OA_OE_PATTERN.sub(_to_first_vowel, text)
    text = _UY_PATTERN.sub(_to_first_vowel, text)
    return text


__all__ = [
    "normalize_tone",
    "TONE_ON_FIRST_VOWEL",
    "TONE_ON_SECOND_VOWEL",
    "TONE_PAIRS_SECOND_TO_FIRST",
]
