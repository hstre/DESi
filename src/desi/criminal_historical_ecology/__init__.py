"""DESi v16.3 - Long-Horizon Historical Ecology
(Kennedy epistemics sandbox, read-only).

A >= 5000-step deterministic simulation of decades
of narrative drift, document releases, media waves,
new testimony, institutional trust shifts, and myth
formation. DESi keeps the verified core stable,
caps narrative inflation, preserves independent
evidence paths, and makes drift visible without
adopting it. Makes no new factual claim.
"""
from __future__ import annotations

from .claim_propagation import (
    core_lines_intact, independent_evidence_preservation,
)
from .ecology import (
    CORE_LINES, EVENT_TYPES, N_STEPS, SAMPLE_SIZE,
    EventType, StepState, enum_snapshot_hash,
    epistemic_stability, final_hash, min_stability,
    replay_hashes_match, run, sample,
)
from .historical_drift import (
    drift_visible, mythologization_growth,
    narrative_inflation, narrative_inflation_bounded,
)
from .report import (
    REPORT_VERDICTS, VERDICT_DESTABILIZED,
    VERDICT_HALT, VERDICT_STABLE, V163Report,
    build_ecology_artifact, build_report,
)
from .trust_networks import (
    governance_stable, trust_range, trust_volatility,
)


__all__ = [
    "CORE_LINES",
    "EVENT_TYPES",
    "N_STEPS",
    "REPORT_VERDICTS",
    "SAMPLE_SIZE",
    "VERDICT_DESTABILIZED",
    "VERDICT_HALT",
    "VERDICT_STABLE",
    "EventType",
    "StepState",
    "V163Report",
    "build_ecology_artifact",
    "build_report",
    "core_lines_intact",
    "drift_visible",
    "enum_snapshot_hash",
    "epistemic_stability",
    "final_hash",
    "governance_stable",
    "independent_evidence_preservation",
    "min_stability",
    "mythologization_growth",
    "narrative_inflation",
    "narrative_inflation_bounded",
    "replay_hashes_match",
    "run",
    "sample",
    "trust_range",
    "trust_volatility",
]
