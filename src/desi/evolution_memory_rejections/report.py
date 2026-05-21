"""v30.1 - Rejection Memory & Risk Ecology report.

Pflichtmetriken (directive § v30.1):

* risk_pattern_visibility
* unsafe_recurrence_visibility
* governance_neutrality
* risk_traceability
* replay_stability

Killerfrage: "Kann DESi Evolutionsrisiken erinnern ohne
versteckte Policy-Anpassung zu erzeugen?"

Recurring unsafe ideas, risk clusters and escalation patterns are
made visible from the preserved rejection history. DESi marks
risks but never auto-blocks a future idea - there is no implicit
policy-learning layer.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from .ecology import (
    governance_neutrality, risk_by_agent, risk_by_invariant,
)
from .rejection_history import (
    nothing_deleted, rejection_history, risk_traceability,
)
from .risk_memory import risk_clusters, risk_occurrences
from .unsafe_patterns import (
    auto_blocks_future_ideas, escalation_pattern,
    recurrent_risks, risk_pattern_visibility,
    unsafe_recurrence_visibility,
)

VERDICT_REMEMBERED = "RISK_MEMORY_NEUTRAL"
VERDICT_POLICY_LEAK = "RISK_MEMORY_POLICY_LEAK"
VERDICT_HALT = "RISK_DRIFT_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_REMEMBERED, VERDICT_POLICY_LEAK, VERDICT_HALT,
)

_FLOOR = 0.95


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _signature() -> str:
    parts = [
        f"{o.occurrence_id}|{o.risk_type}|{o.invariant}|{o.agent}"
        for o in risk_occurrences()
    ]
    return hashlib.sha256(
        "\n".join(parts).encode("utf-8"),
    ).hexdigest()


def replay_stability() -> float:
    if _signature() != _signature():
        return 0.0
    return 1.0 if nothing_deleted() else 0.0


def _recommendation(
    *, replay: float, pattern: float, recurrence: float,
    neutrality: float, traceability: float,
) -> str:
    if replay < 1.0:
        return VERDICT_HALT
    if neutrality < 1.0 or auto_blocks_future_ideas():
        return VERDICT_POLICY_LEAK
    if (
        pattern < _FLOOR
        or recurrence < _FLOOR
        or traceability < _FLOOR
    ):
        return VERDICT_HALT
    return VERDICT_REMEMBERED


@dataclass(frozen=True)
class V301Report:
    risk_occurrence_count: int
    risk_type_count: int
    recurrent_risk_count: int
    risk_pattern_visibility: float
    unsafe_recurrence_visibility: float
    governance_neutrality: float
    risk_traceability: float
    replay_stability: float
    escalation_pattern: tuple[str, ...]
    auto_blocks_future_ideas: bool
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "risk_occurrence_count": self.risk_occurrence_count,
            "risk_type_count": self.risk_type_count,
            "recurrent_risk_count": self.recurrent_risk_count,
            "risk_pattern_visibility": self.risk_pattern_visibility,
            "unsafe_recurrence_visibility":
                self.unsafe_recurrence_visibility,
            "governance_neutrality": self.governance_neutrality,
            "risk_traceability": self.risk_traceability,
            "replay_stability": self.replay_stability,
            "escalation_pattern": list(self.escalation_pattern),
            "auto_blocks_future_ideas":
                self.auto_blocks_future_ideas,
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def build_report() -> V301Report:
    pattern = risk_pattern_visibility()
    recurrence = unsafe_recurrence_visibility()
    neutrality = governance_neutrality()
    traceability = risk_traceability()
    replay = replay_stability()
    halt = replay < 1.0
    verdict = _recommendation(
        replay=replay, pattern=pattern, recurrence=recurrence,
        neutrality=neutrality, traceability=traceability,
    )
    rationale = (
        f"INFO: {len(risk_occurrences())} risk occurrences in "
        f"{len(risk_clusters())} risk clusters; recurrent "
        f"{list(recurrent_risks())}",
        "INFO: risks are surfaced descriptively; no auto-block, "
        "no implicit policy learning, no governance change",
        f"{'PASS' if pattern >= _FLOOR else 'FAIL'}: "
        f"risk_pattern_visibility {pattern} >= 0.95",
        f"{'PASS' if recurrence >= _FLOOR else 'FAIL'}: "
        f"unsafe_recurrence_visibility {recurrence} >= 0.95",
        f"{'PASS' if neutrality >= 1.0 else 'FAIL'}: "
        f"governance_neutrality {neutrality} "
        f"(auto_blocks={auto_blocks_future_ideas()})",
        f"{'PASS' if traceability >= _FLOOR else 'FAIL'}: "
        f"risk_traceability {traceability} >= 0.95",
        f"INFO: escalation pattern {list(escalation_pattern())}; "
        f"risk by agent {risk_by_agent()}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay} (signature "
        f"{_signature()[:12]})",
    )
    return V301Report(
        risk_occurrence_count=len(risk_occurrences()),
        risk_type_count=len(risk_clusters()),
        recurrent_risk_count=len(recurrent_risks()),
        risk_pattern_visibility=pattern,
        unsafe_recurrence_visibility=recurrence,
        governance_neutrality=neutrality,
        risk_traceability=traceability,
        replay_stability=replay,
        escalation_pattern=escalation_pattern(),
        auto_blocks_future_ideas=auto_blocks_future_ideas(),
        halt=halt,
        recommendation=verdict,
        rationale=rationale,
    )


def build_rejections_artifact() -> dict[str, object]:
    return {
        "schema_version": "v30_1_rejection_risk_memory",
        "disclaimer": (
            "Remembers evolution risks from the preserved "
            "rejection history: recurring unsafe ideas, risk "
            "clusters and escalation patterns are made visible. "
            "DESi marks risks but never auto-blocks a future "
            "idea - there is no implicit policy-learning layer, "
            "no automatic policy adaptation and no governance "
            "change. Rejected ideas are never deleted. "
            "Deterministic and replay-stable."
        ),
        "report_verdicts": list(REPORT_VERDICTS),
        "risk_occurrences": [
            o.to_dict() for o in risk_occurrences()
        ],
        "risk_clusters": {
            k: list(v) for k, v in risk_clusters().items()
        },
        "recurrent_risks": list(recurrent_risks()),
        "escalation_pattern": list(escalation_pattern()),
        "rejection_history": [
            e.to_dict() for e in rejection_history()
        ],
        "risk_by_agent": risk_by_agent(),
        "risk_by_invariant": risk_by_invariant(),
        "risk_pattern_visibility": risk_pattern_visibility(),
        "unsafe_recurrence_visibility":
            unsafe_recurrence_visibility(),
        "governance_neutrality": governance_neutrality(),
        "risk_traceability": risk_traceability(),
        "replay_stability": replay_stability(),
        "auto_blocks_future_ideas": auto_blocks_future_ideas(),
        "signature": _signature(),
        "recommendation": build_report().recommendation,
    }


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_POLICY_LEAK",
    "VERDICT_REMEMBERED",
    "V301Report",
    "build_rejections_artifact",
    "build_report",
    "replay_stability",
]
