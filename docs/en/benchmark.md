# vs difflib / rapidfuzz

The numbers below are **generated** by `bench/run_bench.py` in CI on every docs build — never typed
by hand. Full per-pair report: [`bench/RESULTS.md`](https://github.com/nightskat/vi-textmatch/blob/main/bench/RESULTS.md) (Vietnamese).

--8<-- "bench-summary.md"

## Method

- All data is **fabricated**: 100 hand-written pairs + pairs from `bench/gen_extended.py`
  (fixed seed): addresses, company names, contract numbers, multi-format amounts, dates, names.
- Labels come **from the transformation** (meaning-preserving or not), never from running the
  library. Some meaning-preserving inputs the library does not handle
  (`2900 triệu`, dates in words) are kept and show up as false-diff.
- `difflib`/`rapidfuzz`: cutoff 0.9 on raw strings; `+normalize` rows run on `normalize()`.
- **false-equal** (says EQUAL, actually different) is the dangerous error; CI fails if
  `vi_textmatch` gains a false-equal not in `bench/baseline.json`.

## Known limitation

`TEXT` still false-equals near-identical addresses / company names — see [Kinds](kinds.md#text).
