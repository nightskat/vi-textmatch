"""4-step Vietnamese text normalization pipeline.

Each step is individually callable and executed in strict numerical sequence:
Step 1: unicodedata.normalize("NFC", s)
Step 2: Standardize tone mark placement (via vi_textmatch.tone)
Step 3: Whitespace cleanup (remove U+00A0 nbsp, U+200B zero-width space,
        collapse consecutive spaces, trim)
Step 4: casefold()
"""

import re
import unicodedata

from vi_textmatch.tone import normalize_tone


def normalize_unicode(s: str) -> str:
    """Step 1: Normalize string to Unicode NFC canonical form."""
    if not isinstance(s, str):
        raise TypeError("Input must be a string")
    return unicodedata.normalize("NFC", s)


def normalize_whitespace(s: str) -> str:
    """Step 3: Remove U+00A0 (NBSP) and U+200B, collapse consecutive whitespaces, and trim."""
    if not isinstance(s, str):
        raise TypeError("Input must be a string")
    # Replace non-breaking space with regular space
    s = s.replace("\u00a0", " ")
    # Remove zero-width space
    s = s.replace("\u200b", "")
    # Collapse multiple whitespaces and strip
    return re.sub(r"\s+", " ", s).strip()


def normalize_case(s: str) -> str:
    """Step 4: Apply casefold() normalization."""
    if not isinstance(s, str):
        raise TypeError("Input must be a string")
    return s.casefold()


def normalize(s: str) -> str:
    """Execute all 4 normalization steps in strict order (1 -> 2 -> 3 -> 4)."""
    s = normalize_unicode(s)
    # Drop zero-width spaces BEFORE the tone step: "o\u200bà" must become
    # "òa" in one pass, otherwise normalize() is not idempotent (found by
    # hypothesis: the ZWSP hid the 'oa' pair from step 2, step 3 then joined it).
    s = s.replace("\u200b", "")
    s = normalize_tone(s)
    s = normalize_whitespace(s)
    s = normalize_case(s)
    return s


__all__ = [
    "normalize_unicode",
    "normalize_tone",
    "normalize_whitespace",
    "normalize_case",
    "normalize",
]
