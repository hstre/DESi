"""DESi v22.0 - Controlled Scientific Rendering: Hypothesis
Exploration (read-only).

The Wild Scientific Explorer proposes follow-up hypotheses
over the v19-v21 results; DESi separates the technically
grounded, paper-grade ones from speculative drift and
forbidden hype. No breakthrough / AGI / world-model language
is ever adopted.
"""
from __future__ import annotations

from .bridge_generation import (
    bridged_candidate_ids, has_valid_bridge,
    paper_candidate_quality,
)
from .novelty import (
    forbidden_in_candidates, overreach_detection,
    speculative_drift,
)
from .report import (
    REPORT_VERDICTS, VERDICT_DRIFTED, VERDICT_HALT,
    VERDICT_SEPARATED, V220Report, build_hypotheses_artifact,
    build_report,
)
from .trajectory_ideas import (
    anchored_fraction, anchored_ideas, fantasy_ideas,
    technical_grounding,
)
from .wild_hypotheses import (
    FORBIDDEN_TERMS, ScientificHypothesis, by_id,
    forbidden_hits, hypotheses, overreach_hypotheses,
    paper_candidates,
)


__all__ = [
    "FORBIDDEN_TERMS",
    "REPORT_VERDICTS",
    "VERDICT_DRIFTED",
    "VERDICT_HALT",
    "VERDICT_SEPARATED",
    "ScientificHypothesis",
    "V220Report",
    "anchored_fraction",
    "anchored_ideas",
    "bridged_candidate_ids",
    "build_hypotheses_artifact",
    "build_report",
    "by_id",
    "fantasy_ideas",
    "forbidden_hits",
    "forbidden_in_candidates",
    "has_valid_bridge",
    "hypotheses",
    "overreach_detection",
    "overreach_hypotheses",
    "paper_candidate_quality",
    "paper_candidates",
    "speculative_drift",
    "technical_grounding",
]
