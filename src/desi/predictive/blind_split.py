"""v3.65 — deterministic train/test split.

Sort the 190 plateau-anchor pairs by (a, b) tuple and
assign every third pair to the TEST fold; the rest go
to TRAIN. No randomness, no PYTHONHASHSEED
dependence. Approximate 67/33 split (127 train, 63
test on the 190-pair universe).
"""
from __future__ import annotations

from dataclasses import dataclass

from ..causal_complementarity.ablation import (
    PairFactors, all_pair_factors,
)


TEST_STRIDE: int = 3


@dataclass(frozen=True)
class FoldedPair:
    pair: PairFactors
    fold: str       # "train" | "test"


def folded_pairs() -> tuple[FoldedPair, ...]:
    pairs = sorted(
        all_pair_factors(),
        key=lambda p: (p.a, p.b),
    )
    out: list[FoldedPair] = []
    for i, p in enumerate(pairs):
        fold = (
            "test"
            if (i + 1) % TEST_STRIDE == 0
            else "train"
        )
        out.append(FoldedPair(pair=p, fold=fold))
    return tuple(out)


def train_pairs() -> tuple[PairFactors, ...]:
    return tuple(
        fp.pair for fp in folded_pairs()
        if fp.fold == "train"
    )


def test_pairs() -> tuple[PairFactors, ...]:
    return tuple(
        fp.pair for fp in folded_pairs()
        if fp.fold == "test"
    )


__all__ = [
    "FoldedPair", "TEST_STRIDE", "folded_pairs",
    "test_pairs", "train_pairs",
]
