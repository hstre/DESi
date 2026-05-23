"""v15.2 - closed risk-family taxonomy.

A risk family is a recurring SHAPE of structural
tension, defined over the signature axes - not an
industry. A firm is assigned every family whose
defining axes are elevated; a firm with no
elevated axis is STRUCTURALLY_SOUND.

risk_family_detection measures how much of the
closed taxonomy the corpus actually surfaces.

Reads no post-hoc label.
"""
from __future__ import annotations

from enum import Enum

from .trajectory_similarity import (
    SIGNATURE_AXES, signature, signatures,
)

_AXIS_ELEVATED = 0.40


class RiskFamily(str, Enum):
    """Closed set of structural risk-shapes."""
    CASH_NARRATIVE_DIVERGENCE = (
        "cash_narrative_divergence"
    )
    DISCLOSURE_OPACITY = "disclosure_opacity"
    NARRATIVE_INSTABILITY = "narrative_instability"
    DISCLOSURE_DRIFT = "disclosure_drift"
    STRUCTURALLY_SOUND = "structurally_sound"


RISK_FAMILIES: tuple[str, ...] = tuple(
    f.value for f in RiskFamily
)

# The non-sound families and the signature axes
# that define each.
_FAMILY_AXES: dict[RiskFamily, tuple[str, ...]] = {
    RiskFamily.CASH_NARRATIVE_DIVERGENCE: (
        "cash_misalignment", "narrative_gap",
    ),
    RiskFamily.DISCLOSURE_OPACITY: (
        "opacity", "bridge_gap",
    ),
    RiskFamily.NARRATIVE_INSTABILITY: (
        "narrative_drift", "semantic_reframing",
        "inconsistency",
    ),
    RiskFamily.DISCLOSURE_DRIFT: (
        "bridge_degradation",
    ),
}

_NON_SOUND: tuple[RiskFamily, ...] = tuple(
    _FAMILY_AXES.keys()
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _axis(values: tuple[float, ...], name: str) -> float:
    return values[SIGNATURE_AXES.index(name)]


def firm_risk_families(firm_id: str) -> tuple[str, ...]:
    """Every family whose defining axes are
    elevated for this firm; STRUCTURALLY_SOUND if
    none."""
    vals = signature(firm_id).values
    out: list[str] = []
    for fam in _NON_SOUND:
        if any(
            _axis(vals, ax) >= _AXIS_ELEVATED
            for ax in _FAMILY_AXES[fam]
        ):
            out.append(fam.value)
    if not out:
        out.append(RiskFamily.STRUCTURALLY_SOUND.value)
    return tuple(out)


def firm_family_count(firm_id: str) -> int:
    """Number of NON-sound families a firm carries."""
    fams = firm_risk_families(firm_id)
    if fams == (
        RiskFamily.STRUCTURALLY_SOUND.value,
    ):
        return 0
    return len(fams)


def detected_families() -> tuple[str, ...]:
    seen: list[str] = []
    for sig in signatures():
        for fam in firm_risk_families(sig.firm_id):
            if (
                fam != (
                    RiskFamily
                    .STRUCTURALLY_SOUND.value
                )
                and fam not in seen
            ):
                seen.append(fam)
    return tuple(sorted(seen))


def risk_family_detection() -> float:
    """Fraction of the closed non-sound taxonomy
    that the corpus surfaces, in [0, 1]."""
    return _round(
        len(detected_families())
        / len(_NON_SOUND),
    )


def family_assignments() -> dict[str, tuple[str, ...]]:
    return {
        sig.firm_id: firm_risk_families(sig.firm_id)
        for sig in signatures()
    }


__all__ = [
    "RISK_FAMILIES",
    "RiskFamily",
    "detected_families",
    "family_assignments",
    "firm_family_count",
    "firm_risk_families",
    "risk_family_detection",
]
