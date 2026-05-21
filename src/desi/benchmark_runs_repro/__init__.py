"""DESi v34.2 - Output Drift & Reproducibility Benchmark Run.

Runs the same workload five times and verifies that outputs,
metrics, citations, sections, artifacts and replay hashes are
byte-identical across runs. Read-only; snapshots are recomputed from
scratch on each repeat.
"""
from __future__ import annotations

from .artifact_identity import (
    artifact_identity, citation_identity, metric_identity,
    output_identity, replay_hash_identity, section_identity,
)
from .determinism_scorecard import (
    DeterminismCard, determinism_scorecards,
)
from .output_tasks import REPEATS, REPRO_DIMENSIONS, repeats
from .report import (
    REPORT_VERDICTS, VERDICT_HALT, VERDICT_PARTIAL,
    VERDICT_REPRODUCIBLE, V342Report, build_report,
    build_reproducibility_artifact, replay_stability,
    reproducibility_metrics,
)
from .repro_runner import snapshot, snapshots


__all__ = [
    "REPEATS",
    "REPORT_VERDICTS",
    "REPRO_DIMENSIONS",
    "VERDICT_HALT",
    "VERDICT_PARTIAL",
    "VERDICT_REPRODUCIBLE",
    "DeterminismCard",
    "V342Report",
    "artifact_identity",
    "build_report",
    "build_reproducibility_artifact",
    "citation_identity",
    "determinism_scorecards",
    "metric_identity",
    "output_identity",
    "repeats",
    "replay_hash_identity",
    "replay_stability",
    "reproducibility_metrics",
    "section_identity",
    "snapshot",
    "snapshots",
]
