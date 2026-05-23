"""Aufgabe 6 + 7 — patch-effect measurement.

Re-runs the v4.1 external pipeline on the v4.0 corpus with the
patched ``LogicalAuditor``. Because the patch is deterministic
the per-strategy outcomes are recomputed live; the
``BEFORE`` figures are read from the frozen v4.1 artifact.

Per directive section 7, the report carries:

* false_support_before / after / reduction / reduction_rate
* external_precision_before / after
* external_recall_before / after
* undecidable_rate_before / after
* per-target-class before/after/reduction
* per-non-target-class before/after  (must not be silently
  relabeled).
"""
from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass

from ..external_audit_probe import (
    classify_all, collect_false_support_cases, replay_all,
)
from ..external_audit_probe.enums import ExternalAuditFailure
from ..external_probe.corpus import all_chains
from ..external_probe.enums import Domain, GroundTruth
from ..frame_inference import InferenceStrategy, run_strategy
from ..logic.audit import LogicalAuditor, LogicalState
from ..logic.inference import InferenceRule
from .extensions import PATCHED_CLUSTERS


_REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
_V41_ARTIFACT = _REPO_ROOT / "artifacts" / "v4_1" / "report.json"


def _load_v41_frozen() -> dict:
    if not _V41_ARTIFACT.exists():
        raise FileNotFoundError(
            f"v4.1 artifact missing at {_V41_ARTIFACT}"
        )
    return json.loads(_V41_ARTIFACT.read_text(encoding="utf-8"))


def _v41_baseline() -> dict[str, float | int]:
    data = _load_v41_frozen()
    # Pick the F4 strategy as the canonical baseline for ingress
    # (F4 had the highest external_recall in v4.1 = 0.675); the
    # directive treats v4.1's "before" as the v4.1 corpus result
    # under whichever strategy unlocks the chains.
    strategies = {s["strategy"]: s for s in data["strategy_reports"]}
    # Aggregate false_support across all strategies (a case is
    # false_support if at least one strategy unlocks it -> v4.2
    # confirmed 143 such chains).
    return {
        "f4_external_precision":
            strategies["F4_context_window"]["pipeline_metrics"][
                "external_precision"
            ],
        "f4_external_recall":
            strategies["F4_context_window"]["pipeline_metrics"][
                "external_recall"
            ],
        "f4_external_false_support":
            strategies["F4_context_window"]["pipeline_metrics"][
                "external_false_support"
            ],
        "f4_external_undecidable_rate":
            strategies["F4_context_window"]["pipeline_metrics"][
                "external_undecidable_rate"
            ],
    }


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
    false_support_reduction: int
    reduction_rate: float
    external_precision_before: float
    external_precision_after: float
    external_recall_before: float
    external_recall_after: float
    undecidable_rate_before: float
    undecidable_rate_after: float
    per_class: tuple[PerClassEffect, ...]
    non_target_relabel_count: int

    def to_dict(self) -> dict[str, object]:
        return {
            "false_support_before":
                self.false_support_before,
            "false_support_after":
                self.false_support_after,
            "false_support_reduction":
                self.false_support_reduction,
            "reduction_rate": self.reduction_rate,
            "external_precision_before":
                self.external_precision_before,
            "external_precision_after":
                self.external_precision_after,
            "external_recall_before":
                self.external_recall_before,
            "external_recall_after":
                self.external_recall_after,
            "undecidable_rate_before":
                self.undecidable_rate_before,
            "undecidable_rate_after":
                self.undecidable_rate_after,
            "per_class": [p.to_dict() for p in self.per_class],
            "non_target_relabel_count":
                self.non_target_relabel_count,
        }


def _current_false_support_count() -> int:
    """Count chains in the v4.0 corpus whose ground_truth is
    INVALID and that still audit as LOGICALLY_SUPPORTED under
    CAUSAL_CHAIN with the *patched* auditor."""
    auditor = LogicalAuditor()
    n = 0
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
            n += 1
    return n


