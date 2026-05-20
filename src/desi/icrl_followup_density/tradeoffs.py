"""v23.2 - explicit design tradeoffs.

Each design decision is stated with both a benefit and a
cost, so the revision does not read as one-sided advocacy. A
decision with only an upside would be invisible-tradeoff and
counts against the metric.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Tradeoff:
    tradeoff_id: str
    decision: str
    benefit: str
    cost: str

    def is_two_sided(self) -> bool:
        return bool(self.benefit.strip()) and bool(
            self.cost.strip()
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "tradeoff_id": self.tradeoff_id,
            "decision": self.decision,
            "benefit": self.benefit,
            "cost": self.cost,
            "is_two_sided": self.is_two_sided(),
        }


_TRADEOFFS: tuple[Tradeoff, ...] = (
    Tradeoff(
        "T1", "Soft re-weighting instead of pruning",
        "every trajectory is preserved, so exploration "
        "diversity is not lost to deletion",
        "redundant search is only down-weighted, not removed, "
        "so some redundancy remains in the run."),
    Tradeoff(
        "T2", "Read-only governance layer",
        "the governor never edits the policy, so it cannot "
        "inject hidden optimisation authority",
        "it can only observe and re-weight, so it cannot "
        "directly repair an already-collapsed policy."),
    Tradeoff(
        "T3", "Admitting the Wild Explorer",
        "novelty_gain rises because states DESi-alone misses "
        "are reached",
        "the generator adds hallucination pressure that must "
        "be contained, which costs governance overhead."),
    Tradeoff(
        "T4", "Deterministic synthetic fixtures",
        "every number is replay-exact and fully auditable",
        "results are scoped to the sandbox and do not measure "
        "a real trained policy."),
    Tradeoff(
        "T5", "Bounded saturating drift model",
        "accumulated authority stays bounded over a long "
        "horizon",
        "the bound is a modelling choice on the fixtures, not "
        "a guarantee about real systems."),
)


def tradeoffs() -> tuple[Tradeoff, ...]:
    return _TRADEOFFS


def one_sided_tradeoffs() -> tuple[str, ...]:
    return tuple(
        t.tradeoff_id for t in _TRADEOFFS
        if not t.is_two_sided()
    )


def tradeoff_visibility() -> float:
    """Fraction of design decisions that state both a benefit
    and a cost, in [0, 1]."""
    rows = _TRADEOFFS
    if not rows:
        return 0.0
    two_sided = sum(1 for t in rows if t.is_two_sided())
    return round(two_sided / len(rows), 6)


__all__ = [
    "Tradeoff",
    "one_sided_tradeoffs",
    "tradeoff_visibility",
    "tradeoffs",
]
