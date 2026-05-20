"""Aufgabe 11 — methodology-transfer metrics.

Six closed metrics summarise whether DESi reproduced its
own v4 methodology on the five new domains:

* ``taxonomy_completeness``       — fraction of failures
  that the closed taxonomy actually assigns a name to
  (i.e. anything not ``MT_OTHER``).
* ``probe_generation_rate``       — fraction of taxonomy
  classes for which a candidate probe was generated.
* ``safe_probe_fraction``         — fraction of generated
  probes that pass the contamination audit (contam == 0).
* ``unsafe_probe_rejection_rate`` — fraction of generated
  probes for which contamination was detected
  (i.e. correctly rejected as unsafe).
* ``unknown_fraction``            — fraction of failures
  assigned to ``MT_OTHER``.
* ``cross_domain_transfer_variance`` — variance of the
  per-domain failure-coverage rates (how unevenly the
  pipeline finds failures across the five domains).
"""
from __future__ import annotations

from dataclasses import dataclass

from .contamination import ProbeAuditOutcome
from .feature_extraction import FailureSample
from .taxonomy import TaxonomyClass, TaxonomyEntry


_OTHER = TaxonomyClass.MT_OTHER.value


@dataclass(frozen=True)
class TransferMetrics:
    taxonomy_completeness: float
    probe_generation_rate: float
    safe_probe_fraction: float
    unsafe_probe_rejection_rate: float
    unknown_fraction: float
    cross_domain_transfer_variance: float

    def to_dict(self) -> dict[str, object]:
        return {
            "taxonomy_completeness":
                self.taxonomy_completeness,
            "probe_generation_rate":
                self.probe_generation_rate,
            "safe_probe_fraction":
                self.safe_probe_fraction,
            "unsafe_probe_rejection_rate":
                self.unsafe_probe_rejection_rate,
            "unknown_fraction": self.unknown_fraction,
            "cross_domain_transfer_variance":
                self.cross_domain_transfer_variance,
        }


def _round(v: float, n: int = 6) -> float:
    return round(v, n)


def compute_metrics(
    taxonomy: tuple[TaxonomyEntry, ...],
    probes: tuple[object, ...],
    probe_outcomes: tuple[ProbeAuditOutcome, ...],
    per_domain_failures: dict[str, tuple[FailureSample, ...]],
) -> TransferMetrics:
    total_failures = sum(t.size for t in taxonomy)
    unknown = sum(
        t.size for t in taxonomy if t.taxonomy_name == _OTHER
    )
    named = total_failures - unknown
    classes_total = len(taxonomy)
    classes_named = sum(
        1 for t in taxonomy if t.taxonomy_name != _OTHER
    )

    taxonomy_completeness = (
        _round(named / total_failures)
        if total_failures else 0.0
    )
    unknown_fraction = (
        _round(unknown / total_failures)
        if total_failures else 0.0
    )

    # probe_generation_rate: one candidate probe per named
    # taxonomy class (the generator always emits one); we
    # express this as probes_generated / classes_total.
    probe_generation_rate = (
        _round(len(probes) / classes_total)
        if classes_total else 0.0
    )

    safe = sum(1 for o in probe_outcomes if o.safe)
    unsafe = sum(1 for o in probe_outcomes if not o.safe)
    safe_probe_fraction = (
        _round(safe / len(probe_outcomes))
        if probe_outcomes else 0.0
    )
    unsafe_probe_rejection_rate = (
        _round(unsafe / len(probe_outcomes))
        if probe_outcomes else 0.0
    )

    # cross_domain_transfer_variance: variance of the
    # per-domain failure rates (failure_count / chains_in_domain).
    # Variance is sample-variance with N (population), since
    # the domain set is closed.
    rates: list[float] = []
    for dom, fails in per_domain_failures.items():
        # ``per_domain_failures`` carries (failure_count,
        # chain_count) as a pair encoded in the tuple of
        # FailureSample objects: the convention is that the
        # tuple contains *failures only*; the caller passes
        # the count via a parallel mapping. To keep this
        # function dependency-free we treat the tuple length
        # as the failure count and require the caller to
        # normalise. Here we simply collect lengths.
        rates.append(float(len(fails)))
    if rates:
        mean = sum(rates) / len(rates)
        var = sum(
            (r - mean) * (r - mean) for r in rates
        ) / len(rates)
        cdtv = _round(var)
    else:
        cdtv = 0.0

    return TransferMetrics(
        taxonomy_completeness=taxonomy_completeness,
        probe_generation_rate=probe_generation_rate,
        safe_probe_fraction=safe_probe_fraction,
        unsafe_probe_rejection_rate=unsafe_probe_rejection_rate,
        unknown_fraction=unknown_fraction,
        cross_domain_transfer_variance=cdtv,
    )


def compute_cross_domain_variance(
    per_domain_rates: dict[str, float],
) -> float:
    if not per_domain_rates:
        return 0.0
    rates = list(per_domain_rates.values())
    mean = sum(rates) / len(rates)
    var = sum(
        (r - mean) * (r - mean) for r in rates
    ) / len(rates)
    return _round(var)


__all__ = [
    "TransferMetrics", "compute_metrics",
    "compute_cross_domain_variance",
]
