# Changelog

## [0.3.0] - 2026-11-02

Minor bump — behaviour changes below.

### Changed (behaviour)
- `MONEY`: two explicit, different currencies (`100$` vs `100€`) are now `DIFFERENT`
  (detail `Currencies differ (USD vs EUR)`). Before: `IDENTICAL`. Aliases of the same
  currency (`đ`/`₫`/`VND`/`VNĐ`/`đồng`) still match; a value without a marker still
  matches any currency.
- `ID`: dots are ignored like spaces and hyphens: `0312.345.678 == 0312345678`.
  Before: `DIFFERENT`. `_` is still significant.
- `DATE`: ambiguous year-last dates (both first parts ≤ 12 and different, e.g.
  `02/01/2026`) return `match=False, level="AMBIGUOUS"` unless `day_first` is given.
  Before: silently read as DD/MM. Unambiguous inputs are unchanged.
- `normalize()`: zero-width spaces are removed before tone placement, so
  `normalize("Ho\u200bà") == "hòa"` and `normalize` is idempotent (bug found by
  hypothesis). Before: `"hoà"`.

### Added
- `compare(..., day_first: bool | None = None)`; `Verdict.level` may be `"AMBIGUOUS"`.
- CLI: `--day-first` / `--month-first` for `compare` and `closest`.
- Property-based tests (hypothesis): normalize idempotence, compare symmetry,
  5 tones × `oa`/`oe`/`uy`.
- CI: install the package (`pip install .`), smoke-test the installed CLI, ruff,
  mypy (strict), Python 3.14 in the matrix.
- `[project.optional-dependencies] dev` (pytest, hypothesis, ruff, mypy).

## [0.2.0]
- CLI, `py.typed`, CI.
