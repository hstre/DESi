"""v3.107 — extended candidate-dimension taxonomy
for adaptive search.

Building on the closed v3.101 candidate enum, we
add four additional candidates that are likely
to discriminate the SYLLOGISM / POST_HOC family
collisions that contradiction_type cannot
separate:

* ``LETTER_PREFIX_HASH``     - integer code of
  the family's letter prefix.
* ``FIRST_CONTENT_WORD_HASH`` - 4-bit sha256
  digest of the first content word in the text
  (skip stop-tokens).
* ``TEXT_LENGTH_BUCKET``     - log-scale bucket
  of the trajectory text length.
* ``CORPUS_HASH``            - 4-bit sha256
  digest of the trajectory id's corpus prefix.

Each candidate maps any trajectory text to a
single float, broadcast into 5 extra slots when
augmenting tail vectors.
"""
from __future__ import annotations

import re
from enum import Enum
from functools import lru_cache
from hashlib import sha256

from ..t10.candidate import (
    CANDIDATE_DIMS as _V3101_CANDIDATE_DIMS,
    candidate_values as _v3101_values,
)


class AdaptiveCandidate(str, Enum):
    LETTER_PREFIX_HASH      = (
        "letter_prefix_hash"
    )
    FIRST_CONTENT_WORD_HASH = (
        "first_content_word_hash"
    )
    TEXT_LENGTH_BUCKET      = (
        "text_length_bucket"
    )
    CORPUS_HASH             = "corpus_hash"


ADAPTIVE_CANDIDATES: tuple[str, ...] = tuple(
    c.value for c in AdaptiveCandidate
)

ALL_CANDIDATES: tuple[str, ...] = tuple(
    list(_V3101_CANDIDATE_DIMS)
    + list(ADAPTIVE_CANDIDATES)
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


_LETTER_TO_INT: dict[str, int] = {
    chr(ord("a") + i): i for i in range(26)
}


def _letter_prefix_hash_from_id(
    trajectory_id: str,
) -> float:
    if ":" not in trajectory_id:
        return 0.0
    tail = trajectory_id.split(":", 1)[1]
    m = re.match(r"([A-Za-z]+)", tail)
    if not m:
        return 0.0
    letter = m.group(1)[0].lower()
    return float(_LETTER_TO_INT.get(letter, 0))


def _first_content_word_hash(text: str) -> float:
    low = text.lower()
    words = re.findall(r"[a-z]+", low)
    for w in words:
        if len(w) >= 3:
            digest = sha256(
                w.encode("utf-8"),
            ).digest()
            return float(digest[0] & 0x0F)
    return 0.0


def _text_length_bucket(text: str) -> float:
    n = len(text)
    if n <= 0:
        return 0.0
    # log2-floor bucket; max 8 to cap dim
    # variance.
    out = 0
    while n > 1 and out < 8:
        n //= 2
        out += 1
    return float(out)


def _corpus_hash(trajectory_id: str) -> float:
    if ":" not in trajectory_id:
        return 0.0
    corpus = trajectory_id.split(":", 1)[0]
    digest = sha256(
        corpus.encode("utf-8"),
    ).digest()
    return float(digest[0] & 0x0F)


def adaptive_value(
    candidate: str,
    trajectory_id: str,
    text: str,
) -> float:
    if candidate == (
        AdaptiveCandidate.LETTER_PREFIX_HASH.value
    ):
        return _letter_prefix_hash_from_id(
            trajectory_id,
        )
    if candidate == (
        AdaptiveCandidate
        .FIRST_CONTENT_WORD_HASH.value
    ):
        return _first_content_word_hash(text)
    if candidate == (
        AdaptiveCandidate.TEXT_LENGTH_BUCKET.value
    ):
        return _text_length_bucket(text)
    if candidate == (
        AdaptiveCandidate.CORPUS_HASH.value
    ):
        return _corpus_hash(trajectory_id)
    # Fall through to v3.101 candidate values
    # (which are keyed on the trajectory id only,
    # so we accept the unused ``text`` arg).
    vals = _v3101_values(candidate)
    return float(vals.get(trajectory_id, 0.0))


@lru_cache(maxsize=None)
def candidate_values_for_ids(
    candidate: str,
    member_ids: tuple[str, ...],
) -> dict[str, float]:
    from ..epistemic_trajectory.extractor import (
        extract_all_trajectories,
    )
    text_lookup = {
        t.trajectory_id: t.text
        for t in extract_all_trajectories()
    }
    return {
        mid: adaptive_value(
            candidate, mid,
            text_lookup.get(mid, ""),
        )
        for mid in member_ids
    }


__all__ = [
    "ADAPTIVE_CANDIDATES",
    "ALL_CANDIDATES",
    "AdaptiveCandidate",
    "adaptive_value",
    "candidate_values_for_ids",
]
