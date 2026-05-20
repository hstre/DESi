"""Aufgabe 6 — taxonomy-only metrics on the RAW corpus.

The v5.2 ``classify_all`` cascade and centroid-based
confidence are imported unchanged and applied to every
RAW chain. This channel never touches the safe probes;
every number it produces declares
``RawEvalChannel.TAXONOMY_ONLY``.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from ..taxonomy_generalization.canonical import (
    CanonicalReference, load_canonical_reference,
)
from ..taxonomy_generalization.classifier import (
    ClassificationResult, classify_all,
)
from ..taxonomy_generalization.corpus import (
    GeneralizationChain,
)
from .enums import RawEvalChannel


DOMINANT_CLUSTER = "MT_AMBIGUITY_DECISIVENESS"


@dataclass(frozen=True)
class TaxonomyMetrics:
    channel: str  # always taxonomy_only
    taxonomy_coverage: float
    taxonomy_unknown_fraction: float
    taxonomy_confidence_mean: float
    taxonomy_confidence_variance: float
    taxonomy_cross_domain_variance: float
    dominant_cluster_rank_stability: float
    dominant_cluster_size_shift: float

    def to_dict(self) -> dict[str, object]:
        return {
            "channel": self.channel,
            "taxonomy_coverage": self.taxonomy_coverage,
            "taxonomy_unknown_fraction":
                self.taxonomy_unknown_fraction,
            "taxonomy_confidence_mean":
                self.taxonomy_confidence_mean,
            "taxonomy_confidence_variance":
                self.taxonomy_confidence_variance,
            "taxonomy_cross_domain_variance":
                self.taxonomy_cross_domain_variance,
            "dominant_cluster_rank_stability":
                self.dominant_cluster_rank_stability,
            "dominant_cluster_size_shift":
                self.dominant_cluster_size_shift,
        }


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _variance(xs: list[float]) -> float:
    if not xs:
        return 0.0
    mean = sum(xs) / len(xs)
    return sum((x - mean) ** 2 for x in xs) / len(xs)


def evaluate_taxonomy(
    chains: tuple[GeneralizationChain, ...],
    ref: CanonicalReference | None = None,
) -> tuple[TaxonomyMetrics, tuple[ClassificationResult, ...]]:
    r = ref if ref is not None else load_canonical_reference()
    results = classify_all(chains, r)
    n = len(results)
    if n == 0:
        empty = TaxonomyMetrics(
            channel=RawEvalChannel.TAXONOMY_ONLY.value,
            taxonomy_coverage=0.0,
            taxonomy_unknown_fraction=0.0,
            taxonomy_confidence_mean=0.0,
            taxonomy_confidence_variance=0.0,
            taxonomy_cross_domain_variance=0.0,
            dominant_cluster_rank_stability=0.0,
            dominant_cluster_size_shift=0.0,
        )
        return empty, ()
    unknown = sum(
        1 for r in results if r.assigned_class == "UNKNOWN"
    )
    coverage = (n - unknown) / n
    unk_frac = unknown / n
    confs = [r.confidence for r in results]
    conf_mean = sum(confs) / n
    conf_var = sum(
        (c - conf_mean) ** 2 for c in confs
    ) / n

    # Cross-domain variance of canonical-class shares.
    canonical_names = tuple(c.name for c in r.classes)
    domains = sorted({r.domain for r in results})
    per_class_shares: dict[str, list[float]] = {
        name: [] for name in canonical_names
    }
    for dom in domains:
        sub = [r for r in results if r.domain == dom]
        if not sub:
            continue
        ctr = Counter(r.assigned_class for r in sub)
        denom = len(sub)
        for name in canonical_names:
            per_class_shares[name].append(
                ctr.get(name, 0) / denom,
            )
    if len(domains) > 1:
        cross_var = sum(
            _variance(per_class_shares[n])
            for n in canonical_names
        ) / len(canonical_names)
    else:
        cross_var = 0.0

    # Dominant-cluster audit (label-restricted slice).
    ambiguous = [
        r for r in results
        if r.ground_truth == "AMBIGUOUS"
    ]
    if ambiguous:
        v54_dom_share = sum(
            1 for r in ambiguous
            if r.assigned_class == DOMINANT_CLUSTER
        ) / len(ambiguous)
    else:
        v54_dom_share = 0.0
    v50_dom_share = 1.0  # by construction (v5.0 dominant
                         # is cascade-gated on AMBIGUOUS).
    dom_shift = abs(v50_dom_share - v54_dom_share)
    ranks_ok = 0
    for dom in domains:
        sub = [r for r in results if r.domain == dom]
        if not sub:
            continue
        ctr = Counter(r.assigned_class for r in sub)
        ordered = sorted(
            ctr.items(), key=lambda kv: (-kv[1], kv[0]),
        )
        if (
            ordered and ordered[0][0] == DOMINANT_CLUSTER
        ):
            ranks_ok += 1
    rank_stab = (
        ranks_ok / len(domains) if domains else 0.0
    )

    metrics = TaxonomyMetrics(
        channel=RawEvalChannel.TAXONOMY_ONLY.value,
        taxonomy_coverage=_round(coverage),
        taxonomy_unknown_fraction=_round(unk_frac),
        taxonomy_confidence_mean=_round(conf_mean),
        taxonomy_confidence_variance=_round(conf_var),
        taxonomy_cross_domain_variance=_round(cross_var),
        dominant_cluster_rank_stability=_round(rank_stab),
        dominant_cluster_size_shift=_round(dom_shift),
    )
    return metrics, results


__all__ = [
    "DOMINANT_CLUSTER", "TaxonomyMetrics",
    "evaluate_taxonomy",
]
