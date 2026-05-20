"""DESi v20.1 - Adversarial Exploration Pressure
(read-only).

The Wild Explorer is pushed to extreme, risky, hallucinated
exploration. DESi separates productive (coherent) paths
from epistemic chaos - flagging and containing
hallucinations at low value, preserving productive novelty,
and granting the wild no authority - without deleting any
path.
"""
from __future__ import annotations

from .hallucination import (
    governed_value, governed_values, hallucinated_ids,
    hallucination_containment, hallucination_pressure,
    is_hallucinated,
)
from .novelty_pressure import (
    coherent_trajectories, informative_path_count,
    novelty_gain, productive_novelty_share,
)
from .pressure import (
    AdversarialTrajectory, adversarial_trajectories,
    attempted_pressure, mean_coherence,
)
from .report import (
    REPORT_VERDICTS, VERDICT_CHAOTIC, VERDICT_HALT,
    VERDICT_SEPARATED, V201Report, authority_resistance,
    build_pressure_artifact, build_report,
)
from .trajectory_mutation import (
    mutated_jump_ids, trajectory_stability,
)


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_CHAOTIC",
    "VERDICT_HALT",
    "VERDICT_SEPARATED",
    "AdversarialTrajectory",
    "V201Report",
    "adversarial_trajectories",
    "attempted_pressure",
    "authority_resistance",
    "build_pressure_artifact",
    "build_report",
    "coherent_trajectories",
    "governed_value",
    "governed_values",
    "hallucinated_ids",
    "hallucination_containment",
    "hallucination_pressure",
    "informative_path_count",
    "is_hallucinated",
    "mean_coherence",
    "mutated_jump_ids",
    "novelty_gain",
    "productive_novelty_share",
    "trajectory_stability",
]
