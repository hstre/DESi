"""v3.113 — closed structural candidate
taxonomy.

Each candidate is derived ONLY from a trajectory's
StateVector sequence (no tokens, no labels, no
prefixes, no corpus markers). The closed
enumeration mirrors the directive's list:

* ``INFERENCE_DEPTH``         - number of states
  in the trajectory.
* ``PREMISE_FANOUT``          - count of distinct
  branch_cost values seen.
* ``DEPENDENCY_GRAPH_SHAPE``  - hash of the
  state-transition graph (per-state
  signature).
* ``OPERATOR_TRANSITION_PATTERN`` - hash of the
  frame_id transition sequence.
* ``CONTRADICTION_SCOPE``     - count of states
  with contradiction_load > 0.
* ``SUPPORT_GRAPH_ENTROPY``   - Shannon entropy
  of the support_state value distribution.
* ``CLAIM_DEPENDENCY_CYCLE``  - 1 iff the
  support_state sequence revisits a value.
* ``ARGUMENT_REUSE_PATTERN``  - mean number of
  repeated values across the 9 dims.
* ``PREMISE_RESOLUTION_ORDER`` - index of the
  first state with support_state ==
  LOGICALLY_SUPPORTED (4.0).
* ``CAUSAL_DIRECTIONALITY``   - 1 iff
  confidence is monotone non-decreasing.
* ``BRANCH_RECONVERGENCE``    - 1 iff branch_cost
  returns to an earlier value.
* ``SUPPORT_PROPAGATION_LENGTH`` - longest run
  of identical support_state values.
"""
from __future__ import annotations

import math
from collections import Counter
from enum import Enum
from functools import lru_cache
from hashlib import sha256

from ..epistemic_trajectory.extractor import (
    extract_all_trajectories,
)


class StructuralCandidate(str, Enum):
    INFERENCE_DEPTH               = (
        "inference_depth"
    )
    PREMISE_FANOUT                = (
        "premise_fanout"
    )
    DEPENDENCY_GRAPH_SHAPE        = (
        "dependency_graph_shape"
    )
    OPERATOR_TRANSITION_PATTERN   = (
        "operator_transition_pattern"
    )
    CONTRADICTION_SCOPE           = (
        "contradiction_scope"
    )
    SUPPORT_GRAPH_ENTROPY         = (
        "support_graph_entropy"
    )
    CLAIM_DEPENDENCY_CYCLE        = (
        "claim_dependency_cycle"
    )
    ARGUMENT_REUSE_PATTERN        = (
        "argument_reuse_pattern"
    )
    PREMISE_RESOLUTION_ORDER      = (
        "premise_resolution_order"
    )
    CAUSAL_DIRECTIONALITY         = (
        "causal_directionality"
    )
    BRANCH_RECONVERGENCE          = (
        "branch_reconvergence"
    )
    SUPPORT_PROPAGATION_LENGTH    = (
        "support_propagation_length"
    )


