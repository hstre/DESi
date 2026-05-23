"""Aufgaben 7 + 8 — effect measurement.

Compares the v4.8 frozen residue (9 cases) with the live
post-patch residue. Reports overall reduction, per
ContentFailure-class delta, and the non-target-relabel
invariant.
"""
from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass

from ..external_probe.corpus import all_chains
from ..external_probe.enums import Domain, GroundTruth
from ..logic.audit import LogicalAuditor, LogicalState
from ..logic.inference import InferenceRule


_REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
_V48_ARTIFACT = _REPO_ROOT / "artifacts" / "v4_8" / "report.json"


TARGET_CLUSTERS: tuple[str, ...] = (
    "DIRECT_CONTRADICTION", "PROPERTY_REVERSAL",
)


@dataclass(frozen=True)
class PerClassEffect:
    cluster: str
    before_count: int
    after_count: int
    reduction: int
    targeted: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "cluster": self.cluster,
            "before_count": self.before_count,
            "after_count": self.after_count,
            "reduction": self.reduction,
            "targeted": self.targeted,
        }


@dataclass(frozen=True)
class EffectReport:
    false_support_before: int
    false_support_after: int
    reduction: int
    reduction_rate: float
    per_class: tuple[PerClassEffect, ...]
    non_target_relabel_count: int

    def to_dict(self) -> dict[str, object]:
        return {
            "false_support_before":
                self.false_support_before,
            "false_support_after":
                self.false_support_after,
            "reduction": self.reduction,
            "reduction_rate": self.reduction_rate,
            "per_class": [p.to_dict() for p in self.per_class],
            "non_target_relabel_count":
                self.non_target_relabel_count,
        }


def _live_false_support_chain_ids() -> set[str]:
    auditor = LogicalAuditor()
    ids: set[str] = set()
    for c in all_chains():
        if c.ground_truth is not GroundTruth.INVALID:
            continue
        if c.domain is Domain.NEGATIVE_CONTROL:
            continue
        a = auditor.audit(c.text)
        if (
            a.state is LogicalState.LOGICALLY_SUPPORTED
            and a.rule is InferenceRule.CAUSAL_CHAIN
        ):
            ids.add(c.chain_id)
    return ids


def measure() -> EffectReport:
    v48 = json.loads(_V48_ARTIFACT.read_text(encoding="utf-8"))
    by_id = {
        c["chain_id"]: c["failure_class"]
        for c in v48["classifications"]
    }
    before_total = len(by_id)
    live_ids = _live_false_support_chain_ids()
    after_total = sum(1 for cid in by_id if cid in live_ids)
    reduction = before_total - after_total
    rate = (
        round(reduction / before_total, 6)
        if before_total else 0.0
    )
    by_class_before: dict[str, set[str]] = {}
    for chain_id, cluster in by_id.items():
        by_class_before.setdefault(cluster, set()).add(chain_id)
    per_class: list[PerClassEffect] = []
    non_target_relabel = 0
    for cluster in sorted(by_class_before):
        before_ids = by_class_before[cluster]
        after_ids = before_ids & live_ids
        targeted = cluster in TARGET_CLUSTERS
        per_class.append(PerClassEffect(
            cluster=cluster,
            before_count=len(before_ids),
            after_count=len(after_ids),
            reduction=len(before_ids) - len(after_ids),
            targeted=targeted,
        ))
        if not targeted and (
            len(before_ids) != len(after_ids)
        ):
            non_target_relabel += abs(
                len(before_ids) - len(after_ids)
            )
    return EffectReport(
        false_support_before=before_total,
        false_support_after=after_total,
        reduction=reduction,
        reduction_rate=rate,
        per_class=tuple(per_class),
        non_target_relabel_count=non_target_relabel,
    )


__all__ = [
    "EffectReport", "PerClassEffect",
    "TARGET_CLUSTERS", "measure",
]
