"""v15.1 - claim lineage and historical_consistency
signal.

Each year management makes forward-looking claims
("receivables will normalise", "third-party
dependence will fall", ...). Lineage tracks
whether a claim made in one year is UPHELD in the
later record or quietly dropped / contradicted.

historical_consistency = fraction of forward
claims that were upheld. Low = the narrative keeps
promising and not delivering - an audit-worthy
inconsistency with its own history, NOT a fraud
claim.

The fulfilment rate is a synthetic per-firm
property of the fixture; lineage just makes it
inspectable. Reads no post-hoc label.
"""
from __future__ import annotations

from dataclasses import dataclass

from .trajectory import (
    NarrativeTrajectory, claim_fulfilment,
    trajectories,
)

# A small closed roster of forward-claim topics,
# cycled deterministically across the years.
_CLAIM_TOPICS: tuple[str, ...] = (
    "receivables_normalise",
    "third_party_dependence_falls",
    "cash_conversion_improves",
    "segment_disclosure_expands",
    "margin_sustained_organically",
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class ClaimRecord:
    firm_id: str
    made_year: int
    topic: str
    upheld: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "firm_id": self.firm_id,
            "made_year": self.made_year,
            "topic": self.topic,
            "upheld": self.upheld,
        }


def claim_lineage_firm(
    tr: NarrativeTrajectory,
) -> tuple[ClaimRecord, ...]:
    """One forward claim per year except the last
    (which has no later year to test it). The
    first ``round(rate * n)`` claims are upheld;
    the rest lapse - a deterministic realisation of
    the firm's fulfilment rate."""
    made_years = [
        y.fiscal_year for y in tr.years[:-1]
    ]
    n = len(made_years)
    if n == 0:
        return ()
    rate = claim_fulfilment(tr.firm_id)
    upheld_count = int(round(rate * n))
    out: list[ClaimRecord] = []
    for i, yr in enumerate(made_years):
        out.append(ClaimRecord(
            firm_id=tr.firm_id,
            made_year=yr,
            topic=_CLAIM_TOPICS[
                i % len(_CLAIM_TOPICS)
            ],
            upheld=i < upheld_count,
        ))
    return tuple(out)


def historical_consistency_firm(
    tr: NarrativeTrajectory,
) -> float:
    """Fraction of forward claims upheld, in
    [0, 1]. 1.0 = every promise kept."""
    claims = claim_lineage_firm(tr)
    if not claims:
        return 1.0
    upheld = sum(1 for c in claims if c.upheld)
    return _round(upheld / len(claims))


def historical_consistency() -> float:
    """Corpus mean of per-firm historical
    consistency."""
    trs = trajectories()
    if not trs:
        return 1.0
    vals = [
        historical_consistency_firm(t)
        for t in trs
    ]
    return _round(sum(vals) / len(vals))


def claim_lineage() -> tuple[ClaimRecord, ...]:
    out: list[ClaimRecord] = []
    for tr in trajectories():
        out.extend(claim_lineage_firm(tr))
    return tuple(out)


__all__ = [
    "ClaimRecord",
    "claim_lineage",
    "claim_lineage_firm",
    "historical_consistency",
    "historical_consistency_firm",
]
