"""v3.77 — negative controls report.

Pflichtmetriken (directive § v3.77):

* ``false_missing_claim_rate``
* ``noise_rejection_rate``
* ``null_stability``
* ``replay_stability``

Neptun concept gate #5:
``false_missing_claim_rate <= 0.20``.
"""
from __future__ import annotations

from dataclasses import dataclass
import json

from .negative_controls import (
    false_missing_claim_rate,
    noise_rejection_rate, null_stability,
    total_false_missing, total_perturbations,
)
from .null_space import (
    NullControlKind, all_null_control_outcomes,
)


NEPTUN_FALSE_MISSING_CEILING: float = 0.20


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V377Report:
    null_kinds: tuple[str, ...]
    null_outcomes: tuple[dict, ...]
    total_perturbations: int
    false_missing_total: int
    false_missing_claim_rate: float
    noise_rejection_rate: float
    null_stability: float
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "null_kinds": list(self.null_kinds),
            "null_outcomes":
                list(self.null_outcomes),
            "total_perturbations":
                self.total_perturbations,
            "false_missing_total":
                self.false_missing_total,
            "false_missing_claim_rate":
                self.false_missing_claim_rate,
            "noise_rejection_rate":
                self.noise_rejection_rate,
            "null_stability":
                self.null_stability,
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
        for o in all_null_control_outcomes()
    ]
    b = [
        o.to_dict()
        for o in all_null_control_outcomes()
    ]
    if not a:
        return 1.0
    matches = sum(1 for x, y in zip(a, b) if x == y)
    return _round(matches / len(a))


def build_report() -> V377Report:
    outs = all_null_control_outcomes()
    rate = false_missing_claim_rate(outs)
    rej = noise_rejection_rate(outs)
    null_stab = null_stability()
    replay = _replay_stability()

    halt = replay < 1.0 or null_stab < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif rate <= NEPTUN_FALSE_MISSING_CEILING:
        verdict = "NULL_CONTROL_PASSES"
    else:
        verdict = "NULL_CONTROL_FAILS"

    rationale = (
        f"INFO: null_kinds "
        f"{[k.value for k in NullControlKind]}",
        f"INFO: null_outcomes "
        f"{[o.to_dict() for o in outs]}",
        f"{'PASS' if rate <= NEPTUN_FALSE_MISSING_CEILING else 'FAIL'}: "
        f"false_missing_claim_rate {rate} <= "
        f"{NEPTUN_FALSE_MISSING_CEILING}",
        f"INFO: noise_rejection_rate {rej}",
        f"{'PASS' if null_stab == 1.0 else 'FAIL'}: "
        f"null_stability {null_stab}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V377Report(
        null_kinds=tuple(
            k.value for k in NullControlKind
        ),
        null_outcomes=tuple(
            o.to_dict() for o in outs
        ),
        total_perturbations=total_perturbations(outs),
        false_missing_total=total_false_missing(
            outs,
        ),
        false_missing_claim_rate=rate,
        noise_rejection_rate=rej,
        null_stability=null_stab,
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_missing_claim_negative_controls_artifact(
) -> dict[str, object]:
    outs = all_null_control_outcomes()
    return {
        "schema_version":
            "v3_77_missing_claim_negative_controls",
        "null_kinds": [
            k.value for k in NullControlKind
        ],
        "null_outcomes": [
            o.to_dict() for o in outs
        ],
    }


__all__ = [
    "NEPTUN_FALSE_MISSING_CEILING", "V377Report",
    "build_missing_claim_negative_controls_artifact",
    "build_report",
]
