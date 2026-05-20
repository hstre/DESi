"""DESi v15.2 - Financial Blindness Pools (DAX
retrospective, read-only).

Clusters firms by their epistemic STRUCTURE
(blind-spot shape), not by industry, to reveal
shared risk families, structural redundancy, and
how recoverable a blind spot is across a pool.
Never concludes fraud, never rates, never advises.
Post-hoc outcomes are validation labels only.
"""
from __future__ import annotations

from .clusters import (
    BlindnessPool, blindness_pool_count,
    multi_member_pools, pool_of, pools,
)
from .redundancy import (
    recoverability_signal, redundant_firm_fraction,
    structural_redundancy,
)
from .report import (
    FirmPoolVerdict, V152Report,
    build_blindness_artifact, build_report,
    clean_firm_sound_rate, corpus_priority_label,
    ex_ante_pool_recall, firm_pool_verdicts,
    pool_priority_label,
)
from .risk_families import (
    RISK_FAMILIES, RiskFamily, detected_families,
    family_assignments, firm_family_count,
    firm_risk_families, risk_family_detection,
)
from .trajectory_similarity import (
    SIGNATURE_AXES, StructuralSignature, distance,
    signature, signatures, similarity,
    similarity_matrix,
)


__all__ = [
    "RISK_FAMILIES",
    "SIGNATURE_AXES",
    "BlindnessPool",
    "FirmPoolVerdict",
    "RiskFamily",
    "StructuralSignature",
    "V152Report",
    "blindness_pool_count",
    "build_blindness_artifact",
    "build_report",
    "clean_firm_sound_rate",
    "corpus_priority_label",
    "detected_families",
    "distance",
    "ex_ante_pool_recall",
    "family_assignments",
    "firm_family_count",
    "firm_pool_verdicts",
    "firm_risk_families",
    "multi_member_pools",
    "pool_of",
    "pool_priority_label",
    "pools",
    "recoverability_signal",
    "redundant_firm_fraction",
    "risk_family_detection",
    "signature",
    "signatures",
    "similarity",
    "similarity_matrix",
    "structural_redundancy",
]
