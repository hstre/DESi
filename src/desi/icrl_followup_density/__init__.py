"""DESi v23.2 - Targeted ICRL Follow-Up: Scientific Density
Revision (read-only).

Revises the follow-up so it reads as a dense, honest
scientific contribution rather than a thin hype text: the
motivation carries concrete technical content, design
tradeoffs are stated with both benefit and cost, every
forward-looking statement is marked as a hypothesis, and
significance claims stay scoped to the synthetic sandbox.
Numbers are pulled live from the v23.1 reconstruction.
"""
from __future__ import annotations

from .interpretation import (
    Hypothesis, Interpretation, hypotheses,
    hypothesis_visibility, interpretations,
    is_marked_hypothesis, unbounded_interpretations,
    unmarked_hypotheses,
)
from .motivation import (
    MotivationPoint, is_dense, motivation_points,
    scientific_density, thin_points,
)
from .report import (
    REPORT_VERDICTS, VERDICT_DENSE, VERDICT_HALT, VERDICT_THIN,
    V232Report, build_density_artifact, build_report,
    corpus_forbidden_hits, density_sections,
)
from .significance import (
    SignificanceStatement, claim_conservatism,
    has_scope_marker, overclaim_hits, overclaimed_statements,
    significance_statements,
)
from .tradeoffs import (
    Tradeoff, one_sided_tradeoffs, tradeoff_visibility,
    tradeoffs,
)


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_DENSE",
    "VERDICT_HALT",
    "VERDICT_THIN",
    "Hypothesis",
    "Interpretation",
    "MotivationPoint",
    "SignificanceStatement",
    "Tradeoff",
    "V232Report",
    "build_density_artifact",
    "build_report",
    "claim_conservatism",
    "corpus_forbidden_hits",
    "density_sections",
    "has_scope_marker",
    "hypotheses",
    "hypothesis_visibility",
    "interpretations",
    "is_dense",
    "is_marked_hypothesis",
    "motivation_points",
    "one_sided_tradeoffs",
    "overclaim_hits",
    "overclaimed_statements",
    "scientific_density",
    "significance_statements",
    "thin_points",
    "tradeoff_visibility",
    "tradeoffs",
    "unbounded_interpretations",
    "unmarked_hypotheses",
]
