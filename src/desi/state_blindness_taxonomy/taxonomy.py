"""v3.118 — closed blindness-type taxonomy.

For each v3.117 blindness pool we classify the
collapse using a single text-overlap
discriminator computed from the pool members'
raw trajectory text. The mean pairwise unigram
Jaccard within the pool determines the kind:

* ``DUPLICATE_COLLAPSE``   - mean text Jaccard
  >= 0.50: members share most of their text
  (literal cross-corpus duplicates).
* ``STRUCTURAL_COLLAPSE``  - 0.10 <= mean text
  Jaccard < 0.50: partial overlap, often a
  template difference.
* ``SEMANTIC_COLLAPSE``    - mean text Jaccard
  < 0.10: genuinely different texts mapping to
  the same StateVector signature.
* ``ROUTING_COLLAPSE``     - any pool where the
  routing_state coordinate is non-zero on every
  pool member AND the pool's text Jaccard sits
  in the structural band; surfaces routing-
  dominated collisions.
* ``UNKNOWN``              - any pool whose
  texts are empty or whose classification
  cannot be inferred.
"""
from __future__ import annotations

import itertools
import re
from enum import Enum
from functools import lru_cache

from ..epistemic_trajectory.extractor import (
    extract_all_trajectories,
)
from ..state_blindness.census import (
    BlindnessPool, cross_family_pools,
)


_TOKEN_RE = re.compile(r"[a-zA-Z]+")
_MIN_TOKEN_LEN: int = 3

_DUPLICATE_THRESHOLD: float = 0.50
_SEMANTIC_CEILING: float = 0.10


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


class BlindnessKind(str, Enum):
    DUPLICATE_COLLAPSE  = "duplicate_collapse"
    SEMANTIC_COLLAPSE   = "semantic_collapse"
    STRUCTURAL_COLLAPSE = "structural_collapse"
    ROUTING_COLLAPSE    = "routing_collapse"
    UNKNOWN             = "unknown"


def _tokens(text: str) -> set[str]:
    return {
        t.lower()
        for t in _TOKEN_RE.findall(text.lower())
        if len(t) >= _MIN_TOKEN_LEN
    }


@lru_cache(maxsize=1)
def _text_lookup() -> dict[str, str]:
    return {
        t.trajectory_id: t.text
        for t in extract_all_trajectories()
    }


def _mean_pairwise_jaccard(
    member_ids: tuple[str, ...],
) -> float:
    texts = _text_lookup()
    tok_sets = [
        _tokens(texts.get(m, ""))
        for m in member_ids
    ]
    if any(not s for s in tok_sets):
        return 0.0
    sims: list[float] = []
    for a, b in itertools.combinations(
        tok_sets, 2,
    ):
        union = a | b
        if union:
            sims.append(len(a & b) / len(union))
    if not sims:
        return 0.0
    return _round(sum(sims) / len(sims))


def _routing_active_for_all(
    pool: BlindnessPool,
) -> bool:
    """True iff the pool's signature has a
    non-zero routing_state in any state slot.
    The state signature is identical across all
    pool members, so reading the first member's
    sig is sufficient."""
    if not pool.state_signature:
        return False
    # Coordinate 8 is routing_state in the
    # 9-tuple per state.
    return any(
        s[8] != 0.0
        for s in pool.state_signature
    )


def classify_pool(
    pool: BlindnessPool,
) -> str:
    jaccard = _mean_pairwise_jaccard(
        pool.member_ids,
    )
    if jaccard == 0.0 and not pool.member_ids:
        return BlindnessKind.UNKNOWN.value
    routing_active = _routing_active_for_all(pool)
    if jaccard >= _DUPLICATE_THRESHOLD:
        return (
            BlindnessKind.DUPLICATE_COLLAPSE.value
        )
    if jaccard < _SEMANTIC_CEILING:
        return (
            BlindnessKind.SEMANTIC_COLLAPSE.value
        )
    # Middle band: distinguish structural vs
    # routing collapse.
    if routing_active:
        return (
            BlindnessKind.ROUTING_COLLAPSE.value
        )
    return (
        BlindnessKind.STRUCTURAL_COLLAPSE.value
    )


__all__ = [
    "BlindnessKind",
    "_mean_pairwise_jaccard",
    "classify_pool",
]
