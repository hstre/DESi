"""v9.2 — coalition-warfare report.

Five Pflichtmetriken:

* ``coalition_detection``
* ``consensus_integrity``
* ``dissent_preservation``
* ``lineage_stability``
* ``replay_stability``

Killerfrage: "Kann DESi epistemische Vielfalt
gegen koordinierte Narrative verteidigen?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .coalitions import (
    COALITION_ROLES, fixture, role_counts,
)
from .lineage import (
    coalition_detection, detected_coalitions,
    lineage_nodes, lineage_stability,
)
from .propagation import (
    consensus_integrity,
    dissent_preservation,
    isolated_preservation,
)


@dataclass(frozen=True)
class V92Report:
    broadcast_count: int
    coalition_count: int
    coalition_detection: float
    consensus_integrity: float
    dissent_preservation: float
    isolated_preservation: float
    lineage_stability: float
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "broadcast_count":
                self.broadcast_count,
            "coalition_count":
                self.coalition_count,
            "coalition_detection":
                self.coalition_detection,
            "consensus_integrity":
                self.consensus_integrity,
            "dissent_preservation":
                self.dissent_preservation,
            "isolated_preservation":
                self.isolated_preservation,
            "lineage_stability":
                self.lineage_stability,
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
        coalition_detection(),
        consensus_integrity(),
        dissent_preservation(),
        isolated_preservation(),
        lineage_stability(),
    )
    b = (
        coalition_detection(),
        consensus_integrity(),
        dissent_preservation(),
        isolated_preservation(),
        lineage_stability(),
    )
    return 1.0 if a == b else 0.0


def _recommendation(
    *, replay: float, cd: float, ci: float,
    dp: float, ip: float, ls: float,
) -> str:
    if replay < 1.0:
        return "HALT_REPLAY_DRIFT"
    if ls < 1.0:
        return "COALITION_LINEAGE_DRIFT"
    if dp < 1.0:
        return "COALITION_DISSENT_SUPPRESSED"
    if ip < 1.0:
        return "COALITION_ISOLATED_SWALLOWED"
    if cd < 0.90:
        return "COALITION_DETECTION_WEAK"
    if ci < 0.90:
        return "COALITION_CONSENSUS_FAKE"
    return "COALITION_RESILIENT"


def build_report() -> V92Report:
    cd = coalition_detection()
    ci = consensus_integrity()
    dp = dissent_preservation()
    ip = isolated_preservation()
    ls = lineage_stability()
    replay = _replay_stability()
    halt = replay < 1.0
    verdict = _recommendation(
        replay=replay, cd=cd, ci=ci,
        dp=dp, ip=ip, ls=ls,
    )
    rationale = (
        f"INFO: broadcast_count "
        f"{len(fixture())}",
        f"INFO: role_counts {role_counts()}",
        f"INFO: detected_coalition_count "
        f"{len(detected_coalitions())}",
        f"{'PASS' if cd >= 0.90 else 'FAIL'}: "
        f"coalition_detection {cd} >= 0.90",
        f"{'PASS' if ci >= 0.90 else 'FAIL'}: "
        f"consensus_integrity {ci} >= 0.90",
        f"{'PASS' if dp == 1.0 else 'FAIL'}: "
        f"dissent_preservation {dp}",
        f"{'PASS' if ip == 1.0 else 'FAIL'}: "
        f"isolated_preservation {ip}",
        f"{'PASS' if ls == 1.0 else 'FAIL'}: "
        f"lineage_stability {ls}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )
    return V92Report(
        broadcast_count=len(fixture()),
        coalition_count=len(
            detected_coalitions(),
        ),
        coalition_detection=cd,
        consensus_integrity=ci,
        dissent_preservation=dp,
        isolated_preservation=ip,
        lineage_stability=ls,
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_coalition_warfare_artifact(
) -> dict[str, object]:
    return {
        "schema_version":
            "v9_2_coalition_warfare",
        "coalition_roles":
            list(COALITION_ROLES),
        "broadcast_count": len(fixture()),
        "role_counts": role_counts(),
        "broadcasts": [
            b.to_dict() for b in fixture()
        ],
        "lineage": [
            n.to_dict()
            for n in lineage_nodes()
        ],
        "detected_coalitions": [
            {
                "root": root,
                "members": list(members),
            }
            for root, members in
            detected_coalitions()
        ],
        "coalition_detection":
            coalition_detection(),
        "consensus_integrity":
            consensus_integrity(),
        "dissent_preservation":
            dissent_preservation(),
        "isolated_preservation":
            isolated_preservation(),
        "lineage_stability":
            lineage_stability(),
    }


__all__ = [
    "V92Report",
    "build_coalition_warfare_artifact",
    "build_report",
]
