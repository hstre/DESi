"""v3.99 — divergence/separation metrics over the
perturbed entangled (G+E) vectors.

For every ``(perturbation_kind, magnitude)`` pair
we compute the pairwise ROC AUC against the
``same_family`` label using
``score = -euclidean(perturbed_a, perturbed_b)``.

* ``perturbation_divergence`` - mean |AUC -
  baseline_AUC| across the grid.
* ``separation_rate`` - fraction of cells where
  AUC reaches the SEPARATION_THRESHOLD.
* ``coupling_stability`` - ``1 -
  separation_rate``.
* ``chaos_threshold`` - smallest magnitude across
  any kind that crosses SEPARATION_THRESHOLD; if
  nothing crosses, returns -1.0 (sentinel for
  "no chaos threshold detected").
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass
from functools import lru_cache

from ..entangled.variance import (
    ENTANGLED_FAMILY_IDS,
    entangled_members,
)
from ..field_leakage.distance import euclidean
from ..novel_families import all_family_members
from .perturb import (
    MAGNITUDE_GRID, PERTURBATION_KINDS,
    baseline_vectors, perturbed_vectors,
)


SEPARATION_THRESHOLD: float = 0.70
NO_CHAOS_SENTINEL: float = -1.0


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@lru_cache(maxsize=1)
def _family_lookup() -> dict[str, str]:
    return {
        m: fid
        for fid, ms in all_family_members().items()
        for m in ms
    }


def _pairwise_auc(
    vecs: dict[str, tuple[float, ...]],
) -> float:
    fam = _family_lookup()
    pos: list[float] = []
    neg: list[float] = []
    for a, b in itertools.combinations(
        sorted(vecs), 2,
    ):
        s = -euclidean(vecs[a], vecs[b])
        if fam.get(a) == fam.get(b):
            pos.append(s)
        else:
            neg.append(s)
    if not pos or not neg:
        return 0.5
    wins = 0
    ties = 0
    for sp in pos:
        for sn in neg:
            if sp > sn:
                wins += 1
            elif sp == sn:
                ties += 1
    return _round(
        (wins + 0.5 * ties)
        / (len(pos) * len(neg)),
    )


@lru_cache(maxsize=1)
def baseline_auc() -> float:
    return _pairwise_auc(baseline_vectors())


@dataclass(frozen=True)
class PerturbationOutcome:
    kind: str
    magnitude: float
    auc: float
    auc_delta: float
    separation_achieved: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "kind": self.kind,
            "magnitude": self.magnitude,
            "auc": self.auc,
            "auc_delta": self.auc_delta,
            "separation_achieved":
                self.separation_achieved,
        }


@lru_cache(maxsize=1)
def all_perturbation_outcomes() -> tuple[
    PerturbationOutcome, ...,
]:
    base = baseline_auc()
    out: list[PerturbationOutcome] = []
    for kind in PERTURBATION_KINDS:
        for mag in MAGNITUDE_GRID:
            vecs = perturbed_vectors(kind, mag)
            auc = _pairwise_auc(vecs)
            out.append(PerturbationOutcome(
                kind=kind,
                magnitude=mag,
                auc=auc,
                auc_delta=_round(auc - base),
                separation_achieved=(
                    auc >= SEPARATION_THRESHOLD
                ),
            ))
    return tuple(out)


def perturbation_divergence() -> float:
    base = baseline_auc()
    outs = all_perturbation_outcomes()
    if not outs:
        return 0.0
    total = sum(abs(o.auc - base) for o in outs)
    return _round(total / len(outs))


def separation_rate() -> float:
    outs = all_perturbation_outcomes()
    if not outs:
        return 0.0
    sep = sum(
        1 for o in outs if o.separation_achieved
    )
    return _round(sep / len(outs))


def coupling_stability() -> float:
    return _round(1.0 - separation_rate())


def chaos_threshold() -> float:
    outs = all_perturbation_outcomes()
    seps = [
        o.magnitude for o in outs
        if o.separation_achieved
    ]
    if not seps:
        return NO_CHAOS_SENTINEL
    return _round(min(seps))


__all__ = [
    "NO_CHAOS_SENTINEL",
    "PerturbationOutcome",
    "SEPARATION_THRESHOLD",
    "all_perturbation_outcomes",
    "baseline_auc",
    "chaos_threshold",
    "coupling_stability",
    "perturbation_divergence",
    "separation_rate",
]
