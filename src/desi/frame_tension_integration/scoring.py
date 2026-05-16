"""Aufgaben 4–8 — metrics + composite integration score.

Per-insertion-point metrics computed deterministically over the
simulation outcomes:

* ``tension_detection_rate`` — fraction of adversarial cases
  blocked specifically as ``FRAME_INHERITANCE_BLOCKED``
  (TENSION block).
* ``manipulation_block_rate`` — fraction of adversarial cases
  blocked under *any* of the three block events.
* ``false_block_rate`` — fraction of CONFIRMED-expected
  benign cases that were nonetheless blocked.
* ``undecidable_rate`` — fraction of *all* cases falling into
  ``FRAME_UNDECIDABLE_BLOCKED``.
* ``contamination_risk`` — fraction of CONFIRMED-expected
  benign cases that were incorrectly *allowed* with a wrong
  observed consistency, **OR** at POST_ROUTING the fraction
  of adversarial cases that escaped the upstream gate.
* ``late_block_rate`` — POST_ROUTING-specific: every block
  event counts as late. Always 0 at other insertion points
  by definition.
* ``recovered_manipulations`` — POST_ROUTING-specific: number
  of adversarial cases blocked late.

Composite ``integration_score`` (Aufgabe 8), normalised to
[0, 1]:

    raw  = manipulation_block_rate + tension_detection_rate
         - false_block_rate - contamination_risk - undecidable_rate
    score = clamp((raw + 2.0) / 4.0, 0.0, 1.0)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .enums import InsertionPoint
from .simulators import SimulationOutcome


@dataclass(frozen=True)
class InsertionMetrics:
    insertion_point: InsertionPoint
    total: int
    adversarial: int
    benign: int
    tension_detection_rate: float
    manipulation_block_rate: float
    false_block_rate: float
    undecidable_rate: float
    contamination_risk: float
    late_block_rate: float
    recovered_manipulations: int
    integration_score: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "insertion_point": self.insertion_point.value,
            "total": self.total,
            "adversarial": self.adversarial,
            "benign": self.benign,
            "tension_detection_rate": self.tension_detection_rate,
            "manipulation_block_rate": self.manipulation_block_rate,
            "false_block_rate": self.false_block_rate,
            "undecidable_rate": self.undecidable_rate,
            "contamination_risk": self.contamination_risk,
            "late_block_rate": self.late_block_rate,
            "recovered_manipulations": self.recovered_manipulations,
            "integration_score": self.integration_score,
        }


_BLOCK_EVENTS: frozenset[str] = frozenset({
    "frame_inheritance_blocked",
    "frame_conflict_blocked",
    "frame_undecidable_blocked",
})


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def _integration_score(
    *,
    manipulation_block_rate: float,
    tension_detection_rate: float,
    false_block_rate: float,
    contamination_risk: float,
    undecidable_rate: float,
) -> float:
    raw = (
        manipulation_block_rate
        + tension_detection_rate
        - false_block_rate
        - contamination_risk
        - undecidable_rate
    )
    # Raw lives in [-3, +2]; shift+scale into [0, 1].
    return round(_clamp((raw + 3.0) / 5.0, 0.0, 1.0), 6)


def compute_metrics(
    point: InsertionPoint,
    outcomes: tuple[SimulationOutcome, ...],
) -> InsertionMetrics:
    total = len(outcomes)
    adversarial = sum(1 for o in outcomes if o.is_adversarial)
    benign = total - adversarial

    benign_outcomes = [o for o in outcomes if not o.is_adversarial]
    adv_outcomes    = [o for o in outcomes if o.is_adversarial]

    # tension_detection_rate: of adversarial, fraction with TENSION
    # block event.
    tension_block = sum(
        1 for o in adv_outcomes
        if o.event == "frame_inheritance_blocked"
    )
    tension_detection_rate = (
        round(tension_block / adversarial, 6) if adversarial else 0.0
    )

    # manipulation_block_rate: of adversarial, fraction blocked
    # under any of the three block events.
    manip_blocked = sum(
        1 for o in adv_outcomes if o.event in _BLOCK_EVENTS
    )
    manipulation_block_rate = (
        round(manip_blocked / adversarial, 6) if adversarial else 0.0
    )

    # false_block_rate: of benign cases expected to be CONFIRMED,
    # fraction that the layer blocked.
    confirmed_expected = [
        o for o in benign_outcomes if o.expected_consistency == "confirmed"
    ]
    false_blocks = sum(
        1 for o in confirmed_expected if o.event in _BLOCK_EVENTS
    )
    false_block_rate = (
        round(false_blocks / len(confirmed_expected), 6)
        if confirmed_expected else 0.0
    )

    # undecidable_rate over *all* cases.
    undecidable = sum(
        1 for o in outcomes if o.event == "frame_undecidable_blocked"
    )
    undecidable_rate = (
        round(undecidable / total, 6) if total else 0.0
    )

    # contamination_risk
    if point is InsertionPoint.POST_ROUTING:
        # At POST_ROUTING the gate runs *after* the claim has
        # already been routed to a downstream pipeline. Every
        # adversarial that ends up blocked here is contamination
        # by definition — the wrong pipeline already saw it. Even
        # a perfect block rate at this point means perfect
        # post-hoc audit, not gating.
        contamination_risk = (
            round(manip_blocked / total, 6) if total else 0.0
        )
    else:
        # Benign cases that the layer wrongly *allowed* with a
        # mismatched observed consistency (e.g. observed TENSION
        # but allowed=True — shouldn't happen with the v3.11
        # mapping, but we measure it explicitly).
        wrong_allow = sum(
            1 for o in benign_outcomes
            if o.inherited_allowed and o.observed_consistency
            != "confirmed"
        )
        contamination_risk = (
            round(wrong_allow / benign, 6) if benign else 0.0
        )

    if point is InsertionPoint.POST_ROUTING:
        late_blocks = sum(
            1 for o in outcomes if o.event in _BLOCK_EVENTS
        )
        late_block_rate = (
            round(late_blocks / total, 6) if total else 0.0
        )
        recovered_manipulations = sum(
            1 for o in adv_outcomes if o.event in _BLOCK_EVENTS
        )
    else:
        late_block_rate = 0.0
        recovered_manipulations = 0

    score = _integration_score(
        manipulation_block_rate=manipulation_block_rate,
        tension_detection_rate=tension_detection_rate,
        false_block_rate=false_block_rate,
        contamination_risk=contamination_risk,
        undecidable_rate=undecidable_rate,
    )

    return InsertionMetrics(
        insertion_point=point,
        total=total,
        adversarial=adversarial,
        benign=benign,
        tension_detection_rate=tension_detection_rate,
        manipulation_block_rate=manipulation_block_rate,
        false_block_rate=false_block_rate,
        undecidable_rate=undecidable_rate,
        contamination_risk=contamination_risk,
        late_block_rate=late_block_rate,
        recovered_manipulations=recovered_manipulations,
        integration_score=score,
    )


__all__ = [
    "InsertionMetrics",
    "compute_metrics",
]
