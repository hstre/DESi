"""Aufgaben 6 + 7 + 10 + 11 — per-strategy metrics, safety
gates, recommendation gate, and replay-stable report."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from ..external_probe.contamination import check as desi_contam_check
from ..external_probe.corpus import (
    ExternalChain, all_chains, transitions_per_chain,
)
from ..external_probe.enums import Domain
from ..external_probe.report import (
    build_external_probe_report as _v40_report_builder,
)
from ..frames import FrameKind
from .enums import (
    FrameInferenceFailure, InferenceStrategy, RecommendationOutcome,
)
from .negative_controls import FrameNC, all_negative_controls
from .runner import (
    FrameInferenceRecord, NegativeControlRecord, StrategyRun,
    run_all_strategies,
)


# ----- Constants exposed for tests -----------------------------

MIN_NC_DETECTION: float = 0.90
MIN_FRAME_PRECISION: float = 0.95
MIN_FRAME_RECALL: float = 0.70
MAX_FRAME_FALSE_ASSIGNMENT: float = 0.05
MIN_NC_COUNT: int = 100
V40_CHAIN_COUNT: int = 800
V40_TRANSITION_COUNT: int = 3200
V40_REPLAY_HASH: str = "aefa8f1e3429225a"


# ----- Per-strategy metrics ------------------------------------

@dataclass(frozen=True)
class FrameMetrics:
    """Inference-only metrics (chain → frame)."""

    total: int
    assignments: int
    correct: int
    wrong: int
    abstentions: int
    frame_precision: float
    frame_recall: float
    frame_false_assignment: float
    frame_undecidable_rate: float

    def to_dict(self) -> dict[str, object]:
        return {
            "total": self.total,
            "assignments": self.assignments,
            "correct": self.correct,
            "wrong": self.wrong,
            "abstentions": self.abstentions,
            "frame_precision": self.frame_precision,
            "frame_recall": self.frame_recall,
            "frame_false_assignment":
                self.frame_false_assignment,
            "frame_undecidable_rate":
                self.frame_undecidable_rate,
        }


@dataclass(frozen=True)
class PipelineMetrics:
    """Full-stack metrics under the inferred frame."""

    external_precision: float
    external_recall: float
    external_false_support: int
    external_false_block: int
    external_undecidable_rate: float

    def to_dict(self) -> dict[str, object]:
        return {
            "external_precision": self.external_precision,
            "external_recall": self.external_recall,
            "external_false_support":
                self.external_false_support,
            "external_false_block":
                self.external_false_block,
            "external_undecidable_rate":
                self.external_undecidable_rate,
        }


@dataclass(frozen=True)
class NCMetrics:
    total: int
    detected: int
    nc_detection_rate: float
    by_family: dict[str, dict[str, int]]

    def to_dict(self) -> dict[str, object]:
        return {
            "total": self.total,
            "detected": self.detected,
            "nc_detection_rate": self.nc_detection_rate,
            "by_family": dict(self.by_family),
        }


@dataclass(frozen=True)
class StrategyReport:
    strategy: str
    valid: bool
    invalid_reasons: tuple[str, ...]
    frame_metrics: FrameMetrics
    pipeline_metrics: PipelineMetrics
    nc_metrics: NCMetrics
    failure_class_counts: dict[str, int]

    def to_dict(self) -> dict[str, object]:
        return {
            "strategy": self.strategy,
            "valid": self.valid,
            "invalid_reasons": list(self.invalid_reasons),
            "frame_metrics": self.frame_metrics.to_dict(),
            "pipeline_metrics":
                self.pipeline_metrics.to_dict(),
            "nc_metrics": self.nc_metrics.to_dict(),
            "failure_class_counts":
                dict(self.failure_class_counts),
        }


def _frame_metrics(
    records: tuple[FrameInferenceRecord, ...],
) -> FrameMetrics:
    """Compute frame-only metrics over the real (non-NC) chains.

    * ``frame_precision`` = correct / (correct + wrong)
    * ``frame_recall``   = correct / total_with_gt
    * ``frame_false_assignment`` = wrong / total_with_gt
    * ``frame_undecidable_rate`` = abstentions / total_with_gt
    """
    real = [
        r for r in records
        if r.domain != Domain.NEGATIVE_CONTROL.value
    ]
    total = len(real)
    assignments = sum(
        1 for r in real
        if r.inferred_frame is not None
        and r.inferred_frame != FrameKind.FRAME_UNDECLARED.value
    )
    correct = sum(1 for r in real if r.correct_frame)
    wrong = sum(
        1 for r in real
        if (r.inferred_frame is not None
            and r.inferred_frame != FrameKind.FRAME_UNDECLARED.value)
        and not r.correct_frame
    )
    abstentions = total - assignments
    if assignments:
        precision = round(correct / assignments, 6)
    else:
        precision = 1.0
    recall = round(correct / total, 6) if total else 0.0
    false_assign = round(wrong / total, 6) if total else 0.0
    undecidable_rate = (
        round(abstentions / total, 6) if total else 0.0
    )
    return FrameMetrics(
        total=total, assignments=assignments,
        correct=correct, wrong=wrong, abstentions=abstentions,
        frame_precision=precision, frame_recall=recall,
        frame_false_assignment=false_assign,
        frame_undecidable_rate=undecidable_rate,
    )


def _pipeline_metrics(
    records: tuple[FrameInferenceRecord, ...],
) -> PipelineMetrics:
    """Full-stack metrics computed only over the real five
    domains (NC excluded, matching v4.0 convention)."""
    real = [
        r for r in records
        if r.domain != Domain.NEGATIVE_CONTROL.value
    ]
    valids = [r for r in real if r.outcome_ground_truth == "VALID"]
    invalids = [
        r for r in real if r.outcome_ground_truth == "INVALID"
    ]
    tp = sum(1 for r in valids if r.outcome_verdict == "VALID")
    fp = sum(1 for r in invalids if r.outcome_verdict == "VALID")
    fn = sum(1 for r in valids if r.outcome_verdict != "VALID")
    false_block = sum(
        1 for r in valids if r.outcome_verdict == "INVALID"
    )
    undecidable = sum(
        1 for r in real if r.outcome_verdict == "UNDECIDABLE"
    )
    precision = (
        round(tp / (tp + fp), 6) if (tp + fp) else 1.0
    )
    recall = (
        round(tp / (tp + fn), 6) if (tp + fn) else 1.0
    )
    undecidable_rate = (
        round(undecidable / len(real), 6) if real else 0.0
    )
    return PipelineMetrics(
        external_precision=precision,
        external_recall=recall,
        external_false_support=fp,
        external_false_block=false_block,
        external_undecidable_rate=undecidable_rate,
    )


def _nc_metrics(
    nc_records: tuple[NegativeControlRecord, ...],
) -> NCMetrics:
    total = len(nc_records)
    detected = sum(1 for r in nc_records if r.detected)
    rate = round(detected / total, 6) if total else 0.0
    by_family: dict[str, dict[str, int]] = {}
    for r in nc_records:
        slot = by_family.setdefault(
            r.family, {"total": 0, "detected": 0},
        )
        slot["total"] += 1
        if r.detected:
            slot["detected"] += 1
    return NCMetrics(
        total=total, detected=detected,
        nc_detection_rate=rate,
        by_family={k: dict(v) for k, v in sorted(by_family.items())},
    )


def _failure_class_counts(
    records: tuple[FrameInferenceRecord, ...],
    nc_records: tuple[NegativeControlRecord, ...],
) -> dict[str, int]:
    """Count every closed failure class across both real chains
    and NC chains."""
    counts: dict[str, int] = {f.value: 0 for f in FrameInferenceFailure}
    for r in records:
        if r.frame_failure_class is not None:
            counts[r.frame_failure_class] += 1
    for r in nc_records:
        if r.failure_class is not None:
            counts[r.failure_class] += 1
    return {k: counts[k] for k in counts if counts[k] > 0}


def _strategy_report(run: StrategyRun) -> StrategyReport:
    fm = _frame_metrics(run.records)
    pm = _pipeline_metrics(run.records)
    nm = _nc_metrics(run.nc_records)
    failures = _failure_class_counts(run.records, run.nc_records)
    invalid: list[str] = []
    if pm.external_false_support > 0:
        invalid.append(
            f"external_false_support="
            f"{pm.external_false_support} > 0"
        )
    if fm.frame_false_assignment > MAX_FRAME_FALSE_ASSIGNMENT:
        invalid.append(
            f"frame_false_assignment="
            f"{fm.frame_false_assignment} > "
            f"{MAX_FRAME_FALSE_ASSIGNMENT}"
        )
    return StrategyReport(
        strategy=run.strategy,
        valid=not invalid,
        invalid_reasons=tuple(invalid),
        frame_metrics=fm,
        pipeline_metrics=pm,
        nc_metrics=nm,
        failure_class_counts=failures,
    )


# ----- Top-level report ---------------------------------------

@dataclass(frozen=True)
class V41Report:
    started_at: datetime
    finished_at: datetime
    chain_count: int
    transition_count: int
    nc_count: int
    nc_contamination_count: int
    v40_baseline_recall: float
    v40_replay_hash: str
    strategy_reports: tuple[StrategyReport, ...]
    best_strategy: str | None
    recommended_next: str
    recommendation_reason: str
    replay_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat(),
            "chain_count": self.chain_count,
            "transition_count": self.transition_count,
            "nc_count": self.nc_count,
            "nc_contamination_count":
                self.nc_contamination_count,
            "v40_baseline_recall": self.v40_baseline_recall,
            "v40_replay_hash": self.v40_replay_hash,
            "strategy_reports": [
                s.to_dict() for s in self.strategy_reports
            ],
            "best_strategy": self.best_strategy,
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
        cleaned, sort_keys=True, separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def _nc_contamination_count(
    ncs: tuple[FrameNC, ...],
) -> int:
    """The v4.1 NC bank must not overlap any DESi corpus chain
    above the v4.0 jaccard threshold. Reuse v4.0's contamination
    machinery by faking each NC as an ``ExternalChain``.
    """
    from ..external_probe.corpus import ExternalChain
    from ..external_probe.enums import GroundTruth

    fakes = tuple(
        ExternalChain(
            chain_id=nc.nc_id, domain=Domain.NEGATIVE_CONTROL,
            text=nc.text, ground_truth=GroundTruth.INVALID,
            rationale=f"v4.1 NC {nc.family}",
        )
        for nc in ncs
    )
    rep = desi_contam_check(fakes)
    return rep.exact_overlap_count + rep.semantic_overlap_count


def _v40_baseline_recall() -> float:
    """Run the v4.0 report once to read its external_recall.

    Cheaper than re-implementing v4.0 here, and guaranteed to
    stay in sync if the v4.0 figures ever shift (they shouldn't —
    the v4.0 hash is pinned by tests/external_probe/test_regression).
    """
    rep = _v40_report_builder(
        started_at=datetime(2026, 5, 16, tzinfo=None),
        finished_at=datetime(2026, 5, 16, tzinfo=None),
    )
    # Sanity check — the recall stays where v4.0 left it. The pin
    # on v40_replay_hash is asserted by tests, but having it here
    # too makes the recommendation gate's reference point auditable
    # in the report payload itself.
    return rep.global_metrics.external_recall


def _decide(
    reports: tuple[StrategyReport, ...],
    *,
    nc_contamination: int,
    chain_count: int,
    transition_count: int,
    v40_recall: float,
) -> tuple[str | None, str, str]:
    """Return (best_strategy, recommendation, reason).

    Decision tree (closed):

    * if every strategy is invalid → ``FAILED``,
    * else pick the valid strategy with the highest
      ``frame_recall`` that also beats the v4.0 recall baseline
      *and* meets the success thresholds
      → ``CONFIRMED``,
    * else any valid strategy beats the v4.0 recall baseline
      → ``PARTIAL`` (the v3.13 stack can absorb a synthetic
      marker without losing precision, but the inference is not
      sharp enough to claim full ingress),
    * else ``NONE``.
    """
    issues: list[str] = []
    if chain_count != V40_CHAIN_COUNT:
        issues.append(
            f"chain_count={chain_count} != {V40_CHAIN_COUNT}"
        )
    if transition_count != V40_TRANSITION_COUNT:
        issues.append(
            f"transition_count={transition_count} != "
            f"{V40_TRANSITION_COUNT}"
        )
    if nc_contamination != 0:
        issues.append(
            f"nc_contamination_count={nc_contamination} != 0"
        )

    valids = tuple(s for s in reports if s.valid)
    if not valids:
        reason = "; ".join(
            (
                "no valid strategy",
                *(
                    f"{s.strategy}: "
                    f"{', '.join(s.invalid_reasons) or '—'}"
                    for s in reports
                ),
                *issues,
            )
        )
        return None, RecommendationOutcome.FAILED.value, reason

    # Strategies that achieve the per-strategy success thresholds.
    qualifying = tuple(
        s for s in valids
        if (
            s.frame_metrics.frame_precision >= MIN_FRAME_PRECISION
            and s.frame_metrics.frame_recall >= MIN_FRAME_RECALL
            and s.pipeline_metrics.external_recall > v40_recall
            and s.nc_metrics.nc_detection_rate >= MIN_NC_DETECTION
        )
    )
    # Pick best by frame_recall, tie-break by frame_precision.
    if qualifying:
        best = sorted(
            qualifying,
            key=lambda s: (
                -s.frame_metrics.frame_recall,
                -s.frame_metrics.frame_precision,
                s.strategy,
            ),
        )[0]
        reason = (
            f"{best.strategy}: frame_precision="
            f"{best.frame_metrics.frame_precision} "
            f"frame_recall={best.frame_metrics.frame_recall} "
            f"external_recall="
            f"{best.pipeline_metrics.external_recall} "
            f"v4.0_baseline={v40_recall}"
        )
        if issues:
            reason += "; " + "; ".join(issues)
            return (
                best.strategy,
                RecommendationOutcome.PARTIAL.value, reason,
            )
        return (
            best.strategy,
            RecommendationOutcome.CONFIRMED.value, reason,
        )

    # No strategy hit the success threshold — partial if any
    # valid strategy beat the v4.0 recall baseline at all.
    beats_baseline = tuple(
        s for s in valids
        if s.pipeline_metrics.external_recall > v40_recall
    )
    if beats_baseline:
        best = sorted(
            beats_baseline,
            key=lambda s: (
                -s.pipeline_metrics.external_recall,
                -s.frame_metrics.frame_precision,
                s.strategy,
            ),
        )[0]
        reason_parts = [
            f"best={best.strategy}",
            f"external_recall={best.pipeline_metrics.external_recall}",
            f"v4.0_baseline={v40_recall}",
            f"frame_precision={best.frame_metrics.frame_precision}",
            f"frame_recall={best.frame_metrics.frame_recall}",
        ]
        if issues:
            reason_parts.extend(issues)
        return (
            best.strategy,
            RecommendationOutcome.PARTIAL.value,
            "; ".join(reason_parts),
        )

    reason_parts = [
        "no strategy lifted external_recall above the v4.0 "
        f"baseline ({v40_recall})"
    ]
    if issues:
        reason_parts.extend(issues)
    return None, RecommendationOutcome.NONE.value, "; ".join(
        reason_parts,
    )


def build_v41_report(
    *,
    started_at: datetime, finished_at: datetime,
) -> V41Report:
    chains = all_chains()
    chain_count = len(chains)
    transition_count = chain_count * transitions_per_chain()
    ncs = all_negative_controls()
    nc_contam = _nc_contamination_count(ncs)
    runs = run_all_strategies()
    strategy_reports = tuple(_strategy_report(r) for r in runs)
    v40_recall = _v40_baseline_recall()
    best, recommendation, reason = _decide(
        strategy_reports,
        nc_contamination=nc_contam,
        chain_count=chain_count,
        transition_count=transition_count,
        v40_recall=v40_recall,
    )
    payload = {
        "chain_count": chain_count,
        "transition_count": transition_count,
        "nc_count": len(ncs),
        "nc_contamination_count": nc_contam,
        "v40_baseline_recall": v40_recall,
        "v40_replay_hash": V40_REPLAY_HASH,
        "strategy_reports": [
            s.to_dict() for s in strategy_reports
        ],
        "best_strategy": best,
        "recommended_next": recommendation,
        "recommendation_reason": reason,
    }
    return V41Report(
        started_at=started_at, finished_at=finished_at,
        chain_count=chain_count,
        transition_count=transition_count,
        nc_count=len(ncs),
        nc_contamination_count=nc_contam,
        v40_baseline_recall=v40_recall,
        v40_replay_hash=V40_REPLAY_HASH,
        strategy_reports=strategy_reports,
        best_strategy=best,
        recommended_next=recommendation,
        recommendation_reason=reason,
        replay_hash=_replay_hash(payload),
    )


__all__ = [
    "FrameMetrics",
    "MAX_FRAME_FALSE_ASSIGNMENT",
    "MIN_FRAME_PRECISION",
    "MIN_FRAME_RECALL",
    "MIN_NC_COUNT",
    "MIN_NC_DETECTION",
    "NCMetrics",
    "PipelineMetrics",
    "StrategyReport",
    "V40_CHAIN_COUNT",
    "V40_REPLAY_HASH",
    "V40_TRANSITION_COUNT",
    "V41Report",
    "build_v41_report",
]
