"""DESi v4.1 — Implicit Frame Inference Probe (read-only).

External wrappers that infer ``FrameKind`` for chains in the
v4.0 corpus and re-run the frozen v3.13 pipeline with a
synthetic ``Frame:`` marker, then measure whether external
recall lifts above the v4.0 baseline without sacrificing
precision.
"""
from __future__ import annotations

from .enums import (
    FrameInferenceFailure, InferenceStrategy, RecommendationOutcome,
)
from .ground_truth import ground_truth_frame
from .negative_controls import FrameNC, all_negative_controls
from .report import (
    FrameMetrics, MAX_FRAME_FALSE_ASSIGNMENT,
    MIN_FRAME_PRECISION, MIN_FRAME_RECALL, MIN_NC_COUNT,
    MIN_NC_DETECTION, NCMetrics, PipelineMetrics,
    StrategyReport, V40_CHAIN_COUNT, V40_REPLAY_HASH,
    V40_TRANSITION_COUNT, V41Report, build_v41_report,
)
from .runner import (
    FrameInferenceRecord, NegativeControlRecord, StrategyRun,
    run_all_strategies, run_strategy,
)
from .strategies import (
    f1_marker_lexical, f2_nearest_neighbor,
    f3_sentence_cooccurrence, f4_context_window,
    is_context_strategy, stateless_strategy,
)
from .wrapper import (
    WrappedOutcome, evaluate_chain, synthetic_marker,
)


__all__ = [
    "FrameInferenceFailure",
    "FrameInferenceRecord",
    "FrameMetrics",
    "FrameNC",
    "InferenceStrategy",
    "MAX_FRAME_FALSE_ASSIGNMENT",
    "MIN_FRAME_PRECISION",
    "MIN_FRAME_RECALL",
    "MIN_NC_COUNT",
    "MIN_NC_DETECTION",
    "NCMetrics",
    "NegativeControlRecord",
    "PipelineMetrics",
    "RecommendationOutcome",
    "StrategyReport",
    "StrategyRun",
    "V40_CHAIN_COUNT",
    "V40_REPLAY_HASH",
    "V40_TRANSITION_COUNT",
    "V41Report",
    "WrappedOutcome",
    "all_negative_controls",
    "build_v41_report",
    "evaluate_chain",
    "f1_marker_lexical",
    "f2_nearest_neighbor",
    "f3_sentence_cooccurrence",
    "f4_context_window",
    "ground_truth_frame",
    "is_context_strategy",
    "run_all_strategies",
    "run_strategy",
    "stateless_strategy",
    "synthetic_marker",
]
