"""v15.0 — per-firm audit-priority scoring and
ex-ante / post-hoc validation.

The closed output vocabulary is STRICTLY audit-
priority. There is NO "fraud" / "Betrug" value,
no rating, no buy/sell signal. DESi's strongest
statement about any firm is "this structure
deserves a closer audit / governance review".

The coarse ``post_hoc_label`` is read ONLY inside
the ex-ante validators below, and ONLY to measure
whether DESi's ex-ante structure ranking lines up
with later outcomes. No scoring function reads it.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from functools import lru_cache

from .bridges import (
    bridge_validity_firm, opacity_firm,
)
from .cashflow import cashflow_alignment_firm
from .narratives import narrative_consistency_firm
from .statements import (
    ADVERSE_POST_HOC, Firm, firms,
)


class AuditPriority(str, Enum):
    """Closed, phase-wide output vocabulary."""
    LOW_AUDIT_PRIORITY = "LOW_AUDIT_PRIORITY"
    MEDIUM_AUDIT_PRIORITY = "MEDIUM_AUDIT_PRIORITY"
    HIGH_AUDIT_PRIORITY = "HIGH_AUDIT_PRIORITY"
    GOVERNANCE_REVIEW_RECOMMENDED = (
        "GOVERNANCE_REVIEW_RECOMMENDED"
    )
    UNRESOLVED = "UNRESOLVED"


AUDIT_PRIORITIES: tuple[str, ...] = tuple(
    p.value for p in AuditPriority
)

# Severity rank for aggregating / comparing labels
# (UNRESOLVED is most severe: DESi cannot resolve
# a determinate priority and must hand off).
_SEVERITY: dict[str, int] = {
    AuditPriority.LOW_AUDIT_PRIORITY.value: 0,
    AuditPriority.MEDIUM_AUDIT_PRIORITY.value: 1,
    AuditPriority.HIGH_AUDIT_PRIORITY.value: 2,
    AuditPriority.GOVERNANCE_REVIEW_RECOMMENDED.value: 3,
    AuditPriority.UNRESOLVED.value: 4,
}

# Labels that count as "DESi raised the firm for a
# closer look" (>= MEDIUM, excluding UNRESOLVED).
ELEVATED: frozenset[str] = frozenset({
    AuditPriority.MEDIUM_AUDIT_PRIORITY.value,
    AuditPriority.HIGH_AUDIT_PRIORITY.value,
    AuditPriority.GOVERNANCE_REVIEW_RECOMMENDED.value,
})

# Per-axis "this axis is individually elevated"
# threshold (counts toward breadth of concern).
_AXIS_ELEVATED = 0.40
# A single axis at/above this is severe enough to
# warrant a closer look on its own.
_AXIS_SEVERE = 0.50


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class FirmSignals:
    cash_misalignment: float
    narrative_gap: float
    opacity: float
    bridge_gap: float

    def as_list(self) -> list[float]:
        return [
            self.cash_misalignment,
            self.narrative_gap,
            self.opacity,
            self.bridge_gap,
        ]


def firm_signals(firm: Firm) -> FirmSignals:
    """The four audit-worthiness tensions, each in
    [0, 1], derived from published fields only."""
    return FirmSignals(
        cash_misalignment=_round(
            1.0 - cashflow_alignment_firm(firm),
        ),
        narrative_gap=_round(
            1.0 - narrative_consistency_firm(firm),
        ),
        opacity=_round(opacity_firm(firm)),
        bridge_gap=_round(
            1.0 - bridge_validity_firm(firm),
        ),
    )


def firm_priority_score(firm: Firm) -> float:
    """Equal-weighted mean of the four tensions,
    in [0, 1]. Published-field only."""
    vals = firm_signals(firm).as_list()
    return _round(sum(vals) / len(vals))


def firm_priority_label(firm: Firm) -> str:
    """Map the structure of a firm to the closed
    audit-priority vocabulary.

    The mapping reflects both DEPTH (the composite
    score) and BREADTH (how many of the four axes
    are individually elevated):

    * GOVERNANCE_REVIEW_RECOMMENDED - broad AND
      deep: composite high AND >= 3 axes elevated.
      The concern spans the whole disclosure
      structure, not one quirky line.
    * HIGH_AUDIT_PRIORITY - deep overall, OR >= 3
      axes elevated.
    * MEDIUM_AUDIT_PRIORITY - a moderate composite,
      OR two elevated axes, OR a single severe one
      ("worth a closer look at that").
    * LOW_AUDIT_PRIORITY - otherwise.
    * UNRESOLVED - too few profitable years to
      score.
    """
    if not _has_scoreable_years(firm):
        return AuditPriority.UNRESOLVED.value
    sig = firm_signals(firm)
    score = firm_priority_score(firm)
    axes = sig.as_list()
    elevated_axes = sum(
        1 for v in axes if v >= _AXIS_ELEVATED
    )
    severe_axis = any(
        v >= _AXIS_SEVERE for v in axes
    )
    if score >= 0.45 and elevated_axes >= 3:
        return (
            AuditPriority
            .GOVERNANCE_REVIEW_RECOMMENDED.value
        )
    if score >= 0.45 or elevated_axes >= 3:
        return AuditPriority.HIGH_AUDIT_PRIORITY.value
    if (
        score >= 0.25
        or elevated_axes >= 2
        or severe_axis
    ):
        return (
            AuditPriority.MEDIUM_AUDIT_PRIORITY.value
        )
    return AuditPriority.LOW_AUDIT_PRIORITY.value


def _has_scoreable_years(firm: Firm) -> bool:
    return any(
        y.reported_net_profit_eur_m > 0
        for y in firm.years
    )


@dataclass(frozen=True)
class FirmVerdict:
    firm_id: str
    sector: str
    priority_score: float
    priority_label: str
    cash_misalignment: float
    narrative_gap: float
    opacity: float
    bridge_gap: float
    post_hoc_label: str

    def to_dict(self) -> dict[str, object]:
        return {
            "firm_id": self.firm_id,
            "sector": self.sector,
            "priority_score": self.priority_score,
            "priority_label": self.priority_label,
            "cash_misalignment":
                self.cash_misalignment,
            "narrative_gap": self.narrative_gap,
            "opacity": self.opacity,
            "bridge_gap": self.bridge_gap,
            "post_hoc_label": self.post_hoc_label,
        }


@lru_cache(maxsize=1)
def firm_verdicts() -> tuple[FirmVerdict, ...]:
    out: list[FirmVerdict] = []
    for f in firms():
        sig = firm_signals(f)
        out.append(FirmVerdict(
            firm_id=f.firm_id,
            sector=f.sector,
            priority_score=firm_priority_score(f),
            priority_label=firm_priority_label(f),
            cash_misalignment=sig.cash_misalignment,
            narrative_gap=sig.narrative_gap,
            opacity=sig.opacity,
            bridge_gap=sig.bridge_gap,
            post_hoc_label=f.post_hoc_label,
        ))
    out.sort(key=lambda v: v.firm_id)
    return tuple(out)


def severity_rank(label: str) -> int:
    return _SEVERITY[label]


def corpus_priority_label() -> str:
    """The single most-severe firm label present
    (UNRESOLVED dominates only if a firm is itself
    unresolved)."""
    verdicts = firm_verdicts()
    if not verdicts:
        return AuditPriority.UNRESOLVED.value
    return max(
        (v.priority_label for v in verdicts),
        key=severity_rank,
    )


# --- Post-hoc validation (read post_hoc_label) ---
def ex_ante_structure_recall() -> float:
    """POST-HOC VALIDATION ONLY.

    Of the firms that later had an adverse outcome
    (post_hoc_label in ADVERSE_POST_HOC), what
    fraction did DESi flag as elevated (>= MEDIUM)
    using ONLY ex-ante published structure? This
    is the Killerfrage measure: did DESi raise the
    later-troubled firms before humans looked?"""
    verdicts = firm_verdicts()
    adverse = [
        v for v in verdicts
        if v.post_hoc_label in ADVERSE_POST_HOC
    ]
    if not adverse:
        return 1.0
    flagged = sum(
        1 for v in adverse
        if v.priority_label in ELEVATED
    )
    return _round(flagged / len(adverse))


def clean_firm_low_priority_rate() -> float:
    """POST-HOC VALIDATION ONLY.

    Of the firms with NO later adverse outcome
    (post_hoc_label == no_adverse_event), what
    fraction did DESi keep at LOW priority? This
    guards the "don't become a rating / accusation
    machine" invariant: clean firms must not be
    swept up."""
    from .statements import PostHocLabel
    verdicts = firm_verdicts()
    clean = [
        v for v in verdicts
        if v.post_hoc_label == (
            PostHocLabel.NO_ADVERSE_EVENT.value
        )
    ]
    if not clean:
        return 1.0
    low = sum(
        1 for v in clean
        if v.priority_label == (
            AuditPriority.LOW_AUDIT_PRIORITY.value
        )
    )
    return _round(low / len(clean))


__all__ = [
    "AUDIT_PRIORITIES",
    "AuditPriority",
    "ELEVATED",
    "FirmSignals",
    "FirmVerdict",
    "clean_firm_low_priority_rate",
    "corpus_priority_label",
    "ex_ante_structure_recall",
    "firm_priority_label",
    "firm_priority_score",
    "firm_signals",
    "firm_verdicts",
    "severity_rank",
]
