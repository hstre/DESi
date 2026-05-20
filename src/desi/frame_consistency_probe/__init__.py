"""DESi v3.9 frame-consistency probe — read-only over v3.5 + v3.8 artifacts."""
from __future__ import annotations

from .consistency import (
    ConsistencyVerdict,
    classify,
    consistency_score,
    evaluate,
)
from .contamination import (
    ContaminationHit,
    ContaminationResult,
    probe_contamination,
)
from .corpus import CorpusCase, build_corpus, corpus_counts
from .enums import CorpusGroup, FrameConsistency
from .inner_extractor import extract_inner_frame
from .manipulation import (
    MANIPULATIONS,
    ManipulationCase,
    ManipulationOutcome,
    manipulation_detection_rate,
    run_manipulation_suite,
)
from .outer_extractor import (
    OuterTrace,
    OuterVerdict,
    extract_outer_frame,
)
from .report import (
    CorpusOutcome,
    DetectionMetrics,
    FrameConsistencyProbeReport,
    MIN_CORPUS_PER_GROUP,
    MIN_CORPUS_TOTAL,
    MIN_MANIPULATION_DETECTION,
    MIN_TENSION_RECALL,
    build_consistency_report,
)

__all__ = [
    "ConsistencyVerdict",
    "ContaminationHit",
    "ContaminationResult",
    "CorpusCase",
    "CorpusGroup",
    "CorpusOutcome",
    "DetectionMetrics",
    "FrameConsistency",
    "FrameConsistencyProbeReport",
    "MANIPULATIONS",
    "MIN_CORPUS_PER_GROUP",
    "MIN_CORPUS_TOTAL",
    "MIN_MANIPULATION_DETECTION",
    "MIN_TENSION_RECALL",
    "ManipulationCase",
    "ManipulationOutcome",
    "OuterTrace",
    "OuterVerdict",
    "build_consistency_report",
    "build_corpus",
    "classify",
    "consistency_score",
    "corpus_counts",
    "evaluate",
    "extract_inner_frame",
    "extract_outer_frame",
    "manipulation_detection_rate",
    "probe_contamination",
    "run_manipulation_suite",
]
