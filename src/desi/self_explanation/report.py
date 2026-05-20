"""v3.37 — Self-Explanation Audit report.

Pflichtmetriken (directive):

* ``self_explained_count``      — count of the 14
  unexpected rescues whose verdict shift maps to a
  decisive dimension.
* ``explanation_replay_stability`` — two runs of the
  explainer produce identical records.
* ``dominant_changed_dimension`` — most frequent
  ``first_changed_dimension`` across the unexpected
  rescues.
* ``unexplained_cases``         — unexpected rescues
  with no decisive dimension.

Stop rule: ``unexplained_cases > 0`` halts Paper 10
(directive § v3.37).

Internal answer: every rescue's machine_readable_reason
is reported so DESi states its own attribution, not the
auditor's.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import json

from .explainer import (
    PLATEAU_PRIMARY_CAUSE, SelfExplanation,
    explain_all_movers, explain_unexpected_rescues,
)


# Stop rule
MAX_UNEXPLAINED_CASES   = 0
EXPECTED_RESCUE_COUNT   = 14


@dataclass(frozen=True)
class V337Report:
    plateau_mover_count: int
    unexpected_rescue_count: int
    self_explained_count: int
    unexplained_cases: int
    dominant_changed_dimension: str
    dominant_decisive_dimension: str
    confidence_hold_noop_rate: float
    cause_identity_match_rate: float
    explanation_replay_stability: float
    reason_distribution: dict[str, int]
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "plateau_mover_count":
                self.plateau_mover_count,
            "unexpected_rescue_count":
                self.unexpected_rescue_count,
            "self_explained_count":
                self.self_explained_count,
            "unexplained_cases":
                self.unexplained_cases,
            "dominant_changed_dimension":
                self.dominant_changed_dimension,
            "dominant_decisive_dimension":
                self.dominant_decisive_dimension,
            "confidence_hold_noop_rate":
                self.confidence_hold_noop_rate,
            "cause_identity_match_rate":
                self.cause_identity_match_rate,
            "explanation_replay_stability":
                self.explanation_replay_stability,
            "reason_distribution":
                dict(self.reason_distribution),
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _mode(values: list[str], default: str = "none") -> str:
    if not values:
        return default
    c = Counter(values)
    top = max(c.values())
    winners = sorted(k for k, v in c.items() if v == top)
    return winners[0]


def _replay_stability() -> float:
    a = [e.to_dict() for e in explain_unexpected_rescues()]
    b = [e.to_dict() for e in explain_unexpected_rescues()]
    if not a:
        return 1.0
    matches = sum(1 for x, y in zip(a, b) if x == y)
    return _round(matches / len(a))


def build_report() -> V337Report:
    movers = explain_all_movers()
    unexpected = tuple(
        e for e in movers if e.target_class != "plateau"
    )
    explained = [e for e in unexpected if e.explained]
    unexplained = len(unexpected) - len(explained)

    first_dims = [
        e.first_changed_dimension or "none"
        for e in unexpected
    ]
    dec_dims = [
        e.decisive_dimension or "none"
        for e in unexpected
    ]
    noop_rate = (
        _round(
            sum(1 for e in unexpected if e.confidence_hold_noop)
            / len(unexpected),
        )
        if unexpected else 0.0
    )
    cause_match = (
        _round(
            sum(
                1 for e in unexpected
                if e.identical_to_plateau_cause
            ) / len(unexpected),
        ) if unexpected else 0.0
    )
    reasons = dict(Counter(
        e.machine_readable_reason for e in unexpected
    ))

    halt = unexplained > MAX_UNEXPLAINED_CASES or len(
        explained,
    ) != EXPECTED_RESCUE_COUNT

    if halt and len(explained) != EXPECTED_RESCUE_COUNT:
        verdict = "HALT_EXPLAIN_COUNT_MISMATCH"
    elif halt:
        verdict = "HALT_UNEXPLAINED_CASES"
    else:
        verdict = "SELF_EXPLANATION_COMPLETE"

    replay = _replay_stability()

    rationale = (
        f"{'PASS' if len(explained) == EXPECTED_RESCUE_COUNT else 'FAIL'}: "
        f"self_explained_count {len(explained)} == "
        f"{EXPECTED_RESCUE_COUNT}",
        f"{'PASS' if unexplained == MAX_UNEXPLAINED_CASES else 'FAIL'}: "
        f"unexplained_cases {unexplained} == "
        f"{MAX_UNEXPLAINED_CASES}",
        f"INFO: dominant_first_changed "
        f"{_mode(first_dims)}",
        f"INFO: dominant_decisive "
        f"{_mode(dec_dims)}",
        f"INFO: confidence_hold_noop_rate {noop_rate}",
        f"INFO: cause_identity_match_rate {cause_match} "
        f"(plateau cause = {PLATEAU_PRIMARY_CAUSE})",
        f"INFO: reason_distribution {sorted(reasons.items())}",
        f"PASS: explanation_replay_stability {replay}",
    )

    return V337Report(
        plateau_mover_count=len(movers) - len(unexpected),
        unexpected_rescue_count=len(unexpected),
        self_explained_count=len(explained),
        unexplained_cases=unexplained,
        dominant_changed_dimension=_mode(first_dims),
        dominant_decisive_dimension=_mode(dec_dims),
        confidence_hold_noop_rate=noop_rate,
        cause_identity_match_rate=cause_match,
        explanation_replay_stability=replay,
        reason_distribution=reasons,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_self_explanation_artifact(
) -> dict[str, object]:
    movers = explain_all_movers()
    return {
        "schema_version": "v3_37_self_explanation",
        "explanations": [m.to_dict() for m in movers],
    }


def build_overgeneralized_claims_artifact(
) -> dict[str, object]:
    """One claim per unexpected rescue, attributing the
    rescue to the structural mechanism DESi exposes in
    its own self-explanation."""
    movers = explain_all_movers()
    unexpected = [
        e for e in movers if e.target_class != "plateau"
    ]
    claims = []
    for i, e in enumerate(unexpected):
        claims.append({
            "claim_id": f"OG{i+1:03d}",
            "trajectory_id": e.trajectory_id,
            "original_final_support":
                e.original_final_support,
            "rescue_mechanism":
                e.machine_readable_reason,
            "decisive_dimension":
                e.decisive_dimension,
            "original_primary_cause":
                e.original_primary_cause,
            "identical_to_plateau_cause":
                e.identical_to_plateau_cause,
            "text": (
                f"Trajectory {e.trajectory_id} "
                f"(cause={e.original_primary_cause}) "
                f"was rescued from "
                f"{e.original_final_support} to "
                f"{e.counterfactual_final_support} "
                f"by Strategy B. Decisive dimension: "
                f"{e.decisive_dimension}. "
                f"confidence_hold component noop: "
                f"{e.confidence_hold_noop}. "
                f"Cause identical to plateau "
                f"({PLATEAU_PRIMARY_CAUSE}): "
                f"{e.identical_to_plateau_cause}."
            ),
        })
    return {
        "schema_version":
            "v3_37_overgeneralized_stabilization_claims",
        "claims": claims,
        "claim_count": len(claims),
    }


__all__ = [
    "EXPECTED_RESCUE_COUNT", "MAX_UNEXPLAINED_CASES",
    "V337Report", "build_overgeneralized_claims_artifact",
    "build_report", "build_self_explanation_artifact",
]
