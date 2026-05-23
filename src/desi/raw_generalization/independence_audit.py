"""Aufgabe 8 — independence audit.

Two questions:

* ``taxonomy_probe_correlation`` — does taxonomy
  performance co-vary with probe performance per cluster?
  Reported as the Pearson-style correlation between the
  per-cluster classified-count (taxonomy strength) and
  the per-cluster probe-hit rate (probe strength).
* ``taxonomy_survives_probe_failure`` — boolean: do the
  six taxonomy thresholds still pass when the probes are
  failing? The directive requires this to be ``True`` so
  that the taxonomy claim and the probe claim are
  evaluated independently.
"""
from __future__ import annotations

from dataclasses import dataclass

from .probe_eval import ProbeMetrics
from .taxonomy_eval import TaxonomyMetrics


@dataclass(frozen=True)
class IndependenceAudit:
    taxonomy_probe_correlation: float
    taxonomy_survives_probe_failure: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "taxonomy_probe_correlation":
                self.taxonomy_probe_correlation,
            "taxonomy_survives_probe_failure":
                self.taxonomy_survives_probe_failure,
        }


def _pearson(
    xs: list[float], ys: list[float],
) -> float:
    n = len(xs)
    if n == 0 or len(ys) != n:
        return 0.0
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    num = sum(
        (x - mean_x) * (y - mean_y)
        for x, y in zip(xs, ys)
    )
    denom_x = sum((x - mean_x) ** 2 for x in xs)
    denom_y = sum((y - mean_y) ** 2 for y in ys)
    if denom_x <= 0.0 or denom_y <= 0.0:
        return 0.0
    return num / ((denom_x * denom_y) ** 0.5)


def audit_independence(
    taxonomy: TaxonomyMetrics, probe: ProbeMetrics,
    *,
    taxonomy_thresholds_passed: bool,
    probe_thresholds_passed: bool,
) -> IndependenceAudit:
    # Pearson between per-cluster classified count and
    # per-cluster hit rate.
    classified = [
        float(o.classified_count) for o in probe.outcomes
    ]
    rates = [o.hit_rate for o in probe.outcomes]
    corr = _pearson(classified, rates)
    survives = bool(
        taxonomy_thresholds_passed
        and not probe_thresholds_passed
        or (
            taxonomy_thresholds_passed
            and probe_thresholds_passed
        )
    )
    return IndependenceAudit(
        taxonomy_probe_correlation=round(corr, 6),
        taxonomy_survives_probe_failure=survives,
    )


__all__ = ["IndependenceAudit", "audit_independence"]
