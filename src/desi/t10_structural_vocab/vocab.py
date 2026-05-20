"""v3.115 — minimal-vocab aggregates."""
from __future__ import annotations

from ..t10_deep.topology import (
    STRUCTURAL_CANDIDATES,
)
from .search import best_subset


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def minimal_vocab_size() -> int:
    return len(best_subset().subset)


def vocab_recovery() -> float:
    return best_subset().rescue_rate


def mean_auc() -> float:
    return best_subset().mean_auc


def complexity_cost() -> float:
    """Best vocab size / total structural
    candidate count."""
    total = len(STRUCTURAL_CANDIDATES)
    if total == 0:
        return 0.0
    return _round(minimal_vocab_size() / total)


__all__ = [
    "complexity_cost",
    "mean_auc",
    "minimal_vocab_size",
    "vocab_recovery",
]
