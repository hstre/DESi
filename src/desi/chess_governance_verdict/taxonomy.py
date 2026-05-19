"""v11.4 — closed chess-governance-class
taxonomy. Five outcome classes."""
from __future__ import annotations

from enum import Enum


class ChessGovernanceClass(str, Enum):
    EPISTEMIC_SEARCH_COMPRESSOR = (
        "A_epistemic_search_compressor"
    )
    BOUNDED_COMPUTE_REDUCER     = (
        "B_bounded_compute_reducer"
    )
    TACTICAL_RISK_OPTIMIZER     = (
        "C_tactical_risk_optimizer"
    )
    BRUTE_FORCE_DEPENDENT       = (
        "D_brute_force_dependent"
    )
    SEARCH_DEGRADING            = (
        "E_search_degrading"
    )


CHESS_GOVERNANCE_CLASSES: tuple[
    str, ...,
] = tuple(
    c.value for c in ChessGovernanceClass
)


__all__ = [
    "CHESS_GOVERNANCE_CLASSES",
    "ChessGovernanceClass",
]
