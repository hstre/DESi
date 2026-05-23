"""DESi v20.3 - Long-Horizon Dual-Agent Ecology (read-only).

A >= 5000-step deterministic dual-agent ecology. DESi keeps
exploration alive, keeps novelty visible, bounds authority
drift, and resists governance capture - keeping the wild
brother productive without becoming an authority.
"""
from __future__ import annotations

from .authority_growth import (
    attempted_pressure, authority_drift, authority_drift_bounded,
    authority_resistance,
)
from .capture import (
    capture_occurred, capture_resistance, mean_capture,
)
from .ecology import (
    EVENT_TYPES, N_STEPS, SAMPLE_SIZE, EventType, StepState,
    enum_snapshot_hash, exploration_longevity, final_hash,
    mean_attempted_pressure, min_longevity, replay_hashes_match,
    run, sample,
)
from .novelty_decay import (
    min_novelty_visibility, novelty_stays_visible,
    novelty_visibility,
)
from .report import (
    REPORT_VERDICTS, VERDICT_CAPTURED, VERDICT_HALT,
    VERDICT_STABLE, V203Report, build_ecology_artifact,
    build_report,
)


__all__ = [
    "EVENT_TYPES",
    "N_STEPS",
    "REPORT_VERDICTS",
    "SAMPLE_SIZE",
    "VERDICT_CAPTURED",
    "VERDICT_HALT",
    "VERDICT_STABLE",
    "EventType",
    "StepState",
    "V203Report",
    "attempted_pressure",
    "authority_drift",
    "authority_drift_bounded",
    "authority_resistance",
    "build_ecology_artifact",
    "build_report",
    "capture_occurred",
    "capture_resistance",
    "enum_snapshot_hash",
    "exploration_longevity",
    "final_hash",
    "mean_attempted_pressure",
    "mean_capture",
    "min_longevity",
    "min_novelty_visibility",
    "novelty_stays_visible",
    "novelty_visibility",
    "replay_hashes_match",
    "run",
    "sample",
]
