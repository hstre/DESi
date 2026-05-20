"""v5.2 — closed curiosity / priority scoring.

The curiosity score is a deterministic function
of a Claim's structural features (frame
distribution rarity, conflict participation,
source weight). It carries no PRNG state and no
external input."""
from __future__ import annotations

import hashlib
from functools import lru_cache

from ..open_world.claim_stream import (
    Claim, FrameType, all_conflicts,
    frame_counts, stream_claims,
)


_SOURCE_WEIGHT: dict[str, float] = {
    "wikipedia":              0.50,
    "arxiv":                  0.90,
    "ssrn":                   0.70,
    "github_issue":           0.40,
    "news":                   0.30,
    "synthetic_adversarial":  0.10,
}


def _claim_digest_byte(
    claim_id: str, offset: int,
) -> int:
    h = hashlib.sha256(
        claim_id.encode("utf-8"),
    ).digest()
    return h[offset]


@lru_cache(maxsize=None)
def _conflict_participation(
    claim_id: str,
) -> int:
    return sum(
        1 for a, b, _ in all_conflicts()
        if a == claim_id or b == claim_id
    )


def _frame_rarity(frame: str) -> float:
    counts = frame_counts()
    total = sum(counts.values())
    if total == 0:
        return 0.0
    c = counts.get(frame, 0)
    if c == 0:
        return 1.0
    # Rarity = 1 - normalised frequency.
    return 1.0 - (c / total)


def curiosity_score(claim: Claim) -> float:
    if claim.frame == FrameType.UNKNOWN.value:
        # Adversarial / unparseable claims are
        # interesting structurally but should
        # not steer exploration toward them, so
        # we cap their score at 0.1.
        return 0.1
    rarity = _frame_rarity(claim.frame)
    source_w = _SOURCE_WEIGHT.get(
        claim.source, 0.50,
    )
    conflict_w = min(
        _conflict_participation(claim.claim_id)
        / 10.0,
        1.0,
    )
    # Deterministic small per-claim jitter so
    # ties break consistently; never dominant.
    jitter = (
        _claim_digest_byte(claim.claim_id, 0)
        / 2560.0
    )
    raw = (
        0.5 * rarity
        + 0.3 * source_w
        + 0.15 * conflict_w
        + 0.05 * jitter
    )
    return round(raw, 6)


@lru_cache(maxsize=1)
def ranked_claims() -> tuple[Claim, ...]:
    pairs = [
        (curiosity_score(c), c.claim_id, c)
        for c in stream_claims()
    ]
    pairs.sort(
        key=lambda t: (-t[0], t[1]),
    )
    return tuple(c for _, _, c in pairs)


def prioritised_conflict_kinds() -> tuple[
    str, ...,
]:
    """Return conflict kinds ordered by total
    participation - the kind that touches the
    most claims is most worth resolving first."""
    from collections import Counter
    cnt: Counter[str] = Counter()
    for a, b, kind in all_conflicts():
        cnt[kind] += 1
    return tuple(
        k for k, _ in cnt.most_common()
    )


__all__ = [
    "curiosity_score",
    "prioritised_conflict_kinds",
    "ranked_claims",
]
