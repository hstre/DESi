"""v3.97 — token-level and structural semantic
divergence between the entangled (G_v316susp +
E_v317h) family pair.

The probe operates EXCLUSIVELY on the raw
trajectory ``text`` field. No StateVector, no
frame, no coverage signal feeds the comparison.
The point is: how different are the two families
when DESi's representation is stripped away?

Closed token-pipeline:

1. lower-case
2. strip ``Therefore`` / ``Theref`` punctuation
3. split on whitespace and discard tokens that
   are pure punctuation
4. drop tokens shorter than 3 characters
   (stop-word approximation that needs no
   dictionary)
5. emit unigrams and bigrams
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache

from ..entangled.variance import (
    ENTANGLED_FAMILY_IDS,
    entangled_members,
)
from ..epistemic_trajectory.extractor import (
    extract_all_trajectories,
)
from ..novel_families import all_family_members


_TOKEN_RE = re.compile(r"[a-zA-Z]+")
_MIN_TOKEN_LEN: int = 3


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _tokenise(text: str) -> tuple[str, ...]:
    raw = _TOKEN_RE.findall(text.lower())
    return tuple(
        t for t in raw if len(t) >= _MIN_TOKEN_LEN
    )


def _bigrams(
    tokens: tuple[str, ...],
) -> tuple[tuple[str, str], ...]:
    return tuple(
        (tokens[i], tokens[i + 1])
        for i in range(len(tokens) - 1)
    )


@lru_cache(maxsize=1)
def _family_texts() -> dict[str, list[str]]:
    fams = all_family_members()
    members = set(entangled_members())
    by_fam: dict[str, list[str]] = {
        fid: []
        for fid in ENTANGLED_FAMILY_IDS
    }
    for t in extract_all_trajectories():
        if t.trajectory_id not in members:
            continue
        for fid, ms in fams.items():
            if (
                fid in by_fam
                and t.trajectory_id in ms
            ):
                by_fam[fid].append(t.text)
    return by_fam


@dataclass(frozen=True)
class FamilyTokenStats:
    family_id: str
    member_count: int
    unique_unigrams: int
    unique_bigrams: int
    total_unigrams: int

    def to_dict(self) -> dict[str, object]:
        return {
            "family_id": self.family_id,
            "member_count": self.member_count,
            "unique_unigrams":
                self.unique_unigrams,
            "unique_bigrams":
                self.unique_bigrams,
            "total_unigrams":
                self.total_unigrams,
        }


def _family_unigram_set(
    family_id: str,
) -> set[str]:
    texts = _family_texts().get(family_id, [])
    out: set[str] = set()
    for t in texts:
        out.update(_tokenise(t))
    return out


def _family_bigram_set(
    family_id: str,
) -> set[tuple[str, str]]:
    texts = _family_texts().get(family_id, [])
    out: set[tuple[str, str]] = set()
    for t in texts:
        out.update(_bigrams(_tokenise(t)))
    return out


def _family_total_unigram_count(
    family_id: str,
) -> int:
    texts = _family_texts().get(family_id, [])
    return sum(len(_tokenise(t)) for t in texts)


def family_token_stats() -> tuple[
    FamilyTokenStats, ...,
]:
    return tuple(
        FamilyTokenStats(
            family_id=fid,
            member_count=len(
                _family_texts().get(fid, []),
            ),
            unique_unigrams=len(
                _family_unigram_set(fid),
            ),
            unique_bigrams=len(
                _family_bigram_set(fid),
            ),
            total_unigrams=(
                _family_total_unigram_count(fid)
            ),
        )
        for fid in ENTANGLED_FAMILY_IDS
    )


def jaccard_unigrams() -> float:
    a = _family_unigram_set(
        ENTANGLED_FAMILY_IDS[0],
    )
    b = _family_unigram_set(
        ENTANGLED_FAMILY_IDS[1],
    )
    union = a | b
    if not union:
        return 0.0
    return _round(len(a & b) / len(union))


def jaccard_bigrams() -> float:
    a = _family_bigram_set(
        ENTANGLED_FAMILY_IDS[0],
    )
    b = _family_bigram_set(
        ENTANGLED_FAMILY_IDS[1],
    )
    union = a | b
    if not union:
        return 0.0
    return _round(len(a & b) / len(union))


def semantic_overlap() -> float:
    """Mean of unigram and bigram Jaccard
    similarities."""
    return _round(
        (jaccard_unigrams() + jaccard_bigrams())
        / 2.0,
    )


def semantic_distance() -> float:
    return _round(1.0 - semantic_overlap())


def family_uniqueness() -> dict[str, float]:
    """For each family: fraction of its unique
    unigrams that do NOT appear in the other
    family. 1.0 = totally disjoint vocabulary."""
    a_id, b_id = ENTANGLED_FAMILY_IDS
    a = _family_unigram_set(a_id)
    b = _family_unigram_set(b_id)
    return {
        a_id: (
            _round(len(a - b) / len(a))
            if a else 0.0
        ),
        b_id: (
            _round(len(b - a) / len(b))
            if b else 0.0
        ),
    }


__all__ = [
    "ENTANGLED_FAMILY_IDS",
    "FamilyTokenStats",
    "family_token_stats",
    "family_uniqueness",
    "jaccard_bigrams",
    "jaccard_unigrams",
    "semantic_distance",
    "semantic_overlap",
]
