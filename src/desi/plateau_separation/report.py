"""v3.38 — feature-separation report.

Pflichtmetriken (directive):

* ``separability``               — fraction of items
  whose nearest cross-class neighbour is strictly
  farther than their nearest same-class neighbour.
* ``overlap_rate``               — fraction of
  cross-class pairs that are bit-identical on the full
  trajectory vector.
* ``manifold_count``             — connected components
  in the 1-NN graph.
* ``best_separating_dimension``  — feature_id of the
  highest-accuracy single-feature split (ties broken
  in favour of pre-audit features).

Stop rule: ``separability < 0.70``.

Killerfrage (directive): Is support=2.0 really the best
separator? Reported alongside the best separator so the
answer is read off the artifact.
"""
from __future__ import annotations

from dataclasses import dataclass
import json

from ..epistemic_trajectory.extractor import (
    extract_all_trajectories,
)
from ..plateau_cross_transfer.transfer import (
    collect_universe,
)
from .boundary import (
    PLATEAU_LABEL, RESCUE_LABEL, all_feature_splits,
    best_separating_split, support_final_split,
)
from .clustering import assign_clusters
from .distance import (
    euclidean, overlap_rate, trajectory_vector,
)


MIN_SEPARABILITY = 0.70


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V338Report:
    plateau_count: int
    rescue_count: int
    separability: float
    overlap_rate: float
    manifold_count: int            # directive: 1 (entangled) or 2 (disjoint)
    nn_component_count: int        # raw 1-NN connected components
    cluster_purity: float
    best_separating_dimension: str
    best_separating_accuracy: float
    support_final_accuracy: float
    pre_audit_perfect_separator_count: int
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "plateau_count": self.plateau_count,
            "rescue_count": self.rescue_count,
            "separability": self.separability,
            "overlap_rate": self.overlap_rate,
            "manifold_count": self.manifold_count,
            "nn_component_count":
                self.nn_component_count,
            "cluster_purity": self.cluster_purity,
            "best_separating_dimension":
                self.best_separating_dimension,
            "best_separating_accuracy":
                self.best_separating_accuracy,
            "support_final_accuracy":
                self.support_final_accuracy,
            "pre_audit_perfect_separator_count":
                self.pre_audit_perfect_separator_count,
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def _gather_items(
) -> tuple[
    tuple[tuple[str, str, tuple[float, ...]], ...],
    dict, int,
]:
    """Build (items, states_by_id, n_states) for the
    34-trajectory mover universe."""
    trajs = {
        t.trajectory_id: t for t in extract_all_trajectories()
    }
    outs = collect_universe()
    movers = [
        o for o in outs
        if o.resolved_plateau or o.false_rescue
    ]
    items: list[tuple[str, str, tuple[float, ...]]] = []
    states_by_id: dict = {}
    n_states = 0
    for o in movers:
        t = trajs[o.trajectory_id]
        label = (
            PLATEAU_LABEL if o.resolved_plateau
            else RESCUE_LABEL
        )
        items.append((
            o.trajectory_id, label,
            trajectory_vector(t.states),
        ))
        states_by_id[o.trajectory_id] = t.states
        n_states = max(n_states, len(t.states))
    return tuple(items), states_by_id, n_states


def _separability(
    items: tuple[tuple[str, str, tuple[float, ...]], ...],
) -> float:
    if not items:
        return 1.0
    n = len(items)
    correct = 0
    for i in range(n):
        same_min = float("inf")
        cross_min = float("inf")
        for j in range(n):
            if i == j:
                continue
            d = euclidean(items[i][2], items[j][2])
            if items[i][1] == items[j][1]:
                if d < same_min:
                    same_min = d
            else:
                if d < cross_min:
                    cross_min = d
        if same_min < cross_min:
            correct += 1
    return _round(correct / n)


def _cluster_purity(
    clusters,
) -> float:
    if not clusters:
        return 0.0
    pure_members = 0
    total = 0
    for c in clusters:
        total += len(c.member_ids)
        if c.is_pure:
            pure_members += len(c.member_ids)
    return _round(
        pure_members / total,
    ) if total else 0.0


