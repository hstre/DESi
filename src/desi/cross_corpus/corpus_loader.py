"""v3.53 — corpus loader.

Closed enumeration of the directive's reference corpora
(v2.3, v3.14, v3.15, v3.16) plus per-corpus subset
accessors. Trajectories are partitioned by ID prefix:

* ``V23``  — prefix ``v23``
* ``V314`` — prefix ``v314``
* ``V315`` — prefix ``v315``
* ``V316`` — prefix ``v316`` (includes both
  ``v316-surv`` and ``v316-susp`` sub-corpora)

If a directive-named corpus is empty the loader
returns an empty tuple. The directive requires
documentation, not substitution.
"""
from __future__ import annotations

from enum import Enum
from functools import lru_cache

from ..epistemic_trajectory.extractor import (
    Trajectory, extract_all_trajectories,
)
from ..plateau_specificity_recovery.policy import (
    apply_policy,
)
from ..plateau_specificity_recovery.selector import (
    SelectorKind, fires,
)
from ..support_plateau.extractor import (
    plateau_trajectory_ids,
)


_SUPPORTED = 4.0


class CorpusKind(str, Enum):
    V23  = "v23"
    V314 = "v314"
    V315 = "v315"
    V316 = "v316"


REFERENCE_CORPORA: tuple[str, ...] = tuple(
    k.value for k in CorpusKind
)


def normalised_prefix(trajectory_id: str) -> str:
    """Take the bit before any ':' or '-' so that
    ``v316-susp:A01`` and ``v316-surv:A01`` both map
    to ``v316``."""
    head = trajectory_id.split(":", 1)[0]
    return head.split("-", 1)[0]


def corpus_of(trajectory_id: str) -> str | None:
    p = normalised_prefix(trajectory_id)
    return p if p in REFERENCE_CORPORA else None


@lru_cache(maxsize=None)
def corpus_trajectories(
    corpus: str,
) -> tuple[Trajectory, ...]:
    return tuple(
        t for t in extract_all_trajectories()
        if normalised_prefix(t.trajectory_id) == corpus
    )


@lru_cache(maxsize=None)
def corpus_plateau_anchors(
    corpus: str,
) -> tuple[Trajectory, ...]:
    pids = set(plateau_trajectory_ids())
    return tuple(
        t for t in corpus_trajectories(corpus)
        if t.trajectory_id in pids
    )


@lru_cache(maxsize=None)
def corpus_leakage_trajectories(
    corpus: str,
) -> tuple[Trajectory, ...]:
    """Per-corpus leakage cohort: SUPPORTED trajectories
    that the v3.39 frame_stability_condition would
    audit-withdraw."""
    pids = set(plateau_trajectory_ids())
    sel = SelectorKind.FRAME_STABILITY.value
    out: list[Trajectory] = []
    for t in corpus_trajectories(corpus):
        if t.trajectory_id in pids:
            continue
        if t.states[-1].support_state != _SUPPORTED:
            continue
        if not fires(sel, t.states):
            continue
        cf = apply_policy(t.states, sel)
        if cf[-1].support_state != _SUPPORTED:
            out.append(t)
    return tuple(out)


def corpus_present(corpus: str) -> bool:
    return bool(corpus_trajectories(corpus))


__all__ = [
    "CorpusKind", "REFERENCE_CORPORA",
    "corpus_leakage_trajectories", "corpus_of",
    "corpus_plateau_anchors", "corpus_present",
    "corpus_trajectories", "normalised_prefix",
]
