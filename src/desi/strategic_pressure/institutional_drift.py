"""v9.3 — institutional drift / trust collapse
diagnostics over the 5000-step trajectory."""
from __future__ import annotations

from .pressure_ecology import trajectory


SHORT_WINDOW: int = 500


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _early_trust() -> float:
    steps = trajectory()[:SHORT_WINDOW]
    if not steps:
        return 0.0
    return sum(s.trust for s in steps) / len(steps)


def _late_trust() -> float:
    steps = trajectory()[-SHORT_WINDOW:]
    if not steps:
        return 0.0
    return sum(s.trust for s in steps) / len(steps)


def trust_collapse() -> float:
    """Absolute drop in mean trust between the
    early and late window. Near 0 means trust
    dynamics stayed stable."""
    return _round(
        max(0.0, _early_trust() - _late_trust()),
    )


def _opportunism_share(steps: tuple) -> float:
    """Fraction of steps that exit HIGH-trust
    (>= 0.90) but were ground-truth gaming
    (verdict in the GAMING enum and not NORMAL).
    """
    if not steps:
        return 0.0
    gaming_verdicts = {
        "rule_lawyering", "metric_gaming",
        "replay_edge_case",
        "governance_loophole",
        "threshold_exploit",
        "uncertainty_abuse",
    }
    sus = sum(
        1 for s in steps
        if s.trust >= 0.90
        and s.verdict in gaming_verdicts
    )
    return sus / len(steps)


def opportunism_growth() -> float:
    """Late-minus-early opportunism share,
    clipped at 0."""
    e = _opportunism_share(
        trajectory()[:SHORT_WINDOW],
    )
    l = _opportunism_share(
        trajectory()[-SHORT_WINDOW:],
    )
    return _round(max(0.0, l - e))


def governance_erosion() -> float:
    """Fraction of steps with a gate_bypass
    flag. Should be 0."""
    n = len(trajectory())
    if n == 0:
        return 0.0
    return _round(sum(
        1 for s in trajectory() if s.gate_bypass
    ) / n)


def capture_risk() -> float:
    """Any drift in the governance_snapshot_hash
    across the trajectory indicates that the
    closed enum sets were redefined at runtime -
    structural capture."""
    hashes = {
        s.governance_snapshot_hash
        for s in trajectory()
    }
    return 0.0 if len(hashes) <= 1 else 1.0


def gate_violation_count() -> int:
    return sum(
        1 for s in trajectory() if s.gate_bypass
    )


def replay_stability() -> float:
    from .pressure_ecology import (
        replay_trajectory, trajectory,
    )
    a = [s.to_dict() for s in trajectory()]
    b = [
        s.to_dict()
        for s in replay_trajectory()
    ]
    return 1.0 if a == b else 0.0


__all__ = [
    "SHORT_WINDOW",
    "capture_risk",
    "gate_violation_count",
    "governance_erosion",
    "opportunism_growth",
    "replay_stability",
    "trust_collapse",
]
