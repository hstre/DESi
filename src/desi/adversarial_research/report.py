"""v13.2 — adversarial-research-manipulation
report.

Five Pflichtmetriken:

* ``manipulation_detection``
* ``false_certainty_rate``
* ``overclaim_detection``
* ``methodological_integrity``
* ``replay_stability``

Killerfrage: "Erkennt DESi wissenschaftliche
Manipulation - auch wenn sie sprachlich perfekt
aussieht?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .confidence_inflation import (
    detection_recall_on_inflated,
    false_certainty_rate,
    methodological_integrity,
)
from .manipulation import (
    MANIPULATION_KINDS, fixture, kind_counts,
)
from .overclaiming import (
    overclaim_detection,
)
from .selective_reporting import (
    classified_manipulations,
    manipulation_detection,
)


@dataclass(frozen=True)
class V132Report:
    claim_count: int
    manipulation_detection: float
    false_certainty_rate: float
    overclaim_detection: float
    methodological_integrity: float
    detection_recall_on_inflated: float
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "claim_count": self.claim_count,
            "manipulation_detection":
                self.manipulation_detection,
            "false_certainty_rate":
                self.false_certainty_rate,
            "overclaim_detection":
                self.overclaim_detection,
            "methodological_integrity":
                self.methodological_integrity,
            "detection_recall_on_inflated":
                (
                    self
                    .detection_recall_on_inflated
                ),
            "replay_stability":
                self.replay_stability,
            "halt": self.halt,
            "recommendation":
                self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def _replay_stability() -> float:
    a = (
        manipulation_detection(),
        false_certainty_rate(),
        overclaim_detection(),
        methodological_integrity(),
        detection_recall_on_inflated(),
    )
    b = (
        manipulation_detection(),
        false_certainty_rate(),
        overclaim_detection(),
        methodological_integrity(),
        detection_recall_on_inflated(),
    )
    return 1.0 if a == b else 0.0


def _recommendation(
    *, replay: float, md: float, ocd: float,
    mi: float, drinf: float,
) -> str:
    if replay < 1.0:
        return "HALT_REPLAY_DRIFT"
    if md < 0.90:
        return "MANIPULATION_LEAK"
    if ocd < 0.90:
        return "MANIPULATION_OVERCLAIM_LEAK"
    if drinf < 0.90:
        return "MANIPULATION_INFLATION_LEAK"
    if mi < 0.20:
        return "MANIPULATION_HONEST_SHRUNK"
    return "MANIPULATION_RESILIENT"


def build_report() -> V132Report:
    md = manipulation_detection()
    fcr = false_certainty_rate()
    ocd = overclaim_detection()
    mi = methodological_integrity()
    drinf = detection_recall_on_inflated()
    replay = _replay_stability()
    halt = replay < 1.0
    verdict = _recommendation(
        replay=replay, md=md, ocd=ocd,
        mi=mi, drinf=drinf,
    )
    rationale = (
        f"INFO: claim_count {len(fixture())}",
        f"INFO: kind_counts {kind_counts()}",
        f"INFO: detection_recall_on_inflated "
        f"{drinf}",
        f"{'PASS' if md >= 0.90 else 'FAIL'}: "
        f"manipulation_detection {md} >= 0.90",
        f"INFO: false_certainty_rate {fcr}",
        f"{'PASS' if ocd >= 0.90 else 'FAIL'}: "
        f"overclaim_detection {ocd} >= 0.90",
        f"INFO: methodological_integrity {mi}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )
    return V132Report(
        claim_count=len(fixture()),
        manipulation_detection=md,
        false_certainty_rate=fcr,
        overclaim_detection=ocd,
        methodological_integrity=mi,
        detection_recall_on_inflated=drinf,
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_adversarial_artifact(
) -> dict[str, object]:
    return {
        "schema_version":
            "v13_2_adversarial_research",
        "manipulation_kinds":
            list(MANIPULATION_KINDS),
        "claim_count": len(fixture()),
        "kind_counts": kind_counts(),
        "claims": [
            c.to_dict() for c in fixture()
        ],
        "classified_manipulations": [
            r.to_dict()
            for r in classified_manipulations()
        ],
        "manipulation_detection":
            manipulation_detection(),
        "false_certainty_rate":
            false_certainty_rate(),
        "overclaim_detection":
            overclaim_detection(),
        "methodological_integrity":
            methodological_integrity(),
        "detection_recall_on_inflated":
            detection_recall_on_inflated(),
    }


__all__ = [
    "V132Report",
    "build_adversarial_artifact",
    "build_report",
]
