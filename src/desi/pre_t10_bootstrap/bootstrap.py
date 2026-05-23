"""v3.120b — deterministic bootstrap of the
pre-T10 threshold.

For each seed we draw ``len(pools)`` pools
with replacement from the v3.119 rescuability
table and compute the threshold that would
keep TPR == 1.0 on the bootstrap sample
(= the minimum text_variance among the
sampled rescuable pools). If no rescuable
pool is sampled we record ``-1.0`` for that
seed.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256

from ..t10_boundary.boundary import (
    all_pool_recoverability,
)


BOOTSTRAP_SEEDS: tuple[int, ...] = tuple(
    range(0, 50),
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _det_index(
    seed: int, draw_index: int, n: int,
) -> int:
    """Deterministic uint -> [0, n) draw."""
    key = f"bootstrap|seed{seed}|draw{draw_index}"
    digest = sha256(key.encode("utf-8")).digest()
    return int.from_bytes(
        digest[:8], "big",
    ) % n


def _bootstrap_threshold(seed: int) -> float:
    outs = list(all_pool_recoverability())
    n = len(outs)
    rescuable_vars: list[float] = []
    for i in range(n):
        idx = _det_index(seed, i, n)
        o = outs[idx]
        if o.rescuable:
            rescuable_vars.append(
                o.text_variance,
            )
    if not rescuable_vars:
        return -1.0
    return _round(min(rescuable_vars))


@dataclass(frozen=True)
class BootstrapDraw:
    seed: int
    threshold: float

    def to_dict(self) -> dict[str, object]:
        return {
            "seed": self.seed,
            "threshold": self.threshold,
        }


@lru_cache(maxsize=1)
def all_bootstrap_draws() -> tuple[
    BootstrapDraw, ...,
]:
    return tuple(
        BootstrapDraw(
            seed=s,
            threshold=_bootstrap_threshold(s),
        )
        for s in BOOTSTRAP_SEEDS
    )


__all__ = [
    "BOOTSTRAP_SEEDS",
    "BootstrapDraw",
    "all_bootstrap_draws",
]
