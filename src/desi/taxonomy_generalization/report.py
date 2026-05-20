"""Aufgabe 11 — v5.2 report and recommendation gate.

Closed three-value cascade:

* ``TAXONOMY_GENERALIZES``           — all thresholds pass,
  ``nc_accuracy >= 0.95`` and
  ``safe_probe_false_activation == 0``.
* ``TAXONOMY_PARTIAL_GENERALIZATION`` —
  ``taxonomy_coverage >= 0.75`` but at least one other
  threshold fails.
* ``TAXONOMY_OVERFIT``               —
  ``taxonomy_coverage < 0.75`` or
  ``unknown_fraction > 0.10`` or
  ``safe_probe_false_activation > 0``.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import json

from .canonical import (
    CanonicalReference, load_canonical_reference,
)
from .classifier import (
    ClassificationResult, classify_all,
)
from .corpus import GeneralizationChain, all_chains
from .enums import GeneralizationRecommendation
from .generalization_metrics import (
    GeneralizationMetrics, compute_metrics,
)
from .negative_controls import (
    all_generalization_ncs, classification_accuracy,
)
from .novelty_audit import (
    NoveltyAuditEntry, audit_unknown_chains,
    true_novelty_fraction,
)
from .probe_transfer import (
    ProbeTransferOutcome, SAFE_PROBE_CLASSES,
    audit_probe_transfer, summarise_probe_transfer,
)


# ---------------------------------------------------------------------------
# Gate thresholds (closed)
# ---------------------------------------------------------------------------


MIN_TAXONOMY_COVERAGE     = 0.90
MAX_UNKNOWN_FRACTION      = 0.10
MAX_CROSS_DOMAIN_VARIANCE = 0.15
MIN_PROBE_TRANSFER_RATE   = 0.80
MIN_CONFIDENCE_MEAN       = 0.80
MIN_DOMINANT_RANK_STABILITY = 0.80
MAX_DOMINANT_SIZE_SHIFT   = 0.20
MAX_TRUE_NOVELTY_FRACTION = 0.10
MIN_NC_ACCURACY           = 0.95
PARTIAL_FLOOR_COVERAGE    = 0.75


DOMINANT_CLUSTER_NAME = "MT_AMBIGUITY_DECISIVENESS"


# ---------------------------------------------------------------------------
# Dominant-cluster audit (Aufgabe 7)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DominantClusterAudit:
    canonical_name: str
    v50_share: float
    v52_share: float
    rank_generalization_stability: float
    size_shift: float

    def to_dict(self) -> dict[str, object]:
        return {
            "canonical_name": self.canonical_name,
            "v50_share": self.v50_share,
            "v52_share": self.v52_share,
            "rank_generalization_stability":
                self.rank_generalization_stability,
            "size_shift": self.size_shift,
        }


def _dominant_audit(
    results: tuple[ClassificationResult, ...],
    ref: CanonicalReference,
) -> DominantClusterAudit:
    """Dominant-cluster audit normalised against the
    matching label slice. The v5.0 dominant cluster
    (MT_AMBIGUITY_DECISIVENESS) fires only on chains whose
    ground truth is AMBIGUOUS — both v5.0 and v5.2
    produced their dominant class from this slice. We
    measure dominance over the AMBIGUOUS slice for both
    corpora so the comparison is apples-to-apples."""
    counts = Counter(r.assigned_class for r in results)
    ambiguous_results = tuple(
        r for r in results
        if r.ground_truth == "AMBIGUOUS"
    )
    v52_ambig_total = len(ambiguous_results)
    v52_dom_in_ambig = sum(
        1 for r in ambiguous_results
        if r.assigned_class == DOMINANT_CLUSTER_NAME
    )
    v52_share = (
        v52_dom_in_ambig / v52_ambig_total
        if v52_ambig_total else 0.0
    )
    # v5.0 reference: MT_AMBIGUITY_DECISIVENESS members
    # are by construction drawn from the AMBIGUOUS slice
    # (the cascade rule requires expected_ambiguous=1), so
    # the v5.0 within-slice share is 1.0 by definition.
    # We instead compare share-of-failures (the natural
    # v5.0 denominator) — taxonomy.json reports both the
    # 195 dominant size and the total 346 failures.
    total_failures = sum(c.size for c in ref.classes)
    v50_share = (
        next(
            (c.size for c in ref.classes
             if c.name == DOMINANT_CLUSTER_NAME),
            0,
        ) / total_failures if total_failures else 0.0
    )
    # Both denominators are "label-restricted classified
    # chains for the dominant cluster's eligible slice".
    # Re-express the v5.0 anchor as the same within-slice
    # share v5.2 uses: 1.0 (all v5.0 dominant samples
    # came from AMBIGUOUS chains). size_shift is the
    # absolute difference between the two within-slice
    # rates. This is the apples-to-apples comparison.
    v50_within_slice = 1.0  # by construction
    size_shift = abs(v50_within_slice - v52_share)
    # Rank stability: per-domain rank of MT_AMBIGUITY in
    # v5.2; fraction of domains where it ranks #1.
    domains = sorted({r.domain for r in results})
    ranks_ok = 0
    for dom in domains:
        sub = tuple(
            r for r in results if r.domain == dom
        )
        c = Counter(r.assigned_class for r in sub)
        ordered = sorted(
            c.items(),
            key=lambda kv: (-kv[1], kv[0]),
        )
        if (
            ordered
            and ordered[0][0] == DOMINANT_CLUSTER_NAME
        ):
            ranks_ok += 1
    rank_stab = (
        round(ranks_ok / len(domains), 6)
        if domains else 0.0
    )
    return DominantClusterAudit(
        canonical_name=DOMINANT_CLUSTER_NAME,
        v50_share=round(v50_share, 6),
        v52_share=round(v52_share, 6),
        rank_generalization_stability=rank_stab,
        size_shift=round(size_shift, 6),
    )


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class V52Report:
    corpus_size: int
    domain_chain_counts: dict[str, int]
    per_label_counts: dict[str, int]
    classification_distribution: dict[str, int]
    metrics: GeneralizationMetrics
    dominant_audit: DominantClusterAudit
    probe_outcomes: tuple[ProbeTransferOutcome, ...]
    safe_probe_hit_rate: float
    safe_probe_false_activation: int
    novelty_entries: tuple[NoveltyAuditEntry, ...]
    true_novelty_fraction: float
    nc_count: int
    nc_accuracy: float
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "corpus_size": self.corpus_size,
            "domain_chain_counts":
                dict(self.domain_chain_counts),
            "per_label_counts":
                dict(self.per_label_counts),
            "classification_distribution":
                dict(self.classification_distribution),
            "metrics": self.metrics.to_dict(),
            "dominant_audit":
                self.dominant_audit.to_dict(),
            "probe_outcomes":
                [o.to_dict() for o in self.probe_outcomes],
            "safe_probe_hit_rate":
                self.safe_probe_hit_rate,
            "safe_probe_false_activation":
                self.safe_probe_false_activation,
            "novelty_summary": {
                "count": len(self.novelty_entries),
                "true_novelty_fraction":
                    self.true_novelty_fraction,
                "kinds": dict(Counter(
                    e.novelty_kind
                    for e in self.novelty_entries
                )),
            },
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
    *, metrics: GeneralizationMetrics,
    dominant: DominantClusterAudit,
    safe_probe_false: int, nc_accuracy: float,
    novelty_frac: float,
) -> tuple[str, tuple[str, ...]]:
    checks = (
        (
            metrics.taxonomy_coverage
            >= MIN_TAXONOMY_COVERAGE,
            f"taxonomy_coverage "
            f"{metrics.taxonomy_coverage} >= "
            f"{MIN_TAXONOMY_COVERAGE}",
        ),
        (
            metrics.unknown_fraction
            <= MAX_UNKNOWN_FRACTION,
            f"unknown_fraction "
            f"{metrics.unknown_fraction} <= "
            f"{MAX_UNKNOWN_FRACTION}",
        ),
        (
            metrics.cross_domain_variance
            <= MAX_CROSS_DOMAIN_VARIANCE,
            f"cross_domain_variance "
            f"{metrics.cross_domain_variance} <= "
            f"{MAX_CROSS_DOMAIN_VARIANCE}",
        ),
        (
            metrics.probe_transfer_rate
            >= MIN_PROBE_TRANSFER_RATE,
            f"probe_transfer_rate "
            f"{metrics.probe_transfer_rate} >= "
            f"{MIN_PROBE_TRANSFER_RATE}",
        ),
        (
            metrics.confidence_mean
            >= MIN_CONFIDENCE_MEAN,
            f"confidence_mean "
            f"{metrics.confidence_mean} >= "
            f"{MIN_CONFIDENCE_MEAN}",
        ),
        (
            dominant.rank_generalization_stability
            >= MIN_DOMINANT_RANK_STABILITY,
            f"dominant rank_generalization_stability "
            f"{dominant.rank_generalization_stability} "
            f">= {MIN_DOMINANT_RANK_STABILITY}",
        ),
        (
            dominant.size_shift
            <= MAX_DOMINANT_SIZE_SHIFT,
            f"dominant size_shift "
            f"{dominant.size_shift} <= "
            f"{MAX_DOMINANT_SIZE_SHIFT}",
        ),
        (
            novelty_frac <= MAX_TRUE_NOVELTY_FRACTION,
            f"true_novelty_fraction {novelty_frac} <= "
            f"{MAX_TRUE_NOVELTY_FRACTION}",
        ),
        (
            nc_accuracy >= MIN_NC_ACCURACY,
            f"nc_accuracy {nc_accuracy} >= "
            f"{MIN_NC_ACCURACY}",
        ),
        (
            safe_probe_false == 0,
            f"safe_probe_false_activation "
            f"{safe_probe_false} == 0",
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
    # OVERFIT triggers (any of them)
    if (
        metrics.taxonomy_coverage < PARTIAL_FLOOR_COVERAGE
        or metrics.unknown_fraction > MAX_UNKNOWN_FRACTION
        or safe_probe_false > 0
    ):
        return (
            GeneralizationRecommendation.OVERFIT.value,
            tuple(reasons),
        )
    if passed == len(checks):
        return (
            GeneralizationRecommendation.GENERALIZES.value,
            tuple(reasons),
        )
    return (
        GeneralizationRecommendation.PARTIAL.value,
        tuple(reasons),
    )


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------


def build_report() -> V52Report:
    ref = load_canonical_reference()
    chains = all_chains()
    results = classify_all(chains, ref)
    probe_outcomes = audit_probe_transfer(chains, results)
    safe_hit, safe_false = summarise_probe_transfer(
        probe_outcomes,
    )
    metrics = compute_metrics(
        results, probe_outcomes, ref,
    )
    dominant = _dominant_audit(results, ref)
    novelty = audit_unknown_chains(results, ref)
    novelty_frac = true_novelty_fraction(results, novelty)
    nc_acc = classification_accuracy()
    nc_count = len(all_generalization_ncs())
    verdict, rationale = _decide(
        metrics=metrics, dominant=dominant,
        safe_probe_false=safe_false, nc_accuracy=nc_acc,
        novelty_frac=novelty_frac,
    )
    return V52Report(
        corpus_size=len(chains),
        domain_chain_counts=dict(
            Counter(c.domain for c in chains)
        ),
        per_label_counts=dict(
            Counter(c.ground_truth for c in chains)
        ),
        classification_distribution=dict(
            Counter(r.assigned_class for r in results)
        ),
        metrics=metrics,
        dominant_audit=dominant,
        probe_outcomes=probe_outcomes,
        safe_probe_hit_rate=safe_hit,
        safe_probe_false_activation=safe_false,
        novelty_entries=novelty,
        true_novelty_fraction=novelty_frac,
        nc_count=nc_count,
        nc_accuracy=nc_acc,
        recommendation=verdict,
        rationale=rationale,
    )


def build_classification_matrix_artifact(
) -> dict[str, object]:
    ref = load_canonical_reference()
    chains = all_chains()
    results = classify_all(chains, ref)
    return {
        "canonical_classes":
            list(ref.class_names),
        "results": [r.to_dict() for r in results],
    }


__all__ = [
    "DOMINANT_CLUSTER_NAME",
    "DominantClusterAudit",
    "MAX_CROSS_DOMAIN_VARIANCE",
    "MAX_DOMINANT_SIZE_SHIFT",
    "MAX_TRUE_NOVELTY_FRACTION",
    "MAX_UNKNOWN_FRACTION",
    "MIN_CONFIDENCE_MEAN",
    "MIN_DOMINANT_RANK_STABILITY",
    "MIN_NC_ACCURACY",
    "MIN_PROBE_TRANSFER_RATE",
    "MIN_TAXONOMY_COVERAGE",
    "PARTIAL_FLOOR_COVERAGE",
    "V52Report",
    "build_classification_matrix_artifact",
    "build_report",
]
