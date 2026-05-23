"""v28.3 - regression survival comparison.

The candidate must survive the same regression as the current
system. Regression survival is a safety invariant: the candidate
may not trade test survival for a quality gain.
"""
from __future__ import annotations

from .evolution_metrics import (
    candidate_vector, current_vector, is_worse,
)


def regression_survival_current() -> float:
    return current_vector()["regression_survival"]


def regression_survival_candidate() -> float:
    return candidate_vector()["regression_survival"]


def regression_survival_preserved() -> bool:
    return not is_worse(
        "regression_survival",
        regression_survival_candidate(),
        regression_survival_current(),
    )


__all__ = [
    "regression_survival_candidate",
    "regression_survival_current",
    "regression_survival_preserved",
]
