# vi-textmatch

Vietnamese text normalization and **type-aware** comparison. Zero dependencies.

Built for document verification — checking a drafted contract against the source record —
where "close enough" is fine for prose and catastrophically wrong for an amount or an ID.

## Install

```bash
pip install vi-textmatch
```

Python 3.11+.

## Quickstart

```python
from vi_textmatch import normalize, compare, Kind

normalize("Nguyễn Thị  Hoà ")          # 'nguyễn thị hòa'

compare("Nguyễn Thị Hòa", "nguyễn thị hoà", kind=Kind.NAME).match      # True
compare("Nguyễn Văn An", "Nguyễn Văn Ân", kind=Kind.NAME).match        # False — another person
compare("2.500.000.000", "2,500,000,000", kind=Kind.MONEY).match       # True
compare("100$", "100€", kind=Kind.MONEY).match                         # False
compare("0312.345.678", "0312345678", kind=Kind.ID).match              # True
compare("02/01/2026", "2026-01-02", kind=Kind.DATE, day_first=True).match  # True
```

`kind` is required: `compare(a, b)` raises `TypeError` instead of silently fuzzy-matching.

## CLI

```bash
vi-textmatch normalize "Nguyễn Thị Hoà"
vi-textmatch compare "0312.345.678" "0312345678" --kind id
```

See [Kinds](kinds.md) and [benchmark](benchmark.md).
