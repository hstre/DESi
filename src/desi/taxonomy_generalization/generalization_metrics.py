"""Aufgabe 6 — seven generalization metrics.

* ``taxonomy_coverage``           — fraction of classified
  chains assigned to a canonical ``MT_*`` class (not
  ``UNKNOWN``).
* ``unknown_fraction``            — fraction assigned to
  ``UNKNOWN``.
* ``class_balance_shift``         — L1 distance between
  the normalised class distribution in v5.2 and the
  normalised v5.0 distribution. Lower = closer to the
  v5.0 prior.
* ``cross_domain_variance``       — mean variance across
  the five v5.2 domains of each canonical class's share.
* ``confidence_mean``             — mean classification
  confidence.
* ``confidence_variance``         — variance of
  classification confidence.
* ``probe_transfer_rate``         — chain-level fraction
  of chains classified into a safe-probe class where the
  v5.0 probe predicate also fires.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from .canonical import CanonicalReference
from .classifier import ClassificationResult
from .probe_transfer import (
    ProbeTransferOutcome, SAFE_PROBE_CLASSES,
    summarise_probe_transfer,
)


_UNKNOWN = "UNKNOWN"


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class GeneralizationMetrics:
    taxonomy_coverage: float
    unknown_fraction: float
    class_balance_shift: float
    cross_domain_variance: float
    confidence_mean: float
    confidence_variance: float
    probe_transfer_rate: float

    def to_dict(self) -> dict[str, object]:
        return {
            "taxonomy_coverage": self.taxonomy_coverage,
            "unknown_fraction": self.unknown_fraction,
            "class_balance_shift":
                self.class_balance_shift,
            "cross_domain_variance":
                self.cross_domain_variance,
            "confidence_mean": self.confidence_mean,
            "confidence_variance":
                self.confidence_variance,
            "probe_transfer_rate":
                self.probe_transfer_rate,
        }


def _distribution(
    results: tuple[ClassificationResult, ...],
    keys: tuple[str, ...],
) -> dict[str, float]:
    if not results:
        return {k: 0.0 for k in keys}
    counter = Counter(r.assigned_class for r in results)
    total = sum(counter.values())
    return {
        k: counter.get(k, 0) / total if total else 0.0
        for k in keys
    }


def compute_metrics(
    results: tuple[ClassificationResult, ...],
    probe_outcomes: tuple[ProbeTransferOutcome, ...],
    canonical_ref: CanonicalReference,
) -> GeneralizationMetrics:
    if not results:
        return GeneralizationMetrics(
            taxonomy_coverage=0.0, unknown_fraction=0.0,
            class_balance_shift=0.0,
            cross_domain_variance=0.0,
            confidence_mean=0.0, confidence_variance=0.0,
            probe_transfer_rate=0.0,
        )

    n = len(results)
    unknown_n = sum(
        1 for r in results if r.assigned_class == _UNKNOWN
    )
    coverage = (n - unknown_n) / n
    unknown_frac = unknown_n / n

    # Class-balance shift: normalised distribution in v5.2
    # vs the v5.0 reference distribution.
    keys = canonical_ref.class_names
    v52_dist = _distribution(results, keys)
    total_v50 = sum(c.size for c in canonical_ref.classes)
    v50_dist = {
        c.name: (c.size / total_v50 if total_v50 else 0.0)
        for c in canonical_ref.classes
    }
    shift = sum(
        abs(v52_dist[k] - v50_dist[k]) for k in keys
    )
    # L1 distance between two distributions is bounded in
    # [0, 2]. Normalise to [0, 1].
    shift_norm = shift / 2.0

    # Cross-domain variance: for each canonical class,
    # compute variance of its share across the five v5.2
    # domains; report the mean.
    domains = sorted({r.domain for r in results})
    per_domain_shares: dict[str, list[float]] = {
        k: [] for k in keys
    }
    for dom in domains:
        sub = tuple(r for r in results if r.domain == dom)
        dom_dist = _distribution(sub, keys)
        for k in keys:
            per_domain_shares[k].append(dom_dist[k])
    if len(domains) > 1:
        variances: list[float] = []
        for k in keys:
            xs = per_domain_shares[k]
            mean = sum(xs) / len(xs)
            v = sum((x - mean) ** 2 for x in xs) / len(xs)
            variances.append(v)
        cross_var = sum(variances) / len(variances)
    else:
        cross_var = 0.0

    confs = [r.confidence for r in results]
    conf_mean = sum(confs) / len(confs)
    conf_var = sum(
        (c - conf_mean) ** 2 for c in confs
    ) / len(confs)

    hit_rate, _ = summarise_probe_transfer(probe_outcomes)

    return GeneralizationMetrics(
        taxonomy_coverage=_round(coverage),
        unknown_fraction=_round(unknown_frac),
        class_balance_shift=_round(shift_norm),
        cross_domain_variance=_round(cross_var),
        confidence_mean=_round(conf_mean),
        confidence_variance=_round(conf_var),
        probe_transfer_rate=_round(hit_rate),
    )


__all__ = [
    "GeneralizationMetrics", "compute_metrics",
]
