# Kinds

| `Kind` | Method | One character apart means |
|---|---|---|
| `TEXT` | `normalize()`, then `difflib` ratio | maybe a typo — graded `IDENTICAL`/`TYPO`/`DIFFERENT` |
| `NAME` | `normalize()`, then each name component exactly (diacritics kept) | **a different person** |
| `ID` | strip whitespace, `.`, `-`, `–`, `—` (not `_`), then **exact** equality | **a different entity** |
| `MONEY` | parse to `Decimal` + currency | **a different amount** |
| `DATE` | parse to `date` | **a different date** |

## TEXT

ratio 1.0 → `IDENTICAL`; ≥ 0.85 → `TYPO` (`match=True`); below → `DIFFERENT`.

!!! warning "TEXT is not safe for addresses or legal entity names"
    The benchmark shows `TEXT` treating `Số 228 …` vs `Số 229 …` (different house number) and
    `Công ty TNHH Hòa Lợi Thuận Phát` vs `Công ty Cổ phần Hòa Lợi Thuận Phát` as `TYPO` → `match=True`. Compare the number / legal
    form separately with `ID`, or treat `TYPO` as "re-check".

## NAME

Forgives only NFC/NFD, tone placement (`hoà`/`hòa`), whitespace and case. Any other difference in
any component is `DIFFERENT`, typos included (`Sơnn`) — deliberately sent back to a human.

## ID

`0312.345.678 == 0312345678`; `031234567890 != 031234567891`. Labels such as `MST` are not stripped.

## MONEY

- VN `2.500.000,50`, US `2,500,000.50`, plain `2500000`.
- `đ`, `₫`, `VND`, `VNĐ`, `đồng` are one currency; two **explicit different** currencies
  (`$` vs `€`) are `DIFFERENT`; no marker = value only.
- Words (`2900 triệu`, `1,5 tỷ`) are not parsed → **`ValueError`** (fail-closed).

## DATE

- `DD/MM/YYYY`, `D/M/YYYY`, `YYYY-MM-DD`, separators `/ - . space`; 4-digit years only.
- Ambiguous (`02/01/2026`) → `match=False, level="AMBIGUOUS"` unless `day_first` is given.
- Dates in words (`ngày 04 tháng 04 năm 2022`) are not supported → `ValueError`.
