"""Aufgabe 6 — corpus-level bias metrics.

Six closed metrics summarise how much human shaping the
v5.2 corpus received:

* ``rewrite_fraction``           — fraction of chains
  whose conclusion was edited.
* ``valid_probe_avoidance_rate`` — fraction of VALID
  chains whose RAW conclusion fired a safe probe and
  whose FINAL conclusion does not.
* ``invalid_probe_alignment_rate`` — fraction of INVALID
  chains whose RAW conclusion did not fire any safe probe
  but whose FINAL conclusion does.
* ``domain_bias_variance``       — variance of rewrite
  rate across the five v5.2 domains.
* ``semantic_shift_mean``        — mean ``1 - jaccard``
  over rewritten chains.
* ``semantic_shift_max``         — max ``1 - jaccard``
  over rewritten chains.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from .diff import ChainAudit


@dataclass(frozen=True)
class BiasMetrics:
    rewrite_fraction: float
    valid_probe_avoidance_rate: float
    invalid_probe_alignment_rate: float
    domain_bias_variance: float
    semantic_shift_mean: float
    semantic_shift_max: float

    def to_dict(self) -> dict[str, object]:
        return {
            "rewrite_fraction": self.rewrite_fraction,
            "valid_probe_avoidance_rate":
                self.valid_probe_avoidance_rate,
            "invalid_probe_alignment_rate":
                self.invalid_probe_alignment_rate,
            "domain_bias_variance":
                self.domain_bias_variance,
            "semantic_shift_mean":
                self.semantic_shift_mean,
            "semantic_shift_max":
                self.semantic_shift_max,
        }


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _variance(values: list[float]) -> float:
    if not values:
        return 0.0
    mean = sum(values) / len(values)
    return sum((v - mean) ** 2 for v in values) / len(values)


def compute_bias_metrics(
    audits: tuple[ChainAudit, ...],
) -> BiasMetrics:
    n = len(audits)
    if n == 0:
        return BiasMetrics(
            rewrite_fraction=0.0,
            valid_probe_avoidance_rate=0.0,
            invalid_probe_alignment_rate=0.0,
            domain_bias_variance=0.0,
            semantic_shift_mean=0.0,
            semantic_shift_max=0.0,
        )
    rewritten = [a for a in audits if a.was_rewritten]
    rewrite_fraction = len(rewritten) / n

    valid = [a for a in audits if a.ground_truth == "VALID"]
    valid_avoidance = (
        sum(
            1 for a in valid
            if a.probe_avoidance_delta > 0
        ) / len(valid) if valid else 0.0
    )

    invalid = [
        a for a in audits if a.ground_truth == "INVALID"
    ]
    invalid_alignment = (
        sum(
            1 for a in invalid
            if a.probe_alignment_delta > 0
        ) / len(invalid) if invalid else 0.0
    )

    domain_rates: list[float] = []
    domain_counts = Counter(a.domain for a in audits)
    for dom, dom_n in sorted(domain_counts.items()):
        dom_rewritten = sum(
            1 for a in audits
            if a.domain == dom and a.was_rewritten
        )
        domain_rates.append(dom_rewritten / dom_n)
    dom_var = _variance(domain_rates)

    if rewritten:
        shifts = [
            1.0 - a.semantic_similarity for a in rewritten
        ]
        shift_mean = sum(shifts) / len(shifts)
        shift_max = max(shifts)
    else:
        shift_mean = 0.0
        shift_max = 0.0

    return BiasMetrics(
        rewrite_fraction=_round(rewrite_fraction),
        valid_probe_avoidance_rate=_round(valid_avoidance),
        invalid_probe_alignment_rate=_round(
            invalid_alignment,
        ),
        domain_bias_variance=_round(dom_var),
        semantic_shift_mean=_round(shift_mean),
        semantic_shift_max=_round(shift_max),
    )


__all__ = ["BiasMetrics", "compute_bias_metrics"]
