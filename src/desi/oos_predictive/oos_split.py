"""v3.66 — out-of-sample (OOS) corpus split.

The directive's "komplett neue Trajektorien" rule has
to be implemented inside the closed v2/v3 trajectory
inventory. We use the v3.53 reference corpora
{v23, v314, v315, v316} as the IN-SAMPLE training
universe and treat any pair touching v317 / v317-h /
v318-wmf / sample as OUT-OF-SAMPLE.

Split:

* TRAIN — both anchors in REFERENCE_CORPORA
* OOS   — at least one anchor outside REFERENCE_CORPORA

(For the v3.50 universe of 20 plateau anchors:
11 in-sample anchors yield 55 train pairs; the 9
out-of-sample anchors and the cross-pairs yield 135
OOS pairs. Total = 190 matches v3.65's universe.)
"""
from __future__ import annotations

from ..causal_complementarity.ablation import (
    PairFactors, all_pair_factors,
)
from ..cross_corpus.corpus_loader import (
    normalised_prefix,
)


REFERENCE_CORPORA: tuple[str, ...] = (
    "v23", "v314", "v315", "v316",
)


def _in_reference(pid: str) -> bool:
    return normalised_prefix(pid) in REFERENCE_CORPORA


def in_sample_pairs() -> tuple[PairFactors, ...]:
    return tuple(
        p for p in all_pair_factors()
        if _in_reference(p.a) and _in_reference(p.b)
    )


def out_of_sample_pairs() -> tuple[PairFactors, ...]:
    return tuple(
        p for p in all_pair_factors()
        if not (
            _in_reference(p.a) and _in_reference(p.b)
        )
    )


__all__ = [
    "REFERENCE_CORPORA", "in_sample_pairs",
    "out_of_sample_pairs",
]