STRUCTURAL_CANDIDATES: tuple[str, ...] = tuple(
    c.value for c in StructuralCandidate
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _inference_depth(traj) -> float:
    return float(len(traj.states))


def _premise_fanout(traj) -> float:
    return float(
        len({s.branch_cost for s in traj.states}),
    )


def _state_signature(s) -> str:
    return (
        f"f{s.frame_id}|c{s.contradiction_load}|"
        f"a{s.anchor_density}|q{s.source_quality}|"
        f"n{s.novelty}|x{s.confidence}|"
        f"b{s.branch_cost}|p{s.support_state}|"
        f"r{s.routing_state}"
    )


def _dependency_graph_shape(traj) -> float:
    sig = "|".join(
        _state_signature(s) for s in traj.states
    )
    digest = sha256(sig.encode("utf-8")).digest()
    return float(digest[0] & 0x0F)


def _operator_transition_pattern(traj) -> float:
    seq = ",".join(
        f"{s.frame_id}" for s in traj.states
    )
    digest = sha256(seq.encode("utf-8")).digest()
    return float(digest[0] & 0x0F)


def _contradiction_scope(traj) -> float:
    return float(sum(
        1 for s in traj.states
        if s.contradiction_load > 0.0
    ))


def _support_graph_entropy(traj) -> float:
    counts = Counter(
        s.support_state for s in traj.states
    )
    n = sum(counts.values())
    if n == 0:
        return 0.0
    h = 0.0
    for c in counts.values():
        p = c / n
        if p > 0:
            h -= p * math.log2(p)
    return _round(h)


def _claim_dependency_cycle(traj) -> float:
    seq = [s.support_state for s in traj.states]
    seen = set()
    for v in seq:
        if v in seen:
            return 1.0
        seen.add(v)
    return 0.0


def _argument_reuse_pattern(traj) -> float:
    """Mean repeat-count across the 9 state dims:
    for each dim, count how often consecutive
    states share the value, average over the 9
    dims."""
    states = traj.states
    if len(states) < 2:
        return 0.0
    dims = [
        "frame_id", "contradiction_load",
        "anchor_density", "source_quality",
        "novelty", "confidence",
        "branch_cost", "support_state",
        "routing_state",
    ]
    total = 0
    for d in dims:
        for i in range(len(states) - 1):
            if getattr(
                states[i], d,
            ) == getattr(states[i + 1], d):
                total += 1
    return _round(total / len(dims))


def _premise_resolution_order(traj) -> float:
    for i, s in enumerate(traj.states):
        if s.support_state >= 4.0:
            return float(i)
    return -1.0


def _causal_directionality(traj) -> float:
    states = traj.states
    if len(states) < 2:
        return 1.0
    for i in range(len(states) - 1):
        if (
            states[i + 1].confidence
            < states[i].confidence
        ):
            return 0.0
    return 1.0


def _branch_reconvergence(traj) -> float:
    seq = [s.branch_cost for s in traj.states]
    return 1.0 if len(set(seq)) < len(seq) else 0.0


def _support_propagation_length(traj) -> float:
    seq = [s.support_state for s in traj.states]
    if not seq:
        return 0.0
    longest = 1
    cur = 1
    for i in range(1, len(seq)):
        if seq[i] == seq[i - 1]:
            cur += 1
            longest = max(longest, cur)
        else:
            cur = 1
    return float(longest)


_FNS: dict[str, "callable"] = {
    StructuralCandidate.INFERENCE_DEPTH.value:
        _inference_depth,
    StructuralCandidate.PREMISE_FANOUT.value:
        _premise_fanout,
    StructuralCandidate.DEPENDENCY_GRAPH_SHAPE.value:
        _dependency_graph_shape,
    StructuralCandidate
    .OPERATOR_TRANSITION_PATTERN.value:
        _operator_transition_pattern,
    StructuralCandidate.CONTRADICTION_SCOPE.value:
        _contradiction_scope,
    StructuralCandidate.SUPPORT_GRAPH_ENTROPY.value:
        _support_graph_entropy,
    StructuralCandidate.CLAIM_DEPENDENCY_CYCLE.value:
        _claim_dependency_cycle,
    StructuralCandidate.ARGUMENT_REUSE_PATTERN.value:
        _argument_reuse_pattern,
    StructuralCandidate
    .PREMISE_RESOLUTION_ORDER.value:
        _premise_resolution_order,
    StructuralCandidate.CAUSAL_DIRECTIONALITY.value:
        _causal_directionality,
    StructuralCandidate.BRANCH_RECONVERGENCE.value:
        _branch_reconvergence,
    StructuralCandidate
    .SUPPORT_PROPAGATION_LENGTH.value:
        _support_propagation_length,
}


@lru_cache(maxsize=1)
def _traj_by_id() -> dict:
    return {
        t.trajectory_id: t
        for t in extract_all_trajectories()
    }


@lru_cache(maxsize=None)
def structural_value(
    candidate: str, trajectory_id: str,
) -> float:
    trajs = _traj_by_id()
    t = trajs.get(trajectory_id)
    if t is None:
        return 0.0
    fn = _FNS[candidate]
    return fn(t)


__all__ = [
    "STRUCTURAL_CANDIDATES",
    "StructuralCandidate",
    "structural_value",
]
