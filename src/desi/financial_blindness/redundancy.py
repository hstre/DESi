"""v15.2 - structural redundancy and
recoverability.

* structural_redundancy: the fraction of all firm
  pairs that are structurally redundant - same
  pool AND near-identical signatures. Redundant
  firms are interchangeable audit targets, so this
  is exactly the slack a later sprint can compress.
* recoverability_signal: the fraction of firms
  whose signature sits within the pool radius of
  their own pool centroid - i.e. once a blind spot
  is found in a pool, it recovers across the pool.

Reads no post-hoc label.
"""
from __future__ import annotations

from .clusters import pool_of, pools
from .trajectory_similarity import (
    distance, signature, signatures, similarity,
)

# A pair counts as redundant above this similarity.
_REDUNDANT_SIM = 0.90
# Recoverability radius (matches the pool radius).
_TAU = 0.10


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _all_pairs() -> list[tuple[str, str]]:
    ids = [sig.firm_id for sig in signatures()]
    out: list[tuple[str, str]] = []
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            out.append((a, b))
    return out


def _same_pool(a: str, b: str) -> bool:
    return pool_of(a).pool_id == pool_of(b).pool_id


def structural_redundancy() -> float:
    """Fraction of firm pairs that are same-pool
    and near-identical, in [0, 1]."""
    pairs = _all_pairs()
    if not pairs:
        return 0.0
    redundant = sum(
        1 for a, b in pairs
        if _same_pool(a, b)
        and similarity(a, b) >= _REDUNDANT_SIM
    )
    return _round(redundant / len(pairs))


def recoverability_signal() -> float:
    """Fraction of firms within the pool radius of
    their own pool centroid, in [0, 1]."""
    sigs = signatures()
    if not sigs:
        return 0.0
    ok = 0
    for sig in sigs:
        p = pool_of(sig.firm_id)
        # distance from firm signature to centroid
        sq = sum(
            (x - c) ** 2
            for x, c in zip(sig.values, p.centroid)
        )
        dim_norm = len(sig.values) ** 0.5
        d = (sq ** 0.5) / dim_norm
        if d <= _TAU:
            ok += 1
    return _round(ok / len(sigs))


def redundant_firm_fraction() -> float:
    """Fraction of firms that share a multi-member
    pool (i.e. are not the sole occupant of their
    pool)."""
    sigs = signatures()
    if not sigs:
        return 0.0
    in_multi = sum(
        1 for sig in sigs
        if pool_of(sig.firm_id).size > 1
    )
    return _round(in_multi / len(sigs))


__all__ = [
    "recoverability_signal",
    "redundant_firm_fraction",
    "structural_redundancy",
]
