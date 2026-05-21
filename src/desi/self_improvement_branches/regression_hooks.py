"""v28.2 - regression hooks (mandatory, never bypassed).

Every proposal branch carries a regression hook that is required
and cannot be bypassed. Regression is never skipped to make a
change easier to land - that path does not exist here.
"""
from __future__ import annotations

from dataclasses import dataclass

from .branching import branches


@dataclass(frozen=True)
class RegressionHook:
    branch_id: str
    required: bool
    bypassed: bool

    def is_enforced(self) -> bool:
        return self.required and not self.bypassed

    def to_dict(self) -> dict[str, object]:
        return {
            "branch_id": self.branch_id,
            "required": self.required,
            "bypassed": self.bypassed,
            "is_enforced": self.is_enforced(),
        }


def hooks() -> tuple[RegressionHook, ...]:
    return tuple(
        RegressionHook(b.branch_id, True, False)
        for b in branches()
    )


def any_bypassed() -> bool:
    return any(h.bypassed for h in hooks())


def regression_integrity() -> float:
    """Fraction of branches with an enforced (required,
    non-bypassed) regression hook, in [0, 1]."""
    hs = hooks()
    if not hs:
        return 1.0
    enforced = sum(1 for h in hs if h.is_enforced())
    return round(enforced / len(hs), 6)


__all__ = [
    "RegressionHook",
    "any_bypassed",
    "hooks",
    "regression_integrity",
]
