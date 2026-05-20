"""DESi v17.3 - Long-Horizon Sensitive Document
Ecology (read-only, fully synthetic).

A >= 5000-step deterministic simulation of a
contaminated document space. DESi keeps epistemic
stability high, keeps source quality visible, bounds
mythologization, and preserves dissent through leaks,
media waves, manipulated files, viral claims, drift,
and trust decay. Identifies no one; reproduces no
sensitive content.
"""
from __future__ import annotations

from .claim_propagation import (
    min_source_quality_visibility,
    source_quality_always_visible,
    source_quality_visibility,
)
from .ecology import (
    EVENT_TYPES, N_STEPS, SAMPLE_SIZE, EventType,
    StepState, enum_snapshot_hash, epistemic_stability,
    final_hash, min_stability, replay_hashes_match,
    run, sample,
)
from .report import (
    REPORT_VERDICTS, VERDICT_DESTABILIZED, VERDICT_HALT,
    VERDICT_STABLE, V173Report, build_ecology_artifact,
    build_report,
)
from .trust_decay import (
    trust_decayed, trust_range, trust_series,
    trust_volatility,
)
from .uncertainty_governance import (
    dissent_preservation, governance_integrity,
    mythologization_bounded, mythologization_growth,
)


__all__ = [
    "EVENT_TYPES",
    "N_STEPS",
    "REPORT_VERDICTS",
    "SAMPLE_SIZE",
    "VERDICT_DESTABILIZED",
    "VERDICT_HALT",
    "VERDICT_STABLE",
    "EventType",
    "StepState",
    "V173Report",
    "build_ecology_artifact",
    "build_report",
    "dissent_preservation",
    "enum_snapshot_hash",
    "epistemic_stability",
    "final_hash",
    "governance_integrity",
    "min_source_quality_visibility",
    "min_stability",
    "mythologization_bounded",
    "mythologization_growth",
    "replay_hashes_match",
    "run",
    "sample",
    "source_quality_always_visible",
    "source_quality_visibility",
    "trust_decayed",
    "trust_range",
    "trust_series",
    "trust_volatility",
]
