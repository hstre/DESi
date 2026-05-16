"""DESi v4.2 — External Audit Failure Probe (read-only).

Pure failure localisation. Selects every chain on which the
unmodified ``LogicalAuditor`` returns ``LOGICALLY_SUPPORTED``
under ``CAUSAL_CHAIN`` despite a ground-truth INVALID label,
replays the frozen stack to capture every observable surface
artefact, classifies the case into a closed
``ExternalAuditFailure`` taxonomy, and reports per-cluster
counterfactual reduction + contamination on the existing
benchmarks.
"""
from __future__ import annotations

from .cases import FalseSupportCase, collect_false_support_cases
from .classifier import Classification, classify, classify_all
from .counterfactual import (
    ClusterCounterfactual, evaluate_all as counterfactual_evaluate_all,
    evaluate_cluster as counterfactual_evaluate_cluster,
)
from .distribution import (
    DistributionSummary, summarise as distribution_summarise,
)
from .enums import ExternalAuditFailure, RecommendationOutcome
from .guards import (
    GuardPressure, GuardPressureSummary,
    measure_guard_pressure, summarise as guards_summarise,
)
from .negative_controls import (
    FailureFixture, all_failure_fixtures,
)
from .replay import ReplayRecord, replay_all, replay_case
from .report import (
    EXPECTED_FALSE_SUPPORT_COUNT, MAX_UNKNOWN_FRACTION,
    MIN_CLASSIFICATION_ACCURACY, MIN_FALSE_SUPPORT_CASES,
    MIN_LARGEST_CLUSTER, MIN_NC_COUNT,
    NCClassificationOutcome, V40_REPLAY_HASH, V41_REPLAY_HASH,
    V42Report, build_v42_report,
)


__all__ = [
    "Classification",
    "ClusterCounterfactual",
    "DistributionSummary",
    "EXPECTED_FALSE_SUPPORT_COUNT",
    "ExternalAuditFailure",
    "FailureFixture",
    "FalseSupportCase",
    "GuardPressure",
    "GuardPressureSummary",
    "MAX_UNKNOWN_FRACTION",
    "MIN_CLASSIFICATION_ACCURACY",
    "MIN_FALSE_SUPPORT_CASES",
    "MIN_LARGEST_CLUSTER",
    "MIN_NC_COUNT",
    "NCClassificationOutcome",
    "RecommendationOutcome",
    "ReplayRecord",
    "V40_REPLAY_HASH",
    "V41_REPLAY_HASH",
    "V42Report",
    "all_failure_fixtures",
    "build_v42_report",
    "classify",
    "classify_all",
    "collect_false_support_cases",
    "counterfactual_evaluate_all",
    "counterfactual_evaluate_cluster",
    "distribution_summarise",
    "guards_summarise",
    "measure_guard_pressure",
    "replay_all",
    "replay_case",
]
