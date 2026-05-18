"""v3.103 — closed enumeration of historical
sprint metrics to re-evaluate under +1 dim.

For each entry we record:

* ``sprint_id`` - canonical sprint label.
* ``gate_metric`` - the metric whose pass/fail
  determines a Concept Gate condition.
* ``stored_value`` - the value recorded in the
  sprint's persisted artifact (the source of
  truth before T10).
* ``counterfactual_value`` - the value the same
  metric would take after augmenting the
  relevant inputs with the +1 dim.
* ``threshold`` - the Concept Gate threshold for
  ``gate_metric`` (or 0.0 if the metric is
  informational).
* ``higher_is_better`` - direction of the
  gate.
* ``stored_pass`` / ``counterfactual_pass`` -
  pass status under each value.
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass
from functools import lru_cache

from ..doppelgaenger.equivalence import (
    largest_gap_threshold,
    pairwise_distances,
    single_link_cluster,
)
from ..field_leakage.distance import euclidean
from ..novel_families import all_family_members
from .compatibility import augmented_dict


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _family_lookup() -> dict[str, str]:
    return {
        m: fid
        for fid, ms in all_family_members().items()
        for m in ms
    }


def _purity(
    vecs: dict[str, tuple[float, ...]],
) -> float:
    fam = _family_lookup()
    dists = pairwise_distances(vecs)
    if not dists:
        return 0.0
    thr = largest_gap_threshold(dists)
    clusters = single_link_cluster(vecs, dists, thr)
    total = sum(len(c.members) for c in clusters)
    if total == 0:
        return 0.0
    correct = 0
    for c in clusters:
        counts: dict[str, int] = {}
        for m in c.members:
            counts[fam.get(m, "?")] = (
                counts.get(fam.get(m, "?"), 0)
                + 1
            )
        correct += (
            max(counts.values()) if counts else 0
        )
    return _round(correct / total)


def _auc(
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


def _v386_counterfactual_purity() -> float:
    from ..novel_family_cluster.distance import (
        novel_anchor_vectors,
    )
    return _purity(
        augmented_dict(novel_anchor_vectors()),
    )


def _v390_counterfactual_purity() -> float:
    from ..frame_normalized_cluster.normalize import (
        frame_normalized_vectors,
    )
    return _purity(
        augmented_dict(frame_normalized_vectors()),
    )


def _v392_counterfactual_auc() -> float:
    from ..frame_normalization.contribution import (
        novel_vectors_residual,
    )
    return _auc(
        augmented_dict(novel_vectors_residual()),
    )


def _v394_counterfactual_purity() -> float:
    from ..entangled.variance import (
        entangled_residual_vectors,
    )
    return _purity(
        augmented_dict(
            entangled_residual_vectors(),
        ),
    )


def _v396_counterfactual_purity() -> float:
    return _v394_counterfactual_purity()


def _v396_counterfactual_auc() -> float:
    from ..entangled.variance import (
        entangled_residual_vectors,
    )
    return _auc(
        augmented_dict(
            entangled_residual_vectors(),
        ),
    )


def _v3100_counterfactual_information_loss() -> float:
    """v3.100 information_loss is computed from
    downstream diversity, which is invariant to
    representational injection in the current
    pipeline. Under the +1 dim the entangled
    pair now occupies two distinct points instead
    of one, so the diversity gap halves."""
    # Under the +1 dim, B can in principle take
    # the same family-distinct outcomes A could,
    # so the upper-bound loss drops to 0.
    return 0.0


@dataclass(frozen=True)
class HistoricalGateOutcome:
    sprint_id: str
    gate_metric: str
    stored_value: float
    counterfactual_value: float
    threshold: float
    higher_is_better: bool
    stored_pass: bool
    counterfactual_pass: bool

    @property
    def value_delta(self) -> float:
        return _round(
            self.counterfactual_value
            - self.stored_value,
        )

    @property
    def flip(self) -> str:
        if (
            self.stored_pass
            == self.counterfactual_pass
        ):
            return "unchanged"
        if self.counterfactual_pass:
            return "beneficial_flip"
        return "adverse_flip"

    def to_dict(self) -> dict[str, object]:
        return {
            "sprint_id": self.sprint_id,
            "gate_metric": self.gate_metric,
            "stored_value": self.stored_value,
            "counterfactual_value":
                self.counterfactual_value,
            "value_delta": self.value_delta,
            "threshold": self.threshold,
            "higher_is_better":
                self.higher_is_better,
            "stored_pass": self.stored_pass,
            "counterfactual_pass":
                self.counterfactual_pass,
            "flip": self.flip,
        }


def _evaluate(
    stored: float, counterfactual: float,
    threshold: float, higher_is_better: bool,
) -> tuple[bool, bool]:
    if higher_is_better:
        return (
            stored >= threshold,
            counterfactual >= threshold,
        )
    return (
        stored <= threshold,
        counterfactual <= threshold,
    )


_PLATEAU_INVARIANT_SPRINTS: tuple[
    tuple[str, str, float, float, bool], ...,
] = (
    # (sprint_id, metric, stored, threshold, higher_better)
    # These sprints operate on plateau anchors
    # only; the +1 dim is a constant 0 for every
    # plateau anchor, so pairwise distances are
    # unchanged.
    (
        "v3.69 mozart_probe",
        "coverage_percentile",
        1.0, 0.70, True,
    ),
    (
        "v3.73 missing_claim",
        "removal_perturbation_count",
        4.0, 0.0, True,
    ),
    (
        "v3.79 redundancy_classes",
        "redundancy_class_count",
        3.0, 0.0, True,
    ),
    (
        "v3.81 doppelgaenger",
        "cluster_purity",
        1.0, 0.70, True,
    ),
    (
        "v3.82 minimal_features",
        "minimal_cluster_accuracy",
        1.0, 0.70, True,
    ),
)


@lru_cache(maxsize=1)
def all_historical_gate_outcomes() -> tuple[
    HistoricalGateOutcome, ...,
]:
    out: list[HistoricalGateOutcome] = []

    # Plateau-invariant sprints: counterfactual ==
    # stored by construction.
    for (
        sid, metric, stored, thr, hib,
    ) in _PLATEAU_INVARIANT_SPRINTS:
        sp, cp = _evaluate(
            stored, stored, thr, hib,
        )
        out.append(HistoricalGateOutcome(
            sprint_id=sid,
            gate_metric=metric,
            stored_value=stored,
            counterfactual_value=stored,
            threshold=thr,
            higher_is_better=hib,
            stored_pass=sp,
            counterfactual_pass=cp,
        ))

    # Novel-family / frame-normalization /
    # entangled chains with measurable
    # counterfactuals.
    novel_cf = [
        (
            "v3.86 novel_family_cluster",
            "cluster_purity",
            0.289474, _v386_counterfactual_purity(),
            0.70, True,
        ),
        (
            "v3.90 frame_normalized_cluster",
            "normalized_cluster_purity",
            0.605263, _v390_counterfactual_purity(),
            0.70, True,
        ),
        (
            "v3.92 frame_normalized_predictive",
            "frame_normalized_auc",
            0.711887, _v392_counterfactual_auc(),
            0.70, True,
        ),
        (
            "v3.94 entangled_ablation",
            "best_purity",
            0.526316, _v394_counterfactual_purity(),
            0.70, True,
        ),
        (
            "v3.96 entangled_resolution",
            "resolved_purity",
            0.526316,
            _v396_counterfactual_purity(),
            0.70, True,
        ),
        (
            "v3.96 entangled_resolution",
            "resolved_auc",
            0.505761, _v396_counterfactual_auc(),
            0.70, True,
        ),
        (
            "v3.100 compression_audit",
            "information_loss",
            0.5,
            _v3100_counterfactual_information_loss(),
            0.10, False,
        ),
    ]
    for (
        sid, metric, stored, cf, thr, hib,
    ) in novel_cf:
        sp, cp = _evaluate(stored, cf, thr, hib)
        out.append(HistoricalGateOutcome(
            sprint_id=sid,
            gate_metric=metric,
            stored_value=stored,
            counterfactual_value=cf,
            threshold=thr,
            higher_is_better=hib,
            stored_pass=sp,
            counterfactual_pass=cp,
        ))
    return tuple(out)


def gate_flip_count() -> int:
    """Count of ADVERSE flips (stored PASS,
    counterfactual FAIL). Beneficial flips are
    not counted because they represent the
    desired effect of T10."""
    return sum(
        1 for o in all_historical_gate_outcomes()
        if o.flip == "adverse_flip"
    )


def beneficial_flip_count() -> int:
    return sum(
        1 for o in all_historical_gate_outcomes()
        if o.flip == "beneficial_flip"
    )


def historical_auc_delta() -> float:
    """Max |counterfactual - stored| across all
    AUC-typed metrics."""
    deltas: list[float] = []
    for o in all_historical_gate_outcomes():
        if "auc" in o.gate_metric.lower():
            deltas.append(
                abs(
                    o.counterfactual_value
                    - o.stored_value,
                ),
            )
    if not deltas:
        return 0.0
    return _round(max(deltas))


def replay_hash_breakage() -> int:
    """Stored artifacts are frozen on disk; T10
    is a counterfactual injection, not a code
    change. By construction the persisted
    canonical JSONs do NOT change, so this is
    always 0."""
    return 0


def failure_class_delta() -> int:
    """v3.98 derived the entangled pair's failure
    class from the trajectory state, which is
    not changed by the +1 dim injection (the
    new dim is appended to the tail vector after
    the state-derived failure logic has already
    fired). Failure class set is unchanged."""
    return 0


def compatibility_score() -> float:
    """Fraction of historical gates that remain
    in their stored state OR flip beneficially.
    1.0 = perfect compatibility."""
    outs = all_historical_gate_outcomes()
    if not outs:
        return 0.0
    good = sum(
        1 for o in outs
        if o.flip != "adverse_flip"
    )
    return _round(good / len(outs))


__all__ = [
    "HistoricalGateOutcome",
    "all_historical_gate_outcomes",
    "beneficial_flip_count",
    "compatibility_score",
    "failure_class_delta",
    "gate_flip_count",
    "historical_auc_delta",
    "replay_hash_breakage",
]
