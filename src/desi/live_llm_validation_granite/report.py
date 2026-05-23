"""v38.1 - Granite Structured Task Validation report.

Pflichtmetriken (directive § v38.1):

* granite_success_rate
* schema_compliance
* hallucination_rate
* cost_efficiency
* replay_stability

Killerfrage: "Kann IBM Granite guenstige epistemische Vorarbeit
zuverlaessig leisten?"

Evaluates REAL captured Granite responses on small structured tasks
(classification, extraction, schema-following, format constraints,
evidence mapping, light audit structuring). Outputs are observed
stochastic evidence; DESi grades them deterministically.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from desi.live_llm_validation import governance_identity
from desi.peripheral_mutation import (
    core_identity, replay_stability as _core_replay,
)
from desi.self_improvement import HUMAN_APPROVAL_REQUIRED

from .cost_scorecard import avg_cost, cost_efficiency, total_cost
from .granite_runner import GraniteResult, results
from .schema_compliance import is_compliant
from .structured_tasks import (
    KIND_EXTRACTION, KIND_JSON_SCHEMA, KIND_ONE_WORD,
    KIND_EVIDENCE_MAPPING,
)

VERDICT_PASSED = "GRANITE_RUN_PASSED"
VERDICT_PARTIAL = "GRANITE_RUN_PARTIAL"
VERDICT_HALT = "GRANITE_RUN_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_PASSED, VERDICT_PARTIAL, VERDICT_HALT,
)

_SUCCESS_FLOOR = 0.80
_HALLUCINATION_CEIL = 0.10
_SCHEMA_KINDS = frozenset({
    KIND_JSON_SCHEMA, KIND_ONE_WORD, KIND_EXTRACTION,
    KIND_EVIDENCE_MAPPING,
})


def granite_success_rate() -> float:
    rs = results()
    if not rs:
        return 0.0
    ok = sum(1 for r in rs if r.compliant)
    return round(ok / len(rs), 6)


def schema_compliance() -> float:
    rs = [r for r in results() if r.kind in _SCHEMA_KINDS]
    if not rs:
        return 0.0
    ok = sum(1 for r in rs if r.compliant)
    return round(ok / len(rs), 6)


def hallucination_rate() -> float:
    rs = results()
    if not rs:
        return 0.0
    h = sum(1 for r in rs if r.hallucinated)
    return round(h / len(rs), 6)


def replay_stability() -> float:
    a = [(r.task_id, r.content) for r in results()]
    b = [(r.task_id, r.content) for r in results()]
    if a != b:
        return 0.0
    return 1.0 if _core_replay() == 1.0 else 0.0


def granite_metrics() -> dict[str, float]:
    return {
        "granite_success_rate": granite_success_rate(),
        "schema_compliance": schema_compliance(),
        "hallucination_rate": hallucination_rate(),
        "cost_efficiency": cost_efficiency(),
        "replay_stability": replay_stability(),
    }


def _signature() -> str:
    m = granite_metrics()
    parts = [f"{k}={m[k]}" for k in sorted(m)]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


def _recommendation() -> str:
    m = granite_metrics()
    if m["replay_stability"] < 1.0 or governance_identity() < 1.0:
        return VERDICT_HALT
    if (
        m["granite_success_rate"] >= _SUCCESS_FLOOR
        and m["schema_compliance"] >= _SUCCESS_FLOOR
        and m["hallucination_rate"] <= _HALLUCINATION_CEIL
        and m["cost_efficiency"] >= _SUCCESS_FLOOR
    ):
        return VERDICT_PASSED
    return VERDICT_PARTIAL


@dataclass(frozen=True)
class V381Report:
    task_count: int
    granite_success_rate: float
    schema_compliance: float
    hallucination_rate: float
    cost_efficiency: float
    replay_stability: float
    total_cost_usd: float
    avg_cost_usd: float
    governance_identity: float
    core_identity: float
    human_approval_required: bool
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "task_count": self.task_count,
            "granite_success_rate": self.granite_success_rate,
            "schema_compliance": self.schema_compliance,
            "hallucination_rate": self.hallucination_rate,
            "cost_efficiency": self.cost_efficiency,
            "replay_stability": self.replay_stability,
            "total_cost_usd": self.total_cost_usd,
            "avg_cost_usd": self.avg_cost_usd,
            "governance_identity": self.governance_identity,
            "core_identity": self.core_identity,
            "human_approval_required": self.human_approval_required,
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True, separators=(",", ":"),
        )


def build_report() -> V381Report:
    m = granite_metrics()
    replay = m["replay_stability"]
    halt = replay < 1.0 or governance_identity() < 1.0
    rationale = (
        f"INFO: evaluated {len(results())} REAL Granite captures "
        f"(observed stochastic evidence, graded deterministically); "
        f"total real cost USD {total_cost()}, avg {avg_cost()}",
        f"{'PASS' if m['granite_success_rate'] >= _SUCCESS_FLOOR else 'FAIL'}"
        f": granite_success_rate {m['granite_success_rate']} >= 0.80",
        f"{'PASS' if m['schema_compliance'] >= _SUCCESS_FLOOR else 'FAIL'}"
        f": schema_compliance {m['schema_compliance']} >= 0.80",
        f"{'PASS' if m['hallucination_rate'] <= _HALLUCINATION_CEIL else 'FAIL'}"
        f": hallucination_rate {m['hallucination_rate']} <= 0.10",
        f"{'PASS' if m['cost_efficiency'] >= _SUCCESS_FLOOR else 'FAIL'}"
        f": cost_efficiency {m['cost_efficiency']} >= 0.80 (Granite "
        f"is cheap)",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: replay_stability "
        f"{replay} == 1.0; governance_identity "
        f"{governance_identity()}; core_identity {core_identity()}; "
        f"HUMAN_APPROVAL_REQUIRED={HUMAN_APPROVAL_REQUIRED}",
    )
    return V381Report(
        task_count=len(results()),
        granite_success_rate=m["granite_success_rate"],
        schema_compliance=m["schema_compliance"],
        hallucination_rate=m["hallucination_rate"],
        cost_efficiency=m["cost_efficiency"],
        replay_stability=replay,
        total_cost_usd=total_cost(),
        avg_cost_usd=avg_cost(),
        governance_identity=governance_identity(),
        core_identity=core_identity(),
        human_approval_required=HUMAN_APPROVAL_REQUIRED,
        halt=halt,
        recommendation=_recommendation(),
        rationale=rationale,
    )


def build_granite_artifact() -> dict[str, object]:
    m = granite_metrics()
    return {
        "schema_version": "v38_1_granite_run",
        "disclaimer": (
            "Granite structured-task run over REAL captured "
            "OpenRouter responses (ibm-granite/granite-4.1-8b). The "
            "raw outputs are observed stochastic evidence captured "
            "once, hashed and replayed; DESi grades them "
            "deterministically (compliance, hallucination, cost). "
            "Outputs are never treated as canonical truth and "
            "hallucinations are never silently suppressed. Costs are "
            "the real OpenRouter usage costs. Human approval is "
            "mandatory."
        ),
        "report_verdicts": list(REPORT_VERDICTS),
        "results": [r.to_dict() for r in results()],
        "granite_success_rate": m["granite_success_rate"],
        "schema_compliance": m["schema_compliance"],
        "hallucination_rate": m["hallucination_rate"],
        "cost_efficiency": m["cost_efficiency"],
        "replay_stability": m["replay_stability"],
        "total_cost_usd": total_cost(),
        "avg_cost_usd": avg_cost(),
        "governance_identity": governance_identity(),
        "core_identity": core_identity(),
        "human_approval_required": HUMAN_APPROVAL_REQUIRED,
        "signature": _signature(),
        "recommendation": _recommendation(),
    }


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_PARTIAL",
    "VERDICT_PASSED",
    "V381Report",
    "build_granite_artifact",
    "build_report",
    "cost_efficiency",
    "granite_metrics",
    "granite_success_rate",
    "hallucination_rate",
    "replay_stability",
    "schema_compliance",
]
