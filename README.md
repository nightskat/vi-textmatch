# vi-textmatch

[![test](https://github.com/nightskat/vi-textmatch/actions/workflows/test.yml/badge.svg)](https://github.com/nightskat/vi-textmatch/actions/workflows/test.yml)

Vietnamese text normalization and **type-aware** comparison. Zero dependencies, standard library only.

Built for document verification — checking that a drafted contract matches the source record —
where "close enough" is the right answer for a person's name and a catastrophically wrong answer
for an ID number.

---

## The problem

Two strings that look identical on screen are often not equal in memory:

```python
"Huệ" == "Huệ"   # False
```

One is NFC (`ệ` = 1 codepoint), the other NFD (`e` + combining dot below + combining circumflex = 3).
macOS filenames are NFD; most other sources are NFC.

And Vietnamese tone marks have two accepted positions in open syllables:

```python
"hoà" == "hòa"   # False — same word, different bytes
```

Meanwhile, applying a naive `oà → òa` rewrite corrupts closed syllables:
`hoàn → hòan`, `suýt → súyt`, `huỳnh → hùynh` — none of which are Vietnamese words.
Worse, the corruption creates **false matches** between different words.

## Install

```bash
pip install vi-textmatch
```

Python 3.11+. No third-party dependencies.

## Usage

```python
from vi_textmatch import normalize, compare, Kind

normalize("Nguyễn Thị  Hoà ")     # 'nguyễn thị hòa'
normalize("hoàn")                  # 'hoàn'  — closed syllable, untouched
normalize("suýt")                  # 'suýt'  — closed syllable, untouched

compare("Nguyễn Thị Hòa", "nguyễn thị hoà", kind=Kind.TEXT)
# Verdict(match=True,  level='IDENTICAL')

compare("Nguyễn Thị Hòa", "Nguyễn Thị Hoa",  kind=Kind.TEXT)
# Verdict(match=True,  level='TYPO')        — one character off, likely OCR/typing

compare("Nguyễn Thị Hòa", "Trần Văn Bình",   kind=Kind.TEXT)
# Verdict(match=False, level='DIFFERENT')   — different person

compare("031234567890", "031234567891", kind=Kind.ID)
# Verdict(match=False)   — one digit apart is a different person, not a typo

compare("2.500.000.000", "2,500,000,000", kind=Kind.MONEY)   # match
compare("2.500.000.000", "2.600.000.000", kind=Kind.MONEY)   # no match
compare("100$", "100€", kind=Kind.MONEY)                     # no match — different currency

compare("0312.345.678", "0312345678", kind=Kind.ID)           # match — dots ignored

compare("02/01/2026", "2026-01-02", kind=Kind.DATE)
# Verdict(match=False, level='AMBIGUOUS')  — 2 Jan or 1 Feb? never guessed
compare("02/01/2026", "2026-01-02", kind=Kind.DATE, day_first=True)   # match
```

`kind` is keyword-only and has **no default**. Calling `compare(a, b)` raises `TypeError`
rather than silently falling back to fuzzy text matching.

## Comparison kinds

| `Kind` | Method | One character apart means |
|---|---|---|
| `TEXT` | normalize, then `difflib` ratio | possibly a typo — graded, see below |
| `ID` | strip whitespace, `.`, `-`, `–`, `—` (not `_`), then **exact equality** | **a different entity** |
| `MONEY` | parse to `Decimal` + currency, compare both | **a different amount** |
| `DATE` | parse to `date`, compare values | **a different date** |

- `MONEY`: markers of one currency are interchangeable (`đ`, `₫`, `VND`, `VNĐ`, `đồng`);
  two **explicit, different** currencies (`$` vs `€`) are `DIFFERENT`. No marker = unknown
  currency, compared by value only.
- `DATE`: `DD/MM/YYYY` where both first parts are ≤ 12 and differ (e.g. `02/01/2026`) is
  ambiguous → `match=False, level="AMBIGUOUS"`. Pass `day_first=True` (DD/MM) or
  `day_first=False` (MM/DD); CLI: `--day-first` / `--month-first`. ISO `YYYY-MM-DD` and
  strings whose first part is > 12 are never ambiguous.

`TEXT` grades the difference so you can act on it:

| ratio | level | Interpretation |
|---|---|---|
| 1.0 | `IDENTICAL` | same string after normalization |
| ≥ 0.85 | `TYPO` | likely a typing or OCR error — fix the text |
| < 0.85 | `DIFFERENT` | likely the wrong record — stop and re-check |

Similarity is meaningless for identifiers and amounts, so `ID`, `MONEY` and `DATE` never use it.
`MONEY` and `DATE` raise on input they cannot parse; they never silently degrade to string comparison.

## Normalization pipeline

`normalize()` applies four steps, in this order:

1. **NFC** — compose combining marks. Must come first: step 2 matches single codepoints.
2. **Tone placement** — rewrite `hoà → hòa` **only in open syllables**.
3. **Whitespace** — strip nbsp/zero-width, collapse runs, trim.
4. **casefold** — must come last: step 2 needs the original case to preserve it.

Each step is also exported individually.

### Tone placement rule

The tone mark sits on the syllable nucleus. Two written forms exist **only** for `oa`, `oe`, `uy`
in an **open** syllable (nothing follows the pair). In a **closed** syllable there is exactly one
correct form and it must never be rewritten:

| | Rewritten | Left alone |
|---|---|---|
| open | `hoà → hòa`, `thuỷ → thủy`, `hoè → hòe` | — |
| closed | — | `hoàn`, `suýt`, `huỳnh`, `khuỷu`, `khoét`, `huých` |
| pre-accented vowel (ê ô ơ ă â ư) | — | `huệ`, `thuở`, `chuồn`, `thuyền`, `giường` |
| `qu` / `gi` initial cluster | — | `quý`, `quỳnh`, `quán`, `già`, `giữ` |

This library deliberately avoids the labels "old style" and "new style": published sources use
them in opposite directions. Positions are named explicitly instead.

See [`research/QUY-TAC.md`](research/QUY-TAC.md) for the derivation and sources.

## Scope

This library knows **orthography, not vocabulary**.

It does: normalize spelling variants, compare by data type, grade differences.

It does **not**: know whether a string is a real Vietnamese word, find names inside text (that is
NER — see [underthesea](https://github.com/undertheseanlp/underthesea)), correct spelling, or
understand meaning.

## Development

```bash
python -m pip install -e ".[dev]"   # pytest, hypothesis, ruff, mypy (dev only; runtime has zero deps)
ruff check src tests
mypy
pytest tests/ -q
```

## License

MIT
