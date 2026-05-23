"""DESi v3.36 — plateau noise + timing probes."""
from __future__ import annotations

from .noise import (
    NOISE_LEVELS, NoiseOutcome, all_noise_outcomes,
    apply_noise, run_noise_level, simulate_reaudit,
)
from .report import (
    MIN_NOISE_STABILITY, MIN_TIMING_SENSITIVITY,
    V336Report, build_noise_artifact, build_report,
    build_timing_artifact,
)
from .timing import (
    TimingOutcome, TimingPoint, all_timing_outcomes,
    apply_timed_hold, run_timing,
)


__all__ = [
    "MIN_NOISE_STABILITY",
    "MIN_TIMING_SENSITIVITY", "NOISE_LEVELS",
    "NoiseOutcome", "TimingOutcome", "TimingPoint",
    "V336Report", "all_noise_outcomes",
    "all_timing_outcomes", "apply_noise",
    "apply_timed_hold", "build_noise_artifact",
    "build_report", "build_timing_artifact",
    "run_noise_level", "run_timing",
    "simulate_reaudit",
]
