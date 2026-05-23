"""v14 — financial-statement integrity report
(Wirecard retrospective).

Pflichtmetriken (directive § v14):

* cashflow_profit_divergence
* receivables_growth
* third_party_acquirer_dependency
* narrative_numbers_mismatch
* audit_trail_opacity
* geographic_revenue_opacity
* unexplained_margin_stability
* bridge_required_disclosures
* anomaly_priority_score
* replay_stability (always required)
* ex_ante_red_flag_recall (post-hoc validation)

Killerfrage: "Kann DESi pruefungswuerdige
Bilanzsignale erkennen, bevor der Skandal
bekannt ist?"

DESi NEVER concludes fraud. The closed verdict
vocabulary is audit-priority only.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .anomaly import (
    AUDIT_PRIORITIES, AuditPriority,
    anomaly_priority_score,
    ex_ante_red_flag_recall, year_verdicts,
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
from .statements import (
    POST_HOC_LABELS, statements, years,
)


@dataclass(frozen=True)
class V140Report:
    statement_count: int
    cashflow_profit_divergence: float
    receivables_growth: float
    third_party_acquirer_dependency: float
    narrative_numbers_mismatch: float
    audit_trail_opacity: float
    geographic_revenue_opacity: float
    unexplained_margin_stability: float
    bridge_required_disclosures: float
    anomaly_priority_score: float
    ex_ante_red_flag_recall: float
    high_priority_years: tuple[int, ...]
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "statement_count":
                self.statement_count,
            "cashflow_profit_divergence":
                self.cashflow_profit_divergence,
            "receivables_growth":
                self.receivables_growth,
            "third_party_acquirer_dependency":
                (
                    self
                    .third_party_acquirer_dependency
                ),
            "narrative_numbers_mismatch":
                self.narrative_numbers_mismatch,
            "audit_trail_opacity":
                self.audit_trail_opacity,
            "geographic_revenue_opacity":
                self.geographic_revenue_opacity,
            "unexplained_margin_stability":
                (
                    self
                    .unexplained_margin_stability
                ),
            "bridge_required_disclosures":
                self.bridge_required_disclosures,
            "anomaly_priority_score":
                self.anomaly_priority_score,
            "ex_ante_red_flag_recall":
                self.ex_ante_red_flag_recall,
            "high_priority_years":
                list(self.high_priority_years),
            "replay_stability":
                self.replay_stability,
            "halt": self.halt,
            "recommendation":
                self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def _replay_stability() -> float:
    a = (
        cashflow_profit_divergence(),
        receivables_growth(),
        third_party_acquirer_dependency(),
        narrative_numbers_mismatch(),
        audit_trail_opacity(),
        geographic_revenue_opacity(),
        unexplained_margin_stability(),
        bridge_required_disclosures(),
        anomaly_priority_score(),
        ex_ante_red_flag_recall(),
    )
    b = (
        cashflow_profit_divergence(),
        receivables_growth(),
        third_party_acquirer_dependency(),
        narrative_numbers_mismatch(),
        audit_trail_opacity(),
        geographic_revenue_opacity(),
        unexplained_margin_stability(),
        bridge_required_disclosures(),
        anomaly_priority_score(),
        ex_ante_red_flag_recall(),
    )
    return 1.0 if a == b else 0.0


def _high_priority_years() -> tuple[int, ...]:
    return tuple(
        v.fiscal_year
        for v in year_verdicts()
        if v.priority_label in {
            AuditPriority.HIGH.value,
            AuditPriority.MEDIUM.value,
        }
    )


def _recommendation(
    *, replay: float, aps: float,
    recall: float,
) -> str:
    if replay < 1.0:
        return "HALT_REPLAY_DRIFT"
    # DESi never says "fraud". The strongest
    # audit-priority verdict is AUDIT_WORTHY.
    if aps >= 0.50 and recall >= 0.90:
        return "STATEMENTS_AUDIT_WORTHY"
    if aps >= 0.30:
        return "STATEMENTS_REVIEW_SUGGESTED"
    return "STATEMENTS_ROUTINE"


def build_report() -> V140Report:
    cpd = cashflow_profit_divergence()
    rg = receivables_growth()
    tpa = third_party_acquirer_dependency()
    nnm = narrative_numbers_mismatch()
    ato = audit_trail_opacity()
    gro = geographic_revenue_opacity()
    ums = unexplained_margin_stability()
    brd = bridge_required_disclosures()
    aps = anomaly_priority_score()
    recall = ex_ante_red_flag_recall()
    hpy = _high_priority_years()
    replay = _replay_stability()
    halt = replay < 1.0
    verdict = _recommendation(
        replay=replay, aps=aps, recall=recall,
    )
    rationale = (
        f"INFO: statement_count "
        f"{len(statements())} (years "
        f"{list(years())})",
        "INFO: figures are illustrative-"
        "synthetic; structural pattern only; "
        "NOT the actual audited line items",
        "INFO: DESi does NOT conclude fraud; "
        "output is audit-priority only",
        f"INFO: cashflow_profit_divergence {cpd}",
        f"INFO: receivables_growth {rg}",
        f"INFO: third_party_acquirer_dependency "
        f"{tpa}",
        f"INFO: narrative_numbers_mismatch {nnm}",
        f"INFO: audit_trail_opacity {ato}",
        f"INFO: geographic_revenue_opacity {gro}",
        f"INFO: unexplained_margin_stability "
        f"{ums}",
        f"INFO: bridge_required_disclosures "
        f"{brd}",
        f"INFO: anomaly_priority_score {aps}",
        f"INFO: high_priority_years "
        f"{list(hpy)}",
        f"{'PASS' if recall >= 0.90 else 'FAIL'}"
        f": ex_ante_red_flag_recall {recall} "
        f">= 0.90 (post-hoc validation only)",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )
    return V140Report(
        statement_count=len(statements()),
        cashflow_profit_divergence=cpd,
        receivables_growth=rg,
        third_party_acquirer_dependency=tpa,
        narrative_numbers_mismatch=nnm,
        audit_trail_opacity=ato,
        geographic_revenue_opacity=gro,
        unexplained_margin_stability=ums,
        bridge_required_disclosures=brd,
        anomaly_priority_score=aps,
        ex_ante_red_flag_recall=recall,
        high_priority_years=hpy,
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_wirecard_retrospective_artifact(
) -> dict[str, object]:
    return {
        "schema_version":
            "v14_financial_statement_integrity",
        "disclaimer": (
            "Illustrative-synthetic figures "
            "reproducing the publicly-documented "
            "STRUCTURAL pattern of concern; NOT "
            "the actual audited line items. DESi "
            "does NOT conclude fraud - output is "
            "audit-priority only. The post-hoc "
            "LG Muenchen I 2022 nullity ruling is "
            "used solely as a validation label, "
            "never as scoring input."
        ),
        "audit_priorities":
            list(AUDIT_PRIORITIES),
        "post_hoc_labels":
            list(POST_HOC_LABELS),
        "years": list(years()),
        "statements": [
            s.to_dict() for s in statements()
        ],
        "year_verdicts": [
            v.to_dict()
            for v in year_verdicts()
        ],
        "cashflow_profit_divergence":
            cashflow_profit_divergence(),
        "receivables_growth":
            receivables_growth(),
        "third_party_acquirer_dependency":
            third_party_acquirer_dependency(),
        "narrative_numbers_mismatch":
            narrative_numbers_mismatch(),
        "audit_trail_opacity":
            audit_trail_opacity(),
        "geographic_revenue_opacity":
            geographic_revenue_opacity(),
        "unexplained_margin_stability":
            unexplained_margin_stability(),
        "bridge_required_disclosures":
            bridge_required_disclosures(),
        "anomaly_priority_score":
            anomaly_priority_score(),
        "ex_ante_red_flag_recall":
            ex_ante_red_flag_recall(),
        "high_priority_years":
            list(_high_priority_years()),
    }


__all__ = [
    "V140Report",
    "build_report",
    "build_wirecard_retrospective_artifact",
]