def _per_class_effect(
    before_classes: tuple,
    cases: tuple,
) -> tuple[tuple[PerClassEffect, ...], int]:
    """For every closed failure class compute before/after
    counts. ``after`` counts chains that *still* audit as
    LOGICALLY_SUPPORTED post-patch. ``non_target_relabel_count``
    is the number of cases whose class label would have to
    change to remain in the residue — should be zero."""
    auditor = LogicalAuditor()
    # Build per-class before counts.
    before_counts: dict[str, int] = {}
    after_counts: dict[str, int] = {}
    by_class_cases: dict[str, list] = {}
    for case, cls in zip(cases, before_classes):
        before_counts[cls.failure_class] = (
            before_counts.get(cls.failure_class, 0) + 1
        )
        by_class_cases.setdefault(cls.failure_class, []).append(case)
    for cluster, cases_in_cluster in by_class_cases.items():
        still = 0
        for case in cases_in_cluster:
            a = auditor.audit(case.text)
            if (
                a.state is LogicalState.LOGICALLY_SUPPORTED
                and a.rule is InferenceRule.CAUSAL_CHAIN
            ):
                still += 1
        after_counts[cluster] = still
    out: list[PerClassEffect] = []
    non_target_relabel = 0
    for cluster in sorted(set(before_counts) | set(after_counts)):
        before = before_counts.get(cluster, 0)
        after = after_counts.get(cluster, 0)
        out.append(PerClassEffect(
            cluster=cluster,
            before_count=before,
            after_count=after,
            reduction=before - after,
            targeted=(cluster in PATCHED_CLUSTERS),
        ))
        # Non-target classes must not be silently relabeled:
        # their after_count should equal their before_count.
        if cluster not in PATCHED_CLUSTERS and after != before:
            non_target_relabel += abs(after - before)
    return tuple(out), non_target_relabel


def measure() -> EffectReport:
    """Build the full effect report by replaying v4.0 corpus
    under the patched auditor."""
    cases = collect_false_support_cases.__wrapped__() if hasattr(
        collect_false_support_cases, "__wrapped__"
    ) else collect_false_support_cases()  # noqa
    # We need the BEFORE case list (143 chains identified by the
    # v4.2 collection). That collection is auditor-dependent: it
    # selects chains where the *current* auditor says SUPPORTED.
    # Under the patched auditor it returns fewer. So we must
    # reconstruct the BEFORE set from the historical v4.2
    # artifact.
    v42_path = _REPO_ROOT / "artifacts" / "v4_2" / "report.json"
    v42 = json.loads(v42_path.read_text(encoding="utf-8"))
    before_chain_ids = [
        r["chain_id"] for r in v42["classifications"]
    ]
    by_id = {c.chain_id: c for c in all_chains()}
    before_cases = tuple(by_id[i] for i in before_chain_ids)
    # Wrap into FalseSupportCase shape (for classifier).
    from ..external_audit_probe.cases import FalseSupportCase
    cases = tuple(
        FalseSupportCase(
            chain_id=c.chain_id,
            domain=c.domain.value,
            text=c.text,
            ground_truth=c.ground_truth.value,
        )
        for c in before_cases
    )
    # Run the v4.2 classifier on these cases (text-only -> stable).
    records = replay_all(cases)
    before_classes = classify_all(
        records, {c.chain_id: c.text for c in cases},
    )

    false_support_before = len(cases)
    false_support_after = _current_false_support_count()
    reduction = false_support_before - false_support_after
    reduction_rate = (
        round(reduction / false_support_before, 6)
        if false_support_before else 0.0
    )

    per_class, non_target_relabel = _per_class_effect(
        before_classes, cases,
    )

    baseline = _v41_baseline()

    # Re-run F4 strategy under the patched auditor to get
    # after-metrics. F4 was the highest-recall v4.1 strategy and
    # mirrors v4.1's strongest baseline.
    f4 = run_strategy(InferenceStrategy.F4_CONTEXT_WINDOW)
    real_records = [
        r for r in f4.records
        if r.domain != "negative_control"
    ]
    valids = [
        r for r in real_records
        if r.outcome_ground_truth == "VALID"
    ]
    invalids = [
        r for r in real_records
        if r.outcome_ground_truth == "INVALID"
    ]
    tp = sum(1 for r in valids if r.outcome_verdict == "VALID")
    fp = sum(1 for r in invalids if r.outcome_verdict == "VALID")
    fn = sum(1 for r in valids if r.outcome_verdict != "VALID")
    und = sum(
        1 for r in real_records if r.outcome_verdict == "UNDECIDABLE"
    )
    f4_precision_after = (
        round(tp / (tp + fp), 6) if (tp + fp) else 1.0
    )
    f4_recall_after = (
        round(tp / (tp + fn), 6) if (tp + fn) else 1.0
    )
    f4_und_after = (
        round(und / len(real_records), 6) if real_records else 0.0
    )

    return EffectReport(
        false_support_before=false_support_before,
        false_support_after=false_support_after,
        false_support_reduction=reduction,
        reduction_rate=reduction_rate,
        external_precision_before=baseline["f4_external_precision"],
        external_precision_after=f4_precision_after,
        external_recall_before=baseline["f4_external_recall"],
        external_recall_after=f4_recall_after,
        undecidable_rate_before=
            baseline["f4_external_undecidable_rate"],
        undecidable_rate_after=f4_und_after,
        per_class=per_class,
        non_target_relabel_count=non_target_relabel,
    )


__all__ = ["EffectReport", "PerClassEffect", "measure"]
