"""vi-textmatch: Vietnamese text normalization and data-type aware comparison library."""

from vi_textmatch.compare import Kind, Verdict, closest, compare, explain
from vi_textmatch.normalize import normalize

__all__ = [
    "normalize",
    "compare",
    "explain",
    "closest",
    "Verdict",
    "Kind",
]
