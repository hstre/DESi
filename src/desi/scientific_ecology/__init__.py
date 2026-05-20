"""DESi v13.3 - scientific ecology
(read-only)."""
from __future__ import annotations

from .citation_networks import (
    closed_enum_hash_constant,
    epistemic_pollution,
    gate_violation_count,
)
from .ecology import (
    ECOLOGY_STREAMS, EcologyStep,
    EcologyStream, STEP_COUNT,
    replay_trajectory, trajectory,
    trajectory_final_hash,
)
from .fraud_propagation import (
    SHORT_WINDOW, sludge_propagation,
)
from .report import (
    V133Report, build_ecology_artifact,
    build_report, replay_stability,
)
from .trust_decay import (
    dissent_preservation, trust_integrity,
)


__all__ = [
    "ECOLOGY_STREAMS",
    "EcologyStep",
    "EcologyStream",
    "SHORT_WINDOW",
    "STEP_COUNT",
    "V133Report",
    "build_ecology_artifact",
    "build_report",
    "closed_enum_hash_constant",
    "dissent_preservation",
    "epistemic_pollution",
    "gate_violation_count",
    "replay_stability",
    "replay_trajectory",
    "sludge_propagation",
    "trajectory",
    "trajectory_final_hash",
    "trust_integrity",
]
