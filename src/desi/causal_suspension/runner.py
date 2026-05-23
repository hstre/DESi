"""Aufgabe 7 — run the seven required benchmarks against the
patched runtime and collect every metric the hard-gate check
needs.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from ..benchmark import BenchmarkRunner, compute_metrics
from ..benchmark_multistep import MultiStepBenchmarkRunner
from ..causal_redteam.cases import ALL_ADVERSARIAL_CASES
from ..frame_benchmark import (
    FrameBenchmarkRunner,
    compute_frame_metrics,
)
from ..frame_consistency_probe.manipulation import MANIPULATIONS
from ..frame_tension_integration import (
    FrameRoutingLedgerEvent,
    FrameTensionRouter,
    build_integration_benchmark,
    permitted_events,
)
from ..heldout_causal import build_heldout_report
from ..logic.audit import LogicalAuditor, LogicalState
from ..logic.inference import InferenceRule
from ..tools import ToolBenchmarkRunner
from .leap_classes import LeapClass, classify


_FIXED = datetime(2026, 5, 16, 0, 0, 0, tzinfo=timezone.utc)


# ----------------------------------------------------------------------
# v3.15 — adversarial outcome after the v3.16 patch
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class AdversarialOutcome:
    case_id: str
    family: str
    leap_class: str
    still_supported: bool
    actual_final_state: str
    actual_rule: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "family": self.family,
            "leap_class": self.leap_class,
            "still_supported": self.still_supported,
            "actual_final_state": self.actual_final_state,
            "actual_rule": self.actual_rule,
        }


@dataclass(frozen=True)
class V315Result:
    total: int
    false_support_count: int
    false_support_rate: float
    by_family: dict[str, dict[str, int]]
    by_leap_class: dict[str, int]
    outcomes: tuple[AdversarialOutcome, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "false_support_count": self.false_support_count,
            "false_support_rate": self.false_support_rate,
            "by_family": dict(self.by_family),
            "by_leap_class": dict(self.by_leap_class),
            "outcomes": [o.to_dict() for o in self.outcomes],
        }


def _run_v315() -> V315Result:
    auditor = LogicalAuditor()
    outs: list[AdversarialOutcome] = []
    by_family: dict[str, dict[str, int]] = {}
    by_leap: dict[str, int] = {}
    for c in ALL_ADVERSARIAL_CASES:
        r = auditor.audit(c.text)
        actual_rule = r.rule.value if r.rule else None
        still_supported = (
            r.state == LogicalState.LOGICALLY_SUPPORTED
            and actual_rule == InferenceRule.CAUSAL_CHAIN.value
        )
        leap_value = classify(c.attack_family.value).value
        outs.append(AdversarialOutcome(
            case_id=c.case_id,
            family=c.attack_family.value,
            leap_class=leap_value,
            still_supported=still_supported,
            actual_final_state=r.state.value,
            actual_rule=actual_rule,
        ))
        bucket = by_family.setdefault(
            c.attack_family.value,
            {"total": 0, "supported": 0, "suspended": 0},
        )
        bucket["total"] += 1
        if still_supported:
            bucket["supported"] += 1
            by_leap[leap_value] = by_leap.get(leap_value, 0) + 1
        else:
            bucket["suspended"] += 1
    fs = sum(1 for o in outs if o.still_supported)
    return V315Result(
        total=len(outs),
        false_support_count=fs,
        false_support_rate=round(fs / len(outs), 6) if outs else 0.0,
        by_family={k: by_family[k] for k in sorted(by_family)},
        by_leap_class={k: by_leap[k] for k in sorted(by_leap)},
        outcomes=tuple(outs),
    )


# ----------------------------------------------------------------------
# Downstream benchmark snapshots
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class BenchmarkSnapshot:
    name: str
    metric_payload: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "metrics": dict(self.metric_payload)}


def _snapshot_v15() -> BenchmarkSnapshot:
    m = compute_metrics(BenchmarkRunner().run())
    return BenchmarkSnapshot(
        name="v1_5_main",
        metric_payload={
            "precision": m.precision,
            "recall": m.recall,
            "false_positives": m.false_positives,
            "false_negatives": m.false_negatives,
        },
    )


def _snapshot_v19() -> BenchmarkSnapshot:
    run = ToolBenchmarkRunner().run()
    return BenchmarkSnapshot(
        name="v1_9_tools",
        metric_payload={"tool_case_count": len(run.results)},
    )


def _snapshot_v23() -> BenchmarkSnapshot:
    run = MultiStepBenchmarkRunner().run()
    return BenchmarkSnapshot(
        name="v2_3_multistep",
        metric_payload={"case_count": len(run.results)},
    )


def _snapshot_v34() -> BenchmarkSnapshot:
    m = compute_frame_metrics(FrameBenchmarkRunner().run())
    return BenchmarkSnapshot(
        name="v3_4_frame",
        metric_payload={
            "total": m.total, "fully_correct": m.fully_correct,
        },
    )


def _snapshot_v313() -> BenchmarkSnapshot:
    router = FrameTensionRouter()
    bench = build_integration_benchmark()
    correct = 0
    for c in bench:
        d = router.route(
            claim_id=c.case_id,
            claim_text=c.claim_text,
            inherited_context_text=c.inherited_context_text,
            recorded_at=_FIXED,
        )
        if d.event in permitted_events(c.category):
            correct += 1
    adv_router = FrameTensionRouter()
    adv_blocked = 0
    for m in MANIPULATIONS:
        d = adv_router.route(
            claim_id=f"adv:{m.case_id}",
            claim_text=m.text,
            inherited_context_text=m.ctx_3,
            recorded_at=_FIXED,
        )
        if d.event is not FrameRoutingLedgerEvent.FRAME_ROUTING_ALLOWED:
            adv_blocked += 1
    return BenchmarkSnapshot(
        name="v3_13_routing",
        metric_payload={
            "benchmark_total": len(bench),
            "benchmark_correct": correct,
            "benchmark_accuracy": round(correct / len(bench), 6),
            "adversarial_total": len(MANIPULATIONS),
            "adversarial_blocked": adv_blocked,
            "manipulation_detection_rate": round(
                adv_blocked / len(MANIPULATIONS), 6,
            ),
        },
    )


def _snapshot_v314() -> BenchmarkSnapshot:
    r = build_heldout_report(started_at=_FIXED, finished_at=_FIXED)
    return BenchmarkSnapshot(
        name="v3_14_heldout",
        metric_payload={
            "precision": r.metrics.heldout_precision,
            "recall": r.metrics.heldout_recall,
            "false_positive_count": r.metrics.false_positive_count,
            "trap_block_rate": r.metrics.trap_block_rate,
            "rule_generalization_rate":
                r.metrics.rule_generalization_rate,
        },
    )


def run_all_benchmarks() -> dict[str, BenchmarkSnapshot]:
    return {
        "v1_5":  _snapshot_v15(),
        "v1_9":  _snapshot_v19(),
        "v2_3":  _snapshot_v23(),
        "v3_4":  _snapshot_v34(),
        "v3_13": _snapshot_v313(),
        "v3_14": _snapshot_v314(),
    }


# Public re-exports
def run_v315_adversarial() -> V315Result:
    return _run_v315()


__all__ = [
    "AdversarialOutcome",
    "BenchmarkSnapshot",
    "V315Result",
    "run_all_benchmarks",
    "run_v315_adversarial",
]
