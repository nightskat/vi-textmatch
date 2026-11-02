"""Data-type aware text comparison module.

Provides:
- Kind: Data types for comparison (TEXT, ID, MONEY, DATE)
- Verdict: Result object with match status, level, and detail
- compare(a, b, kind): Compare two strings based on Kind
- explain(a, b): Produce character-level diff explanation
- closest(s, candidates, n): Find close candidate matches
"""

import difflib
import re
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Literal

from vi_textmatch.normalize import normalize

# Threshold constants for TEXT comparison (no magic numbers in code)
THRESHOLD_IDENTICAL: float = 1.0
THRESHOLD_TYPO: float = 0.85


class Kind(str, Enum):
    """Supported comparison data kinds."""
    TEXT = "TEXT"
    ID = "ID"
    MONEY = "MONEY"
    DATE = "DATE"


@dataclass(frozen=True)
class Verdict:
    """Comparison verdict container."""
    match: bool
    level: Literal["IDENTICAL", "TYPO", "DIFFERENT", "AMBIGUOUS"]
    detail: str


# ID separators that are ignored before exact comparison ('_' is NOT one).
_ID_SEPARATORS_RE = re.compile(r"[\s.\-–—]+")

# Strict money grammar: the full string (after stripping one allowed currency
# marker) must match exactly one supported format.
# VN: dot thousands + optional comma decimal, e.g. 2.500.000,50
_MONEY_VN_RE = re.compile(r"[+-]?\d{1,3}(?:\.\d{3})+(?:,\d+)?")
# US: comma thousands + optional dot decimal, e.g. 2,500,000.50
_MONEY_US_RE = re.compile(r"[+-]?\d{1,3}(?:,\d{3})+(?:\.\d+)?")
# Plain: integer or single decimal separator, e.g. 2500000000, 2.5, 2,5
_MONEY_PLAIN_RE = re.compile(r"[+-]?\d+(?:[.,]\d+)?")

# Allowed currency markers, longest first so "đồng" wins over "đ".
_CURRENCY_MARKERS = ("VND", "VNĐ", "đồng", "đ", "₫", "$", "€", "¥")

# Marker -> canonical currency code. Markers of the same currency are
# interchangeable ("100đ" == "100 VND"); different currencies never match.
_CURRENCY_CODES = {
    "VND": "VND",
    "VNĐ": "VND",
    "đồng": "VND",
    "đ": "VND",
    "₫": "VND",
    "$": "USD",
    "€": "EUR",
    "¥": "JPY",
}


def _strip_currency_marker(s: str) -> tuple[str, str | None]:
    """Remove exactly one allowed currency marker from either end.

    Returns the remaining number text and the canonical currency code
    (None when the string carries no marker).
    """
    lowered = s.casefold()
    for marker in _CURRENCY_MARKERS:
        if lowered.endswith(marker.casefold()):
            return s[: len(s) - len(marker)].strip(), _CURRENCY_CODES[marker]
    for marker in _CURRENCY_MARKERS:
        if lowered.startswith(marker.casefold()):
            return s[len(marker):].strip(), _CURRENCY_CODES[marker]
    return s, None


def _parse_money(s: str) -> tuple[Decimal, str | None]:
    """Parse a monetary string into Decimal using a strict grammar.

    Accepts VN (2.500.000,50) and US (2,500,000.50) number formats, with an
    optional allowed currency prefix/suffix. Any other character or separator
    structure is rejected.

    Returns (amount, canonical currency code or None).

    Raises ValueError if the string is not a strictly valid monetary format.
    """
    if not isinstance(s, str):
        raise ValueError("MONEY input must be a string")

    # NFC normalize and strip leading/trailing whitespace
    s = unicodedata.normalize("NFC", s).strip()
    s, currency = _strip_currency_marker(s)

    if _MONEY_VN_RE.fullmatch(s):
        num_str = s.replace(".", "").replace(",", ".")
    elif _MONEY_US_RE.fullmatch(s):
        num_str = s.replace(",", "")
    elif _MONEY_PLAIN_RE.fullmatch(s):
        num_str = s.replace(",", ".")
    else:
        raise ValueError("Cannot parse MONEY: invalid number format")

    try:
        return Decimal(num_str), currency
    except InvalidOperation as err:
        raise ValueError("Cannot parse MONEY: invalid number format") from err


def _parse_date(s: str, day_first: bool | None = None) -> date | None:
    """Parse date string into datetime.date object.

    Only four-digit years are accepted; two-digit years are rejected.

    A year-last string whose first two parts are both <= 12 (e.g. 02/01/2026)
    is ambiguous: day-month or month-day. With ``day_first=None`` it returns
    None (ambiguous); ``True`` reads it as DD-MM-YYYY, ``False`` as MM-DD-YYYY.
    Unambiguous strings are always read as before (YYYY-MM-DD or DD-MM-YYYY).

    Raises ValueError if string cannot be parsed into a valid date.
    """
    if not isinstance(s, str):
        raise ValueError("DATE input must be a string")

    s = unicodedata.normalize("NFC", s).strip()

    # Replace delimiters (/ . space) with '-'
    cleaned = re.sub(r"[\/\.\s]+", "-", s)
    parts = [p for p in cleaned.split("-") if p]

    if len(parts) != 3:
        raise ValueError("Cannot parse DATE: invalid component count")

    p1, p2, p3 = parts
    if not (p1.isdigit() and p2.isdigit() and p3.isdigit()):
        raise ValueError("Cannot parse DATE: non-numeric components")

    if len(p1) == 4:
        # YYYY-MM-DD
        year, month, day = int(p1), int(p2), int(p3)
    elif len(p3) == 4:
        first, second, year = int(p1), int(p2), int(p3)
        if 1 <= first <= 12 and 1 <= second <= 12 and first != second:
            if day_first is None:
                return None
            if day_first:
                day, month = first, second
            else:
                month, day = first, second
        else:
            # DD-MM-YYYY (unambiguous, or both readings give the same date)
            day, month = first, second
    else:
        raise ValueError("Cannot parse DATE: year must be 4 digits")

    try:
        return date(year, month, day)
    except ValueError as err:
        raise ValueError("Cannot parse DATE: out of range date values") from err


