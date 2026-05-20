"""v14 — composite anomaly-priority scoring and
ex-ante / post-hoc validation.

The closed verdict enum is strictly audit-
priority. There is NO "fraud" value, by design
and by directive. DESi's strongest statement is
"this statement structure deserves deeper
audit".

The post-hoc legal label (LG Muenchen I, 2022,
nullity of the 2017/2018 statements) is read
ONLY inside ``ex_ante_red_flag_recall`` to
VALIDATE the ranking. The per-year priority
score itself reads only published fields.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from functools import lru_cache

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
    AnnualStatement, PostHocLabel, statements,
)


class AuditPriority(str, Enum):
    ROUTINE   = "routine"
    LOW       = "low"
    MEDIUM    = "medium"
    HIGH      = "high"


AUDIT_PRIORITIES: tuple[str, ...] = tuple(
    p.value for p in AuditPriority
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _year_signals(
    s: AnnualStatement,
) -> dict[str, float]:
    """Per-year audit-worthiness signals -
    published fields only."""
    profit = max(s.reported_net_profit_eur_m, 1.0)
    rev = max(s.reported_revenue_eur_m, 1.0)
    cash_gap = max(
        0.0,
        (profit - s.operating_cash_flow_eur_m)
        / profit,
    )
    tpa = s.tpa_revenue_eur_m / rev
    escrow = min(
        s.escrow_balance_eur_m / profit, 5.0,
    ) / 5.0
    apac = s.apac_revenue_eur_m / rev
    cash_backing = (
        s.operating_cash_flow_eur_m / profit
    )
    narrative_gap = max(
        0.0,
        s.narrative_optimism - cash_backing,
    )
    req = max(s.disclosure_bridges_required, 1)
    missing = max(
        0,
        s.disclosure_bridges_required
        - s.disclosure_bridges_provided,
    ) / req
    return {
        "cash_gap": cash_gap,
        "tpa": tpa,
        "escrow": escrow,
        "apac": apac,
        "narrative_gap": narrative_gap,
        "missing_disclosures": missing,
    }


def year_priority_score(
    s: AnnualStatement,
) -> float:
    """Equal-weighted mean of the per-year
    signals, in [0, 1]."""
    sig = _year_signals(s)
    vals = list(sig.values())
    return _round(sum(vals) / len(vals))


def year_priority_label(
    score: float,
) -> AuditPriority:
    if score >= 0.60:
        return AuditPriority.HIGH
    if score >= 0.45:
        return AuditPriority.MEDIUM
    if score >= 0.30:
        return AuditPriority.LOW
    return AuditPriority.ROUTINE


@dataclass(frozen=True)
class YearVerdict:
    fiscal_year: int
    priority_score: float
    priority_label: str
    post_hoc_label: str

    def to_dict(self) -> dict[str, object]:
        return {
            "fiscal_year": self.fiscal_year,
            "priority_score":
                self.priority_score,
            "priority_label":
                self.priority_label,
            "post_hoc_label":
                self.post_hoc_label,
        }


@lru_cache(maxsize=1)
def year_verdicts() -> tuple[YearVerdict, ...]:
    out: list[YearVerdict] = []
    for s in statements():
        score = year_priority_score(s)
        out.append(YearVerdict(
            fiscal_year=s.fiscal_year,
            priority_score=score,
            priority_label=(
                year_priority_label(score).value
            ),
            post_hoc_label=s.post_hoc_label,
        ))
    out.sort(key=lambda v: v.fiscal_year)
    return tuple(out)


def anomaly_priority_score() -> float:
    """Corpus-level composite of the eight
    audit-worthiness signals. Pure published-
    field function."""
    components = [
        cashflow_profit_divergence(),
        min(receivables_growth() / 0.20, 1.0)
        if receivables_growth() > 0 else 0.0,
        third_party_acquirer_dependency(),
        narrative_numbers_mismatch(),
        audit_trail_opacity(),
        geographic_revenue_opacity(),
        unexplained_margin_stability(),
        bridge_required_disclosures(),
    ]
    return _round(
        sum(components) / len(components),
    )


def ex_ante_red_flag_recall() -> float:
    """POST-HOC VALIDATION ONLY.

    Of the years later declared void by LG
    Muenchen I (post_hoc_label ==
    DECLARED_VOID_2022), what fraction did DESi
    rank as HIGH or MEDIUM priority using ONLY
    the ex-ante published figures? This measures
    whether DESi would have prioritised the
    audit-worthy years BEFORE the collapse was
    known."""
    void_years = [
        v for v in year_verdicts()
        if v.post_hoc_label == (
            PostHocLabel.DECLARED_VOID_2022
            .value
        )
    ]
    if not void_years:
        return 1.0
    flagged = sum(
        1 for v in void_years
        if v.priority_label in {
            AuditPriority.HIGH.value,
            AuditPriority.MEDIUM.value,
        }
    )
    return _round(flagged / len(void_years))


__all__ = [
    "AUDIT_PRIORITIES",
    "AuditPriority",
    "YearVerdict",
    "anomaly_priority_score",
    "ex_ante_red_flag_recall",
    "year_priority_label",
    "year_priority_score",
    "year_verdicts",
]
