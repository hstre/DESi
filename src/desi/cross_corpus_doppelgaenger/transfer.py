"""v3.83 — cross-corpus transfer + stability.

* ``cross_corpus_classes``: joint clusters that
  span 2+ closed reference corpora.
* ``transfer_accuracy``: fraction of v3.79
  cross-corpus redundancy pairs (restricted to the
  4 closed corpora) recovered as same-cluster
  members in the joint blind clustering.
* ``class_stability``: whether the per-corpus
  clusterings refine the joint clustering. 1.0
  means no per-corpus cluster ever crosses a joint
  cluster boundary.
"""
from __future__ import annotations

import itertools
from functools import lru_cache

from ..cross_corpus.corpus_loader import (
    CorpusKind, corpus_of,
)
from ..redundancy_masking.equivalence import (
    redundancy_classes,
)
from .corpus_clustering import (
    corpus_clusters, joint_clusters,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


_CLOSED_CORPORA: frozenset[str] = frozenset(
    k.value for k in CorpusKind
)


def _closed_member(member: str) -> bool:
    return corpus_of(member) in _CLOSED_CORPORA


@lru_cache(maxsize=1)
def restricted_classes() -> tuple[
    tuple[str, ...], ...,
]:
    """v3.79 redundancy classes, each restricted to
    its members from the 4 closed reference
    corpora."""
    out: list[tuple[str, ...]] = []
    for c in redundancy_classes():
        kept = tuple(
            sorted(
                m for m in c.members
                if _closed_member(m)
            )
        )
        out.append(kept)
    return tuple(out)


def cross_corpus_classes() -> int:
    """Joint clusters whose members come from 2+
    distinct closed corpora."""
    n = 0
    for c in joint_clusters():
        corpora = {
            corpus_of(m)
            for m in c.members
            if corpus_of(m) is not None
        }
        if len(corpora) >= 2:
            n += 1
    return n


def _joint_cluster_lookup() -> dict[str, int]:
    return {
        m: c.cluster_id
        for c in joint_clusters()
        for m in c.members
    }


def transfer_accuracy() -> float:
    """Fraction of v3.79 cross-corpus pairs that
    the joint blind clustering reproduces as
    same-cluster pairs."""
    lookup = _joint_cluster_lookup()
    matched = 0
    total = 0
    for members in restricted_classes():
        for a, b in itertools.combinations(
            members, 2,
        ):
            if corpus_of(a) == corpus_of(b):
                continue
            total += 1
            if lookup.get(a) == lookup.get(b):
                matched += 1
    if total == 0:
        return 0.0
    return _round(matched / total)


def class_stability() -> float:
    """Fraction of per-corpus clusters that are
    subsets of some joint cluster."""
    joint_membership: dict[str, int] = (
        _joint_cluster_lookup()
    )
    total = 0
    consistent = 0
    for k in CorpusKind:
        for c in corpus_clusters(k.value):
            total += 1
            ids = {
                joint_membership.get(m, -1)
                for m in c.members
            }
            if len(ids) == 1 and -1 not in ids:
                consistent += 1
    if total == 0:
        return 0.0
    return _round(consistent / total)


def total_cross_corpus_pairs() -> int:
    total = 0
    for members in restricted_classes():
        for a, b in itertools.combinations(
            members, 2,
        ):
            if corpus_of(a) != corpus_of(b):
                total += 1
    return total


__all__ = [
    "class_stability", "cross_corpus_classes",
    "restricted_classes", "total_cross_corpus_pairs",
    "transfer_accuracy",
]
