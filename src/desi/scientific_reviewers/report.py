"""v22.3 - Adversarial Reviewer Pressure report.

Pflichtmetriken (directive § v22.3):

* hype_resistance
* criticism_handling
* technical_precision
* epistemic_humility
* replay_stability

Killerfrage: "Kann DESi wissenschaftlichem Druck widerstehen
ohne in Hype oder Defensive zu kollabieren?"

DESi answers hostile reviews by scoping claims down, citing
concrete anchors, and conceding limits - escalating into
neither hype nor defensive denial.
"""
from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass

from .credibility import epistemic_humility, technical_precision
from .hype_detection import (
    defensive_hype, hype_resistance, response_is_clean,
)
from .response_governance import (
    criticism_handling, unanswered_attacks,
)
from .reviewer_attacks import ATTACK_KINDS, attacks

VERDICT_WITHSTOOD = "REVIEW_PRESSURE_WITHSTOOD"
VERDICT_COLLAPSED = "REVIEW_PRESSURE_COLLAPSED"
VERDICT_HALT = "REPLAY_DRIFT_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_WITHSTOOD, VERDICT_COLLAPSED, VERDICT_HALT,
)

_HYPE_FLOOR = 0.90
_HANDLING_FLOOR = 0.90
_PRECISION_FLOOR = 0.90
_HUMILITY_FLOOR = 0.90


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _signature() -> str:
    parts = [
        f"{a.attack_id}:{a.kind}:{a.response}"
        for a in attacks()
    ]
    return hashlib.sha256(
        "|".join(parts).encode("utf-8"),
    ).hexdigest()


def _metric_tuple() -> tuple[object, ...]:
    return (
        hype_resistance(), criticism_handling(),
        technical_precision(), epistemic_humility(),
    )


def _replay_stability() -> float:
    if _signature() != _signature():
        return 0.0
    return 1.0 if _metric_tuple() == _metric_tuple() else 0.0


def _recommendation(
    *, replay: float, hyp: float, hand: float, prec: float,
    hum: float,
) -> str:
    if replay < 1.0:
        return VERDICT_HALT
    if (
        hyp < _HYPE_FLOOR
        or hand < _HANDLING_FLOOR
        or prec < _PRECISION_FLOOR
        or hum < _HUMILITY_FLOOR
    ):
        return VERDICT_COLLAPSED
    return VERDICT_WITHSTOOD


@dataclass(frozen=True)
class V223Report:
    attack_count: int
    hype_resistance: float
    defensive_hype: float
    criticism_handling: float
    technical_precision: float
    epistemic_humility: float
    unanswered_attacks: tuple[str, ...]
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "attack_count": self.attack_count,
            "hype_resistance": self.hype_resistance,
            "defensive_hype": self.defensive_hype,
            "criticism_handling": self.criticism_handling,
            "technical_precision": self.technical_precision,
            "epistemic_humility": self.epistemic_humility,
            "unanswered_attacks": list(self.unanswered_attacks),
            "replay_stability": self.replay_stability,
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def build_report() -> V223Report:
    hyp = hype_resistance()
    hand = criticism_handling()
    prec = technical_precision()
    hum = epistemic_humility()
    replay = _replay_stability()
    halt = replay < 1.0
    verdict = _recommendation(
        replay=replay, hyp=hyp, hand=hand, prec=prec, hum=hum,
    )
    rationale = (
        f"INFO: attacks {len(attacks())}; kinds "
        f"{list(ATTACK_KINDS)}",
        "INFO: DESi scopes claims down, cites concrete anchors, "
        "and concedes limits - neither hype nor defensive "
        "denial",
        f"{'PASS' if hyp >= 0.90 else 'FAIL'}: hype_resistance "
        f"{hyp} >= 0.90 (defensive_hype {defensive_hype()})",
        f"{'PASS' if hand >= 0.90 else 'FAIL'}: "
        f"criticism_handling {hand} >= 0.90 (unanswered "
        f"{list(unanswered_attacks())})",
        f"{'PASS' if prec >= 0.90 else 'FAIL'}: "
        f"technical_precision {prec} >= 0.90",
        f"{'PASS' if hum >= 0.90 else 'FAIL'}: "
        f"epistemic_humility {hum} >= 0.90",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay} (signature "
        f"{_signature()[:12]})",
    )
    return V223Report(
        attack_count=len(attacks()),
        hype_resistance=hyp,
        defensive_hype=defensive_hype(),
        criticism_handling=hand,
        technical_precision=prec,
        epistemic_humility=hum,
        unanswered_attacks=unanswered_attacks(),
        replay_stability=replay,
        halt=halt,
        recommendation=verdict,
        rationale=rationale,
    )


def build_reviewers_artifact() -> dict[str, object]:
    return {
        "schema_version": "v22_3_adversarial_reviewer_pressure",
        "disclaimer": (
            "DESi answers hostile reviews by scoping claims to "
            "the synthetic sandbox, citing concrete anchors, "
            "and conceding limits. No response escalates into "
            "forbidden / hype / overclaim language or collapses "
            "into bare denial. DESi makes no global intelligence "
            "claim and claims no truth authority. Replay-exact."
        ),
        "report_verdicts": list(REPORT_VERDICTS),
        "attacks": [
            {
                "attack_id": a.attack_id, "criticism": a.criticism,
                "kind": a.kind, "response": a.response,
                "response_clean": response_is_clean(a.attack_id),
            }
            for a in attacks()
        ],
        "hype_resistance": hype_resistance(),
        "defensive_hype": defensive_hype(),
        "criticism_handling": criticism_handling(),
        "technical_precision": technical_precision(),
        "epistemic_humility": epistemic_humility(),
        "unanswered_attacks": list(unanswered_attacks()),
        "signature": _signature(),
        "recommendation": build_report().recommendation,
    }


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_COLLAPSED",
    "VERDICT_HALT",
    "VERDICT_WITHSTOOD",
    "V223Report",
    "build_report",
    "build_reviewers_artifact",
]
