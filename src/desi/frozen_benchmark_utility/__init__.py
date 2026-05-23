"""DESi v32.3 - Evolution Utility Analysis (read-only).

A real, measured analysis of whether the evolution phase produced
genuine epistemic utility or merely complexity. Each evolution
feature carries a measured benefit and complexity; the overengineering
detector flags local attractors - features whose complexity exceeds
their measured benefit. Governance is identical and replay is stable.
"""
from __future__ import annotations

from .memory_utility import is_runtime_benefit, memory_utility
from .mutation_efficiency import (
    feature_efficiency, local_attractors, overengineered_features,
    overengineering_detection, overengineering_free,
)
from .novelty_per_runtime import (
    baseline_novelty_per_runtime, distinct_outputs,
    novelty_per_runtime, novelty_per_runtime_gain,
)
from .report import (
    REPORT_VERDICTS, VERDICT_COMPLEXITY, VERDICT_HALT, VERDICT_MIXED,
    VERDICT_UTILITY, V323Report, build_report, build_utility_artifact,
    replay_stability,
)
from .utility import (
    EvolutionFeature, evolution_features, evolution_utility, feature,
    memory_structuring_benefit,
)


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_COMPLEXITY",
    "VERDICT_HALT",
    "VERDICT_MIXED",
    "VERDICT_UTILITY",
    "EvolutionFeature",
    "V323Report",
    "baseline_novelty_per_runtime",
    "build_report",
    "build_utility_artifact",
    "distinct_outputs",
    "evolution_features",
    "evolution_utility",
    "feature",
    "feature_efficiency",
    "is_runtime_benefit",
    "local_attractors",
    "memory_structuring_benefit",
    "memory_utility",
    "novelty_per_runtime",
    "novelty_per_runtime_gain",
    "overengineered_features",
    "overengineering_detection",
    "overengineering_free",
    "replay_stability",
]
