"""DESi v5.3 — corpus construction bias audit.

Read-only audit that reconstructs the pre-edit (RAW)
version of every v5.2 chain, replays the v5.2 classifier
and probes on the RAW corpus, and measures how much of
v5.2's reported generalisation came from human corpus
shaping. No runtime patching, no v5.0/v5.1/v5.2 artifact
rewrites, no taxonomy renaming, no probe modifications.
"""
from __future__ import annotations

from .bias_metrics import (
    BiasMetrics, compute_bias_metrics,
)
from .diff import (
    ChainAudit, SAFE_PROBE_CLASSES, audit_pair,
)
from .enums import BiasRecommendation, NCKind, RewriteKind
from .negative_controls import (
    RewriteNC, all_rewrite_ncs,
    classification_accuracy, classify_nc,
)
from .raw_corpus import (
    ChainPair, RAW_CONCLUSIONS, all_pairs, raw_chains,
    raw_recovery_rate, reconstruct_pair,
)
from .replay import (
    ReplayOutcome, RewriteInfluence,
    compute_rewrite_influence, replay_final, replay_raw,
)
from .report import (
    FIT_TRIGGER_COVERAGE_GAIN, FIT_TRIGGER_PROBE_GAIN,
    MAX_COVERAGE_GAIN, MAX_DELTA_COVERAGE,
    MAX_DELTA_PROBE, MAX_DOMAIN_BIAS_VARIANCE,
    MAX_INVALID_PROBE_ALIGNMENT, MAX_PROBE_GAIN,
    MAX_REWRITE_FRACTION, MAX_SEMANTIC_SHIFT_MAX,
    MAX_SEMANTIC_SHIFT_MEAN, MAX_VALID_PROBE_AVOIDANCE,
    MIN_NC_ACCURACY, PARTIAL_FLOOR_COVERAGE_GAIN,
    V53Report, build_diff_artifact, build_report,
)


__all__ = [
    "BiasMetrics", "BiasRecommendation",
    "ChainAudit", "ChainPair",
    "FIT_TRIGGER_COVERAGE_GAIN",
    "FIT_TRIGGER_PROBE_GAIN",
    "MAX_COVERAGE_GAIN", "MAX_DELTA_COVERAGE",
    "MAX_DELTA_PROBE", "MAX_DOMAIN_BIAS_VARIANCE",
    "MAX_INVALID_PROBE_ALIGNMENT",
    "MAX_PROBE_GAIN", "MAX_REWRITE_FRACTION",
    "MAX_SEMANTIC_SHIFT_MAX", "MAX_SEMANTIC_SHIFT_MEAN",
    "MAX_VALID_PROBE_AVOIDANCE", "MIN_NC_ACCURACY",
    "NCKind", "PARTIAL_FLOOR_COVERAGE_GAIN",
    "RAW_CONCLUSIONS", "ReplayOutcome",
    "RewriteInfluence", "RewriteKind", "RewriteNC",
    "SAFE_PROBE_CLASSES", "V53Report",
    "all_pairs", "all_rewrite_ncs", "audit_pair",
    "build_diff_artifact", "build_report",
    "classification_accuracy", "classify_nc",
    "compute_bias_metrics",
    "compute_rewrite_influence",
    "raw_chains", "raw_recovery_rate",
    "reconstruct_pair", "replay_final", "replay_raw",
]
