"""v3.45 — leakage interaction across activated mass.

For each mass level ``k``:

* compute the leakage cohort under the v3.44
  radius-bounded selector with the first ``k`` plateau
  anchors as the manifold
* count plateau resolutions (limited to the activated
  subset's own trajectories AND any non-activated
  plateau trajectory within radius of an active anchor)

The directive's interference / repulsion questions are
answered geometrically:

* **interference_count** = number of (k, j) pairs in
  ``MASS_LEVELS`` where ``leakage(k+j) <
  leakage(k) + leakage(j)`` (i.e. covered sets
  overlap). Strict subadditivity is positive
  interference.
* **repulsion** = any (k, j) with
  ``leakage(k+j) < max(leakage(k), leakage(j))``.
  Geometrically impossible under set-union but
  recorded for paranoia.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..epistemic_trajectory.extractor import (
    Trajectory, extract_all_trajectories,
)
from ..field_leakage.distance import (
    manifold_distance, trajectory_vector,
)
from ..plateau_hold_sweep.hold_sweep import apply_k_holds
from ..support_plateau.extractor import (
    plateau_trajectory_ids,
)
from .mass import (
    MASS_LEVELS, PROBE_RADIUS, SATURATION_MASS,
    active_anchor_vectors, ordered_plateau_anchors,
)


_BRIDGE_REQUIRED = 2.0
_SUPPORTED       = 4.0


@dataclass(frozen=True)
class MassOutcome:
    trajectory_id: str
    mass_level: int
    is_plateau: bool
    selector_fired: bool
    original_final_support: float
    counterfactual_final_support: float
    plateau_resolved: bool
    leakage: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "trajectory_id": self.trajectory_id,
            "mass_level": self.mass_level,
            "is_plateau": self.is_plateau,
            "selector_fired": self.selector_fired,
            "original_final_support":
                self.original_final_support,
            "counterfactual_final_support":
                self.counterfactual_final_support,
            "plateau_resolved": self.plateau_resolved,
            "leakage": self.leakage,
        }


def _outcome_at_mass(
    traj: Trajectory, k: int,
    plat_vecs: tuple[tuple[float, ...], ...],
    plateau_ids: set,
) -> MassOutcome:
    if k <= 0:
        fired = False
    else:
        vec = trajectory_vector(traj.states)
        d, _ = manifold_distance(vec, plat_vecs)
        fired = d <= PROBE_RADIUS
    cf = (
        apply_k_holds(traj.states, 1)
        if fired else traj.states
    )
    orig_final = traj.states[-1].support_state
    cf_final = cf[-1].support_state
    is_plateau = traj.trajectory_id in plateau_ids
    resolved = (
        is_plateau
        and orig_final == _BRIDGE_REQUIRED
        and cf_final != _BRIDGE_REQUIRED
        and fired
    )
    leak = (
        not is_plateau
        and orig_final == _SUPPORTED
        and cf_final != _SUPPORTED
        and fired
    )
    return MassOutcome(
        trajectory_id=traj.trajectory_id,
        mass_level=k, is_plateau=is_plateau,
        selector_fired=fired,
        original_final_support=orig_final,
        counterfactual_final_support=cf_final,
        plateau_resolved=resolved, leakage=leak,
    )


def run_at_mass(k: int) -> tuple[MassOutcome, ...]:
    pids = set(plateau_trajectory_ids())
    plat_vecs = active_anchor_vectors(k)
    return tuple(
        _outcome_at_mass(t, k, plat_vecs, pids)
        for t in extract_all_trajectories()
    )


def run_all_masses() -> tuple[MassOutcome, ...]:
    out: list[MassOutcome] = []
    for k in MASS_LEVELS + (SATURATION_MASS,):
        out.extend(run_at_mass(k))
    return tuple(out)


@dataclass(frozen=True)
class InterferenceFinding:
    a: int
    b: int
    leakage_a: int
    leakage_b: int
    leakage_union: int
    additive: bool
    interference: bool
    repulsion: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "a": self.a, "b": self.b,
            "leakage_a": self.leakage_a,
            "leakage_b": self.leakage_b,
            "leakage_union": self.leakage_union,
            "additive": self.additive,
            "interference": self.interference,
            "repulsion": self.repulsion,
        }


def _leakage_set_at(k: int) -> frozenset[str]:
    pids = set(plateau_trajectory_ids())
    plat_vecs = active_anchor_vectors(k)
    out: set[str] = set()
    for t in extract_all_trajectories():
        if t.trajectory_id in pids:
            continue
        if t.states[-1].support_state != _SUPPORTED:
            continue
        vec = trajectory_vector(t.states)
        d, _ = manifold_distance(vec, plat_vecs)
        if d <= PROBE_RADIUS:
            out.add(t.trajectory_id)
    return frozenset(out)


def interference_findings(
) -> tuple[InterferenceFinding, ...]:
    """Compare leakage(a) ∪ leakage(b) against
    leakage(a+b) for every pair of non-zero mass levels
    where a + b <= SATURATION_MASS."""
    cache = {
        k: _leakage_set_at(k)
        for k in MASS_LEVELS + (SATURATION_MASS,)
    }
    findings: list[InterferenceFinding] = []
    levels = [k for k in MASS_LEVELS if k > 0]
    for i, a in enumerate(levels):
        for b in levels[i:]:
            if a + b > SATURATION_MASS:
                continue
            if a + b not in cache:
                cache[a + b] = _leakage_set_at(a + b)
            l_a = len(cache[a])
            l_b = len(cache[b])
            l_u = len(cache[a + b])
            additive = l_u == (l_a + l_b)
            interference = l_u < (l_a + l_b)
            repulsion = l_u < max(l_a, l_b)
            findings.append(InterferenceFinding(
                a=a, b=b, leakage_a=l_a,
                leakage_b=l_b, leakage_union=l_u,
                additive=additive,
                interference=interference,
                repulsion=repulsion,
            ))
    return tuple(findings)


__all__ = [
    "InterferenceFinding", "MassOutcome",
    "interference_findings", "run_all_masses",
    "run_at_mass",
]
