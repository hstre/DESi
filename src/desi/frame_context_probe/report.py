"""FrameContextProbeReport — Aufgaben 8 + 9.

Aggregates the inheritance simulation, the false-inheritance
probe, and the contamination probe into a single deterministic
report with a ``recommended_next`` field.

The recommendation gate is intentionally strict:

* inheritance accuracy on entropy targets must reach a minimum
  threshold (``MIN_INHERITANCE_ACCURACY``);
* the false-inheritance absorption rate must stay below a
  maximum (``MAX_FALSE_INHERITANCE_RATE``);
* contamination must be zero for **every** fixture phrase the
  simulator uses.

If any of those fail the recommendation collapses to ``NONE`` —
the probe refuses to propose a deployment of context
inheritance unless all three diagnostics line up.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from ..frames import FrameKind
from .contamination import (
    ContaminationResult,
    aggregate_contamination,
    probe_all_fixtures,
)
from .extractor import TargetCase, extract_entropy_targets
from .false_inheritance import (
    FalseInheritanceOutcome,
    NEGATIVE_CONTROLS,
    run_false_inheritance,
)
from .inheritance import InheritanceResult, simulate_all
from .signals import ContextSignal


MIN_INHERITANCE_ACCURACY: float = 0.95
MAX_FALSE_INHERITANCE_RATE: float = 0.10
MIN_TARGETS: int = 25
MIN_FALSE_INHERITANCE: int = 10


@dataclass(frozen=True)
class InheritanceSummary:
    total: int
    correct: int
    accuracy: float
    by_signal: dict[str, int]
    by_layer: dict[str, int]
    by_frame_accuracy: dict[str, float]

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "correct": self.correct,
            "accuracy": self.accuracy,
            "by_signal": dict(self.by_signal),
            "by_layer": dict(self.by_layer),
            "by_frame_accuracy": dict(self.by_frame_accuracy),
        }


@dataclass(frozen=True)
class FalseInheritanceSummary:
    total: int
    absorbed_misleading: int
    absorption_rate: float
    correct_against_ground_truth: int
    ground_truth_precision: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "absorbed_misleading": self.absorbed_misleading,
            "absorption_rate": self.absorption_rate,
            "correct_against_ground_truth":
                self.correct_against_ground_truth,
            "ground_truth_precision": self.ground_truth_precision,
        }


@dataclass(frozen=True)
class FrameContextProbeReport:
    started_at: datetime
    finished_at: datetime
    target_count: int
    false_inheritance_count: int
    contamination_phrase_count: int
    targets: tuple[TargetCase, ...]
    inheritance_results: tuple[InheritanceResult, ...]
    inheritance_summary: InheritanceSummary
    false_inheritance_outcomes: tuple[FalseInheritanceOutcome, ...]
    false_inheritance_summary: FalseInheritanceSummary
    contamination_results: tuple[ContaminationResult, ...]
    contamination_summary: dict[str, Any]
    recommended_next: str
    recommendation_reason: str
    replay_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat(),
            "target_count": self.target_count,
            "false_inheritance_count": self.false_inheritance_count,
            "contamination_phrase_count":
                self.contamination_phrase_count,
            "targets": [t.to_dict() for t in self.targets],
            "inheritance_results":
                [r.to_dict() for r in self.inheritance_results],
            "inheritance_summary": self.inheritance_summary.to_dict(),
            "false_inheritance_outcomes":
                [o.to_dict() for o in self.false_inheritance_outcomes],
            "false_inheritance_summary":
                self.false_inheritance_summary.to_dict(),
            "contamination_results":
                [c.to_dict() for c in self.contamination_results],
            "contamination_summary": self.contamination_summary,
            "recommended_next": self.recommended_next,
            "recommendation_reason": self.recommendation_reason,
            "replay_hash": self.replay_hash,
        }


def _replay_hash(payload: dict[str, Any]) -> str:
    cleaned = {
        k: v for k, v in payload.items()
        if k not in ("started_at", "finished_at", "replay_hash")
    }
    raw = json.dumps(
        cleaned, sort_keys=True, separators=(",", ":"), default=str,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def _summarise_inheritance(
    results: tuple[InheritanceResult, ...]
) -> InheritanceSummary:
    total = len(results)
    correct = sum(1 for r in results if r.correct)
    accuracy = round(correct / total, 6) if total else 0.0
    by_signal: dict[str, int] = {}
    by_layer: dict[str, int] = {}
    for r in results:
        by_signal[r.winning_signal.value] = (
            by_signal.get(r.winning_signal.value, 0) + 1
        )
        layer_key = r.winning_layer or "none"
        by_layer[layer_key] = by_layer.get(layer_key, 0) + 1

    # Per-expected-frame accuracy.
    by_frame_totals: dict[str, int] = {}
    by_frame_correct: dict[str, int] = {}
    for r in results:
        k = r.expected_frame.value
        by_frame_totals[k] = by_frame_totals.get(k, 0) + 1
        if r.correct:
            by_frame_correct[k] = by_frame_correct.get(k, 0) + 1
    by_frame_accuracy = {
        k: round(by_frame_correct.get(k, 0) / by_frame_totals[k], 6)
        for k in sorted(by_frame_totals)
    }
    return InheritanceSummary(
        total=total,
        correct=correct,
        accuracy=accuracy,
        by_signal=dict(sorted(by_signal.items())),
        by_layer=dict(sorted(by_layer.items())),
        by_frame_accuracy=by_frame_accuracy,
    )


def _summarise_false_inheritance(
    outs: tuple[FalseInheritanceOutcome, ...]
) -> FalseInheritanceSummary:
    total = len(outs)
    absorbed = sum(1 for o in outs if o.absorbed_misleading_frame)
    correct = sum(1 for o in outs if o.correct_against_ground_truth)
    rate = round(absorbed / total, 6) if total else 0.0
    precision = round(correct / total, 6) if total else 0.0
    return FalseInheritanceSummary(
        total=total,
        absorbed_misleading=absorbed,
        absorption_rate=rate,
        correct_against_ground_truth=correct,
        ground_truth_precision=precision,
    )


def _decide_recommendation(
    inh: InheritanceSummary,
    fi: FalseInheritanceSummary,
    cont: dict[str, Any],
) -> tuple[str, str]:
    issues: list[str] = []
    if inh.accuracy < MIN_INHERITANCE_ACCURACY:
        issues.append(
            f"inheritance_accuracy={inh.accuracy} "
            f"< {MIN_INHERITANCE_ACCURACY}"
        )
    if fi.absorption_rate > MAX_FALSE_INHERITANCE_RATE:
        issues.append(
            f"false_inheritance_absorption_rate="
            f"{fi.absorption_rate} > {MAX_FALSE_INHERITANCE_RATE}"
        )
    if cont["nonzero_risk_phrases"] > 0:
        issues.append(
            f"contamination: {cont['nonzero_risk_phrases']} of "
            f"{cont['total_phrases']} phrases overlap protected pools"
        )
    if issues:
        return "NONE", "; ".join(issues)
    return (
        "DEPLOY_CONTEXT_INHERITANCE",
        "all three gates passed",
    )


def build_context_probe_report(
    *,
    started_at: datetime,
    finished_at: datetime,
) -> FrameContextProbeReport:
    targets = extract_entropy_targets()
    if len(targets) < MIN_TARGETS:
        raise RuntimeError(
            f"only {len(targets)} entropy targets, need >= {MIN_TARGETS}"
        )
    if len(NEGATIVE_CONTROLS) < MIN_FALSE_INHERITANCE:
        raise RuntimeError(
            f"only {len(NEGATIVE_CONTROLS)} false-inheritance fixtures, "
            f"need >= {MIN_FALSE_INHERITANCE}"
        )

    inh_results = simulate_all(targets)
    inh_summary = _summarise_inheritance(inh_results)

    fi_outs = run_false_inheritance()
    fi_summary = _summarise_false_inheritance(fi_outs)

    cont_results = probe_all_fixtures()
    cont_summary = aggregate_contamination(cont_results)

    rec, reason = _decide_recommendation(
        inh_summary, fi_summary, cont_summary,
    )

    payload = {
        "target_count": len(targets),
        "false_inheritance_count": len(fi_outs),
        "contamination_phrase_count": len(cont_results),
        "targets": [t.to_dict() for t in targets],
        "inheritance_results": [r.to_dict() for r in inh_results],
        "inheritance_summary": inh_summary.to_dict(),
        "false_inheritance_outcomes":
            [o.to_dict() for o in fi_outs],
        "false_inheritance_summary": fi_summary.to_dict(),
        "contamination_results":
            [c.to_dict() for c in cont_results],
        "contamination_summary": cont_summary,
        "recommended_next": rec,
        "recommendation_reason": reason,
    }
    return FrameContextProbeReport(
        started_at=started_at,
        finished_at=finished_at,
        target_count=len(targets),
        false_inheritance_count=len(fi_outs),
        contamination_phrase_count=len(cont_results),
        targets=targets,
        inheritance_results=inh_results,
        inheritance_summary=inh_summary,
        false_inheritance_outcomes=fi_outs,
        false_inheritance_summary=fi_summary,
        contamination_results=cont_results,
        contamination_summary=cont_summary,
        recommended_next=rec,
        recommendation_reason=reason,
        replay_hash=_replay_hash(payload),
    )


__all__ = [
    "FrameContextProbeReport",
    "FalseInheritanceSummary",
    "InheritanceSummary",
    "MAX_FALSE_INHERITANCE_RATE",
    "MIN_INHERITANCE_ACCURACY",
    "build_context_probe_report",
]
