"""v14 — Wirecard-retrospective financial-
statement fixture.

CRITICAL HONESTY NOTES
======================
1. The euro figures below are ILLUSTRATIVE
   SYNTHETIC values. They reproduce the
   STRUCTURAL pattern of the publicly-
   documented concerns about Wirecard's
   2015-2018 statements (operating-cashflow vs
   reported-profit divergence, heavy third-
   party-acquirer dependency, escrow / trust-
   account opacity, suspiciously stable margins
   under rapid growth). They are NOT the actual
   audited line items - this sandbox does not
   ingest the real annual reports.

2. The ONLY documented external fact used is the
   post-hoc legal outcome: the Landgericht
   Muenchen I declared the 2017 and 2018 annual
   financial statements NULL AND VOID in 2022.
   That fact lives ONLY in the ``post_hoc_label``
   field and is used SOLELY to validate DESi's
   ex-ante ranking. It is NEVER read by any
   scoring function.

3. DESi NEVER concludes "fraud". The output
   vocabulary is strictly audit-priority:
   "this statement structure deserves deeper
   audit". The closed verdict enum contains no
   fraud / Betrug value.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PostHocLabel(str, Enum):
    """Post-hoc validation labels ONLY. Never
    used as scoring input."""
    DECLARED_VOID_2022     = (
        "declared_void_2022"
    )
    QUESTIONED_NOT_RULED   = (
        "questioned_not_ruled"
    )


POST_HOC_LABELS: tuple[str, ...] = tuple(
    p.value for p in PostHocLabel
)


@dataclass(frozen=True)
class AnnualStatement:
    fiscal_year: int
    is_synthetic_illustrative: bool
    reported_revenue_eur_m: float
    reported_net_profit_eur_m: float
    operating_cash_flow_eur_m: float
    receivables_eur_m: float
    tpa_revenue_eur_m: float
    escrow_balance_eur_m: float
    apac_revenue_eur_m: float
    net_margin: float
    narrative_optimism: float
    disclosure_bridges_required: int
    disclosure_bridges_provided: int
    # Post-hoc ONLY - never an input to scoring.
    post_hoc_label: str

    def to_dict(self) -> dict[str, object]:
        return {
            "fiscal_year": self.fiscal_year,
            "is_synthetic_illustrative":
                self.is_synthetic_illustrative,
            "reported_revenue_eur_m":
                self.reported_revenue_eur_m,
            "reported_net_profit_eur_m":
                self.reported_net_profit_eur_m,
            "operating_cash_flow_eur_m":
                self.operating_cash_flow_eur_m,
            "receivables_eur_m":
                self.receivables_eur_m,
            "tpa_revenue_eur_m":
                self.tpa_revenue_eur_m,
            "escrow_balance_eur_m":
                self.escrow_balance_eur_m,
            "apac_revenue_eur_m":
                self.apac_revenue_eur_m,
            "net_margin": self.net_margin,
            "narrative_optimism":
                self.narrative_optimism,
            "disclosure_bridges_required":
                self.disclosure_bridges_required,
            "disclosure_bridges_provided":
                self.disclosure_bridges_provided,
            "post_hoc_label":
                self.post_hoc_label,
        }


# Illustrative-synthetic figures (eur millions).
# Pattern reproduced from public concern record:
# revenue and reported profit climb steadily,
# operating cash flow lags reported profit by a
# widening gap, receivables grow faster than
# revenue, third-party-acquirer share stays
# dominant, escrow balances balloon, APAC share
# stays high, net margin is suspiciously stable
# despite rapid growth, and disclosure bridges
# are increasingly required but not provided.
_FIXTURE: tuple[AnnualStatement, ...] = (
    AnnualStatement(
        fiscal_year=2015,
        is_synthetic_illustrative=True,
        reported_revenue_eur_m=1000.0,
        reported_net_profit_eur_m=250.0,
        operating_cash_flow_eur_m=180.0,
        receivables_eur_m=300.0,
        tpa_revenue_eur_m=480.0,
        escrow_balance_eur_m=400.0,
        apac_revenue_eur_m=520.0,
        net_margin=0.250,
        narrative_optimism=0.80,
        disclosure_bridges_required=4,
        disclosure_bridges_provided=3,
        post_hoc_label=(
            PostHocLabel.QUESTIONED_NOT_RULED
            .value
        ),
    ),
    AnnualStatement(
        fiscal_year=2016,
        is_synthetic_illustrative=True,
        reported_revenue_eur_m=1300.0,
        reported_net_profit_eur_m=330.0,
        operating_cash_flow_eur_m=210.0,
        receivables_eur_m=470.0,
        tpa_revenue_eur_m=660.0,
        escrow_balance_eur_m=700.0,
        apac_revenue_eur_m=700.0,
        net_margin=0.254,
        narrative_optimism=0.84,
        disclosure_bridges_required=5,
        disclosure_bridges_provided=3,
        post_hoc_label=(
            PostHocLabel.QUESTIONED_NOT_RULED
            .value
        ),
    ),
    AnnualStatement(
        fiscal_year=2017,
        is_synthetic_illustrative=True,
        reported_revenue_eur_m=1500.0,
        reported_net_profit_eur_m=390.0,
        operating_cash_flow_eur_m=210.0,
        receivables_eur_m=700.0,
        tpa_revenue_eur_m=780.0,
        escrow_balance_eur_m=1100.0,
        apac_revenue_eur_m=830.0,
        net_margin=0.260,
        narrative_optimism=0.88,
        disclosure_bridges_required=7,
        disclosure_bridges_provided=3,
        post_hoc_label=(
            PostHocLabel.DECLARED_VOID_2022
            .value
        ),
    ),
    AnnualStatement(
        fiscal_year=2018,
        is_synthetic_illustrative=True,
        reported_revenue_eur_m=2000.0,
        reported_net_profit_eur_m=540.0,
        operating_cash_flow_eur_m=250.0,
        receivables_eur_m=1050.0,
        tpa_revenue_eur_m=1080.0,
        escrow_balance_eur_m=1900.0,
        apac_revenue_eur_m=1160.0,
        net_margin=0.270,
        narrative_optimism=0.92,
        disclosure_bridges_required=9,
        disclosure_bridges_provided=3,
        post_hoc_label=(
            PostHocLabel.DECLARED_VOID_2022
            .value
        ),
    ),
)


def statements() -> tuple[AnnualStatement, ...]:
    return _FIXTURE


def by_year(year: int) -> AnnualStatement:
    for s in statements():
        if s.fiscal_year == year:
            return s
    raise KeyError(year)


def years() -> tuple[int, ...]:
    return tuple(
        s.fiscal_year for s in statements()
    )


__all__ = [
    "AnnualStatement",
    "POST_HOC_LABELS",
    "PostHocLabel",
    "by_year",
    "statements",
    "years",
]
