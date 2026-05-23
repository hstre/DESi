"""DESi v29.0 - Replay Cache Evolution: Baseline Measurement.

Makes DESi's own infrastructure cost explicit. Representative
deterministic rebuild workloads are measured (uncached) as a
recompute count - the reproducible proxy for wall-clock cost -
the cache opportunities are exposed, and artifact hashes are
pinned so a later cache optimisation can be proven byte-identical.
This is measurement only; nothing is changed.
"""
from __future__ import annotations

from .artifact_hashes import (
    all_anchors, anchors_signature, anchors_stable,
    desi_artifact_anchors, workload_anchors,
)
from .baseline import (
    Workload, baseline_recompute_count, baseline_run,
    output_hashes, rebuild, workload_output_hash, workloads,
)
from .metrics import (
    artifact_stability, cache_opportunity_visibility,
    recompute_visibility, replay_stability, runtime_visibility,
)
from .report import (
    REPORT_VERDICTS, VERDICT_HALT, VERDICT_OPAQUE,
    VERDICT_VISIBLE, V290Report, build_baseline_artifact,
    build_report,
)
from .timing import RecomputeCounter, wall_clock


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_OPAQUE",
    "VERDICT_VISIBLE",
    "RecomputeCounter",
    "V290Report",
    "Workload",
    "all_anchors",
    "anchors_signature",
    "anchors_stable",
    "artifact_stability",
    "baseline_recompute_count",
    "baseline_run",
    "build_baseline_artifact",
    "build_report",
    "cache_opportunity_visibility",
    "desi_artifact_anchors",
    "output_hashes",
    "rebuild",
    "recompute_visibility",
    "replay_stability",
    "runtime_visibility",
    "wall_clock",
    "workload_anchors",
    "workload_output_hash",
    "workloads",
]
