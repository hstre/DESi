"""DESi v4.6 — Warrant Requirement Probe (read-only).

Investigates the 19 v4.0 false-supports that survive both
v4.3 (marker extension) and v4.5 (bidirectional cycle).
Pure warrant localisation; no runtime change. Classifies
each residue case into a closed ``WarrantFailure`` taxonomy,
simulates five counterfactual warrant probes (W1–W5), and
reports per-probe rescue / contamination tradeoffs alongside
cross-probe agreement.
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
    RecommendationOutcome, WarrantFailure, WarrantProbe,
)
from .negative_controls import WarrantNC, all_warrant_ncs
from .replay import ReplayRecord, replay_all, replay_case
from .report import (
    MAX_UNKNOWN_FRACTION, MIN_CLASSIFICATION_ACCURACY,
    MIN_LARGEST_CLUSTER, MIN_NC_COUNT, NCOutcome,
    V40_PRE_V43_REPLAY_HASH, V41_PRE_V43_REPLAY_HASH,
    V42_PRE_V43_REPLAY_HASH, V43_REPLAY_HASH,
    V44_REPLAY_HASH, V45_REPLAY_HASH, V46Report,
    build_v46_report,
)
from .rescue import (
    AgreementSummary, ProbeRescueSummary, analyse as rescue_analyse,
)
from .warrant_probes import (
    ProbeCaseOutcome, evaluate_all as warrant_probe_evaluate_all,
    evaluate_case as warrant_probe_evaluate_case,
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
    "NCOutcome",
    "ProbeCaseOutcome",
    "ProbeRescueSummary",
    "RecommendationOutcome",
    "ReplayRecord",
    "ResidueCase",
    "V40_PRE_V43_REPLAY_HASH",
    "V41_PRE_V43_REPLAY_HASH",
    "V42_PRE_V43_REPLAY_HASH",
    "V43_REPLAY_HASH",
    "V44_REPLAY_HASH",
    "V45_REPLAY_HASH",
    "V46Report",
    "WarrantFailure",
    "WarrantNC",
    "WarrantProbe",
    "all_warrant_ncs",
    "build_v46_report",
    "classify",
    "classify_all",
    "collect_residue_cases",
    "distribution_summarise",
    "replay_all",
    "replay_case",
    "rescue_analyse",
    "warrant_probe_evaluate_all",
    "warrant_probe_evaluate_case",
]
