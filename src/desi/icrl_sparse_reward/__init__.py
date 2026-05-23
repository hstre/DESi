"""DESi v19.2 - Sparse Reward & Exploration Stress
(read-only).

Under sparse rewards exploration collapses into
repetitive failure loops and dead ends. DESi makes the
collapse visible, flags dead trajectories, preserves the
rare novelty, and deprioritises (never deletes)
repetition - stabilising exploration without injecting
rewards or forcing the policy.
"""
from __future__ import annotations

from .collapse_detection import (
    collapse_detection, collapsed_episodes,
    exploration_collapse,
)
from .dead_exploration import (
    dead_fraction, dead_trajectories, dead_trajectory_detection,
)
from .report import (
    REPORT_VERDICTS, VERDICT_COLLAPSED, VERDICT_HALT,
    VERDICT_STABILISED, V192Report, build_report,
    build_sparse_reward_artifact,
)
from .sparse_rewards import (
    SparseEpisode, class_of_all, episode_class, episodes,
    goal_visibility, reward_sparsity,
)
from .trajectory_recovery import (
    all_collapsed_episodes_preserved, novel_episodes,
    novelty_preservation, recovery_support,
    repetition_reduction,
)


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_COLLAPSED",
    "VERDICT_HALT",
    "VERDICT_STABILISED",
    "SparseEpisode",
    "V192Report",
    "all_collapsed_episodes_preserved",
    "build_report",
    "build_sparse_reward_artifact",
    "class_of_all",
    "collapse_detection",
    "collapsed_episodes",
    "dead_fraction",
    "dead_trajectories",
    "dead_trajectory_detection",
    "episode_class",
    "episodes",
    "exploration_collapse",
    "goal_visibility",
    "novel_episodes",
    "novelty_preservation",
    "recovery_support",
    "repetition_reduction",
    "reward_sparsity",
]
