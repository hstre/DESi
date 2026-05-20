"""v3.93 — proxy information loss.

The v3.82 minimal proxy is
``{branch_cost, contradiction_load}``. We ask: how
much of the residual variance carried by the
entangled (G+E) pair lives OUTSIDE that proxy? A
non-trivial outside-proxy share means there is at
least some signal the proxy is throwing away.
"""
from __future__ import annotations

from ..novel_minimal_features.minimal import (
    PROXY_DIMS,
)
from .variance import (
    residual_total_variance,
    residual_variance_by_dim,
    variance_share_by_dim,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def proxy_dims() -> tuple[str, ...]:
    return PROXY_DIMS()


def proxy_variance_share() -> float:
    shares = variance_share_by_dim()
    return _round(
        sum(shares.get(d, 0.0) for d in proxy_dims()),
    )


def non_proxy_variance_share() -> float:
    return _round(1.0 - proxy_variance_share())


def proxy_information_loss() -> float:
    """Fraction of entangled-pair residual variance
    that the proxy cannot see. Equal to
    ``non_proxy_variance_share`` - the value lives
    in dims outside ``PROXY_DIMS``."""
    return non_proxy_variance_share()


def hidden_dim_candidates() -> tuple[str, ...]:
    """Dimensions outside the proxy whose share of
    residual variance is non-zero."""
    shares = variance_share_by_dim()
    proxy = set(proxy_dims())
    return tuple(sorted(
        d for d, s in shares.items()
        if d not in proxy and s > 0.0
    ))


__all__ = [
    "hidden_dim_candidates",
    "non_proxy_variance_share",
    "proxy_dims",
    "proxy_information_loss",
    "proxy_variance_share",
]
