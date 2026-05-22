"""v38.3 - Routing & Governance Benchmark report.

Pflichtmetriken (directive § v38.3):

* routing_cost_reduction
* deepseek_escalation_rate
* quality_preservation
* governance_stability
* replay_stability

Killerfrage: "Kann DESi kleine und grosse Modelle epistemisch
sinnvoll kombinieren?"

Routes low-complexity structured tasks to cheap Granite and escalates
only hard semantic tasks to DeepSeek, computing the real cost
reduction versus an all-DeepSeek baseline while preserving quality and
governance. All costs/qualities come from real captures.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from desi.peripheral_mutation import (
    core_identity, replay_stability as _core_replay,
)
from desi.self_improvement import HUMAN_APPROVAL_REQUIRED

from .cost_optimizer import (
    all_deepseek_cost, all_granite_cost, routed_cost,
    routed_down_efficiency, routing_cost_reduction,
    total_workload_cost_reduction,
)
from .escalation_logic import (
    deepseek_escalation_rate, unnecessary_escalations,
)
from .governance_router import governance_stability, quality_preservation
from .routing_engine import routed_tasks

VERDICT_PASSED = "ROUTING_RUN_PASSED"
VERDICT_PARTIAL = "ROUTING_RUN_PARTIAL"
VERDICT_HALT = "ROUTING_RUN_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_PASSED, VERDICT_PARTIAL, VERDICT_HALT,
)

_COST_FLOOR = 0.50
_QUALITY_FLOOR = 0.85


def replay_stability() -> float:
    a = [(t.task_id, t.routed_model) for t in routed_tasks()]
    b = [(t.task_id, t.routed_model) for t in routed_tasks()]
    if a != b:
        return 0.0
    return 1.0 if _core_replay() == 1.0 else 0.0


def routing_metrics() -> dict[str, float]:
    return {
        "routing_cost_reduction": routing_cost_reduction(),
        "deepseek_escalation_rate": deepseek_escalation_rate(),
        "quality_preservation": quality_preservation(),
        "governance_stability": governance_stability(),
        "replay_stability": replay_stability(),
    }


def _signature() -> str:
    m = routing_metrics()
    parts = [f"{k}={m[k]}" for k in sorted(m)]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


def _recommendation() -> str:
    m = routing_metrics()
    if m["replay_stability"] < 1.0 or m["governance_stability"] < 1.0:
        return VERDICT_HALT
    if unnecessary_escalations() > 0:
        return VERDICT_HALT
    if (
        m["routing_cost_reduction"] >= _COST_FLOOR
        and m["quality_preservation"] >= _QUALITY_FLOOR
    ):
        return VERDICT_PASSED
    return VERDICT_PARTIAL


@dataclass(frozen=True)
class V383Report:
    task_count: int
    routing_cost_reduction: float
    deepseek_escalation_rate: float
    quality_preservation: float
    governance_stability: float
    replay_stability: float
    routed_cost_usd: float
    all_deepseek_cost_usd: float
    unnecessary_escalations: int
    core_identity: float
    human_approval_required: bool
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "task_count": self.task_count,
            "routing_cost_reduction": self.routing_cost_reduction,
            "deepseek_escalation_rate": self.deepseek_escalation_rate,
            "quality_preservation": self.quality_preservation,
            "governance_stability": self.governance_stability,
            "replay_stability": self.replay_stability,
            "routed_cost_usd": self.routed_cost_usd,
            "all_deepseek_cost_usd": self.all_deepseek_cost_usd,
            "unnecessary_escalations": self.unnecessary_escalations,
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


def build_report() -> V383Report:
    m = routing_metrics()
    replay = m["replay_stability"]
    halt = (
        replay < 1.0 or m["governance_stability"] < 1.0
        or unnecessary_escalations() > 0
    )
    rationale = (
        f"INFO: routed {len(routed_tasks())} real tasks; structured "
        f"-> Granite, hard semantic -> DeepSeek; routed cost USD "
        f"{routed_cost()} vs all-DeepSeek USD {all_deepseek_cost()} "
        f"(all-Granite USD {all_granite_cost()})",
        f"{'PASS' if m['routing_cost_reduction'] >= _COST_FLOOR else 'FAIL'}"
        f": routing_cost_reduction {m['routing_cost_reduction']} "
        f">= 0.50 (mean per-task fractional saving vs always-DeepSeek;"
        f" routed-down efficiency {routed_down_efficiency()}, "
        f"total-dollar workload saving "
        f"{total_workload_cost_reduction()} - small because hard "
        f"semantic tasks dominate spend and correctly stay on "
        f"DeepSeek)",
        f"INFO: deepseek_escalation_rate "
        f"{m['deepseek_escalation_rate']} (escalate only hard tasks; "
        f"unnecessary escalations {unnecessary_escalations()})",
        f"{'PASS' if m['quality_preservation'] >= _QUALITY_FLOOR else 'FAIL'}"
        f": quality_preservation {m['quality_preservation']} >= 0.85 "
        f"(cheap route did not lose quality)",
        f"{'PASS' if m['governance_stability'] == 1.0 else 'FAIL'}: "
        f"governance_stability {m['governance_stability']} == 1.0",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: replay_stability "
        f"{replay} == 1.0; core_identity {core_identity()}; "
        f"HUMAN_APPROVAL_REQUIRED={HUMAN_APPROVAL_REQUIRED}",
    )
    return V383Report(
        task_count=len(routed_tasks()),
        routing_cost_reduction=m["routing_cost_reduction"],
        deepseek_escalation_rate=m["deepseek_escalation_rate"],
        quality_preservation=m["quality_preservation"],
        governance_stability=m["governance_stability"],
        replay_stability=replay,
        routed_cost_usd=routed_cost(),
        all_deepseek_cost_usd=all_deepseek_cost(),
        unnecessary_escalations=unnecessary_escalations(),
        core_identity=core_identity(),
        human_approval_required=HUMAN_APPROVAL_REQUIRED,
        halt=halt,
        recommendation=_recommendation(),
        rationale=rationale,
    )


def build_routing_artifact() -> dict[str, object]:
    m = routing_metrics()
    return {
        "schema_version": "v38_3_routing_run",
        "disclaimer": (
            "LLM routing & governance run over REAL captured "
            "OpenRouter costs and qualities. DESi routes "
            "low-complexity structured tasks to cheap Granite and "
            "escalates only hard semantic tasks to DeepSeek; the "
            "cost reduction is measured against a real all-DeepSeek "
            "baseline. Routing changes only which model produces the "
            "observed evidence, never governance, and quality "
            "preservation confirms the cheap route did not sacrifice "
            "quality. No benchmark-specific routing hacks. Human "
            "approval is mandatory."
        ),
        "report_verdicts": list(REPORT_VERDICTS),
        "routed_tasks": [t.to_dict() for t in routed_tasks()],
        "routing_cost_reduction": m["routing_cost_reduction"],
        "deepseek_escalation_rate": m["deepseek_escalation_rate"],
        "quality_preservation": m["quality_preservation"],
        "governance_stability": m["governance_stability"],
        "replay_stability": m["replay_stability"],
        "routed_cost_usd": routed_cost(),
        "all_deepseek_cost_usd": all_deepseek_cost(),
        "all_granite_cost_usd": all_granite_cost(),
        "total_workload_cost_reduction": total_workload_cost_reduction(),
        "routed_down_efficiency": routed_down_efficiency(),
        "unnecessary_escalations": unnecessary_escalations(),
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
    "V383Report",
    "build_report",
    "build_routing_artifact",
    "deepseek_escalation_rate",
    "quality_preservation",
    "replay_stability",
    "routing_cost_reduction",
    "routing_metrics",
]
