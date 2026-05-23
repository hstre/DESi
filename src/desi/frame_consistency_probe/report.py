"""Aufgaben 6 + 9 — detection metrics + recommendation gate."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .consistency import ConsistencyVerdict, evaluate
from .contamination import ContaminationResult, probe_contamination
from .corpus import CorpusCase, build_corpus
from .enums import CorpusGroup, FrameConsistency
from .inner_extractor import extract_inner_frame
from .manipulation import (
    ManipulationOutcome,
    manipulation_detection_rate,
    run_manipulation_suite,
)
from .outer_extractor import extract_outer_frame


MIN_TENSION_RECALL: float = 0.80
MIN_MANIPULATION_DETECTION: float = 0.80
MIN_CORPUS_PER_GROUP: int = 20
MIN_CORPUS_TOTAL: int = 60


@dataclass(frozen=True)
class CorpusOutcome:
    case_id: str
    group: CorpusGroup
    inner_detected: str | None
    outer_detected: str | None
    score: float
    classification: FrameConsistency
    ground_truth_relation: FrameConsistency

    @property
    def correct(self) -> bool:
        return self.classification is self.ground_truth_relation

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "group": self.group.value,
            "inner_detected": self.inner_detected,
            "outer_detected": self.outer_detected,
            "score": self.score,
            "classification": self.classification.value,
            "ground_truth_relation": self.ground_truth_relation.value,
            "correct": self.correct,
        }


@dataclass(frozen=True)
class DetectionMetrics:
    consistency_accuracy: float
    tension_recall: float
    conflict_precision: float
    undecidable_rate: float
    per_group_accuracy: dict[str, float]

    def to_dict(self) -> dict[str, Any]:
        return {
            "consistency_accuracy": self.consistency_accuracy,
            "tension_recall": self.tension_recall,
            "conflict_precision": self.conflict_precision,
            "undecidable_rate": self.undecidable_rate,
            "per_group_accuracy": dict(self.per_group_accuracy),
        }


@dataclass(frozen=True)
class FrameConsistencyProbeReport:
    started_at: datetime
    finished_at: datetime
    corpus_total: int
    corpus_per_group: dict[str, int]
    manipulation_total: int
    manipulation_detection_rate: float
    contamination: ContaminationResult
    metrics: DetectionMetrics
    corpus_outcomes: tuple[CorpusOutcome, ...]
    manipulation_outcomes: tuple[ManipulationOutcome, ...]
    recommended_next: str
    recommendation_reason: str
    replay_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat(),
            "corpus_total": self.corpus_total,
            "corpus_per_group": dict(self.corpus_per_group),
            "manipulation_total": self.manipulation_total,
            "manipulation_detection_rate":
                self.manipulation_detection_rate,
            "contamination": self.contamination.to_dict(),
            "metrics": self.metrics.to_dict(),
            "corpus_outcomes":
                [o.to_dict() for o in self.corpus_outcomes],
            "manipulation_outcomes":
                [m.to_dict() for m in self.manipulation_outcomes],
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


def _run_corpus(
    cases: tuple[CorpusCase, ...]
) -> tuple[tuple[CorpusOutcome, ...], DetectionMetrics]:
    outcomes: list[CorpusOutcome] = []
    for c in cases:
        inner = extract_inner_frame(c.text)
        outer = extract_outer_frame(c.ctx_1, c.ctx_2, c.ctx_3).frame
        v: ConsistencyVerdict = evaluate(inner, outer)
        outcomes.append(CorpusOutcome(
            case_id=c.case_id,
            group=c.group,
            inner_detected=inner.value if inner else None,
            outer_detected=outer.value if outer else None,
            score=v.score,
            classification=v.classification,
            ground_truth_relation=c.ground_truth_relation,
        ))
    total = len(outcomes)
    accuracy = (
        round(sum(1 for o in outcomes if o.correct) / total, 6)
        if total else 0.0
    )

    # tension_recall: of all ground-truth tension cases, fraction we
    # caught (predicted TENSION or stronger, i.e. not CONFIRMED).
    truth_tension = [
        o for o in outcomes
        if o.ground_truth_relation is FrameConsistency.FRAME_TENSION
    ]
    recall_hits = sum(
        1 for o in truth_tension
        if o.classification is not FrameConsistency.FRAME_CONFIRMED
    )
    tension_recall = (
        round(recall_hits / len(truth_tension), 6)
        if truth_tension else 0.0
    )

    # conflict_precision: of all predicted CONFLICT, fraction whose
    # ground truth was CONFLICT or TENSION (any real mismatch).
    pred_conflict = [
        o for o in outcomes
        if o.classification is FrameConsistency.FRAME_CONFLICT
    ]
    real_mismatches = sum(
        1 for o in pred_conflict
        if o.ground_truth_relation in (
            FrameConsistency.FRAME_CONFLICT,
            FrameConsistency.FRAME_TENSION,
        )
    )
    conflict_precision = (
        round(real_mismatches / len(pred_conflict), 6)
        if pred_conflict else 0.0
    )

    undecidable = sum(
        1 for o in outcomes
        if o.classification is FrameConsistency.FRAME_UNDECIDABLE
    )
    undecidable_rate = round(undecidable / total, 6) if total else 0.0

    # Per-group accuracy.
    per_group_totals: dict[str, int] = {}
    per_group_correct: dict[str, int] = {}
    for o in outcomes:
        k = o.group.value
        per_group_totals[k] = per_group_totals.get(k, 0) + 1
        if o.correct:
            per_group_correct[k] = per_group_correct.get(k, 0) + 1
    per_group = {
        k: round(per_group_correct.get(k, 0) / per_group_totals[k], 6)
        for k in sorted(per_group_totals)
    }

    metrics = DetectionMetrics(
        consistency_accuracy=accuracy,
        tension_recall=tension_recall,
        conflict_precision=conflict_precision,
        undecidable_rate=undecidable_rate,
        per_group_accuracy=per_group,
    )
    return tuple(outcomes), metrics


def _decide_recommendation(
    metrics: DetectionMetrics,
    manip_rate: float,
    cont: ContaminationResult,
) -> tuple[str, str]:
    issues: list[str] = []
    if metrics.tension_recall < MIN_TENSION_RECALL:
        issues.append(
            f"tension_recall={metrics.tension_recall} "
            f"< {MIN_TENSION_RECALL}"
        )
    if manip_rate < MIN_MANIPULATION_DETECTION:
        issues.append(
            f"manipulation_detection_rate={manip_rate} "
            f"< {MIN_MANIPULATION_DETECTION}"
        )
    if cont.contamination_risk != 0.0:
        issues.append(
            f"contamination_risk={cont.contamination_risk} != 0.0"
        )
    if issues:
        return "NONE", "; ".join(issues)
    return "FRAME_TENSION_LAYER", "all three gates passed"


def build_consistency_report(
    *,
    started_at: datetime,
    finished_at: datetime,
) -> FrameConsistencyProbeReport:
    cases = build_corpus()
    if len(cases) < MIN_CORPUS_TOTAL:
        raise RuntimeError(
            f"corpus has {len(cases)} cases, need >= {MIN_CORPUS_TOTAL}"
        )
    per_group: dict[str, int] = {g.value: 0 for g in CorpusGroup}
    for c in cases:
        per_group[c.group.value] += 1
    for g, n in per_group.items():
        if n < MIN_CORPUS_PER_GROUP:
            raise RuntimeError(
                f"group {g} has {n} cases, need >= {MIN_CORPUS_PER_GROUP}"
            )

    corpus_outcomes, metrics = _run_corpus(cases)
    manip_outcomes = run_manipulation_suite()
    manip_rate = manipulation_detection_rate(manip_outcomes)
    cont = probe_contamination()
    rec, reason = _decide_recommendation(metrics, manip_rate, cont)

    payload = {
        "corpus_total": len(cases),
        "corpus_per_group": per_group,
        "manipulation_total": len(manip_outcomes),
        "manipulation_detection_rate": manip_rate,
        "contamination": cont.to_dict(),
        "metrics": metrics.to_dict(),
        "corpus_outcomes": [o.to_dict() for o in corpus_outcomes],
        "manipulation_outcomes":
            [m.to_dict() for m in manip_outcomes],
        "recommended_next": rec,
        "recommendation_reason": reason,
    }
    return FrameConsistencyProbeReport(
        started_at=started_at,
        finished_at=finished_at,
        corpus_total=len(cases),
        corpus_per_group=dict(sorted(per_group.items())),
        manipulation_total=len(manip_outcomes),
        manipulation_detection_rate=manip_rate,
        contamination=cont,
        metrics=metrics,
        corpus_outcomes=corpus_outcomes,
        manipulation_outcomes=manip_outcomes,
        recommended_next=rec,
        recommendation_reason=reason,
        replay_hash=_replay_hash(payload),
    )


__all__ = [
    "CorpusOutcome",
    "DetectionMetrics",
    "FrameConsistencyProbeReport",
    "MIN_CORPUS_PER_GROUP",
    "MIN_CORPUS_TOTAL",
    "MIN_MANIPULATION_DETECTION",
    "MIN_TENSION_RECALL",
    "build_consistency_report",
]
