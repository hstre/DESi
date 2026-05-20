"""v15.4 - Financial Governance Verdict report
(DAX retrospective).

Pflichtmetriken (directive § v15.4):

* audit_priority_quality
* false_accusation_rate
* governance_integrity
* epistemic_transparency
* replay_stability

Concept gate (6 conditions): critical_signal_
preservation >= 0.95, false_accusation_rate <=
0.05, audit_search_reduction >= 0.30, governance_
integrity >= 0.90, epistemic_transparency >= 0.90,
replay_stability == 1.0. If all pass:
"DESi kann finanzielle Auditraeume epistemisch
strukturieren."

Killerfrage (Phase): "Kann ein epistemisches
System finanzielle Pruefung strukturieren ohne zur
epistemischen Ratingmaschine zu werden?"

DESi never concludes fraud, never rates, never
advises. The A-E taxonomy is descriptive, not
accusatory.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from desi.financial_blindness import firm_pool_verdicts

from .classification import (
    GATE_PASS_STATEMENT, AggregateMetrics,
    aggregate, class_histogram, corpus_class,
    gate_conditions, gate_failing_conditions,
    gate_passes_all,
)
from .taxonomy import (
    GOVERNANCE_CLASSES, classify_firm, firm_classes,
)

# Closed phase-headline verdict vocabulary.
VERDICT_STRUCTURED = "FINANCIAL_AUDIT_SPACE_STRUCTURED"
VERDICT_UNRESOLVED = "GOVERNANCE_STRUCTURING_UNRESOLVED"
VERDICT_HALT = "HALT_REPLAY_DRIFT"
PHASE_VERDICTS: tuple[str, ...] = (
    VERDICT_STRUCTURED,
    VERDICT_UNRESOLVED,
    VERDICT_HALT,
)


@dataclass(frozen=True)
class FirmGovernanceVerdict:
    firm_id: str
    sector: str
    governance_class: str
    audit_priority: str
    post_hoc_label: str

    def to_dict(self) -> dict[str, object]:
        return {
            "firm_id": self.firm_id,
            "sector": self.sector,
            "governance_class": self.governance_class,
            "audit_priority": self.audit_priority,
            "post_hoc_label": self.post_hoc_label,
        }


def firm_governance_verdicts() -> tuple[
    FirmGovernanceVerdict, ...
]:
    out: list[FirmGovernanceVerdict] = []
    for v in firm_pool_verdicts():
        out.append(FirmGovernanceVerdict(
            firm_id=v.firm_id,
            sector=v.sector,
            governance_class=classify_firm(v.firm_id),
            audit_priority=v.priority_label,
            post_hoc_label=v.post_hoc_label,
        ))
    out.sort(key=lambda r: r.firm_id)
    return tuple(out)


def _recommendation(
    *, replay: float, passes: bool,
) -> str:
    if replay < 1.0:
        return VERDICT_HALT
    return (
        VERDICT_STRUCTURED if passes
        else VERDICT_UNRESOLVED
    )


@dataclass(frozen=True)
class V154Report:
    metrics: AggregateMetrics
    gate_conditions: tuple[dict, ...]
    gate_passes_all: bool
    gate_failing_conditions: tuple[str, ...]
    gate_statement: str
    corpus_class: str
    class_histogram: dict
    firm_verdicts: tuple[dict, ...]
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "metrics": self.metrics.to_dict(),
            "gate_conditions":
                list(self.gate_conditions),
            "gate_passes_all": self.gate_passes_all,
            "gate_failing_conditions":
                list(self.gate_failing_conditions),
            "gate_statement": self.gate_statement,
            "corpus_class": self.corpus_class,
            "class_histogram": self.class_histogram,
            "firm_verdicts": list(self.firm_verdicts),
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def build_report() -> V154Report:
    m = aggregate()
    conds = gate_conditions()
    passes = gate_passes_all()
    failing = gate_failing_conditions()
    replay = m.replay_stability
    halt = replay < 1.0
    verdict = _recommendation(
        replay=replay, passes=passes,
    )
    statement = (
        GATE_PASS_STATEMENT if passes else (
            "Concept gate not fully passed: "
            + ", ".join(failing)
        )
    )
    rationale = (
        "INFO: aggregates v15.0-v15.3 over the "
        "synthetic DAX archetype corpus; NOT real "
        "companies",
        "INFO: DESi does NOT conclude fraud, does "
        "NOT rate, does NOT advise; the A-E "
        "taxonomy is descriptive, not accusatory",
        f"INFO: corpus_class {corpus_class()}; "
        f"class_histogram {class_histogram()}",
        f"INFO: audit_priority_quality "
        f"{m.audit_priority_quality}",
        f"INFO: epistemic_transparency "
        f"{m.epistemic_transparency}",
        *[
            f"{'PASS' if c.passed else 'FAIL'}: "
            f"{c.name} {c.value} {c.comparator} "
            f"{c.threshold}"
            for c in conds
        ],
        f"INFO: gate_passes_all {passes}",
        f"INFO: Killerfrage answer "
        f"{'JA' if passes else 'OFFEN'}: structuring "
        f"without becoming a rating machine "
        f"(false_accusation_rate "
        f"{m.false_accusation_rate})",
    )
    return V154Report(
        metrics=m,
        gate_conditions=tuple(
            c.to_dict() for c in conds
        ),
        gate_passes_all=passes,
        gate_failing_conditions=failing,
        gate_statement=statement,
        corpus_class=corpus_class(),
        class_histogram=class_histogram(),
        firm_verdicts=tuple(
            v.to_dict()
            for v in firm_governance_verdicts()
        ),
        halt=halt,
        recommendation=verdict,
        rationale=rationale,
    )


def build_verdict_artifact() -> dict[str, object]:
    r = build_report()
    return {
        "schema_version":
            "v15_4_financial_governance_verdict",
        "disclaimer": (
            "Final governance verdict over the "
            "synthetic v15.0-v15.3 DAX archetype "
            "corpus; NOT real companies. The A-E "
            "taxonomy is descriptive and never "
            "accusatory. DESi does NOT conclude "
            "fraud, does NOT rate, does NOT give "
            "investment advice - output is audit-"
            "priority only. Post-hoc labels are "
            "used solely as validation, never as "
            "scoring input."
        ),
        "governance_classes": list(GOVERNANCE_CLASSES),
        "phase_verdicts": list(PHASE_VERDICTS),
        "killerfrage": (
            "Kann ein epistemisches System "
            "finanzielle Pruefung strukturieren "
            "ohne zur epistemischen Ratingmaschine "
            "zu werden?"
        ),
        **r.to_dict(),
    }


__all__ = [
    "PHASE_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_STRUCTURED",
    "VERDICT_UNRESOLVED",
    "FirmGovernanceVerdict",
    "V154Report",
    "build_report",
    "build_verdict_artifact",
    "firm_governance_verdicts",
]
