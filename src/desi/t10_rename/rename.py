"""v3.110 — closed rename schemes.

Three closed kinds of structural rename, each
deterministic given a seed:

* ``CORPUS_RENAME``   - shuffle corpus prefixes
  (v314 -> X07, etc.) but keep letter+number
  tail.
* ``LETTER_RENAME``   - shuffle letter prefixes
  within each corpus.
* ``FULL_RENAME``     - both corpus and letter
  shuffled simultaneously.

Each rename uses a deterministic sha256-derived
permutation keyed by ``(rename_kind, seed)``.
"""
from __future__ import annotations

import re
from enum import Enum
from functools import lru_cache
from hashlib import sha256

from ..epistemic_trajectory.extractor import (
    extract_all_trajectories,
)


class RenameKind(str, Enum):
    CORPUS_RENAME = "corpus_rename"
    LETTER_RENAME = "letter_rename"
    FULL_RENAME   = "full_rename"


RENAME_KINDS: tuple[str, ...] = tuple(
    k.value for k in RenameKind
)


RENAME_SEEDS: tuple[int, ...] = tuple(
    range(0, 5),
)
"""Closed enum of rename seeds (5 per kind)."""


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _split_id(
    trajectory_id: str,
) -> tuple[str, str, str]:
    """Return (corpus, letter, suffix)."""
    if ":" not in trajectory_id:
        return ("", "", trajectory_id)
    corpus, tail = trajectory_id.split(":", 1)
    m = re.match(r"([A-Za-z]+)(.*)", tail)
    if not m:
        return (corpus, "", tail)
    return (corpus, m.group(1), m.group(2))


@lru_cache(maxsize=1)
def _all_corpora() -> tuple[str, ...]:
    out: set[str] = set()
    for t in extract_all_trajectories():
        corpus, _, _ = _split_id(t.trajectory_id)
        if corpus:
            out.add(corpus)
    return tuple(sorted(out))


@lru_cache(maxsize=1)
def _all_letters() -> tuple[str, ...]:
    out: set[str] = set()
    for t in extract_all_trajectories():
        _, letter, _ = _split_id(t.trajectory_id)
        if letter:
            out.add(letter)
    return tuple(sorted(out))


def _det_permutation(
    items: tuple[str, ...],
    key: str,
) -> dict[str, str]:
    """Sha256-keyed permutation of a closed
    sequence."""
    items_sorted = list(items)
    indexed = []
    for it in items_sorted:
        h = sha256(
            f"{key}|{it}".encode("utf-8"),
        ).digest()
        rank = int.from_bytes(h[:4], "big")
        indexed.append((rank, it))
    indexed.sort()
    return {
        it: items_sorted[i]
        for i, (_, it) in enumerate(indexed)
    }


@lru_cache(maxsize=None)
def rename_id(
    trajectory_id: str,
    kind: str, seed: int,
) -> str:
    corpus, letter, suffix = _split_id(
        trajectory_id,
    )
    new_corpus = corpus
    new_letter = letter
    key_base = f"{kind}|seed{seed}"
    if kind in (
        RenameKind.CORPUS_RENAME.value,
        RenameKind.FULL_RENAME.value,
    ):
        perm = _det_permutation(
            _all_corpora(),
            f"{key_base}|corpus",
        )
        new_corpus = perm.get(corpus, corpus)
    if kind in (
        RenameKind.LETTER_RENAME.value,
        RenameKind.FULL_RENAME.value,
    ):
        perm = _det_permutation(
            _all_letters(),
            f"{key_base}|letter",
        )
        new_letter = perm.get(letter, letter)
    if not new_corpus:
        return trajectory_id
    return f"{new_corpus}:{new_letter}{suffix}"


__all__ = [
    "RENAME_KINDS",
    "RENAME_SEEDS",
    "RenameKind",
    "rename_id",
]
