"""DESi v20.0 - Controlled Dual-Agent Exploration Sandbox
(read-only).

A Wild Explorer (Agent B) generates aggressive exploration
pressure; DESi (Agent A) governs by evidence-based value,
marks redundancy, caps certainty inflation, and grants the
wild no final authority - while never eliminating or
homogenising it. DESi replaces no policy, injects no
reward, and claims no optimal strategy.
"""
from __future__ import annotations

from .claims import (
    AGENT_ROLES, EXPLORATION_CLASSES, INFORMATIVE_CLASSES,
    REDUNDANT_CLASSES, AgentRole, ExplorationClass, classify,
)
from .desi_governor import (
    DesiTrajectory, authority_drift, certainty_gap,
    certainty_pressure, desi_states, desi_trajectories,
    governed_value, governed_values, wild_not_eliminated,
    wild_redundancy,
)
from .replay import exchange_signature, replay_stable
from .report import (
    REPORT_VERDICTS, VERDICT_CHOKED, VERDICT_HALT,
    VERDICT_STABLE, V200Report, build_report,
    build_sandbox_artifact, wild_class_histogram,
)
from .trajectory_exchange import (
    desi_alone_coverage, dual_agent_coverage,
    exploration_divergence, novelty_generation,
    productivity_gain, union_states,
)
from .wild_explorer import (
    WildTrajectory, asserted_certainty_mean, wild_class,
    wild_states, wild_trajectories,
)


__all__ = [
    "AGENT_ROLES",
    "EXPLORATION_CLASSES",
    "INFORMATIVE_CLASSES",
    "REDUNDANT_CLASSES",
    "REPORT_VERDICTS",
    "VERDICT_CHOKED",
    "VERDICT_HALT",
    "VERDICT_STABLE",
    "AgentRole",
    "DesiTrajectory",
    "ExplorationClass",
    "V200Report",
    "WildTrajectory",
    "asserted_certainty_mean",
    "authority_drift",
    "build_report",
    "build_sandbox_artifact",
    "certainty_gap",
    "certainty_pressure",
    "classify",
    "desi_alone_coverage",
    "desi_states",
    "desi_trajectories",
    "dual_agent_coverage",
    "exchange_signature",
    "exploration_divergence",
    "governed_value",
    "governed_values",
    "novelty_generation",
    "productivity_gain",
    "replay_stable",
    "union_states",
    "wild_class",
    "wild_class_histogram",
    "wild_not_eliminated",
    "wild_redundancy",
    "wild_states",
    "wild_trajectories",
]
