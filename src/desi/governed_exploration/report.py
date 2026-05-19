"""v12.1 — DESi-governed exploration report.

Five Pflichtmetriken:

* ``redundancy_reduction``
* ``hallucination_containment``
* ``innovation_preservation``
* ``search_governance``
* ``replay_stability``

Killerfrage: "Kann DESi Kreativitaet
domestizieren ohne sie zu zerstoeren?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .blindness import (
    blindness_share, covered_share,
)
from .compression import (
    compressed_groups, compression_count,
    redundancy_reduction,
)
from .recoverability import (
    recoverability_index, recoverable_share,
)
from .risk_control import (
    hallucination_containment,
    innovation_preservation, mean_risk,
    search_governance,
)


@dataclass(frozen=True)
class V121Report:
    redundancy_reduction: float
    hallucination_containment: float
    innovation_preservation: float
    search_governance: float
    recoverability_index: float
    blindness_share: float
    mean_risk: float
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "redundancy_reduction":
                self.redundancy_reduction,
            "hallucination_containment":
                self.hallucination_containment,
            "innovation_preservation":
                self.innovation_preservation,
            "search_governance":
                self.search_governance,
            "recoverability_index":
                self.recoverability_index,
            "blindness_share":
                self.blindness_share,
            "mean_risk": self.mean_risk,
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
        redundancy_reduction(),
        hallucination_containment(),
        innovation_preservation(),
        search_governance(),
        recoverability_index(),
        blindness_share(),
        mean_risk(),
    )
    b = (
        redundancy_reduction(),
        hallucination_containment(),
        innovation_preservation(),
        search_governance(),
        recoverability_index(),
        blindness_share(),
        mean_risk(),
    )
    return 1.0 if a == b else 0.0


def _recommendation(
    *, replay: float, rr: float, hc: float,
    ip: float, sg: float,
) -> str:
    if replay < 1.0:
        return "HALT_REPLAY_DRIFT"
    if hc < 1.0:
        return "GOVERNED_HALLUCINATION_LEAK"
    if sg < 0.95:
        return "GOVERNED_GOVERNANCE_BREACH"
    if ip < 0.70:
        return "GOVERNED_OVER_PRUNED"
    if rr < 0.30:
        return "GOVERNED_NEGLIGIBLE_COMPRESSION"
    return "GOVERNED_BALANCED"


def build_report() -> V121Report:
    rr = redundancy_reduction()
    hc = hallucination_containment()
    ip = innovation_preservation()
    sg = search_governance()
    ri = recoverability_index()
    bs = blindness_share()
    mr = mean_risk()
    replay = _replay_stability()
    halt = replay < 1.0
    verdict = _recommendation(
        replay=replay, rr=rr, hc=hc,
        ip=ip, sg=sg,
    )
    rationale = (
        f"INFO: group_count "
        f"{compression_count()}",
        f"INFO: covered_share "
        f"{covered_share()}",
        f"INFO: mean_risk {mr}",
        f"{'PASS' if rr >= 0.30 else 'FAIL'}: "
        f"redundancy_reduction {rr} >= 0.30",
        f"{'PASS' if hc == 1.0 else 'FAIL'}: "
        f"hallucination_containment {hc}",
        f"{'PASS' if ip >= 0.70 else 'FAIL'}: "
        f"innovation_preservation {ip} "
        f">= 0.70",
        f"{'PASS' if sg >= 0.95 else 'FAIL'}: "
        f"search_governance {sg} >= 0.95",
        f"INFO: recoverability_index {ri}",
        f"INFO: blindness_share {bs}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )
    return V121Report(
        redundancy_reduction=rr,
        hallucination_containment=hc,
        innovation_preservation=ip,
        search_governance=sg,
        recoverability_index=ri,
        blindness_share=bs,
        mean_risk=mr,
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_governed_exploration_artifact(
) -> dict[str, object]:
    return {
        "schema_version":
            "v12_1_governed_exploration",
        "group_count": compression_count(),
        "compressed_groups": [
            {
                "key": key,
                "members": list(members),
            }
            for key, members in compressed_groups()
        ],
        "redundancy_reduction":
            redundancy_reduction(),
        "hallucination_containment":
            hallucination_containment(),
        "innovation_preservation":
            innovation_preservation(),
        "search_governance":
            search_governance(),
        "recoverability_index":
            recoverability_index(),
        "recoverable_share":
            recoverable_share(),
        "blindness_share": blindness_share(),
        "covered_share": covered_share(),
        "mean_risk": mean_risk(),
    }


__all__ = [
    "V121Report",
    "build_governed_exploration_artifact",
    "build_report",
]
