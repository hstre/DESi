"""v3.87 — proxy transfer metrics.

* ``proxy_accuracy``         — purity of the v3.82
  proxy on novel families.
* ``baseline_full_purity``   — purity of full
  feature space on novel families.
* ``proxy_gap``              — ``baseline -
  proxy_accuracy``. A negative gap means the proxy
  outperforms the full feature space (the dropped
  dimensions are noise on novel material).
* ``new_informative_dims``   — dimensions outside
  the v3.82 proxy whose addition meaningfully
  shifts purity. Reported with the signed delta
  so anti-informative dims (noise) are visible.
* ``feature_stability``      — proxy purity on
  novel material divided by proxy purity on the
  v3.82 plateau pool.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..doppelgaenger.blind_cluster import (
    cluster_purity as plateau_cluster_purity,
)
from ..doppelgaenger.equivalence import (
    all_blind_clusters as plateau_blind_clusters,
)
from ..epistemic_trajectory.state import (
    DIMENSION_NAMES,
)
from ..minimal_features.importance import (
    minimal_cluster_accuracy as v382_proxy_purity,
)
from ..novel_families import all_family_members
from ..redundancy_masking.equivalence import (
    redundancy_classes,
)
from .minimal import (
    PROXY_DIMS, cluster_novel_with,
    cluster_with_full, cluster_with_proxy,
)


_DELTA_THRESHOLD: float = 0.05


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _family_lookup() -> dict[str, str]:
    return {
        m: fid
        for fid, ms in all_family_members().items()
        for m in ms
    }


def novel_family_purity(clusters) -> float:
    lookup = _family_lookup()
    total = sum(len(c.members) for c in clusters)
    if total == 0:
        return 0.0
    correct = 0
    for c in clusters:
        counts: dict[str, int] = {}
        for m in c.members:
            counts[lookup.get(m, "?")] = (
                counts.get(lookup.get(m, "?"), 0)
                + 1
            )
        correct += (
            max(counts.values()) if counts else 0
        )
    return _round(correct / total)


def proxy_accuracy() -> float:
    return novel_family_purity(
        cluster_with_proxy(),
    )


def baseline_full_purity() -> float:
    return novel_family_purity(
        cluster_with_full(),
    )


def proxy_gap() -> float:
    return _round(
        baseline_full_purity() - proxy_accuracy(),
    )


@dataclass(frozen=True)
class DimContribution:
    dim: str
    delta_purity: float

    def to_dict(self) -> dict[str, object]:
        return {
            "dim": self.dim,
            "delta_purity": self.delta_purity,
        }


def new_informative_dims() -> tuple[
    DimContribution, ...,
]:
    """Dims OUTSIDE the proxy whose addition
    moves purity by at least the delta threshold
    (in either direction)."""
    proxy = set(PROXY_DIMS())
    base = proxy_accuracy()
    out: list[DimContribution] = []
    for d in DIMENSION_NAMES:
        if d in proxy:
            continue
        clusters = cluster_novel_with(
            frozenset(proxy | {d}),
        )
        p = novel_family_purity(clusters)
        delta = _round(p - base)
        if abs(delta) >= _DELTA_THRESHOLD:
            out.append(DimContribution(
                dim=d, delta_purity=delta,
            ))
    return tuple(sorted(
        out, key=lambda c: (-abs(c.delta_purity), c.dim),
    ))


def feature_stability() -> float:
    """proxy_accuracy on novel / proxy_accuracy on
    plateau (v3.82)."""
    plateau = v382_proxy_purity()
    if plateau <= 0.0:
        return 0.0
    return _round(proxy_accuracy() / plateau)


__all__ = [
    "DimContribution",
    "baseline_full_purity",
    "feature_stability",
    "new_informative_dims",
    "novel_family_purity",
    "proxy_accuracy",
    "proxy_gap",
]
