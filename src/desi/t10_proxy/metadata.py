"""v3.109 — closed metadata-ablation transformer.

Replaces every trajectory id with a sha256-derived
anonymous handle. The transformation:

* strips the corpus prefix (anything before the
  first colon),
* strips the letter prefix and number suffix,
* replaces the whole id with a single
  ``anon:<12-hex-digits>`` token derived from a
  sha256 hash of the ORIGINAL id - so it is
  deterministic across runs but carries no
  semantic information.

Candidates that ONLY look at the id (e.g.,
``corpus_hash`` or ``letter_prefix_hash``) lose
all their discriminating information here.
Candidates that look at the text (e.g.,
``contradiction_type``) are unaffected.
"""
from __future__ import annotations

from functools import lru_cache
from hashlib import sha256

from ..epistemic_trajectory.extractor import (
    extract_all_trajectories,
)


_ANON_PREFIX: str = "anon"


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def anonymize_id(trajectory_id: str) -> str:
    digest = sha256(
        trajectory_id.encode("utf-8"),
    ).hexdigest()[:12]
    return f"{_ANON_PREFIX}:{digest}"


@lru_cache(maxsize=1)
def id_remapping() -> dict[str, str]:
    return {
        t.trajectory_id: anonymize_id(
            t.trajectory_id,
        )
        for t in extract_all_trajectories()
    }


def is_metadata_stripped(
    anon_id: str,
) -> bool:
    return anon_id.startswith(f"{_ANON_PREFIX}:")


__all__ = [
    "anonymize_id",
    "id_remapping",
    "is_metadata_stripped",
]
