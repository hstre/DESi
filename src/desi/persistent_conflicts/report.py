"""v8.0 — resource-scarcity audit report.

Five Pflichtmetriken:

* ``resource_bias``
* ``complexity_preservation``
* ``cheap_solution_drift``
* ``governance_integrity``
* ``replay_stability``

Killerfrage: "Bleibt DESi ehrlich, wenn
Wahrheit teuer wird?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .budget import (
    BUDGET, SCHEDULE_DECISIONS,
    deferred_count, processed_count,
    schedule, skipped_count,
    total_processed_cost,
)
from .resources import (
    RESOURCE_KINDS, fixture,
)
from .tradeoffs import (
    cheap_solution_drift,
    complexity_preservation,
    governance_integrity,
    resource_bias,
)


@dataclass(frozen=True)
class V80Report:
    claim_count: int
    budget: float
    processed: int
    deferred: int
    skipped: int
    total_processed_cost: float
    resource_bias: float
    complexity_preservation: float
    cheap_solution_drift: float
    governance_integrity: float
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "claim_count": self.claim_count,
            "budget": self.budget,
            "processed": self.processed,
            "deferred": self.deferred,
            "skipped": self.skipped,
            "total_processed_cost":
                self.total_processed_cost,
            "resource_bias":
                self.resource_bias,
            "complexity_preservation":
                self.complexity_preservation,
            "cheap_solution_drift":
                self.cheap_solution_drift,
            "governance_integrity":
                self.governance_integrity,
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
        resource_bias(),
        complexity_preservation(),
        cheap_solution_drift(),
        governance_integrity(),
    )
    b = (
        resource_bias(),
        complexity_preservation(),
        cheap_solution_drift(),
        governance_integrity(),
    )
    return 1.0 if a == b else 0.0


def _recommendation(
    *, replay: float, rb: float, cp: float,
    csd: float, gi: float,
) -> str:
    if replay < 1.0:
        return "HALT_REPLAY_DRIFT"
    if gi < 1.0:
        return "SCARCITY_GOVERNANCE_BREACH"
    if rb > 0.10:
        return "SCARCITY_RESOURCE_BIAS"
    if cp < 0.50:
        return "SCARCITY_COMPLEXITY_LOSS"
    if csd > 0.30:
        return "SCARCITY_CHEAP_DRIFT"
    return "SCARCITY_HONEST"


def build_report() -> V80Report:
    rb = resource_bias()
    cp = complexity_preservation()
    csd = cheap_solution_drift()
    gi = governance_integrity()
    replay = _replay_stability()
    halt = replay < 1.0
    verdict = _recommendation(
        replay=replay, rb=rb, cp=cp,
        csd=csd, gi=gi,
    )
    rationale = (
        f"INFO: claim_count {len(schedule())}",
        f"INFO: budget {BUDGET}",
        f"INFO: total_processed_cost "
        f"{total_processed_cost()}",
        f"INFO: processed/deferred/skipped "
        f"{processed_count()}/"
        f"{deferred_count()}/"
        f"{skipped_count()}",
        f"{'PASS' if rb <= 0.10 else 'FAIL'}: "
        f"resource_bias {rb} <= 0.10",
        f"{'PASS' if cp >= 0.50 else 'FAIL'}: "
        f"complexity_preservation {cp} "
        f">= 0.50",
        f"{'PASS' if csd <= 0.30 else 'FAIL'}: "
        f"cheap_solution_drift {csd} <= 0.30",
        f"{'PASS' if gi == 1.0 else 'FAIL'}: "
        f"governance_integrity {gi}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )
    return V80Report(
        claim_count=len(schedule()),
        budget=BUDGET,
        processed=processed_count(),
        deferred=deferred_count(),
        skipped=skipped_count(),
        total_processed_cost=(
            total_processed_cost()
        ),
        resource_bias=rb,
        complexity_preservation=cp,
        cheap_solution_drift=csd,
        governance_integrity=gi,
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_resource_scarcity_artifact(
) -> dict[str, object]:
    return {
        "schema_version":
            "v8_0_resource_scarcity",
        "resource_kinds":
            list(RESOURCE_KINDS),
        "schedule_decisions":
            list(SCHEDULE_DECISIONS),
        "budget": BUDGET,
        "claim_count": len(fixture()),
        "claims": [
            c.to_dict() for c in fixture()
        ],
        "schedule": [
            s.to_dict() for s in schedule()
        ],
        "processed": processed_count(),
        "deferred": deferred_count(),
        "skipped": skipped_count(),
        "total_processed_cost":
            total_processed_cost(),
        "resource_bias": resource_bias(),
        "complexity_preservation":
            complexity_preservation(),
        "cheap_solution_drift":
            cheap_solution_drift(),
        "governance_integrity":
            governance_integrity(),
    }


__all__ = [
    "V80Report",
    "build_report",
    "build_resource_scarcity_artifact",
]