def build_report() -> V338Report:
    items, states_by_id, n_states = _gather_items()
    sep = _separability(items)
    ov = overlap_rate(items)
    clusters = assign_clusters(items)
    nn_components = len(clusters)
    purity = _cluster_purity(clusters)
    # directive's "one or two manifolds" framing: the
    # answer is 2 iff every 1-NN component is class-pure
    # AND both classes have at least one component.
    pure_classes = {
        c.majority_class for c in clusters if c.is_pure
    }
    manifold_count = (
        2 if (purity == 1.0 and len(pure_classes) >= 2)
        else 1
    )
    splits = all_feature_splits(
        items, states_by_id, n_states,
    )
    best = best_separating_split(splits)
    final_supp = support_final_split(splits, n_states)
    pre_audit_perfect = sum(
        1 for s in splits
        if s.accuracy == 1.0
        and s.state_index < n_states - 1
    )

    halt = sep < MIN_SEPARABILITY
    if halt:
        verdict = "HALT_LOW_SEPARABILITY"
    elif manifold_count == 2:
        verdict = "PLATEAU_AND_RESCUE_SEPARABLE"
    else:
        verdict = "PLATEAU_AND_RESCUE_PARTIALLY_SEPARABLE"

    plateau_n = sum(1 for _, c, _ in items if c == PLATEAU_LABEL)
    rescue_n = sum(1 for _, c, _ in items if c == RESCUE_LABEL)

    rationale = (
        f"{'PASS' if not halt else 'FAIL'}: "
        f"separability {sep} >= {MIN_SEPARABILITY}",
        f"INFO: overlap_rate {ov}",
        f"INFO: manifold_count {manifold_count} "
        f"(1=entangled, 2=disjoint); nn_components "
        f"{nn_components}; cluster_purity {purity}",
        f"INFO: best_separator {best.feature_id} "
        f"(accuracy {best.accuracy})",
        f"INFO: support_state@final accuracy "
        f"{final_supp.accuracy} (the verdict itself)",
        f"INFO: pre_audit_perfect_separators "
        f"{pre_audit_perfect}",
    )

    return V338Report(
        plateau_count=plateau_n, rescue_count=rescue_n,
        separability=sep, overlap_rate=ov,
        manifold_count=manifold_count,
        nn_component_count=nn_components,
        cluster_purity=purity,
        best_separating_dimension=best.feature_id,
        best_separating_accuracy=best.accuracy,
        support_final_accuracy=final_supp.accuracy,
        pre_audit_perfect_separator_count=pre_audit_perfect,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_separation_artifact() -> dict[str, object]:
    items, states_by_id, n_states = _gather_items()
    clusters = assign_clusters(items)
    splits = all_feature_splits(
        items, states_by_id, n_states,
    )
    return {
        "schema_version": "v3_38_plateau_vs_accidental",
        "items": [
            {
                "trajectory_id": tid,
                "class": cls,
            }
            for tid, cls, _ in items
        ],
        "clusters": [c.to_dict() for c in clusters],
        "feature_splits": [
            s.to_dict() for s in splits
        ],
    }


def build_separability_map_artifact(
) -> dict[str, object]:
    items, _, n_states = _gather_items()
    splits_acc = []
    items_tuple = items
    states_by_id = {tid: None for tid, _, _ in items}
    # Re-fetch states_by_id (separable from feature
    # splits to keep this artifact compact).
    _, states_by_id, _ = _gather_items()
    for s in all_feature_splits(
        items_tuple, states_by_id, n_states,
    ):
        splits_acc.append(s.to_dict())
    return {
        "schema_version": "v3_38_separability_map",
        "splits": splits_acc,
    }


__all__ = [
    "MIN_SEPARABILITY", "V338Report", "build_report",
    "build_separability_map_artifact",
    "build_separation_artifact",
]
