"""v3.102 — single-dimension T10 injection.

Take the best candidate from v3.101 (currently
``contradiction_type``), append it as a SINGLE
additional slot (not broadcast across the 5
states) to the v3.89 residual vector, and re-run
the v3.86 clustering plus the v3.99 pairwise AUC.

We deliberately use ONE extra slot (not five) so
the dimensionality cost is exactly +1.
"""
from __future__ import annotations

from functools import lru_cache

from ..entangled.variance import (
    entangled_residual_vectors,
)
from ..t10.candidate import candidate_values
from ..t10.search import (
    best_outcome as v3101_best,
)


def selected_candidate() -> str:
    """Pinned to the v3.101 best candidate so
    drift in either side is surfaced."""
    return v3101_best().candidate


@lru_cache(maxsize=1)
def injected_vectors() -> dict[
    str, tuple[float, ...],
]:
    """46-d vector: 45-d residual + 1 slot for
    the selected candidate's value."""
    base = entangled_residual_vectors()
    vals = candidate_values(selected_candidate())
    out: dict[str, tuple[float, ...]] = {}
    for tid, vec in base.items():
        v = vals.get(tid, 0.0)
        out[tid] = vec + (v,)
    return out


def injected_dim() -> int:
    sample = next(iter(injected_vectors().values()))
    return len(sample)


def baseline_dim() -> int:
    sample = next(
        iter(entangled_residual_vectors().values()),
    )
    return len(sample)


__all__ = [
    "baseline_dim",
    "injected_dim",
    "injected_vectors",
    "selected_candidate",
]
