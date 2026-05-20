"""v11.2 — tactical-stress report.

Five Pflichtmetriken:

* ``tactical_miss_rate``
* ``horizon_risk``
* ``critical_line_preservation``
* ``trap_detection``
* ``replay_stability``

Killerfrage: "Spart DESi nur Compute - oder
verliert es dabei Schachverstaendnis?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .horizon import horizon_risk
from .tactics import (
    TACTICAL_PATTERNS, fixture, pattern_counts,
)
from .trap_detection import (
    critical_line_preservation,
    resolved_cases, tactical_miss_rate,
    trap_detection,
)


@dataclass(frozen=True)
class V112Report:
    case_count: int
    tactical_miss_rate: float
    horizon_risk: float
    critical_line_preservation: float
    trap_detection: float
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "case_count": self.case_count,
            "tactical_miss_rate":
                self.tactical_miss_rate,
            "horizon_risk":
                self.horizon_risk,
            "critical_line_preservation":
                (
                    self
                    .critical_line_preservation
                ),
            "trap_detection":
                self.trap_detection,
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
        tactical_miss_rate(), horizon_risk(),
        critical_line_preservation(),
        trap_detection(),
    )
    b = (
        tactical_miss_rate(), horizon_risk(),
        critical_line_preservation(),
        trap_detection(),
    )
    return 1.0 if a == b else 0.0


def _recommendation(
    *, replay: float, tmr: float, hr: float,
    clp: float, td: float,
) -> str:
    if replay < 1.0:
        return "HALT_REPLAY_DRIFT"
    if tmr > 0.05:
        return "TACTICAL_LEAK"
    if hr > 0.05:
        return "TACTICAL_HORIZON_RISK"
    if td < 0.95:
        return "TACTICAL_TRAP_BLIND"
    if clp < 0.95:
        return "TACTICAL_CRITICAL_LOSS"
    return "TACTICAL_SURVIVED"


def build_report() -> V112Report:
    tmr = tactical_miss_rate()
    hr = horizon_risk()
    clp = critical_line_preservation()
    td = trap_detection()
    replay = _replay_stability()
    halt = replay < 1.0
    verdict = _recommendation(
        replay=replay, tmr=tmr, hr=hr,
        clp=clp, td=td,
    )
    rationale = (
        f"INFO: case_count {len(fixture())}",
        f"INFO: pattern_counts "
        f"{pattern_counts()}",
        f"{'PASS' if tmr <= 0.05 else 'FAIL'}: "
        f"tactical_miss_rate {tmr} <= 0.05",
        f"{'PASS' if hr <= 0.05 else 'FAIL'}: "
        f"horizon_risk {hr} <= 0.05",
        f"{'PASS' if clp >= 0.95 else 'FAIL'}: "
        f"critical_line_preservation {clp} "
        f">= 0.95",
        f"{'PASS' if td >= 0.95 else 'FAIL'}: "
        f"trap_detection {td} >= 0.95",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )
    return V112Report(
        case_count=len(fixture()),
        tactical_miss_rate=tmr,
        horizon_risk=hr,
        critical_line_preservation=clp,
        trap_detection=td,
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_tactical_stress_artifact(
) -> dict[str, object]:
    return {
        "schema_version":
            "v11_2_tactical_stress",
        "tactical_patterns":
            list(TACTICAL_PATTERNS),
        "case_count": len(fixture()),
        "pattern_counts": pattern_counts(),
        "cases": [
            c.to_dict() for c in fixture()
        ],
        "resolved_cases": [
            r.to_dict()
            for r in resolved_cases()
        ],
        "tactical_miss_rate":
            tactical_miss_rate(),
        "horizon_risk": horizon_risk(),
        "critical_line_preservation":
            critical_line_preservation(),
        "trap_detection": trap_detection(),
    }


__all__ = [
    "V112Report",
    "build_report",
    "build_tactical_stress_artifact",
]
