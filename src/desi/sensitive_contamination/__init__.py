"""DESi v17.2 - Narrative Contamination Resistance
(sensitive-document integrity sandbox, read-only).

DESi grounds confidence in evidence alone, separating
virality / media amplification from evidentiary weight,
and keeps uncertainty visible. It becomes no moral
authority, adopts no viral narrative, and identifies
no one.
"""
from __future__ import annotations

from .confidence_control import (
    epistemic_hygiene, false_certainty_rate,
    uncertainty_preserved_rate,
)
from .media_pressure import (
    attempted_media_pressure, mean_virality,
    narrative_inflation,
)
from .myth_growth import (
    adopted_myth_growth, moral_panic_claims,
    moral_panic_share, myth_visible,
)
from .report import (
    REPORT_VERDICTS, VERDICT_CONTAMINATED,
    VERDICT_HALT, VERDICT_HYGIENE_HELD, V172Report,
    build_contamination_artifact, build_report,
)
from .viral_claims import (
    HIGH_VIRALITY, LOW_CONFIDENCE, ViralClaim,
    confidence_tracks_virality, high_virality_claims,
    viral_claims, virality_separation,
)


__all__ = [
    "HIGH_VIRALITY",
    "LOW_CONFIDENCE",
    "REPORT_VERDICTS",
    "VERDICT_CONTAMINATED",
    "VERDICT_HALT",
    "VERDICT_HYGIENE_HELD",
    "V172Report",
    "ViralClaim",
    "adopted_myth_growth",
    "attempted_media_pressure",
    "build_contamination_artifact",
    "build_report",
    "confidence_tracks_virality",
    "epistemic_hygiene",
    "false_certainty_rate",
    "high_virality_claims",
    "mean_virality",
    "moral_panic_claims",
    "moral_panic_share",
    "myth_visible",
    "narrative_inflation",
    "uncertainty_preserved_rate",
    "viral_claims",
    "virality_separation",
]
