"""DESi v15.1 - Longitudinal Narrative Drift (DAX
retrospective, read-only).

Tracks how a firm's management narrative evolves
over >=10 years: theme drift, semantic reframing,
consistency with its own past claims, and the
evolution of disclosure bridges. Flags audit-
worthy re-tellings. Never concludes fraud, never
rates, never advises. Post-hoc outcomes are
validation labels only.
"""
from __future__ import annotations

from .bridge_evolution import (
    bridge_evolution_integrity,
    bridge_evolution_integrity_firm,
)
from .lineage import (
    ClaimRecord, claim_lineage,
    claim_lineage_firm, historical_consistency,
    historical_consistency_firm,
)
from .report import (
    DriftSignals, FirmDriftVerdict, V151Report,
    build_narrative_drift_artifact, build_report,
    clean_firm_low_drift_rate,
    corpus_priority_label, drift_priority_label,
    drift_priority_score, drift_signals,
    ex_ante_drift_recall, firm_drift_verdicts,
)
from .semantic_shift import (
    semantic_reframing, semantic_reframing_firm,
)
from .trajectory import (
    THEMES, NarrativeTrajectory, NarrativeYear,
    Theme, by_id, claim_fulfilment,
    narrative_drift, narrative_drift_firm,
    trajectories, years,
)


__all__ = [
    "THEMES",
    "ClaimRecord",
    "DriftSignals",
    "FirmDriftVerdict",
    "NarrativeTrajectory",
    "NarrativeYear",
    "Theme",
    "V151Report",
    "bridge_evolution_integrity",
    "bridge_evolution_integrity_firm",
    "build_narrative_drift_artifact",
    "build_report",
    "by_id",
    "claim_fulfilment",
    "claim_lineage",
    "claim_lineage_firm",
    "clean_firm_low_drift_rate",
    "corpus_priority_label",
    "drift_priority_label",
    "drift_priority_score",
    "drift_signals",
    "ex_ante_drift_recall",
    "firm_drift_verdicts",
    "historical_consistency",
    "historical_consistency_firm",
    "narrative_drift",
    "narrative_drift_firm",
    "semantic_reframing",
    "semantic_reframing_firm",
    "trajectories",
    "years",
]