def compare(
    a: str, b: str, *, kind: Kind, day_first: bool | None = None
) -> Verdict:
    """Compare two strings according to the specified Kind rules.

    Args:
        a: First input string.
        b: Second input string.
        kind: Comparison strategy (TEXT, ID, MONEY, DATE); keyword-only.
        day_first: DATE only. How to read ambiguous dates such as 02/01/2026:
            True = DD/MM/YYYY, False = MM/DD/YYYY, None (default) = refuse to
            guess and return level "AMBIGUOUS" with match=False.

    Returns:
        Verdict containing match status (bool), level (Literal), and detail (str).

    Raises:
        ValueError: If kind is invalid, or if MONEY/DATE cannot be converted.
    """
    if not isinstance(kind, Kind):
        raise ValueError("Invalid comparison kind")

    if kind == Kind.TEXT:
        norm_a = normalize(a)
        norm_b = normalize(b)

        if norm_a == norm_b:
            return Verdict(
                match=True,
                level="IDENTICAL",
                detail="Strings are identical after normalization",
            )

        matcher = difflib.SequenceMatcher(None, norm_a, norm_b)
        ratio = matcher.ratio()

        if ratio >= THRESHOLD_IDENTICAL:
            return Verdict(
                match=True,
                level="IDENTICAL",
                detail=f"Match ratio: {ratio:.4f}",
            )
        elif ratio >= THRESHOLD_TYPO:
            return Verdict(
                match=True,
                level="TYPO",
                detail=f"Match ratio: {ratio:.4f} (typo suspected)",
            )
        else:
            return Verdict(
                match=False,
                level="DIFFERENT",
                detail=f"Match ratio: {ratio:.4f}",
            )

    elif kind == Kind.ID:
        # Separators ignored: whitespace, dot, hyphen, en-dash, em-dash.
        clean_a = _ID_SEPARATORS_RE.sub("", unicodedata.normalize("NFC", a)).casefold()
        clean_b = _ID_SEPARATORS_RE.sub("", unicodedata.normalize("NFC", b)).casefold()

        if clean_a == clean_b:
            return Verdict(
                match=True,
                level="IDENTICAL",
                detail="ID values match exactly after cleaning whitespace, dots and hyphens",
            )
        else:
            return Verdict(
                match=False,
                level="DIFFERENT",
                detail="ID values do not match",
            )

    elif kind == Kind.MONEY:
        dec_a, cur_a = _parse_money(a)
        dec_b, cur_b = _parse_money(b)

        # A missing marker is "unknown currency" and stays compatible; two
        # explicit, different currencies are never the same amount.
        if cur_a is not None and cur_b is not None and cur_a != cur_b:
            return Verdict(
                match=False,
                level="DIFFERENT",
                detail=f"Currencies differ ({cur_a} vs {cur_b})",
            )

        if dec_a == dec_b:
            return Verdict(
                match=True,
                level="IDENTICAL",
                detail="Monetary values match exactly",
            )
        else:
            return Verdict(
                match=False,
                level="DIFFERENT",
                detail="Monetary values differ",
            )

    elif kind == Kind.DATE:
        date_a = _parse_date(a, day_first)
        date_b = _parse_date(b, day_first)

        if date_a is None or date_b is None:
            return Verdict(
                match=False,
                level="AMBIGUOUS",
                detail="Ambiguous date (day/month order unknown); pass day_first",
            )

        if date_a == date_b:
            return Verdict(
                match=True,
                level="IDENTICAL",
                detail="Dates match exactly",
            )
        else:
            return Verdict(
                match=False,
                level="DIFFERENT",
                detail="Dates differ",
            )

    else:
        raise ValueError("Unsupported comparison kind")


def explain(a: str, b: str) -> str:
    """Generate character diff between two strings after normalization."""
    norm_a = normalize(a)
    norm_b = normalize(b)
    diff = difflib.ndiff(norm_a, norm_b)
    return "\n".join(diff)


def closest(
    s: str, candidates: Sequence[str], n: int = 3, cutoff: float = 0.6
) -> list[str]:
    """Find the closest candidate strings based on normalized string matching."""
    norm_s = normalize(s)

    norm_to_orig: dict[str, list[str]] = {}
    norm_candidates: list[str] = []

    for cand in candidates:
        norm_c = normalize(cand)
        if norm_c not in norm_to_orig:
            norm_to_orig[norm_c] = []
            norm_candidates.append(norm_c)
        norm_to_orig[norm_c].append(cand)

    matched_norms = difflib.get_close_matches(
        norm_s, norm_candidates, n=n, cutoff=cutoff
    )

    results: list[str] = []
    for m in matched_norms:
        results.extend(norm_to_orig[m])
        if len(results) >= n:
            break

    return results[:n]


__all__ = [
    "Kind",
    "Verdict",
    "compare",
    "explain",
    "closest",
    "THRESHOLD_IDENTICAL",
    "THRESHOLD_TYPO",
]
