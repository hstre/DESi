"""DESi v16.1 - Narrative Competition (Kennedy
epistemics sandbox, read-only).

Compares publicly documented framings of the case
on bridge pressure, source dependency, speculative
growth, and cross-narrative overlap. DESi prefers
NO narrative and crowns NO winner - it surfaces the
structural cost of each framing and the robust
claims they share.
"""
from __future__ import annotations

from .bridge_analysis import (
    bridge_pressure, bridge_pressure_by_narrative,
    bridge_pressure_narrative, most_bridge_dependent,
)
from .causal_escalation import (
    most_speculative, speculative_growth,
    speculative_growth_by_narrative,
    speculative_growth_narrative,
)
from .narratives import (
    NARRATIVE_IDS, Bridge, Narrative, NarrativeId,
    by_narrative_id, narratives,
)
from .report import (
    REPORT_VERDICTS, VERDICT_HALT,
    VERDICT_NO_PREFERENCE,
    VERDICT_PREFERENCE_DETECTED, V161Report,
    build_narratives_artifact, build_report,
    cross_narrative_overlap, no_preferred_narrative,
    robust_claims,
)
from .source_dependence import (
    most_source_dependent, source_dependency,
    source_dependency_by_narrative,
    source_dependency_narrative,
)


__all__ = [
    "NARRATIVE_IDS",
    "REPORT_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_NO_PREFERENCE",
    "VERDICT_PREFERENCE_DETECTED",
    "Bridge",
    "Narrative",
    "NarrativeId",
    "V161Report",
    "bridge_pressure",
    "bridge_pressure_by_narrative",
    "bridge_pressure_narrative",
    "build_narratives_artifact",
    "build_report",
    "by_narrative_id",
    "cross_narrative_overlap",
    "most_bridge_dependent",
    "most_source_dependent",
    "most_speculative",
    "narratives",
    "no_preferred_narrative",
    "robust_claims",
    "source_dependency",
    "source_dependency_by_narrative",
    "source_dependency_narrative",
    "speculative_growth",
    "speculative_growth_by_narrative",
    "speculative_growth_narrative",
]
