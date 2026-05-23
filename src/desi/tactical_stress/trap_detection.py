"""v11.2 — trap-pattern detection and critical-
line preservation."""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from .horizon import assigned_depth
from .tactics import (
    TacticalCase, TacticalPattern, fixture,
)


@dataclass(frozen=True)
class ResolvedCase:
    case_id: str
    pattern: str
    critical_move: str
    assigned_depth: int
    resolved: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "case_id": self.case_id,
            "pattern": self.pattern,
            "critical_move":
                self.critical_move,
            "assigned_depth":
                self.assigned_depth,
            "resolved": self.resolved,
        }


def _resolved_flag(case: TacticalCase) -> bool:
    """DESi resolves a tactical case if its
    assigned depth covers the required depth.
    Because v11.1's governance always keeps
    critical-tactic branches in SEARCH at full
    depth, this flag is True for every critical
    case."""
    return assigned_depth(case.case_id) >= (
        case.depth_required
    )


@lru_cache(maxsize=1)
def resolved_cases() -> tuple[
    ResolvedCase, ...,
]:
    return tuple(
        ResolvedCase(
            case_id=c.case_id,
            pattern=c.pattern,
            critical_move=c.critical_move,
            assigned_depth=assigned_depth(
                c.case_id,
            ),
            resolved=_resolved_flag(c),
        )
        for c in fixture()
    )


def tactical_miss_rate() -> float:
    """Fraction of CRITICAL cases that DESi
    failed to resolve."""
    rows = resolved_cases()
    critical = [
        r for r in rows
        if any(
            c.is_critical and (
                c.case_id == r.case_id
            )
            for c in fixture()
        )
    ]
    if not critical:
        return 0.0
    missed = sum(
        1 for r in critical
        if not r.resolved
    )
    return round(missed / len(critical), 6)


def critical_line_preservation() -> float:
    """Fraction of CRITICAL cases successfully
    resolved. 1 - tactical_miss_rate."""
    return round(
        1.0 - tactical_miss_rate(), 6,
    )


def trap_detection() -> float:
    """Recall on the TRAP pattern subset."""
    target = [
        r for r in resolved_cases()
        if r.pattern == (
            TacticalPattern.TRAP.value
        )
    ]
    if not target:
        return 1.0
    hit = sum(
        1 for r in target if r.resolved
    )
    return round(hit / len(target), 6)


__all__ = [
    "ResolvedCase",
    "critical_line_preservation",
    "resolved_cases",
    "tactical_miss_rate",
    "trap_detection",
]
