"""v3.98 — downstream equivalence report.

Pflichtmetriken (directive § v3.98):

* ``verdict_overlap``
* ``path_overlap``
* ``intervention_overlap``
* ``outcome_divergence``
* ``failure_class_overlap``
* ``replay_stability``

Concept Gate condition #2: verdict_overlap >=
0.90. Killerfrage: "Verhalten sich die
Doppelgaenger downstream wirklich gleich?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from ..entangled.variance import (
    ENTANGLED_FAMILY_IDS,
)
from .equivalence import (
    AxisOverlap,
    all_axis_overlaps,
    audit_outcome_overlap,
    failure_class_overlap,
    intervention_overlap,
    outcome_divergence,
    path_overlap,
    rescue_eligibility_overlap,
    rollback_overlap,
    verdict_overlap,
)
from .outcomes import (
    all_downstream_signatures,
)


VERDICT_OVERLAP_THRESHOLD: float = 0.90


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V398Report:
    entangled_family_ids: tuple[str, ...]
    verdict_overlap: float
    path_overlap: float
    intervention_overlap: float
    failure_class_overlap: float
    audit_outcome_overlap: float
    rescue_eligibility_overlap: float
    rollback_overlap: float
    outcome_divergence: float
    axis_overlaps: tuple[dict, ...]
    downstream_signatures: tuple[dict, ...]
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "entangled_family_ids":
                list(self.entangled_family_ids),
            "verdict_overlap":
                self.verdict_overlap,
            "path_overlap": self.path_overlap,
            "intervention_overlap":
                self.intervention_overlap,
            "failure_class_overlap":
                self.failure_class_overlap,
            "audit_outcome_overlap":
                self.audit_outcome_overlap,
            "rescue_eligibility_overlap":
                self.rescue_eligibility_overlap,
            "rollback_overlap":
                self.rollback_overlap,
            "outcome_divergence":
                self.outcome_divergence,
            "axis_overlaps":
                list(self.axis_overlaps),
            "downstream_signatures":
                list(self.downstream_signatures),
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
    a = (
        verdict_overlap(), path_overlap(),
        intervention_overlap(),
        outcome_divergence(),
        failure_class_overlap(),
    )
    b = (
        verdict_overlap(), path_overlap(),
        intervention_overlap(),
        outcome_divergence(),
        failure_class_overlap(),
    )
    return 1.0 if a == b else 0.0


def build_report() -> V398Report:
    vo = verdict_overlap()
    po = path_overlap()
    io_ = intervention_overlap()
    fco = failure_class_overlap()
    aoo = audit_outcome_overlap()
    reo = rescue_eligibility_overlap()
    ro = rollback_overlap()
    od = outcome_divergence()
    axes = all_axis_overlaps()
    sigs = all_downstream_signatures()
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif (
        vo >= VERDICT_OVERLAP_THRESHOLD
        and od < 0.10
    ):
        verdict = "DOWNSTREAM_FULLY_EQUIVALENT"
    elif vo >= VERDICT_OVERLAP_THRESHOLD:
        verdict = "DOWNSTREAM_VERDICT_EQUIVALENT"
    else:
        verdict = "DOWNSTREAM_DIVERGES"

    rationale = (
        f"INFO: entangled_family_ids "
        f"{list(ENTANGLED_FAMILY_IDS)}",
        f"{'PASS' if vo >= VERDICT_OVERLAP_THRESHOLD else 'FAIL'}: "
        f"verdict_overlap {vo} "
        f"(threshold "
        f"{VERDICT_OVERLAP_THRESHOLD})",
        f"INFO: path_overlap {po}",
        f"INFO: intervention_overlap {io_}",
        f"INFO: failure_class_overlap {fco}",
        f"INFO: audit_outcome_overlap {aoo}",
        f"INFO: rescue_eligibility_overlap {reo}",
        f"INFO: rollback_overlap {ro}",
        f"INFO: outcome_divergence {od}",
        f"INFO: axis_overlaps "
        f"{[a.to_dict() for a in axes]}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V398Report(
        entangled_family_ids=ENTANGLED_FAMILY_IDS,
        verdict_overlap=vo,
        path_overlap=po,
        intervention_overlap=io_,
        failure_class_overlap=fco,
        audit_outcome_overlap=aoo,
        rescue_eligibility_overlap=reo,
        rollback_overlap=ro,
        outcome_divergence=od,
        axis_overlaps=tuple(
            a.to_dict() for a in axes
        ),
        downstream_signatures=tuple(
            s.to_dict() for s in sigs
        ),
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_downstream_equivalence_artifact(
) -> dict[str, object]:
    axes = all_axis_overlaps()
    sigs = all_downstream_signatures()
    return {
        "schema_version":
            "v3_98_downstream_equivalence",
        "entangled_family_ids":
            list(ENTANGLED_FAMILY_IDS),
        "verdict_overlap": verdict_overlap(),
        "path_overlap": path_overlap(),
        "intervention_overlap":
            intervention_overlap(),
        "failure_class_overlap":
            failure_class_overlap(),
        "outcome_divergence":
            outcome_divergence(),
        "axis_overlaps": [
            a.to_dict() for a in axes
        ],
        "downstream_signatures": [
            s.to_dict() for s in sigs
        ],
    }


__all__ = [
    "VERDICT_OVERLAP_THRESHOLD",
    "V398Report",
    "build_downstream_equivalence_artifact",
    "build_report",
]
