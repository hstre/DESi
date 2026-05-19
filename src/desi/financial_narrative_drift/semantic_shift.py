"""v15.1 - semantic_reframing signal.

Of all the narrative movement, how much is the
SPECIFIC re-spin of sober disclosure themes
(risk-transparency, compliance) into upbeat themes
(growth, innovation)? That directional reframing -
re-describing the same business as a brighter
story - is the audit-worthy part. NOT a fraud
claim.

Reads only the synthetic narrative trajectory.
"""
from __future__ import annotations

from .trajectory import (
    NarrativeTrajectory, Theme, trajectories,
)

_UPBEAT = (Theme.GROWTH, Theme.INNOVATION)
_SOBER = (Theme.RISK_TRANSPARENCY, Theme.COMPLIANCE)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _clip01(x: float) -> float:
    return max(0.0, min(1.0, x))


def _weight_vec(year) -> dict[str, float]:  # noqa: ANN001
    return {k: v for k, v in year.theme_weights}


def semantic_reframing_firm(
    tr: NarrativeTrajectory,
) -> float:
    """Net narrative weight shifted from sober
    themes into upbeat themes, first year to last,
    in [0, 1]. We average the upbeat gain and the
    sober loss so a one-sided artefact cannot
    inflate the score."""
    if len(tr.years) < 2:
        return 0.0
    first = _weight_vec(tr.years[0])
    last = _weight_vec(tr.years[-1])
    upbeat_gain = sum(
        max(0.0, last[t.value] - first[t.value])
        for t in _UPBEAT
    )
    sober_loss = sum(
        max(0.0, first[t.value] - last[t.value])
        for t in _SOBER
    )
    return _round(_clip01(
        0.5 * (upbeat_gain + sober_loss),
    ))


def semantic_reframing() -> float:
    """Corpus mean of per-firm semantic
    reframing."""
    trs = trajectories()
    if not trs:
        return 0.0
    vals = [
        semantic_reframing_firm(t) for t in trs
    ]
    return _round(sum(vals) / len(vals))


__all__ = [
    "semantic_reframing",
    "semantic_reframing_firm",
]
