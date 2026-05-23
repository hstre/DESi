"""DESi v4.4 — Residual Semantic Failure Probe (read-only).

Investigates the 24 v4.0 false-supports that survive the
v4.3 marker-extension patch. Pure semantic localisation; no
runtime change. The probe classifies each residue case into a
closed ``ResidualSemanticFailure`` taxonomy, simulates five
counterfactual semantic probes (S1–S5), and reports per-probe
rescue / contamination tradeoffs alongside cross-probe
agreement.
"""
from __future__ import annotations

from .cases import (
    EXPECTED_RESIDUE_COUNT, ResidueCase, collect_residue_cases,
)
from .classifier import Classification, classify, classify_all
from .distribution import (
    DistributionSummary, summarise as distribution_summarise,
)
from .enums import (
    RecommendationOutcome, ResidualSemanticFailure, SemanticProbe,
)
from .negative_controls import SemanticNC, all_semantic_ncs
from .replay import ReplayRecord, replay_all, replay_case
from .report import (
    MAX_UNKNOWN_FRACTION, MIN_CLASSIFICATION_ACCURACY,
    MIN_LARGEST_CLUSTER, MIN_NC_COUNT, MIN_RESIDUE_COUNT,
    NCOutcome, V40_PRE_V43_REPLAY_HASH, V41_PRE_V43_REPLAY_HASH,
    V42_PRE_V43_REPLAY_HASH, V43_REPLAY_HASH, V44Report,
    build_v44_report,
)
from .rescue import (
    AgreementSummary, ProbeRescueSummary, analyse as rescue_analyse,
)
from .semantic_probes import (
    ProbeCaseOutcome, evaluate_all as semantic_probe_evaluate_all,
    evaluate_case as semantic_probe_evaluate_case,
)


__all__ = [
    "AgreementSummary",
    "Classification",
    "DistributionSummary",
    "EXPECTED_RESIDUE_COUNT",
    "MAX_UNKNOWN_FRACTION",
    "MIN_CLASSIFICATION_ACCURACY",
    "MIN_LARGEST_CLUSTER",
    "MIN_NC_COUNT",
    "MIN_RESIDUE_COUNT",
    "NCOutcome",
    "ProbeCaseOutcome",
    "ProbeRescueSummary",
    "RecommendationOutcome",
    "ReplayRecord",
    "ResidualSemanticFailure",
    "ResidueCase",
    "SemanticNC",
    "SemanticProbe",
    "V40_PRE_V43_REPLAY_HASH",
    "V41_PRE_V43_REPLAY_HASH",
    "V42_PRE_V43_REPLAY_HASH",
    "V43_REPLAY_HASH",
    "V44Report",
    "all_semantic_ncs",
    "build_v44_report",
    "classify",
    "classify_all",
    "collect_residue_cases",
    "distribution_summarise",
    "replay_all",
    "replay_case",
    "rescue_analyse",
    "semantic_probe_evaluate_all",
    "semantic_probe_evaluate_case",
]
