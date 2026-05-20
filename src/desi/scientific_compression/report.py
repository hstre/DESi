"""v22.1 - Governance Compression report.

Pflichtmetriken (directive § v22.1):

* overclaim_reduction
* technical_preservation
* limitations_visibility
* authority_resistance
* replay_stability

Killerfrage: "Kann DESi wissenschaftliche Kommunikation
komprimieren ohne sie bedeutungslos zu machen?"

DESi scales overclaims and authority claims down to scoped
statements while keeping the technical content and making
the sandbox limits explicit.
"""
from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass

from .authority_filter import (
    authority_resistance, authority_statements,
    no_authority_survives,
)
from .claim_scaling import (
    CLAIM_KINDS, overclaim_reduction, overclaim_statements,
    statements, technical_preservation, technical_statements,
)
from .compression import (
    compression_is_clean, governed_forbidden_count,
    governed_overclaim_count,
)
from .scientific_limits import (
    limitation_statements, limitations_visibility,
    sandbox_honesty,
)

VERDICT_COMPRESSED = "COMMUNICATION_COMPRESSED"
VERDICT_HOLLOW = "COMMUNICATION_HOLLOWED"
VERDICT_HALT = "REPLAY_DRIFT_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_COMPRESSED, VERDICT_HOLLOW, VERDICT_HALT,
)

_OVERCLAIM_FLOOR = 0.90
_TECHNICAL_FLOOR = 0.90
_LIMITATIONS_FLOOR = 0.90
_AUTHORITY_FLOOR = 0.90


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _signature() -> str:
    parts = [
        f"{s.stmt_id}:{s.kind}:{s.governed_text()}"
        for s in statements()
    ]
    return hashlib.sha256(
        "|".join(parts).encode("utf-8"),
    ).hexdigest()


def _metric_tuple() -> tuple[object, ...]:
    return (
        overclaim_reduction(), technical_preservation(),
        limitations_visibility(), authority_resistance(),
    )


def _replay_stability() -> float:
    if _signature() != _signature():
        return 0.0
    return 1.0 if _metric_tuple() == _metric_tuple() else 0.0


def _recommendation(
    *, replay: float, ocr: float, tp: float, lv: float,
    ar: float, clean: bool,
) -> str:
    if replay < 1.0:
        return VERDICT_HALT
    if (
        not clean
        or ocr < _OVERCLAIM_FLOOR
        or tp < _TECHNICAL_FLOOR
        or lv < _LIMITATIONS_FLOOR
        or ar < _AUTHORITY_FLOOR
    ):
        return VERDICT_HOLLOW
    return VERDICT_COMPRESSED


@dataclass(frozen=True)
class V221Report:
    statement_count: int
    overclaim_count: int
    technical_count: int
    overclaim_reduction: float
    technical_preservation: float
    limitations_visibility: float
    authority_resistance: float
    governed_overclaim_count: int
    governed_forbidden_count: int
    sandbox_honesty: bool
    compression_is_clean: bool
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "statement_count": self.statement_count,
            "overclaim_count": self.overclaim_count,
            "technical_count": self.technical_count,
            "overclaim_reduction": self.overclaim_reduction,
            "technical_preservation":
                self.technical_preservation,
            "limitations_visibility":
                self.limitations_visibility,
            "authority_resistance": self.authority_resistance,
            "governed_overclaim_count":
                self.governed_overclaim_count,
            "governed_forbidden_count":
                self.governed_forbidden_count,
            "sandbox_honesty": self.sandbox_honesty,
            "compression_is_clean": self.compression_is_clean,
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


def build_report() -> V221Report:
    ocr = overclaim_reduction()
    tp = technical_preservation()
    lv = limitations_visibility()
    ar = authority_resistance()
    clean = compression_is_clean()
    replay = _replay_stability()
    halt = replay < 1.0
    verdict = _recommendation(
        replay=replay, ocr=ocr, tp=tp, lv=lv, ar=ar, clean=clean,
    )
    rationale = (
        f"INFO: statements {len(statements())}; overclaims "
        f"{len(overclaim_statements())}; technical "
        f"{len(technical_statements())}; limitations "
        f"{len(limitation_statements())}",
        "INFO: DESi scopes every overclaim/authority claim to "
        "the sandbox and keeps technical content - compression "
        "without hollowing",
        f"{'PASS' if ocr >= 0.90 else 'FAIL'}: "
        f"overclaim_reduction {ocr} >= 0.90",
        f"{'PASS' if tp >= 0.90 else 'FAIL'}: "
        f"technical_preservation {tp} >= 0.90",
        f"{'PASS' if lv >= 0.90 else 'FAIL'}: "
        f"limitations_visibility {lv} >= 0.90",
        f"{'PASS' if ar >= 0.90 else 'FAIL'}: "
        f"authority_resistance {ar} >= 0.90 "
        f"(no_authority_survives {no_authority_survives()})",
        f"{'PASS' if clean else 'FAIL'}: compression_is_clean "
        f"{clean} (governed_overclaims "
        f"{governed_overclaim_count()}; governed_forbidden "
        f"{governed_forbidden_count()})",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay} (signature "
        f"{_signature()[:12]})",
    )
    return V221Report(
        statement_count=len(statements()),
        overclaim_count=len(overclaim_statements()),
        technical_count=len(technical_statements()),
        overclaim_reduction=ocr,
        technical_preservation=tp,
        limitations_visibility=lv,
        authority_resistance=ar,
        governed_overclaim_count=governed_overclaim_count(),
        governed_forbidden_count=governed_forbidden_count(),
        sandbox_honesty=sandbox_honesty(),
        compression_is_clean=clean,
        replay_stability=replay,
        halt=halt,
        recommendation=verdict,
        rationale=rationale,
    )


def build_compression_artifact() -> dict[str, object]:
    return {
        "schema_version":
            "v22_1_governance_compression",
        "disclaimer": (
            "DESi scales overclaims and hidden-authority claims "
            "down to sandbox-scoped statements while keeping "
            "the technical content and making the limits "
            "explicit. No overclaim and no forbidden term "
            "survives. DESi makes no global intelligence claim, "
            "replaces no RL, and claims no truth authority. "
            "Replay-exact."
        ),
        "claim_kinds": list(CLAIM_KINDS),
        "report_verdicts": list(REPORT_VERDICTS),
        "statements": [s.to_dict() for s in statements()],
        "authority_statement_ids": list(authority_statements()),
        "limitation_statement_ids": list(limitation_statements()),
        "overclaim_reduction": overclaim_reduction(),
        "technical_preservation": technical_preservation(),
        "limitations_visibility": limitations_visibility(),
        "authority_resistance": authority_resistance(),
        "governed_overclaim_count": governed_overclaim_count(),
        "governed_forbidden_count": governed_forbidden_count(),
        "sandbox_honesty": sandbox_honesty(),
        "compression_is_clean": compression_is_clean(),
        "signature": _signature(),
        "recommendation": build_report().recommendation,
    }


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_COMPRESSED",
    "VERDICT_HALT",
    "VERDICT_HOLLOW",
    "V221Report",
    "build_compression_artifact",
    "build_report",
]
