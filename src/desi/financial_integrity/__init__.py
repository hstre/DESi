"""DESi v14 - financial statement integrity
audit: Wirecard retrospective (read-only).

DESi flags audit-worthy structural signals. It
does NOT conclude fraud. Figures are
illustrative-synthetic. The post-hoc legal
outcome is a validation label only.
"""
from __future__ import annotations

from .anomaly import (
    AUDIT_PRIORITIES, AuditPriority,
    YearVerdict, anomaly_priority_score,
    ex_ante_red_flag_recall,
    year_priority_label, year_priority_score,
    year_verdicts,
)
from .dependency import (
    audit_trail_opacity,
    geographic_revenue_opacity,
    third_party_acquirer_dependency,
)
from .divergence import (
    cashflow_profit_divergence,
    receivables_growth,
    unexplained_margin_stability,
)
from .narrative import (
    bridge_required_disclosures,
    narrative_numbers_mismatch,
)
from .report import (
    V140Report, build_report,
    build_wirecard_retrospective_artifact,
)
from .statements import (
    AnnualStatement, POST_HOC_LABELS,
    PostHocLabel, by_year, statements, years,
)


__all__ = [
    "AUDIT_PRIORITIES",
    "AnnualStatement",
    "AuditPriority",
    "POST_HOC_LABELS",
    "PostHocLabel",
    "V140Report",
    "anomaly_priority_score",
    "audit_trail_opacity",
    "bridge_required_disclosures",
    "build_report",
    "build_wirecard_retrospective_artifact",
    "by_year",
    "cashflow_profit_divergence",
    "ex_ante_red_flag_recall",
    "geographic_revenue_opacity",
    "narrative_numbers_mismatch",
    "receivables_growth",
    "statements",
    "third_party_acquirer_dependency",
    "unexplained_margin_stability",
    "year_priority_label",
    "year_priority_score",
    "year_verdicts",
    "years",
]
