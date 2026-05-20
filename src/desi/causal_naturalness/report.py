"""Aufgaben 2 + 5 — inter-corpus separability, metrics, recommendation."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from ..causal_link_typing.enums import CorpusSource
from ..causal_link_typing.extractor import _sentences
from .corpus import all_input_chains
from .detector import (
    AnomalyVerdict,
    ManifoldStats,
    build_manifold,
    classify_all,
    valid_manifold_subset,
)
from .features import NaturalnessVector, compute_vector
from .negative_control import ALL_NC_CHAINS, NCShape


MIN_CHAIN_COUNT: int = 300
MIN_LINK_COUNT: int = 1000
MIN_VALID_ACCEPT_RATE: float = 0.90
MIN_ADVERSARIAL_DETECTION_RATE: float = 0.85
MAX_FALSE_ALARM_RATE: float = 0.05
MIN_HELDOUT_SURVIVAL: float = 0.85


# ----------------------------------------------------------------------
# Per-corpus distribution
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class CorpusDistribution:
    corpus: str
    chain_count: int
    link_count: int
    mean_feature_vector: tuple[float, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "corpus": self.corpus,
            "chain_count": self.chain_count,
            "link_count": self.link_count,
            "mean_feature_vector": list(self.mean_feature_vector),
        }


def _per_corpus_distribution(
    chains: tuple, verdicts: tuple,
) -> dict[str, CorpusDistribution]:
    out: dict[str, dict[str, Any]] = {}
    for c, v in zip(chains, verdicts):
        bucket = out.setdefault(
            c.corpus.value,
            {"chain": 0, "links": 0, "sums": [0.0] * 8},
        )
        bucket["chain"] += 1
        bucket["links"] += max(0, len(_sentences(c.text)) - 1)
        for i, x in enumerate(v.feature_values):
            bucket["sums"][i] += x
    return {
        k: CorpusDistribution(
            corpus=k,
            chain_count=v["chain"],
            link_count=v["links"],
            mean_feature_vector=tuple(
                round(x / v["chain"], 6) for x in v["sums"]
            ) if v["chain"] else tuple([0.0] * 8),
        )
        for k, v in sorted(out.items())
    }


# ----------------------------------------------------------------------
# Inter-corpus separability — Euclidean distance between centroids.
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class CorpusPairSeparation:
    a: str
    b: str
    centroid_distance: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "a": self.a, "b": self.b,
            "centroid_distance": self.centroid_distance,
        }


def _separability(
    distributions: dict[str, CorpusDistribution],
) -> tuple[CorpusPairSeparation, ...]:
    names = sorted(distributions)
    out: list[CorpusPairSeparation] = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            va = distributions[a].mean_feature_vector
            vb = distributions[b].mean_feature_vector
            dist = sum((x - y) ** 2 for x, y in zip(va, vb)) ** 0.5
            out.append(CorpusPairSeparation(
                a=a, b=b, centroid_distance=round(dist, 6),
            ))
    return tuple(out)


# ----------------------------------------------------------------------
# Negative control replay
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class NCResult:
    case_id: str
    shape: str
    expected_natural: bool
    is_anomalous: bool
    correct: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id, "shape": self.shape,
            "expected_natural": self.expected_natural,
            "is_anomalous": self.is_anomalous,
            "correct": self.correct,
        }


def _run_nc(manifold: ManifoldStats) -> tuple[
    tuple[NCResult, ...], dict[str, dict[str, int]],
]:
    out: list[NCResult] = []
    per_shape: dict[str, dict[str, int]] = {
        s.value: {"total": 0, "correct": 0} for s in NCShape
    }
    for nc in ALL_NC_CHAINS:
        v = compute_vector(
            nc.case_id, nc.text, CorpusSource.V315_ADVERSARIAL,
        )
        verdict = next(iter(classify_all((  # single-element tuple
            type("E", (), {
                "chain_id": v.chain_id, "corpus": CorpusSource.V315_ADVERSARIAL,
                "text": nc.text, "expected_natural": nc.expected_natural,
            })(),
        ), manifold)))
        # Easier: classify_anomaly directly.
        from .detector import classify_anomaly
        verdict = classify_anomaly(v, manifold)
        # natural -> accepted == not anomalous; correct if alignment.
        natural_pred = not verdict.is_anomalous
        correct = (natural_pred == nc.expected_natural)
        out.append(NCResult(
            case_id=nc.case_id, shape=nc.shape.value,
            expected_natural=nc.expected_natural,
            is_anomalous=verdict.is_anomalous,
            correct=correct,
        ))
        bucket = per_shape[nc.shape.value]
        bucket["total"] += 1
        if correct:
            bucket["correct"] += 1
    return tuple(out), per_shape


# ----------------------------------------------------------------------
# Report
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class NaturalnessReport:
    started_at: datetime
    finished_at: datetime
    total_chain_count: int
    total_link_count: int
    manifold: ManifoldStats
    distributions: dict[str, CorpusDistribution]
    separability: tuple[CorpusPairSeparation, ...]
    valid_accept_rate: float
    adversarial_detection_rate: float
    false_alarm_rate: float
    heldout_survival: float
    contamination_count: int
    nc_results: tuple[NCResult, ...]
    nc_per_shape: dict[str, dict[str, int]]
    recommended_next: str
    recommendation_reason: str
    replay_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat(),
            "total_chain_count": self.total_chain_count,
            "total_link_count": self.total_link_count,
            "manifold": self.manifold.to_dict(),
            "distributions": {
                k: v.to_dict() for k, v in self.distributions.items()
            },
            "separability": [s.to_dict() for s in self.separability],
            "valid_accept_rate": self.valid_accept_rate,
            "adversarial_detection_rate":
                self.adversarial_detection_rate,
            "false_alarm_rate": self.false_alarm_rate,
            "heldout_survival": self.heldout_survival,
            "contamination_count": self.contamination_count,
            "nc_results": [r.to_dict() for r in self.nc_results],
            "nc_per_shape": dict(self.nc_per_shape),
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
    total_chains: int, total_links: int,
    valid_accept: float, adv_detect: float,
    false_alarm: float, heldout_survival: float,
    contamination: int,
) -> tuple[str, str]:
    issues: list[str] = []
    if total_chains < MIN_CHAIN_COUNT:
        issues.append(
            f"chain_count={total_chains} < {MIN_CHAIN_COUNT}"
        )
    if total_links < MIN_LINK_COUNT:
        issues.append(
            f"link_count={total_links} < {MIN_LINK_COUNT}"
        )
    if valid_accept < MIN_VALID_ACCEPT_RATE:
        issues.append(
            f"valid_accept_rate={valid_accept} "
            f"< {MIN_VALID_ACCEPT_RATE}"
        )
    if adv_detect < MIN_ADVERSARIAL_DETECTION_RATE:
        issues.append(
            f"adversarial_detection_rate={adv_detect} "
            f"< {MIN_ADVERSARIAL_DETECTION_RATE}"
        )
    if false_alarm > MAX_FALSE_ALARM_RATE:
        issues.append(
            f"false_alarm_rate={false_alarm} "
            f"> {MAX_FALSE_ALARM_RATE}"
        )
    if heldout_survival < MIN_HELDOUT_SURVIVAL:
        issues.append(
            f"heldout_survival={heldout_survival} "
            f"< {MIN_HELDOUT_SURVIVAL}"
        )
    if contamination != 0:
        issues.append(
            f"contamination_count={contamination} != 0"
        )
    if issues:
        return "NONE", "; ".join(issues)
    return (
        "CAUSAL_NATURALNESS_GATE",
        "all five hard gates satisfied",
    )


def build_naturalness_report(
    *, started_at: datetime, finished_at: datetime,
) -> NaturalnessReport:
    chains = all_input_chains()
    total_chains = len(chains)
    total_links = sum(
        max(0, len(_sentences(c.text)) - 1) for c in chains
    )
    manifold = build_manifold(valid_manifold_subset(chains))
    verdicts = classify_all(chains, manifold)

    distributions = _per_corpus_distribution(chains, verdicts)
    separability = _separability(distributions)

    valid_total = 0
    valid_accepted = 0
    adv_total = 0
    adv_detected = 0
    heldout_valid_total = 0
    heldout_valid_accepted = 0
    for c, v in zip(chains, verdicts):
        if c.expected_natural:
            valid_total += 1
            if not v.is_anomalous:
                valid_accepted += 1
            if c.corpus is CorpusSource.V314_HELDOUT:
                heldout_valid_total += 1
                if not v.is_anomalous:
                    heldout_valid_accepted += 1
        else:
            adv_total += 1
            if v.is_anomalous:
                adv_detected += 1

    valid_accept = (
        round(valid_accepted / valid_total, 6) if valid_total else 0.0
    )
    adv_detect = (
        round(adv_detected / adv_total, 6) if adv_total else 0.0
    )
    false_alarm = (
        round(1.0 - valid_accept, 6)
    )
    heldout_survival = (
        round(heldout_valid_accepted / heldout_valid_total, 6)
        if heldout_valid_total else 0.0
    )
    contamination = adv_total - adv_detected

    nc_results, nc_per_shape = _run_nc(manifold)

    rec, reason = _decide(
        total_chains=total_chains, total_links=total_links,
        valid_accept=valid_accept, adv_detect=adv_detect,
        false_alarm=false_alarm,
        heldout_survival=heldout_survival,
        contamination=contamination,
    )

    payload = {
        "total_chain_count": total_chains,
        "total_link_count": total_links,
        "manifold": manifold.to_dict(),
        "distributions": {
            k: v.to_dict() for k, v in distributions.items()
        },
        "separability": [s.to_dict() for s in separability],
        "valid_accept_rate": valid_accept,
        "adversarial_detection_rate": adv_detect,
        "false_alarm_rate": false_alarm,
        "heldout_survival": heldout_survival,
        "contamination_count": contamination,
        "nc_results": [r.to_dict() for r in nc_results],
        "nc_per_shape": dict(nc_per_shape),
        "recommended_next": rec,
        "recommendation_reason": reason,
    }
    return NaturalnessReport(
        started_at=started_at,
        finished_at=finished_at,
        total_chain_count=total_chains,
        total_link_count=total_links,
        manifold=manifold,
        distributions=distributions,
        separability=separability,
        valid_accept_rate=valid_accept,
        adversarial_detection_rate=adv_detect,
        false_alarm_rate=false_alarm,
        heldout_survival=heldout_survival,
        contamination_count=contamination,
        nc_results=nc_results,
        nc_per_shape=nc_per_shape,
        recommended_next=rec,
        recommendation_reason=reason,
        replay_hash=_replay_hash(payload),
    )


__all__ = [
    "CorpusDistribution",
    "CorpusPairSeparation",
    "MAX_FALSE_ALARM_RATE",
    "MIN_ADVERSARIAL_DETECTION_RATE",
    "MIN_CHAIN_COUNT",
    "MIN_HELDOUT_SURVIVAL",
    "MIN_LINK_COUNT",
    "MIN_VALID_ACCEPT_RATE",
    "NCResult",
    "NaturalnessReport",
    "build_naturalness_report",
]
