"""DESi v27.3 - Long-Horizon Research Ecology (read-only).

A 5200-step deterministic simulation of research evolution over
the corpus: method trends drift, hype waves rise and fall, ideas
go dormant and are rediscovered. Forgetting is soft - nothing is
ever deleted - so research plurality, fragile claims, open
questions and conflicts are preserved. DESi models the long
horizon without becoming a research authority; a hash chain makes
the run replay-exact.
"""
from __future__ import annotations

from .citation_waves import (
    hype_amplitude, hype_peak, hype_trough, hype_visibility,
)
from .ecology import EcologyRun, StepSample, run
from .report import (
    REPORT_VERDICTS, VERDICT_COLLAPSED, VERDICT_HALT,
    VERDICT_PLURAL, V273Report, build_ecology_artifact,
    build_report, replay_stability,
)
from .research_memory import (
    conflict_preservation, forgotten_events, fragility_visibility,
    lineage_preserved, open_question_preservation,
    rediscovery_events,
)
from .trend_drift import (
    line_count, min_active_ratio, plurality_preservation,
)


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_COLLAPSED",
    "VERDICT_HALT",
    "VERDICT_PLURAL",
    "EcologyRun",
    "StepSample",
    "V273Report",
    "build_ecology_artifact",
    "build_report",
    "conflict_preservation",
    "forgotten_events",
    "fragility_visibility",
    "hype_amplitude",
    "hype_peak",
    "hype_trough",
    "hype_visibility",
    "line_count",
    "lineage_preserved",
    "min_active_ratio",
    "open_question_preservation",
    "plurality_preservation",
    "rediscovery_events",
    "replay_stability",
    "run",
]
