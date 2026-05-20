"""v15.2 - structural trajectory fingerprints and
firm-to-firm similarity.

Each firm is reduced to an eight-axis STRUCTURAL
SIGNATURE that fingerprints its multi-year
trajectory: the four cross-sectional tensions from
v15.0 (cash misalignment, narrative gap, opacity,
bridge gap) and the four longitudinal tensions
from v15.1 (narrative drift, semantic reframing,
inconsistency, bridge degradation).

Crucially the signature is built from EPISTEMIC
STRUCTURE, never from the sector label - so any
clustering it drives groups firms by shared blind-
spot shape, NOT by industry.

Reads no post-hoc label.
"""
from __future__ import annotations

from dataclasses import dataclass

from desi.financial_governance import (
    by_id as _firm_by_id, firm_ids, firm_signals,
)
from desi.financial_narrative_drift import (
    by_id as _traj_by_id, drift_signals,
)

# Axis order is fixed for determinism.
SIGNATURE_AXES: tuple[str, ...] = (
    "cash_misalignment",
    "narrative_gap",
    "opacity",
    "bridge_gap",
    "narrative_drift",
    "semantic_reframing",
    "inconsistency",
    "bridge_degradation",
)

_DIM = len(SIGNATURE_AXES)
# Max possible L2 distance between two unit-cube
# points, used to normalise distances into [0, 1].
_D_NORM = _DIM ** 0.5


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class StructuralSignature:
    firm_id: str
    sector: str
    values: tuple[float, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "firm_id": self.firm_id,
            "sector": self.sector,
            "axes": list(SIGNATURE_AXES),
            "values": [
                round(v, 6) for v in self.values
            ],
        }


def _signature_for(firm_id: str) -> StructuralSignature:
    firm = _firm_by_id(firm_id)
    cross = firm_signals(firm)
    longi = drift_signals(_traj_by_id(firm_id))
    values = (
        cross.cash_misalignment,
        cross.narrative_gap,
        cross.opacity,
        cross.bridge_gap,
        longi.narrative_drift,
        longi.semantic_reframing,
        longi.inconsistency,
        longi.bridge_degradation,
    )
    return StructuralSignature(
        firm_id=firm_id,
        sector=firm.sector,
        values=tuple(values),
    )


_SIGNATURES: dict[str, StructuralSignature] = {
    fid: _signature_for(fid) for fid in firm_ids()
}


def signatures() -> tuple[StructuralSignature, ...]:
    return tuple(
        _SIGNATURES[fid]
        for fid in sorted(_SIGNATURES)
    )


def signature(firm_id: str) -> StructuralSignature:
    return _SIGNATURES[firm_id]


def distance(a: str, b: str) -> float:
    """Normalised Euclidean distance between two
    firms' structural signatures, in [0, 1]."""
    va = _SIGNATURES[a].values
    vb = _SIGNATURES[b].values
    sq = sum(
        (x - y) ** 2 for x, y in zip(va, vb)
    )
    return _round((sq ** 0.5) / _D_NORM)


def similarity(a: str, b: str) -> float:
    """1 - normalised distance, in [0, 1]."""
    return _round(1.0 - distance(a, b))


def similarity_matrix() -> dict[
    str, dict[str, float]
]:
    ids = sorted(_SIGNATURES)
    return {
        a: {b: similarity(a, b) for b in ids}
        for a in ids
    }


__all__ = [
    "SIGNATURE_AXES",
    "StructuralSignature",
    "distance",
    "signature",
    "signatures",
    "similarity",
    "similarity_matrix",
]
