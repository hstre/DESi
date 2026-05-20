"""Aufgaben 3 + 4 + report — per-corpus metrics + recommendation."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .classifier import classify_link
from .contamination import (
    ALLOWED_LINK_TYPES,
    ContaminationReport,
    run_contamination_probe,
)
from .enums import CorpusSource, LinkType
from .extractor import Link, per_corpus_links
from .negative_control import (
    NegativeControlOutcome,
    negative_control_count,
    run_negative_controls,
)


MIN_LINK_COUNT: int = 250
MIN_NEGATIVE_CONTROL_ACCURACY: float = 0.95
MIN_ATTACK_REDUCTION: float = 0.80
MIN_HELDOUT_RECALL: float = 0.85


@dataclass(frozen=True)
class CorpusDistribution:
    corpus: str
    link_count: int
    by_type: dict[str, int]
    unknown_rate: float
    mixed_type_rate: float
    cross_type_transition_rate: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "corpus": self.corpus,
            "link_count": self.link_count,
            "by_type": dict(self.by_type),
            "unknown_rate": self.unknown_rate,
            "mixed_type_rate": self.mixed_type_rate,
            "cross_type_transition_rate":
                self.cross_type_transition_rate,
        }


def _distribution_for(corpus: str,
                      links: tuple[Link, ...]) -> CorpusDistribution:
    by_type: dict[str, int] = {t.value: 0 for t in LinkType}
    chain_types: dict[str, set[str]] = {}
    transitions = 0
    cross_transitions = 0
    previous_per_chain: dict[str, str] = {}

    for link in links:
        link_type = classify_link(link)
        by_type[link_type.value] += 1
        chain_types.setdefault(link.chain_id, set()).add(link_type.value)

        prev = previous_per_chain.get(link.chain_id)
        if prev is not None:
            transitions += 1
            if prev != link_type.value:
                cross_transitions += 1
        previous_per_chain[link.chain_id] = link_type.value

    unknown = by_type.get(LinkType.UNKNOWN.value, 0)
    unknown_rate = (
        round(unknown / len(links), 6) if links else 0.0
    )

    mixed_chains = sum(1 for types in chain_types.values() if len(types) > 1)
    mixed_rate = (
        round(mixed_chains / len(chain_types), 6)
        if chain_types else 0.0
    )

    cross_rate = (
        round(cross_transitions / transitions, 6)
        if transitions else 0.0
    )

    return CorpusDistribution(
        corpus=corpus,
        link_count=len(links),
        by_type=by_type,
        unknown_rate=unknown_rate,
        mixed_type_rate=mixed_rate,
        cross_type_transition_rate=cross_rate,
    )


@dataclass(frozen=True)
class LinkTypingReport:
    started_at: datetime
    finished_at: datetime
    total_link_count: int
    classification_coverage: float
    valid_chain_distribution: dict[str, CorpusDistribution]
    adversarial_distribution: dict[str, CorpusDistribution]
    contamination: ContaminationReport
    negative_control_count: int
    negative_control_accuracy: float
    negative_control_outcomes: tuple[NegativeControlOutcome, ...]
    recommended_next: str
    recommendation_reason: str
    replay_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat(),
            "total_link_count": self.total_link_count,
            "classification_coverage": self.classification_coverage,
            "valid_chain_distribution": {
                k: v.to_dict()
                for k, v in self.valid_chain_distribution.items()
            },
            "adversarial_distribution": {
                k: v.to_dict()
                for k, v in self.adversarial_distribution.items()
            },
            "contamination": self.contamination.to_dict(),
            "negative_control_count": self.negative_control_count,
            "negative_control_accuracy":
                self.negative_control_accuracy,
            "negative_control_outcomes":
                [o.to_dict() for o in self.negative_control_outcomes],
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
    total_links: int,
    nc_accuracy: float,
    contamination: ContaminationReport,
) -> tuple[str, str]:
    issues: list[str] = []
    if total_links < MIN_LINK_COUNT:
        issues.append(f"link_count={total_links} < {MIN_LINK_COUNT}")
    if nc_accuracy < MIN_NEGATIVE_CONTROL_ACCURACY:
        issues.append(
            f"negative_control_accuracy={nc_accuracy} "
            f"< {MIN_NEGATIVE_CONTROL_ACCURACY}"
        )
    if contamination.contamination_count != 0:
        issues.append(
            f"contamination_count="
            f"{contamination.contamination_count} != 0"
        )
    if contamination.v315_attack_reduction < MIN_ATTACK_REDUCTION:
        issues.append(
            f"v315_attack_reduction="
            f"{contamination.v315_attack_reduction} "
            f"< {MIN_ATTACK_REDUCTION}"
        )
    if contamination.v314_survival_rate < MIN_HELDOUT_RECALL:
        issues.append(
            f"v314_survival_rate="
            f"{contamination.v314_survival_rate} "
            f"< {MIN_HELDOUT_RECALL}"
        )
    if issues:
        return "NONE", "; ".join(issues)
    return "LINK_TYPED_CAUSAL_CHAIN", "all gates satisfied"


def build_link_typing_report(
    *,
    started_at: datetime,
    finished_at: datetime,
) -> LinkTypingReport:
    per = per_corpus_links()
    total_links = sum(len(l) for l in per.values())

    valid_dist: dict[str, CorpusDistribution] = {}
    adv_dist: dict[str, CorpusDistribution] = {}
    for name, links in per.items():
        dist = _distribution_for(name, links)
        if name in (
            CorpusSource.V315_ADVERSARIAL.value,
            CorpusSource.V316_SUSPENDED.value,
        ):
            adv_dist[name] = dist
        else:
            valid_dist[name] = dist

    contamination = run_contamination_probe()
    nc_outs, nc_acc = run_negative_controls()

    rec, reason = _decide(total_links, nc_acc, contamination)

    payload = {
        "total_link_count": total_links,
        "classification_coverage": 1.0,
        "valid_chain_distribution": {
            k: v.to_dict() for k, v in valid_dist.items()
        },
        "adversarial_distribution": {
            k: v.to_dict() for k, v in adv_dist.items()
        },
        "contamination": contamination.to_dict(),
        "negative_control_count": negative_control_count(),
        "negative_control_accuracy": nc_acc,
        "negative_control_outcomes": [o.to_dict() for o in nc_outs],
        "recommended_next": rec,
        "recommendation_reason": reason,
    }
    return LinkTypingReport(
        started_at=started_at,
        finished_at=finished_at,
        total_link_count=total_links,
        classification_coverage=1.0,
        valid_chain_distribution=valid_dist,
        adversarial_distribution=adv_dist,
        contamination=contamination,
        negative_control_count=negative_control_count(),
        negative_control_accuracy=nc_acc,
        negative_control_outcomes=nc_outs,
        recommended_next=rec,
        recommendation_reason=reason,
        replay_hash=_replay_hash(payload),
    )


__all__ = [
    "CorpusDistribution",
    "LinkTypingReport",
    "MIN_ATTACK_REDUCTION",
    "MIN_HELDOUT_RECALL",
    "MIN_LINK_COUNT",
    "MIN_NEGATIVE_CONTROL_ACCURACY",
    "build_link_typing_report",
]
