"""v3.93 — per-dim variance audit on the entangled
pair (G_v316susp + E_v317h) of v3.85 novel families.

We work in the v3.89 RESIDUAL projection so the
dominant frame_id variance is already removed.
Inside this subspace, we ask: which dimensions
still carry signal between the two entangled
families?
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from ..epistemic_trajectory.state import (
    DIMENSION_NAMES,
)
from ..frame_normalization.contribution import (
    novel_vectors_residual,
)
from ..novel_families import all_family_members


_STATE_COUNT: int = 5
_DIM_PER_STATE: int = 9


ENTANGLED_FAMILY_IDS: tuple[str, str] = (
    "G_v316susp", "E_v317h",
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@lru_cache(maxsize=1)
def entangled_members() -> tuple[str, ...]:
    fams = all_family_members()
    out: list[str] = []
    for fid in ENTANGLED_FAMILY_IDS:
        out.extend(fams.get(fid, ()))
    return tuple(sorted(out))


@lru_cache(maxsize=1)
def entangled_residual_vectors() -> dict[
    str, tuple[float, ...],
]:
    ids = set(entangled_members())
    res = novel_vectors_residual()
    return {tid: res[tid] for tid in ids if tid in res}


def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def _variance(xs: list[float]) -> float:
    if not xs:
        return 0.0
    m = _mean(xs)
    return sum((x - m) ** 2 for x in xs) / len(xs)


def residual_variance_by_dim() -> dict[str, float]:
    vecs = entangled_residual_vectors()
    ids = sorted(vecs)
    out: dict[str, float] = {}
    for d_idx, name in enumerate(DIMENSION_NAMES):
        total = 0.0
        for s in range(_STATE_COUNT):
            col = [
                vecs[tid][s * _DIM_PER_STATE + d_idx]
                for tid in ids
            ]
            total += _variance(col)
        out[name] = _round(total)
    return out


def residual_total_variance() -> float:
    return _round(
        sum(residual_variance_by_dim().values()),
    )


def variance_share_by_dim() -> dict[str, float]:
    vbd = residual_variance_by_dim()
    total = sum(vbd.values())
    if total <= 0.0:
        return {k: 0.0 for k in vbd}
    return {
        k: _round(v / total) for k, v in vbd.items()
    }


_DOMINANT_THRESHOLD: float = 0.05


def dominant_dims() -> tuple[str, ...]:
    """Dimensions whose share of residual variance
    exceeds the dominance threshold."""
    shares = variance_share_by_dim()
    return tuple(sorted(
        d for d, s in shares.items()
        if s > _DOMINANT_THRESHOLD
    ))


@dataclass(frozen=True)
class FamilyMeanDiff:
    dim: str
    mean_g: float
    mean_e: float
    mean_diff_sum: float

    def to_dict(self) -> dict[str, object]:
        return {
            "dim": self.dim,
            "mean_g": self.mean_g,
            "mean_e": self.mean_e,
            "mean_diff_sum": self.mean_diff_sum,
        }


def family_mean_diffs() -> tuple[
    FamilyMeanDiff, ...,
]:
    """Per-dim absolute difference between the
    mean of G_v316susp and the mean of E_v317h,
    summed across the 5 state slots. This is the
    separation signal a linear classifier could
    use."""
    fams = all_family_members()
    g_ids = set(fams.get("G_v316susp", ()))
    e_ids = set(fams.get("E_v317h", ()))
    vecs = entangled_residual_vectors()
    out: list[FamilyMeanDiff] = []
    for d_idx, name in enumerate(DIMENSION_NAMES):
        mg, me, diff = 0.0, 0.0, 0.0
        for s in range(_STATE_COUNT):
            idx = s * _DIM_PER_STATE + d_idx
            g_col = [
                vecs[t][idx] for t in g_ids
                if t in vecs
            ]
            e_col = [
                vecs[t][idx] for t in e_ids
                if t in vecs
            ]
            mg_s = _mean(g_col)
            me_s = _mean(e_col)
            mg += mg_s
            me += me_s
            diff += abs(mg_s - me_s)
        out.append(FamilyMeanDiff(
            dim=name,
            mean_g=_round(mg),
            mean_e=_round(me),
            mean_diff_sum=_round(diff),
        ))
    return tuple(out)


__all__ = [
    "ENTANGLED_FAMILY_IDS",
    "FamilyMeanDiff",
    "dominant_dims",
    "entangled_members",
    "entangled_residual_vectors",
    "family_mean_diffs",
    "residual_total_variance",
    "residual_variance_by_dim",
    "variance_share_by_dim",
]
