"""v3.108 — three closed expansion strategies.

* ``SINGLE_UNIVERSAL``  - one dimension expected
  to rescue every entanglement
  (``contradiction_type``).
* ``SMALL_VOCAB``       - the union of v3.107's
  used_candidates plus v3.101's
  ``contradiction_type`` for G/E.
* ``CASE_SPECIFIC``     - one dim per
  entanglement type.

Each strategy is scored by

* ``recovery_score``   - mean AUC across the
  union of (v3.93 G/E + v3.105 hidden
  entanglements) under the chosen scheme.
* ``complexity_score`` - fraction of the closed
  ``ALL_CANDIDATES`` taxonomy used; smaller is
  better.
* ``stability_score``  - v3.104a-style
  ``compatibility_score`` projected onto the
  strategy (no adverse flips ⇒ 1.0).
* ``architecture_roi`` - recovery / complexity.
"""
from __future__ import annotations

from enum import Enum
from functools import lru_cache

from ..t10_adaptive.adaptive import (
    ALL_CANDIDATES,
)
from ..t10_adaptive.report import (
    used_candidates as adaptive_used,
)
from ..t10_compat.compatibility import (
    CONTRADICTION_TYPE,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


class ExpansionStrategy(str, Enum):
    SINGLE_UNIVERSAL = "single_universal"
    SMALL_VOCAB      = "small_vocab"
    CASE_SPECIFIC    = "case_specific"


def single_universal_dims() -> tuple[str, ...]:
    return (CONTRADICTION_TYPE,)


@lru_cache(maxsize=1)
def small_vocab_dims() -> tuple[str, ...]:
    """v3.101's contradiction_type +
    v3.107's used_candidates."""
    out = {CONTRADICTION_TYPE}
    out.update(adaptive_used())
    return tuple(sorted(out))


def case_specific_dims() -> tuple[str, ...]:
    """One dim per entanglement instance. The
    set of distinct dims here equals
    ALL_CANDIDATES that could be picked - we use
    the v3.107 outcome to project the actual
    selection."""
    from ..t10_adaptive.search import (
        all_adaptive_outcomes,
    )
    out: set[str] = {CONTRADICTION_TYPE}
    for o in all_adaptive_outcomes():
        if o.best_candidate:
            out.add(o.best_candidate)
    return tuple(sorted(out))


def strategy_dims(strategy: str) -> tuple[str, ...]:
    if strategy == (
        ExpansionStrategy.SINGLE_UNIVERSAL.value
    ):
        return single_universal_dims()
    if strategy == (
        ExpansionStrategy.SMALL_VOCAB.value
    ):
        return small_vocab_dims()
    if strategy == (
        ExpansionStrategy.CASE_SPECIFIC.value
    ):
        return case_specific_dims()
    raise ValueError(strategy)


__all__ = [
    "ExpansionStrategy",
    "case_specific_dims",
    "single_universal_dims",
    "small_vocab_dims",
    "strategy_dims",
]
