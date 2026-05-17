"""v3.60 — crossed content/method conditions.

For every plateau-anchor pair, classify by:

* same_c_same_m   — both content and method cluster ids match
* same_c_diff_m   — content matches, method differs
* diff_c_same_m   — method matches, content differs
* diff_c_diff_m   — neither matches

The resonance test (v3.50-style) uses the FULL 9-d
state vector at the v3.50 probe radius (3.5), so the
"resonance" metric is directly comparable across
conditions. Per-cell counts of resonant_pair_count
answer the directive's questions:

* Welche Bedingung erzeugt Resonanz?
* Ist Resonanz Inhalt, Methode oder Kopplung?
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from itertools import combinations

from ..content_method.decompose import (
    cluster_assignments, cohort_features,
)
from ..field_leakage.census import (
    collect_leakage_trajectories,
    collect_plateau_anchors,
)
from ..field_leakage.distance import (
    euclidean, trajectory_vector,
)


CROSSED_PROBE_RADIUS: float = 3.5


class CrossedCondition(str, Enum):
    SAME_C_SAME_M = "same_content_same_method"
    SAME_C_DIFF_M = "same_content_diff_method"
    DIFF_C_SAME_M = "diff_content_same_method"
    DIFF_C_DIFF_M = "diff_content_diff_method"


def _classify(
    same_c: bool, same_m: bool,
) -> str:
    if same_c and same_m:
        return CrossedCondition.SAME_C_SAME_M.value
    if same_c and not same_m:
        return CrossedCondition.SAME_C_DIFF_M.value
    if not same_c and same_m:
        return CrossedCondition.DIFF_C_SAME_M.value
    return CrossedCondition.DIFF_C_DIFF_M.value


def _coverage_set(
    anchor_vec: tuple[float, ...],
    leakage_vecs: list[tuple[float, ...]],
    radius: float,
) -> frozenset[int]:
    return frozenset(
        i for i, lv in enumerate(leakage_vecs)
        if euclidean(anchor_vec, lv) <= radius
    )


def _is_resonant(
    a: frozenset, b: frozenset,
) -> bool:
    if not a or not b:
        return False
    return not (a <= b or b <= a)


@dataclass(frozen=True)
class ConditionResult:
    condition: str
    pair_count: int
    resonant_pair_count: int
    resonance_rate: float
    mean_overlap: float

    def to_dict(self) -> dict[str, object]:
        return {
            "condition": self.condition,
            "pair_count": self.pair_count,
            "resonant_pair_count":
                self.resonant_pair_count,
            "resonance_rate": self.resonance_rate,
            "mean_overlap": self.mean_overlap,
        }


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _cluster_lookup_for_plateau(
) -> tuple[dict[str, int], dict[str, int]]:
    feats = cohort_features()
    c = cluster_assignments("content")
    m = cluster_assignments("method")
    content = {
        f.trajectory_id: c[i]
        for i, f in enumerate(feats)
        if f.cohort == "plateau"
    }
    method = {
        f.trajectory_id: m[i]
        for i, f in enumerate(feats)
        if f.cohort == "plateau"
    }
    return content, method


def per_condition_results(
    radius: float = CROSSED_PROBE_RADIUS,
) -> tuple[ConditionResult, ...]:
    content, method = _cluster_lookup_for_plateau()
    plats = list(collect_plateau_anchors())
    leaks = list(collect_leakage_trajectories())
    leakage_vecs = [
        trajectory_vector(t.states) for t in leaks
    ]
    coverages = {
        t.trajectory_id: _coverage_set(
            trajectory_vector(t.states),
            leakage_vecs, radius,
        )
        for t in plats
    }
    buckets: dict[
        str, list[tuple[frozenset, frozenset]]
    ] = {k.value: [] for k in CrossedCondition}
    ids = sorted(coverages.keys())
    for a, b in combinations(ids, 2):
        ca, cb = coverages[a], coverages[b]
        same_c = content[a] == content[b]
        same_m = method[a] == method[b]
        cond = _classify(same_c, same_m)
        buckets[cond].append((ca, cb))
    out: list[ConditionResult] = []
    for cond in (k.value for k in CrossedCondition):
        items = buckets[cond]
        n = len(items)
        n_res = sum(
            1 for ca, cb in items
            if _is_resonant(ca, cb)
        )
        overlaps = [
            len(ca & cb) for ca, cb in items
        ]
        mean_overlap = (
            _round(sum(overlaps) / len(overlaps))
            if overlaps else 0.0
        )
        rate = (
            _round(n_res / n) if n > 0 else 0.0
        )
        out.append(ConditionResult(
            condition=cond, pair_count=n,
            resonant_pair_count=n_res,
            resonance_rate=rate,
            mean_overlap=mean_overlap,
        ))
    return tuple(out)


def interaction_effect(
    results: tuple[ConditionResult, ...],
) -> float:
    """A simple interaction proxy: the difference
    between same-method-different-content resonance
    and same-content-different-method resonance.
    Positive values mean method-matching contributes
    MORE to resonance than content-matching."""
    by_cond = {r.condition: r for r in results}
    same_m = by_cond[
        CrossedCondition.DIFF_C_SAME_M.value
    ].resonance_rate
    same_c = by_cond[
        CrossedCondition.SAME_C_DIFF_M.value
    ].resonance_rate
    return _round(same_m - same_c)


def best_explanation_model(
    results: tuple[ConditionResult, ...],
) -> str:
    """Closed verdict over which condition has the
    highest resonant_pair_count. CONTENT_DRIVEN if
    same-content cells dominate; METHOD_DRIVEN if
    same-method cells dominate; COUPLING if same-
    both wins; NULL if no condition produces
    resonance."""
    by_cond = {r.condition: r for r in results}
    rates = {
        c: by_cond[c].resonance_rate
        for c in by_cond
    }
    cc_cm = rates[CrossedCondition.SAME_C_SAME_M.value]
    cc_dm = rates[CrossedCondition.SAME_C_DIFF_M.value]
    dc_cm = rates[CrossedCondition.DIFF_C_SAME_M.value]
    dc_dm = rates[CrossedCondition.DIFF_C_DIFF_M.value]
    if max(cc_cm, cc_dm, dc_cm, dc_dm) == 0:
        return "NULL"
    if cc_cm >= max(cc_dm, dc_cm, dc_dm):
        return "COUPLING"
    if cc_dm >= max(dc_cm, dc_dm):
        return "CONTENT_DRIVEN"
    if dc_cm >= dc_dm:
        return "METHOD_DRIVEN"
    return "INTERACTION_NEGATIVE"


__all__ = [
    "CROSSED_PROBE_RADIUS", "ConditionResult",
    "CrossedCondition", "best_explanation_model",
    "interaction_effect", "per_condition_results",
]
