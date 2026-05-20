"""Aufgabe 10 — v5.4 split-evaluation report.

The recommendation gate is closed:

* ``TAXONOMY_AND_PROBES_GENERALIZE`` — every taxonomy
  threshold passes AND every probe threshold passes AND
  ``nc_accuracy >= 0.95``.
* ``TAXONOMY_GENERALIZES_PROBES_FAIL`` — every taxonomy
  threshold passes AND at least one probe threshold
  fails.
* ``TAXONOMY_FAILS`` — at least one taxonomy threshold
  fails.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import json

from .enums import RawRecommendation
from .independence_audit import (
    IndependenceAudit, audit_independence,
)
from .negative_controls import (
    all_raw_ncs, classification_accuracy,
)
from .probe_eval import ProbeMetrics, evaluate_probes
from .raw_corpus_loader import (
    load_raw_chains, raw_chain_count,
)
from .taxonomy_eval import (
    TaxonomyMetrics, evaluate_taxonomy,
)


# Gate thresholds — taxonomy
MIN_TAXONOMY_COVERAGE              = 0.90
MAX_TAXONOMY_UNKNOWN_FRACTION      = 0.10
MIN_TAXONOMY_CONFIDENCE_MEAN       = 0.80
MAX_TAXONOMY_CROSS_DOMAIN_VARIANCE = 0.15
MIN_DOMINANT_RANK_STABILITY        = 0.80
MAX_DOMINANT_SIZE_SHIFT            = 0.20
# Gate thresholds — probes
MIN_PROBE_HIT_RATE                 = 0.80
MAX_PROBE_FALSE_ACTIVATION         = 0
MAX_PROBE_DOMAIN_VARIANCE          = 0.15
# Gate thresholds — NCs
MIN_NC_ACCURACY                    = 0.95


@dataclass(frozen=True)
class V54Report:
    corpus_size: int
    taxonomy_metrics: TaxonomyMetrics
    probe_metrics: ProbeMetrics
    independence: IndependenceAudit
    taxonomy_passes: bool
    probes_pass: bool
    nc_count: int
    nc_accuracy: float
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "corpus_size": self.corpus_size,
            "taxonomy_metrics":
                self.taxonomy_metrics.to_dict(),
            "probe_metrics": self.probe_metrics.to_dict(),
            "independence": self.independence.to_dict(),
            "taxonomy_passes": self.taxonomy_passes,
            "probes_pass": self.probes_pass,
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


def _check_taxonomy(
    m: TaxonomyMetrics,
) -> tuple[bool, list[str]]:
    checks = (
        (
            m.taxonomy_coverage >= MIN_TAXONOMY_COVERAGE,
            f"taxonomy_coverage {m.taxonomy_coverage} >= "
            f"{MIN_TAXONOMY_COVERAGE}",
        ),
        (
            m.taxonomy_unknown_fraction
            <= MAX_TAXONOMY_UNKNOWN_FRACTION,
            f"taxonomy_unknown_fraction "
            f"{m.taxonomy_unknown_fraction} <= "
            f"{MAX_TAXONOMY_UNKNOWN_FRACTION}",
        ),
        (
            m.taxonomy_confidence_mean
            >= MIN_TAXONOMY_CONFIDENCE_MEAN,
            f"taxonomy_confidence_mean "
            f"{m.taxonomy_confidence_mean} >= "
            f"{MIN_TAXONOMY_CONFIDENCE_MEAN}",
        ),
        (
            m.taxonomy_cross_domain_variance
            <= MAX_TAXONOMY_CROSS_DOMAIN_VARIANCE,
            f"taxonomy_cross_domain_variance "
            f"{m.taxonomy_cross_domain_variance} <= "
            f"{MAX_TAXONOMY_CROSS_DOMAIN_VARIANCE}",
        ),
        (
            m.dominant_cluster_rank_stability
            >= MIN_DOMINANT_RANK_STABILITY,
            f"dominant_cluster_rank_stability "
            f"{m.dominant_cluster_rank_stability} >= "
            f"{MIN_DOMINANT_RANK_STABILITY}",
        ),
        (
            m.dominant_cluster_size_shift
            <= MAX_DOMINANT_SIZE_SHIFT,
            f"dominant_cluster_size_shift "
            f"{m.dominant_cluster_size_shift} <= "
            f"{MAX_DOMINANT_SIZE_SHIFT}",
        ),
    )
    reasons = []
    all_ok = True
    for ok, msg in checks:
        if ok:
            reasons.append(f"PASS[taxonomy_only]: {msg}")
        else:
            reasons.append(f"FAIL[taxonomy_only]: {msg}")
            all_ok = False
    return all_ok, reasons


def _check_probes(
    m: ProbeMetrics,
) -> tuple[bool, list[str]]:
    checks = (
        (
            m.probe_hit_rate >= MIN_PROBE_HIT_RATE,
            f"probe_hit_rate {m.probe_hit_rate} >= "
            f"{MIN_PROBE_HIT_RATE}",
        ),
        (
            m.probe_false_activation
            <= MAX_PROBE_FALSE_ACTIVATION,
            f"probe_false_activation "
            f"{m.probe_false_activation} <= "
            f"{MAX_PROBE_FALSE_ACTIVATION}",
        ),
        (
            m.probe_domain_variance
            <= MAX_PROBE_DOMAIN_VARIANCE,
            f"probe_domain_variance "
            f"{m.probe_domain_variance} <= "
            f"{MAX_PROBE_DOMAIN_VARIANCE}",
        ),
    )
    reasons = []
    all_ok = True
    for ok, msg in checks:
        if ok:
            reasons.append(f"PASS[probe_only]: {msg}")
        else:
            reasons.append(f"FAIL[probe_only]: {msg}")
            all_ok = False
    return all_ok, reasons


def _decide(
    tax_pass: bool, probe_pass: bool, nc_pass: bool,
) -> str:
    if not tax_pass:
        return RawRecommendation.TAXONOMY_FAILS.value
    if tax_pass and probe_pass and nc_pass:
        return RawRecommendation.BOTH_GENERALIZE.value
    return RawRecommendation.TAXONOMY_ONLY.value


def build_report() -> V54Report:
    chains = load_raw_chains()
    tax_metrics, tax_results = evaluate_taxonomy(chains)
    probe_metrics = evaluate_probes(chains, tax_results)
    tax_pass, tax_reasons = _check_taxonomy(tax_metrics)
    probe_pass, probe_reasons = _check_probes(probe_metrics)
    nc_acc = classification_accuracy()
    nc_count = len(all_raw_ncs())
    nc_pass = nc_acc >= MIN_NC_ACCURACY
    nc_reason = (
        f"{'PASS' if nc_pass else 'FAIL'}: nc_accuracy "
        f"{nc_acc} >= {MIN_NC_ACCURACY}"
    )
    independence = audit_independence(
        tax_metrics, probe_metrics,
        taxonomy_thresholds_passed=tax_pass,
        probe_thresholds_passed=probe_pass,
    )
    verdict = _decide(tax_pass, probe_pass, nc_pass)
    rationale = tuple(tax_reasons + probe_reasons + [nc_reason])
    return V54Report(
        corpus_size=len(chains),
        taxonomy_metrics=tax_metrics,
        probe_metrics=probe_metrics,
        independence=independence,
        taxonomy_passes=tax_pass,
        probes_pass=probe_pass,
        nc_count=nc_count,
        nc_accuracy=nc_acc,
        recommendation=verdict,
        rationale=rationale,
    )


def build_split_eval_artifact() -> dict[str, object]:
    chains = load_raw_chains()
    tax_metrics, tax_results = evaluate_taxonomy(chains)
    probe_metrics = evaluate_probes(chains, tax_results)
    classification_dist = Counter(
        r.assigned_class for r in tax_results
    )
    return {
        "corpus_size": len(chains),
        "taxonomy_only": tax_metrics.to_dict(),
        "probe_only": probe_metrics.to_dict(),
        "classification_distribution": dict(
            classification_dist,
        ),
    }


__all__ = [
    "MAX_DOMINANT_SIZE_SHIFT",
    "MAX_PROBE_DOMAIN_VARIANCE",
    "MAX_PROBE_FALSE_ACTIVATION",
    "MAX_TAXONOMY_CROSS_DOMAIN_VARIANCE",
    "MAX_TAXONOMY_UNKNOWN_FRACTION",
    "MIN_DOMINANT_RANK_STABILITY",
    "MIN_NC_ACCURACY",
    "MIN_PROBE_HIT_RATE",
    "MIN_TAXONOMY_CONFIDENCE_MEAN",
    "MIN_TAXONOMY_COVERAGE",
    "V54Report",
    "build_report",
    "build_split_eval_artifact",
]
