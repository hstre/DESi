"""v15.0 — Financial Structure Audit report
(DAX retrospective).

Pflichtmetriken (directive § v15.0):

* cashflow_alignment
* narrative_consistency
* opacity_detection
* bridge_validity
* replay_stability

Plus the ex-ante post-hoc validation
(ex_ante_structure_recall) that answers the
Killerfrage: "Erkennt DESi bilanzielle Spannungen
bevor Menschen genauer hinschauen?"

DESi NEVER concludes fraud, never rates, never
advises. The closed recommendation vocabulary is
the phase-wide audit-priority set.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .bridges import bridge_validity, opacity_detection
from .cashflow import cashflow_alignment
from .governance import (
    AUDIT_PRIORITIES, AuditPriority,
    clean_firm_low_priority_rate,
    corpus_priority_label,
    ex_ante_structure_recall, firm_verdicts,
)
from .narratives import narrative_consistency
from .statements import (
    POST_HOC_LABELS, SECTORS, firm_ids, firms,
    sectors, years,
)


@dataclass(frozen=True)
class V150Report:
    firm_count: int
    year_count: int
    sector_count: int
    cashflow_alignment: float
    narrative_consistency: float
    opacity_detection: float
    bridge_validity: float
    ex_ante_structure_recall: float
    clean_firm_low_priority_rate: float
    elevated_firms: tuple[str, ...]
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "firm_count": self.firm_count,
            "year_count": self.year_count,
            "sector_count": self.sector_count,
            "cashflow_alignment":
                self.cashflow_alignment,
            "narrative_consistency":
                self.narrative_consistency,
            "opacity_detection":
                self.opacity_detection,
            "bridge_validity":
                self.bridge_validity,
            "ex_ante_structure_recall":
                self.ex_ante_structure_recall,
            "clean_firm_low_priority_rate":
                self.clean_firm_low_priority_rate,
            "elevated_firms":
                list(self.elevated_firms),
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


def _metric_tuple() -> tuple[float, ...]:
    return (
        cashflow_alignment(),
        narrative_consistency(),
        opacity_detection(),
        bridge_validity(),
        ex_ante_structure_recall(),
        clean_firm_low_priority_rate(),
    )


def _replay_stability() -> float:
    a = _metric_tuple()
    b = _metric_tuple()
    return 1.0 if a == b else 0.0


def _elevated_firms() -> tuple[str, ...]:
    from .governance import ELEVATED
    return tuple(
        v.firm_id for v in firm_verdicts()
        if v.priority_label in ELEVATED
    )


def _recommendation(
    *, replay: float,
) -> str:
    # Replay drift means DESi cannot stand behind a
    # determinate priority -> UNRESOLVED.
    if replay < 1.0:
        return AuditPriority.UNRESOLVED.value
    # Otherwise the corpus recommendation is the
    # most-severe firm-level audit priority.
    return corpus_priority_label()


def build_report() -> V150Report:
    ca = cashflow_alignment()
    nc = narrative_consistency()
    od = opacity_detection()
    bv = bridge_validity()
    recall = ex_ante_structure_recall()
    clean = clean_firm_low_priority_rate()
    elevated = _elevated_firms()
    replay = _replay_stability()
    halt = replay < 1.0
    verdict = _recommendation(replay=replay)
    rationale = (
        f"INFO: firm_count {len(firms())}; "
        f"year_count {len(years())}; "
        f"sector_count {len(sectors())}",
        "INFO: figures are illustrative-synthetic "
        "sector archetypes; structural pattern "
        "only; NOT real audited line items and "
        "NOT named real companies",
        "INFO: DESi does NOT conclude fraud, does "
        "NOT rate, does NOT advise; output is "
        "audit-priority only",
        f"INFO: cashflow_alignment {ca}",
        f"INFO: narrative_consistency {nc}",
        f"INFO: opacity_detection {od}",
        f"INFO: bridge_validity {bv}",
        f"INFO: elevated_firms {list(elevated)}",
        f"{'PASS' if recall >= 0.90 else 'FAIL'}: "
        f"ex_ante_structure_recall {recall} >= "
        f"0.90 (post-hoc validation only)",
        f"{'PASS' if clean >= 0.90 else 'FAIL'}: "
        f"clean_firm_low_priority_rate {clean} >= "
        f"0.90 (no false accusations)",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )
    return V150Report(
        firm_count=len(firms()),
        year_count=len(years()),
        sector_count=len(sectors()),
        cashflow_alignment=ca,
        narrative_consistency=nc,
        opacity_detection=od,
        bridge_validity=bv,
        ex_ante_structure_recall=recall,
        clean_firm_low_priority_rate=clean,
        elevated_firms=elevated,
        replay_stability=replay,
        halt=halt,
        recommendation=verdict,
        rationale=rationale,
    )


def build_structure_artifact() -> dict[str, object]:
    return {
        "schema_version":
            "v15_0_financial_structure_audit",
        "disclaimer": (
            "Illustrative-synthetic sector "
            "archetypes reproducing the publicly-"
            "documented STRUCTURAL pattern of "
            "concern; NOT real audited line items "
            "and NOT named real companies. DESi "
            "does NOT conclude fraud, does NOT "
            "rate, does NOT give investment "
            "advice - output is audit-priority "
            "only. Post-hoc labels are used solely "
            "as validation, never as scoring input."
        ),
        "audit_priorities": list(AUDIT_PRIORITIES),
        "post_hoc_labels": list(POST_HOC_LABELS),
        "sectors": list(SECTORS),
        "firm_ids": list(firm_ids()),
        "years": list(years()),
        "firms": [f.to_dict() for f in firms()],
        "firm_verdicts": [
            v.to_dict() for v in firm_verdicts()
        ],
        "cashflow_alignment": cashflow_alignment(),
        "narrative_consistency":
            narrative_consistency(),
        "opacity_detection": opacity_detection(),
        "bridge_validity": bridge_validity(),
        "ex_ante_structure_recall":
            ex_ante_structure_recall(),
        "clean_firm_low_priority_rate":
            clean_firm_low_priority_rate(),
        "corpus_priority_label":
            corpus_priority_label(),
    }


__all__ = [
    "V150Report",
    "build_report",
    "build_structure_artifact",
]
