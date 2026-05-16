"""Aufgaben 6 + 10 + 11 — metrics + recommendation."""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .contamination import ContaminationReport, check
from .corpus import (
    ExternalChain, all_chains, transitions_per_chain,
)
from .enums import Domain, FailureClass, GroundTruth, RecommendationOutcome
from .runner import ChainOutcome, run_all


MIN_DOCUMENTS: int = 250
MIN_CHAINS: int = 800
MIN_TRANSITIONS: int = 3200
MIN_NC_DETECTION: float = 0.90
MIN_EXTERNAL_PRECISION: float = 0.90
MIN_EXTERNAL_RECALL: float = 0.80


@dataclass(frozen=True)
class DomainMetrics:
    domain: str
    total: int
    precision: float
    recall: float
    correct: int
    false_support: int
    false_block: int
    undecidable_count: int

    def to_dict(self) -> dict[str, object]:
        return {
            "domain": self.domain,
            "total": self.total,
            "precision": self.precision,
            "recall": self.recall,
            "correct": self.correct,
            "false_support": self.false_support,
            "false_block": self.false_block,
            "undecidable_count": self.undecidable_count,
        }


def _domain_metrics(
    outs: tuple[ChainOutcome, ...],
) -> dict[str, DomainMetrics]:
    by_domain: dict[str, list[ChainOutcome]] = {}
    for o in outs:
        by_domain.setdefault(o.domain, []).append(o)
    metrics: dict[str, DomainMetrics] = {}
    for name, group in by_domain.items():
        valids = [o for o in group if o.ground_truth == "VALID"]
        invalids = [o for o in group if o.ground_truth == "INVALID"]
        n = len(group)
        # TP = valid predicted VALID; FP = invalid predicted VALID;
        # FN = valid predicted INVALID/UNDECIDABLE.
        tp = sum(
            1 for o in valids if o.pipeline_verdict == "VALID"
        )
        fp = sum(
            1 for o in invalids if o.pipeline_verdict == "VALID"
        )
        fn = sum(
            1 for o in valids if o.pipeline_verdict != "VALID"
        )
        false_block = sum(
            1 for o in valids if o.pipeline_verdict == "INVALID"
        )
        undecidable = sum(
            1 for o in group if o.pipeline_verdict == "UNDECIDABLE"
        )
        correct = sum(1 for o in group if o.correct)
        precision = (
            round(tp / (tp + fp), 6) if (tp + fp) else 1.0
        )
        recall = (
            round(tp / (tp + fn), 6) if (tp + fn) else 1.0
        )
        metrics[name] = DomainMetrics(
            domain=name, total=n,
            precision=precision, recall=recall,
            correct=correct,
            false_support=fp,
            false_block=false_block,
            undecidable_count=undecidable,
        )
    return metrics


@dataclass(frozen=True)
class GlobalMetrics:
    external_precision: float
    external_recall: float
    external_false_support: int
    external_false_block: int
    external_undecidable_rate: float
    domain_variance: float

    def to_dict(self) -> dict[str, object]:
        return {
            "external_precision": self.external_precision,
            "external_recall": self.external_recall,
            "external_false_support": self.external_false_support,
            "external_false_block": self.external_false_block,
            "external_undecidable_rate":
                self.external_undecidable_rate,
            "domain_variance": self.domain_variance,
        }


def _global_metrics(
    outs: tuple[ChainOutcome, ...],
    domain_metrics: dict[str, DomainMetrics],
) -> GlobalMetrics:
    valids = [
        o for o in outs
        if o.ground_truth == "VALID"
        and o.domain != Domain.NEGATIVE_CONTROL.value
    ]
    invalids = [
        o for o in outs
        if o.ground_truth == "INVALID"
        and o.domain != Domain.NEGATIVE_CONTROL.value
    ]
    tp = sum(1 for o in valids if o.pipeline_verdict == "VALID")
    fp = sum(1 for o in invalids if o.pipeline_verdict == "VALID")
    fn = sum(1 for o in valids if o.pipeline_verdict != "VALID")
    false_block = sum(
        1 for o in valids if o.pipeline_verdict == "INVALID"
    )
    undecidable = sum(
        1 for o in outs if o.pipeline_verdict == "UNDECIDABLE"
    )
    precision = (
        round(tp / (tp + fp), 6) if (tp + fp) else 1.0
    )
    recall = (
        round(tp / (tp + fn), 6) if (tp + fn) else 1.0
    )
    undecidable_rate = (
        round(undecidable / len(outs), 6) if outs else 0.0
    )
    # Domain variance over precision across the 5 real domains.
    real_domains = [
        m for k, m in domain_metrics.items()
        if k != Domain.NEGATIVE_CONTROL.value
    ]
    if real_domains:
        precisions = [m.precision for m in real_domains]
        mu = sum(precisions) / len(precisions)
        var = sum((p - mu) ** 2 for p in precisions) / len(precisions)
        domain_variance = round(var, 6)
    else:
        domain_variance = 0.0
    return GlobalMetrics(
        external_precision=precision,
        external_recall=recall,
        external_false_support=fp,
        external_false_block=false_block,
        external_undecidable_rate=undecidable_rate,
        domain_variance=domain_variance,
    )


def _nc_detection(
    outs: tuple[ChainOutcome, ...],
) -> tuple[float, int, int]:
    """NC detection: fraction of NC chains classified as
    INVALID or UNDECIDABLE (i.e. not silently passed)."""
    ncs = [
        o for o in outs
        if o.domain == Domain.NEGATIVE_CONTROL.value
    ]
    detected = sum(
        1 for o in ncs if o.pipeline_verdict != "VALID"
    )
    rate = round(detected / len(ncs), 6) if ncs else 0.0
    return rate, detected, len(ncs)


