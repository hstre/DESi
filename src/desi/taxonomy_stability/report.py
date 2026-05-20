"""Aufgabe 10 — v5.1 stability report and recommendation
gate.

Assembles the canonical baseline, perturbation runs,
cluster mapping matrix, stability metrics, dominant-cluster
audit, novel-cluster fraction, and NC accuracy into a
single ``V51Report``. The recommendation is decided by a
closed cascade:

* ``TAXONOMY_STABLE`` — all metric thresholds pass and
  ``nc_accuracy >= 0.95``.
* ``TAXONOMY_PARTIALLY_STABLE`` —
  ``cluster_survival_rate >= 0.70`` but at least one
  threshold fails.
* ``TAXONOMY_UNSTABLE`` —
  ``cluster_survival_rate < 0.70`` or
  ``novel_cluster_fraction > 0.10``.

v5.1 is read-only; the recommendation is purely advisory.
"""
from __future__ import annotations

from dataclasses import dataclass
import json

from .baseline import (
    CanonicalBaseline, load_canonical_baseline,
)
from .cluster_mapper import (
    RunMapping, build_cluster_mapping_matrix,
    map_run_to_canonical,
)
from .enums import StabilityRecommendation
from .negative_controls import (
    all_stability_ncs, classification_accuracy,
)
from .perturbations import (
    PerturbationRun, all_perturbation_runs,
)
from .stability_metrics import (
    RunCharacterisation, StabilityMetrics,
    compute_stability,
)


# ---------------------------------------------------------------------------
# Gate thresholds (closed)
# ---------------------------------------------------------------------------


MIN_SURVIVAL_RATE                = 0.85
MAX_SPLIT_RATE                   = 0.15
MAX_MERGE_RATE                   = 0.15
MIN_LABEL_OVERLAP                = 0.85
MIN_CROSS_RUN_AGREEMENT          = 0.85
MIN_DOMINANT_RANK_STABILITY      = 0.80
MAX_DOMINANT_SIZE_VARIANCE       = 0.15
MAX_NOVEL_CLUSTER_FRACTION       = 0.10
MIN_NC_ACCURACY                  = 0.95
PARTIAL_FLOOR_SURVIVAL           = 0.70


DOMINANT_CLUSTER_NAME = "MT_AMBIGUITY_DECISIVENESS"


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class V51Report:
    baseline_chain_count: int
    baseline_failure_count: int
    baseline_cluster_count: int
    perturbation_count: int
    runs: tuple[PerturbationRun, ...]
    run_chars: tuple[RunCharacterisation, ...]
    mappings: tuple[RunMapping, ...]
    metrics: StabilityMetrics
    nc_count: int
    nc_accuracy: float
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "baseline_chain_count":
                self.baseline_chain_count,
            "baseline_failure_count":
                self.baseline_failure_count,
            "baseline_cluster_count":
                self.baseline_cluster_count,
            "perturbation_count":
                self.perturbation_count,
            "runs": [r.to_dict() for r in self.runs],
            "run_chars":
                [c.to_dict() for c in self.run_chars],
            "mappings":
                [m.to_dict() for m in self.mappings],
            "metrics": self.metrics.to_dict(),
            "nc_count": self.nc_count,
            "nc_accuracy": self.nc_accuracy,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


# ---------------------------------------------------------------------------
# Decision gate
# ---------------------------------------------------------------------------


