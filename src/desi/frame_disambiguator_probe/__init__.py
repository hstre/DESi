"""DESi v3.7 frame-disambiguator probe — read-only over v3.5+v3.6."""
from __future__ import annotations

from .candidates import (
    Candidate,
    CandidateScore,
    generate_candidates,
    score_all,
    score_candidate,
)
from .contamination import (
    ContaminationResult,
    excluded_polysemy_texts,
    probe,
)
from .extractor import (
    CounterCase,
    TargetCase,
    extract_polysemy_targets,
    extract_thermo_counter_set,
)
from .negative_control import NEGATIVE_CONTROLS, MixedCase
from .report import (
    CandidateAssessment,
    FrameDisambiguatorProbeReport,
    NegativeControlOutcome,
    build_disambiguator_report,
)

__all__ = [
    "Candidate",
    "CandidateAssessment",
    "CandidateScore",
    "ContaminationResult",
    "CounterCase",
    "FrameDisambiguatorProbeReport",
    "MixedCase",
    "NEGATIVE_CONTROLS",
    "NegativeControlOutcome",
    "TargetCase",
    "build_disambiguator_report",
    "excluded_polysemy_texts",
    "extract_polysemy_targets",
    "extract_thermo_counter_set",
    "generate_candidates",
    "probe",
    "score_all",
    "score_candidate",
]
