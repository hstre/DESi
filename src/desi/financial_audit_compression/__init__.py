"""DESi v15.3 - Audit Search Compression (DAX
retrospective, read-only).

Compresses the brute-force audit search space by
spending a limited exploration budget on the
highest-priority cells and recovering redundant
pool members from their representative - while
preserving every critical signal. Never concludes
fraud, never rates, never advises. Post-hoc
outcomes are validation labels only.
"""
from __future__ import annotations

from .audit_priority import (
    CRITICAL_THRESHOLD, AuditCell, audit_universe,
    critical_cells, universe_size,
)
from .compression import (
    critical_signal_preservation,
    false_suppression_rate, preserved_critical,
    suppressed_critical,
)
from .exploration_budget import (
    BUDGET_FRACTION, audit_search_reduction,
    budget_size, cost_reduction_proxy,
    selected_cells, selected_keys,
)
from .report import (
    V153Report, build_compression_artifact,
    build_report, ex_ante_critical_preservation,
)
from .risk_ranking import (
    RankedCell, cell_priority, ranked_cells,
    representative,
)


__all__ = [
    "BUDGET_FRACTION",
    "CRITICAL_THRESHOLD",
    "AuditCell",
    "RankedCell",
    "V153Report",
    "audit_search_reduction",
    "audit_universe",
    "budget_size",
    "build_compression_artifact",
    "build_report",
    "cell_priority",
    "cost_reduction_proxy",
    "critical_cells",
    "critical_signal_preservation",
    "ex_ante_critical_preservation",
    "false_suppression_rate",
    "preserved_critical",
    "ranked_cells",
    "representative",
    "selected_cells",
    "selected_keys",
    "suppressed_critical",
    "universe_size",
]
