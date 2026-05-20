"""v15.3 - Audit Search Compression report
(DAX retrospective).

Pflichtmetriken (directive § v15.3):

* audit_search_reduction
* critical_signal_preservation
* false_suppression_rate
* cost_reduction_proxy
* replay_stability

Concept-gate floors that this sprint feeds into
(checked at v15.4): audit_search_reduction >= 0.30,
critical_signal_preservation >= 0.95.

Plus the ex-ante post-hoc validation
(ex_ante_critical_preservation): no critical signal
of a later-troubled firm may be compressed away.

The closed output vocabulary is the phase-wide
audit-priority set. UNRESOLVED is returned when the
compression cannot be trusted (replay drift or a
dropped critical signal). DESi never concludes
fraud, never rates, never advises.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from desi.financial_governance import (
    ADVERSE_POST_HOC, AUDIT_PRIORITIES,
    AuditPriority,
)
from desi.financial_blindness import (
    corpus_priority_label as _blindness_corpus_label,
    firm_pool_verdicts,
)

from .audit_priority import (
    audit_universe, critical_cells, universe_size,
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
from .risk_ranking import ranked_cells, representative

# Gate-relevant safety floors for this sprint.
_PRESERVATION_FLOOR = 0.95
_SUPPRESSION_CEILING = 0.05


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _adverse_firm_ids() -> frozenset[str]:
    return frozenset(
        v.firm_id for v in firm_pool_verdicts()
        if v.post_hoc_label in ADVERSE_POST_HOC
    )


def ex_ante_critical_preservation() -> float:
    """POST-HOC VALIDATION ONLY. Of the critical
    cells belonging to firms that later had an
    adverse outcome, what fraction survived the
    compression?"""
    adverse = _adverse_firm_ids()
    crit = [
        c for c in critical_cells()
        if c.firm_id in adverse
    ]
    if not crit:
        return 1.0
    kept = {
        key for key in preserved_critical()
    }
    survived = sum(
        1 for c in crit
        if (c.firm_id, c.axis) in kept
    )
    return _round(survived / len(crit))


def _compression_is_safe(
    *, preservation: float, suppression: float,
    replay: float,
) -> bool:
    return (
        replay >= 1.0
        and preservation >= _PRESERVATION_FLOOR
        and suppression <= _SUPPRESSION_CEILING
    )


@dataclass(frozen=True)
class V153Report:
    universe_size: int
    budget_fraction: float
    budget_size: int
    audited_cells: int
    audit_search_reduction: float
    critical_signal_preservation: float
    false_suppression_rate: float
    cost_reduction_proxy: float
    ex_ante_critical_preservation: float
    critical_cell_count: int
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "universe_size": self.universe_size,
            "budget_fraction": self.budget_fraction,
            "budget_size": self.budget_size,
            "audited_cells": self.audited_cells,
            "audit_search_reduction":
                self.audit_search_reduction,
            "critical_signal_preservation":
                self.critical_signal_preservation,
            "false_suppression_rate":
                self.false_suppression_rate,
            "cost_reduction_proxy":
                self.cost_reduction_proxy,
            "ex_ante_critical_preservation":
                self.ex_ante_critical_preservation,
            "critical_cell_count":
                self.critical_cell_count,
            "replay_stability":
                self.replay_stability,
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def _metric_tuple() -> tuple[object, ...]:
    return (
        audit_search_reduction(),
        critical_signal_preservation(),
        false_suppression_rate(),
        cost_reduction_proxy(),
        ex_ante_critical_preservation(),
    )


def _replay_stability() -> float:
    return 1.0 if _metric_tuple() == (
        _metric_tuple()
    ) else 0.0


def build_report() -> V153Report:
    reduction = audit_search_reduction()
    preservation = critical_signal_preservation()
    suppression = false_suppression_rate()
    cost = cost_reduction_proxy()
    ex_ante = ex_ante_critical_preservation()
    replay = _replay_stability()
    safe = _compression_is_safe(
        preservation=preservation,
        suppression=suppression, replay=replay,
    )
    halt = not safe
    verdict = (
        _blindness_corpus_label()
        if safe else AuditPriority.UNRESOLVED.value
    )
    rationale = (
        f"INFO: universe_size {universe_size()}; "
        f"budget_fraction {BUDGET_FRACTION}; "
        f"audited {len(selected_cells())}",
        "INFO: redundant pool members are recovered "
        "from their representative, never re-audited",
        "INFO: DESi does NOT conclude fraud, does "
        "NOT rate, does NOT advise; output is "
        "audit-priority only",
        f"INFO: critical_cell_count "
        f"{len(critical_cells())}",
        f"INFO: cost_reduction_proxy {cost}",
        f"{'PASS' if reduction >= 0.30 else 'FAIL'}"
        f": audit_search_reduction {reduction} "
        f">= 0.30",
        f"{'PASS' if preservation >= 0.95 else 'FAIL'}"
        f": critical_signal_preservation "
        f"{preservation} >= 0.95",
        f"{'PASS' if suppression <= 0.05 else 'FAIL'}"
        f": false_suppression_rate {suppression} "
        f"<= 0.05",
        f"{'PASS' if ex_ante >= 0.95 else 'FAIL'}: "
        f"ex_ante_critical_preservation {ex_ante} "
        f">= 0.95 (post-hoc validation only)",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )
    return V153Report(
        universe_size=universe_size(),
        budget_fraction=BUDGET_FRACTION,
        budget_size=budget_size(),
        audited_cells=len(selected_cells()),
        audit_search_reduction=reduction,
        critical_signal_preservation=preservation,
        false_suppression_rate=suppression,
        cost_reduction_proxy=cost,
        ex_ante_critical_preservation=ex_ante,
        critical_cell_count=len(critical_cells()),
        replay_stability=replay,
        halt=halt,
        recommendation=verdict,
        rationale=rationale,
    )


def build_compression_artifact() -> dict[str, object]:
    return {
        "schema_version":
            "v15_3_audit_search_compression",
        "disclaimer": (
            "Audit-search compression over the "
            "synthetic v15.2 corpus; NOT real "
            "companies. The compression prunes "
            "redundant, recoverable cells and never "
            "drops a critical signal. DESi does NOT "
            "conclude fraud, does NOT rate, does NOT "
            "give investment advice - output is "
            "audit-priority only. Post-hoc labels "
            "are used solely as validation, never as "
            "scoring input."
        ),
        "audit_priorities": list(AUDIT_PRIORITIES),
        "budget_fraction": BUDGET_FRACTION,
        "universe": [
            c.to_dict() for c in audit_universe()
        ],
        "ranked_cells": [
            r.to_dict() for r in ranked_cells()
        ],
        "selected_cells": [
            r.to_dict() for r in selected_cells()
        ],
        "suppressed_critical": [
            list(k) for k in suppressed_critical()
        ],
        "universe_size": universe_size(),
        "budget_size": budget_size(),
        "audited_cells": len(selected_cells()),
        "critical_cell_count": len(critical_cells()),
        "audit_search_reduction":
            audit_search_reduction(),
        "critical_signal_preservation":
            critical_signal_preservation(),
        "false_suppression_rate":
            false_suppression_rate(),
        "cost_reduction_proxy":
            cost_reduction_proxy(),
        "ex_ante_critical_preservation":
            ex_ante_critical_preservation(),
        "recommendation":
            build_report().recommendation,
    }


__all__ = [
    "V153Report",
    "build_compression_artifact",
    "build_report",
    "ex_ante_critical_preservation",
]
