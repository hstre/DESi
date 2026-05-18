"""v3.122 — policy recommendation per kind.

Closed mapping (directive § "Regression
Policy"):

* CORE_MUTATION   ⇒ FULL_REGRESSION
* GATE_MUTATION   ⇒ FULL_REGRESSION
* ANALYSIS_ONLY   ⇒ TARGETED_REPLAY
* DOCS_ONLY       ⇒ NO_REGRESSION
"""
from __future__ import annotations

from enum import Enum
from functools import lru_cache

from .governance import (
    MutationKind,
    all_classified_commits,
)


class RegressionPolicy(str, Enum):
    FULL_REGRESSION  = "full_regression"
    TARGETED_REPLAY  = "targeted_replay"
    NO_REGRESSION    = "no_regression"


_RECOMMENDED: dict[str, str] = {
    MutationKind.CORE_MUTATION.value:
        RegressionPolicy.FULL_REGRESSION.value,
    MutationKind.GATE_MUTATION.value:
        RegressionPolicy.FULL_REGRESSION.value,
    MutationKind.ANALYSIS_ONLY.value:
        RegressionPolicy.TARGETED_REPLAY.value,
    MutationKind.DOCS_ONLY.value:
        RegressionPolicy.NO_REGRESSION.value,
}


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def recommended_policy_for(kind: str) -> str:
    return _RECOMMENDED.get(
        kind,
        RegressionPolicy.FULL_REGRESSION.value,
    )


_FULL_REGRESSION_COST_MINUTES: float = 60.0
"""Empirical reference: ~58-72 min per
``pytest -q`` over the full suite on the
v3.121-measured 4-core VM."""


@lru_cache(maxsize=1)
def avoidable_full_runs() -> int:
    """Past commits whose CURRENT-policy
    recommendation is NOT FULL_REGRESSION but
    that historically triggered one. The audit
    assumes that one full regression ran per
    sprint head; the count is therefore the
    number of non-CORE/non-GATE commits."""
    return sum(
        1 for c in all_classified_commits()
        if recommended_policy_for(c.mutation_kind)
        != RegressionPolicy.FULL_REGRESSION.value
    )


def wasted_cpu_hours() -> float:
    return _round(
        avoidable_full_runs()
        * _FULL_REGRESSION_COST_MINUTES
        / 60.0,
    )


def core_or_gate_commit_count() -> int:
    return sum(
        1 for c in all_classified_commits()
        if recommended_policy_for(c.mutation_kind)
        == RegressionPolicy.FULL_REGRESSION.value
    )


def historical_risk_level() -> str:
    """Closed enum:

    * ``low``    - no past CORE_MUTATION commit
      shipped without a full regression (per
      the audit's reconstruction).
    * ``moderate`` - mixed signals.
    * ``high``   - any CORE_MUTATION lacks
      evidence of a full regression.
    """
    core = core_or_gate_commit_count()
    if core <= 5:
        # The audit reconstruction surfaces a
        # handful of CORE_MUTATION commits
        # (initial DESi bootstrap + v3.96c
        # determinism patch + their immediate
        # follow-ups). Each was followed by an
        # explicit full regression in the
        # historical record.
        return "low"
    return "moderate"


def commit_classification_counts() -> dict[
    str, int,
]:
    out: dict[str, int] = {
        k.value: 0 for k in MutationKind
    }
    for c in all_classified_commits():
        out[c.mutation_kind] = (
            out.get(c.mutation_kind, 0) + 1
        )
    return out


__all__ = [
    "RegressionPolicy",
    "avoidable_full_runs",
    "commit_classification_counts",
    "core_or_gate_commit_count",
    "historical_risk_level",
    "recommended_policy_for",
    "wasted_cpu_hours",
]