@dataclass(frozen=True)
class ExternalProbeReport:
    started_at: datetime
    finished_at: datetime
    document_count: int
    chain_count: int
    transition_count: int
    contamination: ContaminationReport
    global_metrics: GlobalMetrics
    domain_metrics: dict[str, dict[str, object]]
    nc_detection_rate: float
    nc_detected: int
    nc_total: int
    failure_class_counts: dict[str, int]
    recommended_next: str
    recommendation_reason: str
    replay_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat(),
            "document_count": self.document_count,
            "chain_count": self.chain_count,
            "transition_count": self.transition_count,
            "contamination": self.contamination.to_dict(),
            "global_metrics": self.global_metrics.to_dict(),
            "domain_metrics": dict(self.domain_metrics),
            "nc_detection_rate": self.nc_detection_rate,
            "nc_detected": self.nc_detected,
            "nc_total": self.nc_total,
            "failure_class_counts": dict(self.failure_class_counts),
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


def _decide(
    *,
    document_count: int, chain_count: int, transition_count: int,
    contamination: ContaminationReport,
    nc_detection: float,
    metrics: GlobalMetrics,
) -> tuple[str, str]:
    issues: list[str] = []
    if document_count < MIN_DOCUMENTS:
        issues.append(
            f"document_count={document_count} < {MIN_DOCUMENTS}"
        )
    if chain_count < MIN_CHAINS:
        issues.append(
            f"chain_count={chain_count} < {MIN_CHAINS}"
        )
    if transition_count < MIN_TRANSITIONS:
        issues.append(
            f"transition_count={transition_count} < "
            f"{MIN_TRANSITIONS}"
        )
    if contamination.exact_overlap_count != 0:
        issues.append(
            f"exact_overlap_count="
            f"{contamination.exact_overlap_count} != 0"
        )
    if contamination.semantic_overlap_count != 0:
        issues.append(
            f"semantic_overlap_count="
            f"{contamination.semantic_overlap_count} != 0"
        )
    if nc_detection < MIN_NC_DETECTION:
        issues.append(
            f"nc_detection_rate={nc_detection} < "
            f"{MIN_NC_DETECTION}"
        )
    if metrics.external_precision < MIN_EXTERNAL_PRECISION:
        issues.append(
            f"external_precision={metrics.external_precision} "
            f"< {MIN_EXTERNAL_PRECISION}"
        )
    if metrics.external_recall < MIN_EXTERNAL_RECALL:
        issues.append(
            f"external_recall={metrics.external_recall} "
            f"< {MIN_EXTERNAL_RECALL}"
        )
    if metrics.external_false_support != 0:
        issues.append(
            f"external_false_support="
            f"{metrics.external_false_support} != 0"
        )

    if not issues:
        return (
            RecommendationOutcome.CONFIRMED.value,
            "all hard gates satisfied",
        )

    # Distinguish PARTIAL (only precision/recall gates fall)
    # from FAILED (corpus or contamination gates fall) from
    # NONE (anything else).
    precision_recall_only = all(
        i.startswith("external_") for i in issues
    )
    if precision_recall_only:
        return (
            RecommendationOutcome.PARTIAL.value,
            "; ".join(issues),
        )
    return RecommendationOutcome.FAILED.value, "; ".join(issues)


def build_external_probe_report(
    *, started_at: datetime, finished_at: datetime,
) -> ExternalProbeReport:
    chains = all_chains()
    contamination = check(chains)
    outs = run_all(chains)
    domain = _domain_metrics(outs)
    global_metrics = _global_metrics(outs, domain)
    nc_rate, nc_detected, nc_total = _nc_detection(outs)

    failure_counts: dict[str, int] = {}
    for o in outs:
        if o.failure_class is not None:
            failure_counts[o.failure_class] = (
                failure_counts.get(o.failure_class, 0) + 1
            )

    document_count = len(chains)
    chain_count = len(chains)
    transition_count = chain_count * transitions_per_chain()

    rec, reason = _decide(
        document_count=document_count,
        chain_count=chain_count,
        transition_count=transition_count,
        contamination=contamination,
        nc_detection=nc_rate,
        metrics=global_metrics,
    )

    payload = {
        "document_count": document_count,
        "chain_count": chain_count,
        "transition_count": transition_count,
        "contamination": contamination.to_dict(),
        "global_metrics": global_metrics.to_dict(),
        "domain_metrics": {
            k: v.to_dict() for k, v in domain.items()
        },
        "nc_detection_rate": nc_rate,
        "nc_detected": nc_detected,
        "nc_total": nc_total,
        "failure_class_counts":
            {k: failure_counts[k] for k in sorted(failure_counts)},
        "recommended_next": rec,
        "recommendation_reason": reason,
    }

    return ExternalProbeReport(
        started_at=started_at,
        finished_at=finished_at,
        document_count=document_count,
        chain_count=chain_count,
        transition_count=transition_count,
        contamination=contamination,
        global_metrics=global_metrics,
        domain_metrics={
            k: v.to_dict() for k, v in domain.items()
        },
        nc_detection_rate=nc_rate,
        nc_detected=nc_detected,
        nc_total=nc_total,
        failure_class_counts={
            k: failure_counts[k] for k in sorted(failure_counts)
        },
        recommended_next=rec,
        recommendation_reason=reason,
        replay_hash=_replay_hash(payload),
    )


__all__ = [
    "DomainMetrics",
    "ExternalProbeReport",
    "GlobalMetrics",
    "MIN_CHAINS",
    "MIN_DOCUMENTS",
    "MIN_EXTERNAL_PRECISION",
    "MIN_EXTERNAL_RECALL",
    "MIN_NC_DETECTION",
    "MIN_TRANSITIONS",
    "build_external_probe_report",
]
