"""v3.106 — apply the v3.101 contradiction_type
candidate to each v3.105 hidden entanglement
without modification.

For every entanglement instance (family_a vs
family_b) we:

* collect the member-level 45-d tail vectors
* append contradiction_type(text) as a single
  46th slot
* re-measure pairwise AUC against the
  same_family label.

If contradiction_type yields a constant value on
both families, AUC stays at the no-skill 0.5
baseline.
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass
from functools import lru_cache

from ..field_leakage.distance import (
    euclidean, trajectory_vector,
)
from ..epistemic_trajectory.extractor import (
    extract_all_trajectories,
)
from ..t10_compat.compatibility import (
    contradiction_type_for_text,
)
from ..t10_generalization.census import (
    EntanglementInstance,
    all_entanglement_instances,
    candidate_families,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@lru_cache(maxsize=1)
def _texts_by_id() -> dict[str, str]:
    return {
        t.trajectory_id: t.text
        for t in extract_all_trajectories()
    }


@lru_cache(maxsize=1)
def _vectors_by_id() -> dict[
    str, tuple[float, ...],
]:
    return {
        t.trajectory_id: trajectory_vector(t.states)
        for t in extract_all_trajectories()
    }


@lru_cache(maxsize=1)
def _families_by_id() -> dict[str, str]:
    out: dict[str, str] = {}
    for f in candidate_families():
        for mid in f.member_ids:
            out[mid] = f.family_id
    return out


def _augmented(
    member_ids: tuple[str, ...],
) -> dict[str, tuple[float, ...]]:
    vecs = _vectors_by_id()
    texts = _texts_by_id()
    out: dict[str, tuple[float, ...]] = {}
    for mid in member_ids:
        if mid not in vecs:
            continue
        ct = contradiction_type_for_text(
            texts.get(mid, ""),
        )
        out[mid] = vecs[mid] + (ct,)
    return out


def _baseline(
    member_ids: tuple[str, ...],
) -> dict[str, tuple[float, ...]]:
    vecs = _vectors_by_id()
    return {
        mid: vecs[mid]
        for mid in member_ids
        if mid in vecs
    }


def _pairwise_auc(
    vecs: dict[str, tuple[float, ...]],
    family_a: str, family_b: str,
) -> float:
    fam = _families_by_id()
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


@dataclass(frozen=True)
class TransferOutcome:
    family_a: str
    family_b: str
    baseline_auc: float
    injected_auc: float
    auc_gain: float
    rescued: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "family_a": self.family_a,
            "family_b": self.family_b,
            "baseline_auc": self.baseline_auc,
            "injected_auc": self.injected_auc,
            "auc_gain": self.auc_gain,
            "rescued": self.rescued,
        }


_RESCUE_AUC_THRESHOLD: float = 0.70


@lru_cache(maxsize=1)
def all_transfer_outcomes() -> tuple[
    TransferOutcome, ...,
]:
    fams_by_id = {
        f.family_id: f for f in candidate_families()
    }
    out: list[TransferOutcome] = []
    for inst in all_entanglement_instances():
        a = fams_by_id.get(inst.family_a)
        b = fams_by_id.get(inst.family_b)
        if a is None or b is None:
            continue
        member_ids = tuple(
            sorted(set(a.member_ids + b.member_ids)),
        )
        base = _pairwise_auc(
            _baseline(member_ids),
            inst.family_a, inst.family_b,
        )
        inj = _pairwise_auc(
            _augmented(member_ids),
            inst.family_a, inst.family_b,
        )
        out.append(TransferOutcome(
            family_a=inst.family_a,
            family_b=inst.family_b,
            baseline_auc=base,
            injected_auc=inj,
            auc_gain=_round(inj - base),
            rescued=(
                inj >= _RESCUE_AUC_THRESHOLD
            ),
        ))
    return tuple(out)


__all__ = [
    "TransferOutcome",
    "all_transfer_outcomes",
]
