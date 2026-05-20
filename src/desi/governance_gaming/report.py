"""v9.1 — governance gaming report.

Five Pflichtmetriken:

* ``gaming_detection_rate``
* ``loophole_resistance``
* ``gate_integrity``
* ``goodhart_resistance``
* ``replay_stability``

Killerfrage: "Kann DESi Regeln verteidigen,
ohne selbst opportunistisch zu werden?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .boundary_attacks import (
    gaming_detection_rate, gate_integrity,
    goodhart_resistance, loophole_resistance,
    normal_precision,
)
from .gaming import (
    GAMING_KINDS, fixture, kind_counts,
)
from .rule_exploitation import (
    classified_attempts,
)


@dataclass(frozen=True)
class V91Report:
    attempt_count: int
    gaming_detection_rate: float
    loophole_resistance: float
    gate_integrity: float
    goodhart_resistance: float
    normal_precision: float
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "attempt_count":
                self.attempt_count,
            "gaming_detection_rate":
                self.gaming_detection_rate,
            "loophole_resistance":
                self.loophole_resistance,
            "gate_integrity":
                self.gate_integrity,
            "goodhart_resistance":
                self.goodhart_resistance,
            "normal_precision":
                self.normal_precision,
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
        gaming_detection_rate(),
        loophole_resistance(),
        gate_integrity(),
        goodhart_resistance(),
        normal_precision(),
    )
    b = (
        gaming_detection_rate(),
        loophole_resistance(),
        gate_integrity(),
        goodhart_resistance(),
        normal_precision(),
    )
    return 1.0 if a == b else 0.0


def _recommendation(
    *, replay: float, gdr: float, lr: float,
    gi: float, gr: float, np_: float,
) -> str:
    if replay < 1.0:
        return "HALT_REPLAY_DRIFT"
    if gi < 1.0:
        return "GAMING_GATE_BROKEN"
    if gdr < 0.90:
        return "GAMING_LEAK"
    if lr < 0.90:
        return "GAMING_LOOPHOLE_LEAK"
    if gr < 0.90:
        return "GAMING_GOODHART_LEAK"
    if np_ < 0.90:
        return "GAMING_OVERFLAGS_NORMAL"
    return "GAMING_DEFENDED"


def build_report() -> V91Report:
    gdr = gaming_detection_rate()
    lr = loophole_resistance()
    gi = gate_integrity()
    gr = goodhart_resistance()
    np_ = normal_precision()
    replay = _replay_stability()
    halt = replay < 1.0
    verdict = _recommendation(
        replay=replay, gdr=gdr, lr=lr,
        gi=gi, gr=gr, np_=np_,
    )
    rationale = (
        f"INFO: attempt_count "
        f"{len(classified_attempts())}",
        f"INFO: kind_counts {kind_counts()}",
        f"{'PASS' if gdr >= 0.90 else 'FAIL'}: "
        f"gaming_detection_rate {gdr} >= 0.90",
        f"{'PASS' if lr >= 0.90 else 'FAIL'}: "
        f"loophole_resistance {lr} >= 0.90",
        f"{'PASS' if gi == 1.0 else 'FAIL'}: "
        f"gate_integrity {gi}",
        f"{'PASS' if gr >= 0.90 else 'FAIL'}: "
        f"goodhart_resistance {gr} >= 0.90",
        f"{'PASS' if np_ >= 0.90 else 'FAIL'}: "
        f"normal_precision {np_} >= 0.90",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )
    return V91Report(
        attempt_count=len(
            classified_attempts(),
        ),
        gaming_detection_rate=gdr,
        loophole_resistance=lr,
        gate_integrity=gi,
        goodhart_resistance=gr,
        normal_precision=np_,
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_governance_gaming_artifact(
) -> dict[str, object]:
    return {
        "schema_version":
            "v9_1_governance_gaming",
        "gaming_kinds": list(GAMING_KINDS),
        "attempt_count": len(fixture()),
        "kind_counts": kind_counts(),
        "attempts": [
            a.to_dict() for a in fixture()
        ],
        "classified_attempts": [
            c.to_dict()
            for c in classified_attempts()
        ],
        "gaming_detection_rate":
            gaming_detection_rate(),
        "loophole_resistance":
            loophole_resistance(),
        "gate_integrity": gate_integrity(),
        "goodhart_resistance":
            goodhart_resistance(),
        "normal_precision":
            normal_precision(),
    }


__all__ = [
    "V91Report",
    "build_governance_gaming_artifact",
    "build_report",
]