def _decide(
    *, metrics: StabilityMetrics, nc_accuracy: float,
) -> tuple[str, tuple[str, ...]]:
    checks = (
        (
            metrics.cluster_survival_rate
            >= MIN_SURVIVAL_RATE,
            f"cluster_survival_rate "
            f"{metrics.cluster_survival_rate} >= "
            f"{MIN_SURVIVAL_RATE}",
        ),
        (
            metrics.cluster_split_rate
            <= MAX_SPLIT_RATE,
            f"cluster_split_rate "
            f"{metrics.cluster_split_rate} <= "
            f"{MAX_SPLIT_RATE}",
        ),
        (
            metrics.cluster_merge_rate
            <= MAX_MERGE_RATE,
            f"cluster_merge_rate "
            f"{metrics.cluster_merge_rate} <= "
            f"{MAX_MERGE_RATE}",
        ),
        (
            metrics.label_overlap_score
            >= MIN_LABEL_OVERLAP,
            f"label_overlap_score "
            f"{metrics.label_overlap_score} >= "
            f"{MIN_LABEL_OVERLAP}",
        ),
        (
            metrics.cross_run_agreement
            >= MIN_CROSS_RUN_AGREEMENT,
            f"cross_run_agreement "
            f"{metrics.cross_run_agreement} >= "
            f"{MIN_CROSS_RUN_AGREEMENT}",
        ),
        (
            metrics.dominant_cluster_rank_stability
            >= MIN_DOMINANT_RANK_STABILITY,
            f"dominant_cluster_rank_stability "
            f"{metrics.dominant_cluster_rank_stability} "
            f">= {MIN_DOMINANT_RANK_STABILITY}",
        ),
        (
            metrics.dominant_cluster_size_variance
            <= MAX_DOMINANT_SIZE_VARIANCE,
            f"dominant_cluster_size_variance "
            f"{metrics.dominant_cluster_size_variance} "
            f"<= {MAX_DOMINANT_SIZE_VARIANCE}",
        ),
        (
            metrics.novel_cluster_fraction
            <= MAX_NOVEL_CLUSTER_FRACTION,
            f"novel_cluster_fraction "
            f"{metrics.novel_cluster_fraction} <= "
            f"{MAX_NOVEL_CLUSTER_FRACTION}",
        ),
        (
            nc_accuracy >= MIN_NC_ACCURACY,
            f"nc_accuracy {nc_accuracy} >= "
            f"{MIN_NC_ACCURACY}",
        ),
    )
    reasons: list[str] = []
    passed = 0
    for ok, msg in checks:
        if ok:
            passed += 1
            reasons.append(f"PASS: {msg}")
        else:
            reasons.append(f"FAIL: {msg}")
    # Hard-unstable triggers
    if (
        metrics.cluster_survival_rate < PARTIAL_FLOOR_SURVIVAL
        or metrics.novel_cluster_fraction
        > MAX_NOVEL_CLUSTER_FRACTION
    ):
        return (
            StabilityRecommendation.UNSTABLE.value,
            tuple(reasons),
        )
    if passed == len(checks):
        return (
            StabilityRecommendation.STABLE.value,
            tuple(reasons),
        )
    return (
        StabilityRecommendation.PARTIALLY_STABLE.value,
        tuple(reasons),
    )


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


def build_report() -> V51Report:
    baseline = load_canonical_baseline()
    runs = all_perturbation_runs()
    mappings = tuple(
        map_run_to_canonical(r, baseline) for r in runs
    )
    metrics, chars = compute_stability(
        runs, baseline,
        dominant_name=DOMINANT_CLUSTER_NAME,
    )
    nc_count = len(all_stability_ncs())
    nc_acc = classification_accuracy()
    verdict, rationale = _decide(
        metrics=metrics, nc_accuracy=nc_acc,
    )
    return V51Report(
        baseline_chain_count=baseline.chain_count,
        baseline_failure_count=baseline.failure_count,
        baseline_cluster_count=baseline.cluster_count,
        perturbation_count=len(runs),
        runs=runs,
        run_chars=chars,
        mappings=mappings,
        metrics=metrics,
        nc_count=nc_count,
        nc_accuracy=nc_acc,
        recommendation=verdict,
        rationale=rationale,
    )


def build_cluster_mapping_matrix_artifact(
) -> dict[str, object]:
    baseline = load_canonical_baseline()
    runs = all_perturbation_runs()
    return build_cluster_mapping_matrix(runs, baseline)


__all__ = [
    "DOMINANT_CLUSTER_NAME",
    "MAX_DOMINANT_SIZE_VARIANCE",
    "MAX_MERGE_RATE", "MAX_NOVEL_CLUSTER_FRACTION",
    "MAX_SPLIT_RATE", "MIN_CROSS_RUN_AGREEMENT",
    "MIN_DOMINANT_RANK_STABILITY", "MIN_LABEL_OVERLAP",
    "MIN_NC_ACCURACY", "MIN_SURVIVAL_RATE",
    "PARTIAL_FLOOR_SURVIVAL", "V51Report", "build_report",
    "build_cluster_mapping_matrix_artifact",
]
