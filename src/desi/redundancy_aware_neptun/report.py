"""v3.80 — redundancy-aware Neptun report.

Pflichtmetriken (directive § v3.80):

* ``redundancy_aware_high_removal``
* ``redundancy_aware_redundant_removal``
* ``gate1_recovered``
* ``localization_accuracy``
* ``candidate_match_score``
* ``false_missing_claim_rate``
* ``replay_stability``

Concept gate #4 (Redundancy Masking):
``gate1_recovered = true``.
"""
from __future__ import annotations

from dataclasses import dataclass
import json

from ..redundancy_masking.equivalence import (
    PROBE_RADIUS, redundancy_classes,
)
from .masking import (
    ClassRemovalOutcome,
    all_class_removal_outcomes,
)
from .neptun_retest import (
    ClassLocalization,
    all_class_localizations,
    candidate_match_score,
    false_missing_claim_rate,
    localization_accuracy,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V380Report:
    probe_radius: float
    class_removal_outcomes: tuple[dict, ...]
    redundancy_aware_high_removal: int
    redundancy_aware_redundant_removal: int
    gate1_recovered: bool
    class_localizations: tuple[dict, ...]
    localization_accuracy: float
    candidate_match_score: float
    false_missing_claim_rate: float
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "probe_radius": self.probe_radius,
            "class_removal_outcomes":
                list(self.class_removal_outcomes),
            "redundancy_aware_high_removal":
                self.redundancy_aware_high_removal,
            "redundancy_aware_redundant_removal":
                self.redundancy_aware_redundant_removal,
            "gate1_recovered":
                self.gate1_recovered,
            "class_localizations":
                list(self.class_localizations),
            "localization_accuracy":
                self.localization_accuracy,
            "candidate_match_score":
                self.candidate_match_score,
            "false_missing_claim_rate":
                self.false_missing_claim_rate,
            "replay_stability":
                self.replay_stability,
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def _replay_stability() -> float:
    a = [
        o.to_dict()
        for o in all_class_removal_outcomes()
    ]
    b = [
        o.to_dict()
        for o in all_class_removal_outcomes()
    ]
    if not a:
        return 1.0
    matches = sum(1 for x, y in zip(a, b) if x == y)
    return _round(matches / len(a))


def build_report() -> V380Report:
    outcomes = all_class_removal_outcomes()
    classes = redundancy_classes()
    # The HIGH class is the one with the largest
    # coverage size.
    high_class = max(
        classes, key=lambda c: c.coverage_size,
    )
    high_outcome = next(
        o for o in outcomes
        if o.class_id == high_class.class_id
    )
    high_removal = high_outcome.perturbation_magnitude
    # "Redundant removal" = removing ONE member of
    # the high class (still redundant within class).
    redundant_removal = high_outcome.single_member_perturbation
    gate1 = high_removal > redundant_removal

    locs = all_class_localizations()
    loc_acc = localization_accuracy(locs)
    cand_score = candidate_match_score(locs)
    fmcr = false_missing_claim_rate()
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif gate1 and loc_acc >= 0.70:
        verdict = "GATE1_RECOVERED"
    elif gate1:
        verdict = "GATE1_PARTIAL_RECOVERY"
    else:
        verdict = "GATE1_NOT_RECOVERED"

    rationale = (
        f"INFO: probe_radius {PROBE_RADIUS}",
        f"INFO: class_removal_outcomes "
        f"{[o.to_dict() for o in outcomes]}",
        f"INFO: redundancy_aware_high_removal "
        f"{high_removal} (class {high_class.class_id} "
        f"with coverage_size {high_class.coverage_size})",
        f"INFO: redundancy_aware_redundant_removal "
        f"{redundant_removal} (single member of the "
        f"same class)",
        f"{'PASS' if gate1 else 'FAIL'}: "
        f"gate1_recovered "
        f"({high_removal} > {redundant_removal})",
        f"INFO: localization_accuracy {loc_acc}",
        f"INFO: candidate_match_score {cand_score}",
        f"INFO: false_missing_claim_rate {fmcr}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V380Report(
        probe_radius=PROBE_RADIUS,
        class_removal_outcomes=tuple(
            o.to_dict() for o in outcomes
        ),
        redundancy_aware_high_removal=high_removal,
        redundancy_aware_redundant_removal=(
            redundant_removal
        ),
        gate1_recovered=gate1,
        class_localizations=tuple(
            l.to_dict() for l in locs
        ),
        localization_accuracy=loc_acc,
        candidate_match_score=cand_score,
        false_missing_claim_rate=fmcr,
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_redundancy_aware_neptun_artifact(
) -> dict[str, object]:
    return {
        "schema_version":
            "v3_80_redundancy_aware_neptun",
        "probe_radius": PROBE_RADIUS,
        "class_removal_outcomes": [
            o.to_dict()
            for o in all_class_removal_outcomes()
        ],
        "class_localizations": [
            l.to_dict()
            for l in all_class_localizations()
        ],
    }


def build_redundancy_masking_claims_artifact(
) -> dict[str, object]:
    """One claim per redundancy class, documenting
    the masking observed in v3.73 and the unmasking
    achieved by class-level removal in v3.80."""
    outcomes = all_class_removal_outcomes()
    claims = []
    for i, o in enumerate(outcomes):
        claims.append({
            "claim_id": f"RM{i+1:03d}",
            "class_id": o.class_id,
            "coverage_size": o.coverage_size,
            "members": list(o.members),
            "single_member_perturbation":
                o.single_member_perturbation,
            "class_removal_perturbation":
                o.perturbation_magnitude,
            "masking_observed":
                o.single_member_perturbation == 0
                and o.perturbation_magnitude > 0,
            "text": (
                f"Class {o.class_id} (coverage_size "
                f"{o.coverage_size}, "
                f"{len(o.members)} members): "
                f"removing one member loses "
                f"{o.single_member_perturbation} "
                f"leakages; removing the entire "
                f"class loses "
                f"{o.perturbation_magnitude}. "
                f"Masking observed: "
                f"{o.single_member_perturbation == 0 and o.perturbation_magnitude > 0}."
            ),
        })
    return {
        "schema_version":
            "v3_80_redundancy_masking_claims",
        "claims": claims,
        "claim_count": len(claims),
    }


__all__ = [
    "V380Report",
    "build_redundancy_aware_neptun_artifact",
    "build_redundancy_masking_claims_artifact",
    "build_report",
]
