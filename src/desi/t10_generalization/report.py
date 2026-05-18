"""v3.105 — hidden entanglement census report.

Pflichtmetriken (directive § v3.105):

* ``hidden_entanglement_count``
* ``family_count``
* ``entanglement_types``
* ``mean_information_loss``
* ``replay_stability``

Killerfrage: "War G/E ein Einzelfall?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .census import (
    all_entanglement_instances,
    all_entanglement_types,
    candidate_families,
)
from .detect import (
    entanglement_type_count,
    family_count_in_entanglements,
    hidden_entanglement_count,
    mean_information_loss,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V3105Report:
    candidate_family_count: int
    hidden_entanglement_count: int
    family_count: int
    entanglement_type_count: int
    entanglement_types: tuple[dict, ...]
    mean_information_loss: float
    entanglement_instances: tuple[dict, ...]
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "candidate_family_count":
                self.candidate_family_count,
            "hidden_entanglement_count":
                self.hidden_entanglement_count,
            "family_count": self.family_count,
            "entanglement_type_count":
                self.entanglement_type_count,
            "entanglement_types":
                list(self.entanglement_types),
            "mean_information_loss":
                self.mean_information_loss,
            "entanglement_instances":
                list(self.entanglement_instances),
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
        hidden_entanglement_count(),
        family_count_in_entanglements(),
        entanglement_type_count(),
        mean_information_loss(),
    )
    b = (
        hidden_entanglement_count(),
        family_count_in_entanglements(),
        entanglement_type_count(),
        mean_information_loss(),
    )
    return 1.0 if a == b else 0.0


def build_report() -> V3105Report:
    fams = candidate_families()
    insts = all_entanglement_instances()
    types = all_entanglement_types()
    hec = hidden_entanglement_count()
    fc = family_count_in_entanglements()
    tc = entanglement_type_count()
    mil = mean_information_loss()
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif hec > 0 and tc > 1:
        verdict = "ENTANGLEMENTS_PERVASIVE"
    elif hec > 0:
        verdict = "ENTANGLEMENT_TYPE_FOUND"
    else:
        verdict = "GE_WAS_ISOLATED_CASE"

    rationale = (
        f"INFO: candidate_family_count "
        f"{len(fams)}",
        f"INFO: hidden_entanglement_count "
        f"{hec} (cross-family pairs)",
        f"INFO: family_count {fc}",
        f"INFO: entanglement_type_count {tc}",
        f"INFO: mean_information_loss {mil}",
        f"INFO: entanglement_types "
        f"{[t for t in types]}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V3105Report(
        candidate_family_count=len(fams),
        hidden_entanglement_count=hec,
        family_count=fc,
        entanglement_type_count=tc,
        entanglement_types=tuple(
            t.to_dict() for t in types
            if len(t.families) >= 2
        ),
        mean_information_loss=mil,
        entanglement_instances=tuple(
            i.to_dict() for i in insts
        ),
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_t10_hidden_entanglements_artifact(
) -> dict[str, object]:
    fams = candidate_families()
    insts = all_entanglement_instances()
    types = all_entanglement_types()
    return {
        "schema_version":
            "v3_105_t10_hidden_entanglements",
        "candidate_family_count": len(fams),
        "hidden_entanglement_count":
            hidden_entanglement_count(),
        "family_count":
            family_count_in_entanglements(),
        "entanglement_type_count":
            entanglement_type_count(),
        "mean_information_loss":
            mean_information_loss(),
        "candidate_families": [
            f.to_dict() for f in fams
        ],
        "entanglement_types": [
            t.to_dict() for t in types
            if len(t.families) >= 2
        ],
        "entanglement_instances": [
            i.to_dict() for i in insts
        ],
    }


__all__ = [
    "V3105Report",
    "build_report",
    "build_t10_hidden_entanglements_artifact",
]
