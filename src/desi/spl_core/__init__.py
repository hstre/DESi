"""DESi SPL-core — the canonical semantic-projection / admissibility layer.

Consolidates three previously-parallel projection layers (the vendored
Alexandria SPL, `desi.spl_adapter`, and the P8 benchmark adapter) onto:

* one entropy model               — :mod:`desi.spl_core.entropy`
* one admissibility gateway        — :mod:`desi.spl_core.gateway`
* one ClaimCandidate               — :mod:`desi.spl_core.candidate`
* one projection entry point        — :mod:`desi.spl_core.projection`

SPL-core is a **projection / admissibility** layer: it decides which atomic
claims are well-formed and confident enough to become comparable candidates. It
is NOT the conflict engine, NOT a truth solver, NOT NER/ontology. See
`artifacts/architecture/spl_consolidation_analysis.md`.
"""
from __future__ import annotations

from .candidate import (
    CanonicalClaimCandidate,
    from_alexandria_candidate,
    from_desi_spl_candidate,
)
from .entropy import (
    DEFAULT_RELATION_SPACE_SIZE,
    CanonicalThresholds,
    normalized_shannon_entropy,
    synthesize_relation_distribution,
)
from .gateway import AdmissionDecision, CanonicalGateway
from .projection import CanonicalProjection, project_atomic_claim

__all__ = [
    "AdmissionDecision",
    "CanonicalClaimCandidate",
    "CanonicalGateway",
    "CanonicalProjection",
    "CanonicalThresholds",
    "DEFAULT_RELATION_SPACE_SIZE",
    "from_alexandria_candidate",
    "from_desi_spl_candidate",
    "normalized_shannon_entropy",
    "project_atomic_claim",
    "synthesize_relation_distribution",
]
