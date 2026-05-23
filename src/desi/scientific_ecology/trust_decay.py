"""v13.3 — trust-integrity + dissent-
preservation metrics."""
from __future__ import annotations

from .ecology import trajectory
from .fraud_propagation import SHORT_WINDOW


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def trust_integrity() -> float:
    """Closed-enum verdicts must all sit in
    the closed sets across the full
    trajectory. If verdicts ever leak out of
    the closed enums, trust integrity drops.
    """
    rows = trajectory()
    if not rows:
        return 1.0
    bypasses = sum(
        1 for r in rows if r.gate_bypass
    )
    return _round(1.0 - bypasses / len(rows))


def dissent_preservation() -> float:
    """Fraction of long-horizon steps whose
    verdict is one of the dissent-shaped
    labels: WEAK, SUSPECT, BORDERLINE,
    SELECTIVE_REPORTING, CAUSAL_EXAGGERATION,
    etc. Dissent stays visible if these
    appear in the late window in roughly the
    same share as early."""
    rows = trajectory()
    if not rows:
        return 1.0
    dissent_labels = {
        "weak_set", "suspect",
        "borderline_set",
        "selective_reporting",
        "causal_exaggeration",
        "methodological_laundering",
    }
    late = rows[-SHORT_WINDOW:]
    early = rows[:SHORT_WINDOW]
    early_share = sum(
        1 for s in early
        if s.verdict in dissent_labels
    ) / max(len(early), 1)
    late_share = sum(
        1 for s in late
        if s.verdict in dissent_labels
    ) / max(len(late), 1)
    # Preservation: late share must be
    # at least 90 percent of the early share.
    if early_share == 0:
        return 1.0
    return _round(
        min(1.0, late_share / early_share),
    )


__all__ = [
    "dissent_preservation",
    "trust_integrity",
]
