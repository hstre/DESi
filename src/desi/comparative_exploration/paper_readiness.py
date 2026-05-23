"""v21.0 - paper-readiness scoring.

A composite score over the publication checklist: does the
dual-agent design (a) add novelty, (b) add diversity,
(c) keep hallucination safe, (d) keep authority safe,
(e) preserve replay, and (f) pass its own concept gate? The
score is the fraction of these criteria met.
"""
from __future__ import annotations

from .comparison import (
    delta_authority_drift, delta_exploration_diversity,
    delta_hallucination_pressure, delta_novelty_gain,
    delta_replay_stability, dual_agent_gate_passed,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def readiness_checklist() -> dict[str, bool]:
    return {
        "novelty_improved": delta_novelty_gain() > 0.0,
        "diversity_improved": (
            delta_exploration_diversity() > 0.0
        ),
        "hallucination_safe": (
            delta_hallucination_pressure() <= 0.10
        ),
        "authority_safe": delta_authority_drift() <= 0.05,
        "replay_preserved": delta_replay_stability() == 0.0,
        "dual_agent_gate_passed": dual_agent_gate_passed(),
    }


def paper_readiness_score() -> float:
    """Fraction of the publication-readiness criteria met,
    in [0, 1]."""
    checks = readiness_checklist()
    if not checks:
        return 0.0
    met = sum(1 for v in checks.values() if v)
    return _round(met / len(checks))


__all__ = [
    "paper_readiness_score",
    "readiness_checklist",
]
