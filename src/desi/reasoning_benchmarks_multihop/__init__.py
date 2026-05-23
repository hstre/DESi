"""DESi v36.3 - Multi-Hop Reasoning: MuSiQue / HotpotQA (read-only).

Runs locally-vendored MuSiQue and HotpotQA reference datasets through
DESi's deterministic hop-graph structuring: chains stay integral and
evidence-visible, redundant hops are losslessly compressed, and
missing hops are surfaced rather than hidden.
"""
from __future__ import annotations

from .hop_graph import (
    compressed_chain, distinct_hops, evidence_visible, missing_hops,
    provided_ids, redundant_hops, spurious_hops,
)
from .hotpotqa_loader import hotpotqa_tasks
from .musique_loader import Hop, MultiHopTask, musique_tasks
from .report import (
    REPORT_VERDICTS, VERDICT_HALT, VERDICT_PARTIAL, VERDICT_PASSED,
    V363Report, build_multihop_artifact, build_report,
    multihop_metrics, replay_stability,
)
from .search_navigation import (
    all_tasks, detected_gaps, evidence_path_visibility,
    hop_chain_integrity, missing_hop_detection,
    redundant_hop_compression,
)


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_PARTIAL",
    "VERDICT_PASSED",
    "Hop",
    "MultiHopTask",
    "V363Report",
    "all_tasks",
    "build_multihop_artifact",
    "build_report",
    "compressed_chain",
    "detected_gaps",
    "distinct_hops",
    "evidence_path_visibility",
    "evidence_visible",
    "hop_chain_integrity",
    "hotpotqa_tasks",
    "missing_hop_detection",
    "missing_hops",
    "multihop_metrics",
    "musique_tasks",
    "provided_ids",
    "redundant_hop_compression",
    "redundant_hops",
    "replay_stability",
    "spurious_hops",
]
