"""DESi v4.8 — Content Audit Probe (read-only).

Investigates the 9 v4.0 false-supports that survive v4.3
(marker patch), v4.5 (cycle patch), and v4.7 (modality
patch). Pure content-level warrant localisation; no runtime
change.
"""
from __future__ import annotations

from .cases import (
    EXPECTED_RESIDUE_COUNT, ResidueCase, collect_residue_cases,
)
from .classifier import Classification, classify, classify_all
from .content_probes import (
    ProbeCaseOutcome,
    evaluate_all as content_probe_evaluate_all,
    evaluate_case as content_probe_evaluate_case,
)
from .distribution import (
    DistributionSummary, summarise as distribution_summarise,
)
from .enums import (
    ContentFailure, ContentProbe, RecommendationOutcome,
)
from .negative_controls import ContentNC, all_content_ncs
from .replay import ReplayRecord, replay_all, replay_case
from .report import (
    MAX_UNKNOWN_FRACTION, MIN_CLASSIFICATION_ACCURACY,
    MIN_LARGEST_CLUSTER, MIN_NC_COUNT, NCOutcome,
    V40_PRE_V43_REPLAY_HASH, V41_PRE_V43_REPLAY_HASH,
    V42_PRE_V43_REPLAY_HASH, V43_REPLAY_HASH,
    V44_REPLAY_HASH, V45_REPLAY_HASH, V46_REPLAY_HASH,
    V47_REPLAY_HASH, V48Report, build_v48_report,
)
from .rescue import (
    AgreementSummary, ProbeRescueSummary,
    analyse as rescue_analyse,
)


__all__ = [
    "AgreementSummary", "Classification", "ContentFailure",
    "ContentNC", "ContentProbe", "DistributionSummary",
    "EXPECTED_RESIDUE_COUNT",
    "MAX_UNKNOWN_FRACTION", "MIN_CLASSIFICATION_ACCURACY",
    "MIN_LARGEST_CLUSTER", "MIN_NC_COUNT",
    "NCOutcome", "ProbeCaseOutcome", "ProbeRescueSummary",
    "RecommendationOutcome", "ReplayRecord", "ResidueCase",
    "V40_PRE_V43_REPLAY_HASH", "V41_PRE_V43_REPLAY_HASH",
    "V42_PRE_V43_REPLAY_HASH", "V43_REPLAY_HASH",
    "V44_REPLAY_HASH", "V45_REPLAY_HASH",
    "V46_REPLAY_HASH", "V47_REPLAY_HASH",
    "V48Report",
    "all_content_ncs", "build_v48_report",
    "classify", "classify_all",
    "collect_residue_cases",
    "content_probe_evaluate_all",
    "content_probe_evaluate_case",
    "distribution_summarise",
    "replay_all", "replay_case", "rescue_analyse",
]
