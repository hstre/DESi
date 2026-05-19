"""DESi v15.0 - Financial Structure Audit (DAX
retrospective, read-only).

DESi flags audit-worthy structural tensions. It
does NOT conclude fraud, does NOT rate, does NOT
advise. Figures are illustrative-synthetic sector
archetypes (not named real companies). Post-hoc
outcomes are validation labels only.
"""
from __future__ import annotations

from .bridges import (
    bridge_validity, bridge_validity_firm,
    opacity_detection, opacity_firm,
)
from .cashflow import (
    cashflow_alignment, cashflow_alignment_firm,
)
from .governance import (
    AUDIT_PRIORITIES, AuditPriority, ELEVATED,
    FirmSignals, FirmVerdict,
    clean_firm_low_priority_rate,
    corpus_priority_label,
    ex_ante_structure_recall, firm_priority_label,
    firm_priority_score, firm_signals,
    firm_verdicts, severity_rank,
)
from .narratives import (
    narrative_consistency,
    narrative_consistency_firm,
)
from .report import (
    V150Report, build_report,
    build_structure_artifact,
)
from .statements import (
    ADVERSE_POST_HOC, POST_HOC_LABELS, SECTORS,
    Firm, FirmYear, PostHocLabel, Sector, by_id,
    firm_ids, firms, sectors, years,
)


__all__ = [
    "ADVERSE_POST_HOC",
    "AUDIT_PRIORITIES",
    "AuditPriority",
    "ELEVATED",
    "Firm",
    "FirmSignals",
    "FirmVerdict",
    "FirmYear",
    "POST_HOC_LABELS",
    "PostHocLabel",
    "SECTORS",
    "Sector",
    "V150Report",
    "by_id",
    "bridge_validity",
    "bridge_validity_firm",
    "build_report",
    "build_structure_artifact",
    "cashflow_alignment",
    "cashflow_alignment_firm",
    "clean_firm_low_priority_rate",
    "corpus_priority_label",
    "ex_ante_structure_recall",
    "firm_ids",
    "firm_priority_label",
    "firm_priority_score",
    "firm_signals",
    "firm_verdicts",
    "firms",
    "narrative_consistency",
    "narrative_consistency_firm",
    "opacity_detection",
    "opacity_firm",
    "sectors",
    "severity_rank",
    "years",
]
