"""v3.114 — inject the v3.113 top structural
candidate as a single +1 dim.

Pinned to ``top_candidate().candidate`` so any
drift in v3.113 surfaces immediately.
"""
from __future__ import annotations

from functools import lru_cache

from ..t10_deep.graph import top_candidate
from ..t10_deep.topology import (
    structural_value,
)


def selected_structural_candidate() -> str:
    return top_candidate().candidate


def proxy_dependence_count() -> int:
    """v3.113 candidates are derived only from
    StateVector content. None depend on ids,
    corpus names, or other metadata - so the
    proxy_dependence count is structurally
    zero."""
    return 0


__all__ = [
    "proxy_dependence_count",
    "selected_structural_candidate",
    "structural_value",
]
