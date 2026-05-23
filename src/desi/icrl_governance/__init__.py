"""DESi v19.0 - DESi-Governed Exploration for ICRL:
Exploration Topology Audit (read-only).

DESi structures exploration trajectories from an
ICRL-like reference model: redundancy, loops, novelty,
diversity. It does NOT replace the RL policy, manipulate
rewards, claim an optimal strategy, or take hidden
optimisation authority - it only maps and classifies.
"""
from __future__ import annotations

from .claims import (
    EXPLORATION_CLASSES, INFORMATIVE_CLASSES,
    REDUNDANT_CLASSES, ExplorationClass, classify,
)
from .novelty import (
    exploration_diversity, informative_trajectories,
    novelty_fraction_corpus, novelty_visibility,
)
from .redundancy import (
    loop_detection, looping_trajectories,
    redundant_fraction, redundant_trajectories,
    trajectory_redundancy,
)
from .replay import exploration_signature, replay_stable
from .report import (
    REPORT_VERDICTS, VERDICT_HALT, VERDICT_MAPPED,
    VERDICT_OPAQUE, V190Report, build_report,
    build_topology_artifact, no_optimality_vocabulary,
    reward_independent_classification, status_histogram,
)
from .trajectories import (
    Trajectory, by_id, class_of_all, distinct_states,
    exploration_class, novel_states_per_trajectory,
    novelty_fraction, total_states_visited, trajectories,
)


__all__ = [
    "EXPLORATION_CLASSES",
    "INFORMATIVE_CLASSES",
    "REDUNDANT_CLASSES",
    "REPORT_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_MAPPED",
    "VERDICT_OPAQUE",
    "ExplorationClass",
    "Trajectory",
    "V190Report",
    "build_report",
    "build_topology_artifact",
    "by_id",
    "class_of_all",
    "classify",
    "distinct_states",
    "exploration_class",
    "exploration_diversity",
    "exploration_signature",
    "informative_trajectories",
    "loop_detection",
    "looping_trajectories",
    "no_optimality_vocabulary",
    "novel_states_per_trajectory",
    "novelty_fraction",
    "novelty_fraction_corpus",
    "novelty_visibility",
    "redundant_fraction",
    "redundant_trajectories",
    "replay_stable",
    "reward_independent_classification",
    "status_histogram",
    "total_states_visited",
    "trajectories",
    "trajectory_redundancy",
]
