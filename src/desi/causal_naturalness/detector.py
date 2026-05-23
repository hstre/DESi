"""Aufgaben 2 + 3 — inter-corpus separability + anomaly detector.

The valid manifold is built from the v2.3 multistep cases and
the v3.14 held-out valid cases. For each feature we compute a
**direction-aware** percentile boundary that turns the
heterogeneous valid set into a unilateral acceptance window:

* "too high" features (marker density / synonym stacking /
  frame-switch frequency / explicitness / marker entropy)
  → flag when the chain exceeds the 90th-percentile of the
  valid set;
* "too low" features (unknown link ratio) → flag when the
  chain falls under the 10th-percentile of the valid set;
* other features (lexical redundancy, transition variance)
  → flag when the absolute distance from the manifold median
  exceeds the 90th-percentile absolute deviation.

A chain is **anomalous** when at least
``MIN_OUTLIER_FEATURES`` directional features fire.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from ..causal_link_typing.enums import CorpusSource
from .corpus import ChainEntry
from .features import NaturalnessVector, compute_vector


# Boundary percentiles for the per-feature acceptance window.
HIGH_PERCENTILE: float = 0.90
LOW_PERCENTILE:  float = 0.10

# A chain is flagged when at least this many features fall
# outside their per-feature acceptance window. v3.18 picked 1
# because the percentile windows are already directional and
# narrowed by the natural-manifold's sparsity (median = 0 for
# most marker-style features). Requiring two simultaneous
# outliers crushed adversarial detection in the calibration runs.
MIN_OUTLIER_FEATURES: int = 2


_FEATURE_NAMES: tuple[str, ...] = (
    "marker_density",
    "marker_entropy",
    "lexical_redundancy",
    "synonym_stacking",
    "transition_variance",
    "frame_switch_frequency",
    "unknown_link_ratio",
    "explicitness_score",
)


# Direction tag per feature.
# "high" → flagged when chain value > P90(valid).
# "low"  → flagged when chain value < P10(valid).
# "abs"  → flagged when |chain - median(valid)| > P90 absolute
#          deviation from the median.
_FEATURE_DIRECTION: dict[str, str] = {
    "marker_density":         "high",
    "marker_entropy":         "high",
    "lexical_redundancy":     "abs",
    "synonym_stacking":       "high",
    "transition_variance":    "abs",
    "frame_switch_frequency": "high",
    "unknown_link_ratio":     "low",
    "explicitness_score":     "high",
}


@dataclass(frozen=True)
class ManifoldStats:
    p10_upper: tuple[float, ...]
    p90_upper: tuple[float, ...]
    medians:   tuple[float, ...]
    p90_abs_deviation: tuple[float, ...]
    sample_size: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "feature_names": list(_FEATURE_NAMES),
            "p10": list(self.p10_upper),
            "p90": list(self.p90_upper),
            "medians": list(self.medians),
            "p90_abs_deviation": list(self.p90_abs_deviation),
            "sample_size": self.sample_size,
        }


def _vectorise(chains: tuple[ChainEntry, ...]) -> tuple[
    NaturalnessVector, ...
]:
    return tuple(
        compute_vector(c.chain_id, c.text, c.corpus) for c in chains
    )


def _percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    if len(s) == 1:
        return s[0]
    k = (len(s) - 1) * p
    f = int(k)
    c = min(f + 1, len(s) - 1)
    return s[f] + (s[c] - s[f]) * (k - f)


def _median(values: list[float]) -> float:
    return _percentile(values, 0.5)


def build_manifold(
    valid_chains: tuple[ChainEntry, ...],
) -> ManifoldStats:
    vectors = _vectorise(valid_chains)
    p10: list[float] = []
    p90: list[float] = []
    medians: list[float] = []
    p90_abs: list[float] = []
    for i in range(len(_FEATURE_NAMES)):
        col = [v.feature_tuple()[i] for v in vectors]
        med = _median(col)
        deviations = [abs(x - med) for x in col]
        p10.append(round(_percentile(col, LOW_PERCENTILE), 6))
        p90.append(round(_percentile(col, HIGH_PERCENTILE), 6))
        medians.append(round(med, 6))
        p90_abs.append(round(_percentile(deviations, HIGH_PERCENTILE), 6))
    return ManifoldStats(
        p10_upper=tuple(p10), p90_upper=tuple(p90),
        medians=tuple(medians),
        p90_abs_deviation=tuple(p90_abs),
        sample_size=len(vectors),
    )


@dataclass(frozen=True)
class AnomalyVerdict:
    chain_id: str
    corpus: str
    feature_values: tuple[float, ...]
    outlier_features: tuple[str, ...]
    outlier_count: int
    distance_from_manifold: float
    is_anomalous: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "chain_id": self.chain_id,
            "corpus": self.corpus,
            "feature_values": list(self.feature_values),
            "outlier_features": list(self.outlier_features),
            "outlier_count": self.outlier_count,
            "distance_from_manifold": self.distance_from_manifold,
            "is_anomalous": self.is_anomalous,
        }


def classify_anomaly(
    vector: NaturalnessVector, manifold: ManifoldStats,
) -> AnomalyVerdict:
    features = vector.feature_tuple()
    outliers: list[str] = []
    z_sum = 0.0
    for i, val in enumerate(features):
        name = _FEATURE_NAMES[i]
        direction = _FEATURE_DIRECTION[name]
        med = manifold.medians[i]
        if direction == "high":
            limit = manifold.p90_upper[i]
            if val > limit:
                outliers.append(name)
            z_sum += max(0.0, val - limit)
        elif direction == "low":
            limit = manifold.p10_upper[i]
            if val < limit:
                outliers.append(name)
            z_sum += max(0.0, limit - val)
        else:  # "abs"
            limit = manifold.p90_abs_deviation[i]
            dev = abs(val - med)
            if dev > limit:
                outliers.append(name)
            z_sum += max(0.0, dev - limit)
    return AnomalyVerdict(
        chain_id=vector.chain_id,
        corpus=vector.corpus,
        feature_values=features,
        outlier_features=tuple(outliers),
        outlier_count=len(outliers),
        distance_from_manifold=round(z_sum, 6),
        is_anomalous=len(outliers) >= MIN_OUTLIER_FEATURES,
    )


def classify_all(
    chains: tuple[ChainEntry, ...], manifold: ManifoldStats,
) -> tuple[AnomalyVerdict, ...]:
    vectors = _vectorise(chains)
    return tuple(classify_anomaly(v, manifold) for v in vectors)


def valid_manifold_subset(
    chains: tuple[ChainEntry, ...],
) -> tuple[ChainEntry, ...]:
    """The naturalness manifold is fit on the v3.14 held-out
    valid cases — the cleanest, most homogeneous source of
    *naturally written* causal chains. v2.3 chains are included
    only as a corpus to evaluate against (their structural
    richness inflates the percentile windows when mixed in).
    v3.14 trap cases are excluded by ``expected_natural``."""
    return tuple(
        c for c in chains
        if c.corpus.value == CorpusSource.V314_HELDOUT.value
        and c.expected_natural
    )


__all__ = [
    "AnomalyVerdict",
    "MIN_OUTLIER_FEATURES",
    "ManifoldStats",
    "SIGMA_K",
    "build_manifold",
    "classify_all",
    "classify_anomaly",
    "valid_manifold_subset",
]
