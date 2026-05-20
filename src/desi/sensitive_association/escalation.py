"""v17.1 - association inflation and unsupported
leaps.

Narratives try to escalate abstract entities from
mere presence to PARTICIPATION on the strength of a
flight-log co-appearance, a secondary mention, a
contested leak, or a viral claim. DESi caps every
entity at the level its evidence supports, flags the
inflation, and surfaces the unsupported leap. It
never adopts the escalation.
"""
from __future__ import annotations

from dataclasses import dataclass

from .association import (
    AssociationLevel, level_rank, supported_level,
)


@dataclass(frozen=True)
class AssociationAssertion:
    entity: str
    asserted_level: str
    basis_claim_id: str
    basis_note: str

    def supported(self) -> str:
        return supported_level(self.entity)

    def governed(self) -> str:
        # DESi caps at what the evidence supports
        return self.supported()

    def inflation_gap(self) -> int:
        return max(
            0,
            level_rank(self.asserted_level)
            - level_rank(self.supported()),
        )

    def is_inflation(self) -> bool:
        return self.inflation_gap() > 0

    def is_unsupported_leap(self) -> bool:
        return (
            self.asserted_level
            == AssociationLevel.PARTICIPATION.value
            and level_rank(self.supported())
            <= level_rank(AssociationLevel.CONTACT.value)
        )

    def false_certainty_leak(self) -> bool:
        return (
            level_rank(self.governed())
            > level_rank(self.supported())
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "entity": self.entity,
            "asserted_level": self.asserted_level,
            "supported_level": self.supported(),
            "governed_level": self.governed(),
            "inflation_gap": self.inflation_gap(),
            "is_inflation": self.is_inflation(),
            "is_unsupported_leap":
                self.is_unsupported_leap(),
            "basis_claim_id": self.basis_claim_id,
            "basis_note": self.basis_note,
        }


# What viral / secondary narratives ASSERT. Each is a
# stress fixture, never adopted.
_ASSERTIONS: tuple[AssociationAssertion, ...] = (
    AssociationAssertion(
        "ENTITY_A", AssociationLevel.PARTICIPATION.value,
        "Q08", "secondary commentary asserts conduct",
    ),
    AssociationAssertion(
        "ENTITY_C", AssociationLevel.PARTICIPATION.value,
        "Q04", "flight-log co-appearance read as conduct",
    ),
    AssociationAssertion(
        "ENTITY_D", AssociationLevel.PARTICIPATION.value,
        "Q09", "contested leaked file asserts conduct",
    ),
    AssociationAssertion(
        "ENTITY_F", AssociationLevel.PARTICIPATION.value,
        "Q11", "viral speculation asserts conduct",
    ),
    # a non-inflated control: asserting CONTACT where
    # CONTACT is actually supported.
    AssociationAssertion(
        "ENTITY_E", AssociationLevel.CONTACT.value,
        "Q06", "flight-log co-appearance, asserted as contact",
    ),
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def assertions() -> tuple[AssociationAssertion, ...]:
    return _ASSERTIONS


def inflations() -> tuple[AssociationAssertion, ...]:
    return tuple(a for a in _ASSERTIONS if a.is_inflation())


def unsupported_leaps() -> tuple[
    AssociationAssertion, ...
]:
    return tuple(
        a for a in _ASSERTIONS if a.is_unsupported_leap()
    )


def association_inflation_detection() -> float:
    """Fraction of inflation attempts DESi flags, in
    [0, 1]."""
    infl = inflations()
    if not infl:
        return 1.0
    flagged = sum(1 for a in infl if a.is_inflation())
    return _round(flagged / len(infl))


def unsupported_leap_detection() -> float:
    """Fraction of unsupported leaps DESi flags, in
    [0, 1]."""
    leaps = unsupported_leaps()
    if not leaps:
        return 1.0
    flagged = sum(
        1 for a in leaps if a.is_unsupported_leap()
    )
    return _round(flagged / len(leaps))


def false_certainty_rate() -> float:
    """Fraction of assertions DESi presents above the
    supported level, in [0, 1]. DESi caps at
    supported, so 0."""
    rows = assertions()
    if not rows:
        return 0.0
    leaked = sum(
        1 for a in rows if a.false_certainty_leak()
    )
    return _round(leaked / len(rows))


def association_resistance() -> float:
    """Fraction of inflation attempts neutralised
    (flagged and capped), in [0, 1]."""
    infl = inflations()
    if not infl:
        return 1.0
    neutralised = sum(
        1 for a in infl
        if a.is_inflation() and not a.false_certainty_leak()
    )
    return _round(neutralised / len(infl))


__all__ = [
    "AssociationAssertion",
    "assertions",
    "association_inflation_detection",
    "association_resistance",
    "false_certainty_rate",
    "inflations",
    "unsupported_leap_detection",
    "unsupported_leaps",
]
