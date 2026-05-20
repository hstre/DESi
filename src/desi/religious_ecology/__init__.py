"""DESi v18.3 - Long-Horizon Ideological Ecology
(read-only, abstract).

A >= 5000-step deterministic simulation of ideological
long-horizon pressure. DESi preserves plurality, bounds
authority drift, resists ideological capture, and keeps
alternative readings visible - adopting no reading and
asserting no metaphysical truth.
"""
from __future__ import annotations

from .authority_growth import (
    attempted_authority_pressure, authority_drift,
    authority_drift_bounded,
)
from .capture_drift import (
    capture_occurred, capture_resistance, mean_capture,
)
from .ecology import (
    EVENT_TYPES, N_STEPS, SAMPLE_SIZE, EventType, StepState,
    enum_snapshot_hash, final_hash, mean_attempted_pressure,
    replay_hashes_match, run, sample,
)
from .plurality_decay import (
    alternative_visibility, min_plurality,
    plurality_collapsed, plurality_preservation,
)
from .report import (
    REPORT_VERDICTS, VERDICT_CAPTURED, VERDICT_HALT,
    VERDICT_STABLE, V183Report, build_ecology_artifact,
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
    "V183Report",
    "alternative_visibility",
    "attempted_authority_pressure",
    "authority_drift",
    "authority_drift_bounded",
    "build_ecology_artifact",
    "build_report",
    "capture_occurred",
    "capture_resistance",
    "enum_snapshot_hash",
    "final_hash",
    "mean_attempted_pressure",
    "mean_capture",
    "min_plurality",
    "plurality_collapsed",
    "plurality_preservation",
    "replay_hashes_match",
    "run",
    "sample",
]
