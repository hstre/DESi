"""Canonical projection: atomic claim → CanonicalClaimCandidate.

This is the single pre-protocol path for a structured atomic claim (the P3
extractor output, or the conflict-benchmark dataset). It owns the pipeline that
the P8 benchmark adapter used to own inline:

    atomic claim {subject, predicate, object, confidence?, claim_type?}
        -> synthesise P_r            (entropy.synthesize_relation_distribution)
        -> CanonicalGateway.admit_projection  (E0–E3)
        -> CanonicalClaimCandidate

`admissible` additionally requires a structurally complete triple (non-empty
subject/predicate/object), matching the full Alexandria emit-then-validate path
(emission gate + `validate_claim_node`). No raw triple is comparable until it
has become a candidate this way.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from .candidate import CanonicalClaimCandidate
from .entropy import (
    DEFAULT_RELATION_SPACE_SIZE,
    CanonicalThresholds,
    synthesize_relation_distribution,
)
from .gateway import CanonicalGateway

_DEFAULT_CONFIDENCE = 0.7


@dataclass
class CanonicalProjection:
    """The projected distribution + provenance (analogue of Alexandria's
    SemanticProjection, kept minimal: only the fields SPL-core actually uses)."""
    projection_id:      str
    unit_id:            str
    P_r:                dict[str, float]
    subject_candidates: list[str]
    object_candidates:  list[str]
    h_norm:             float
    p_illegal:          float = 0.0
    emission_rule:      str | None = None
    admissible:         bool = False

    def to_dict(self) -> dict[str, Any]:
        return {"projection_id": self.projection_id, "unit_id": self.unit_id,
                "P_r": self.P_r, "subject_candidates": self.subject_candidates,
                "object_candidates": self.object_candidates, "h_norm": self.h_norm,
                "p_illegal": self.p_illegal, "emission_rule": self.emission_rule,
                "admissible": self.admissible}


def project_atomic_claim(
    claim: dict,
    *,
    relation_space_size: int = DEFAULT_RELATION_SPACE_SIZE,
    thresholds: CanonicalThresholds | None = None,
    gateway: CanonicalGateway | None = None,
) -> tuple[CanonicalClaimCandidate, CanonicalProjection]:
    """Project one atomic claim. Returns (candidate, projection)."""
    gw = gateway or CanonicalGateway(thresholds)
    subject = str(claim.get("subject", "") or "").strip()
    predicate = str(claim.get("predicate", "") or "").strip()
    obj = str(claim.get("object", "") or "").strip()
    errors: list[str] = []
    if not subject:
        errors.append("empty_subject")
    if not predicate:
        errors.append("empty_predicate")
    if not obj:
        errors.append("empty_object")
    try:
        confidence = float(claim.get("confidence", _DEFAULT_CONFIDENCE))
    except (TypeError, ValueError):
        errors.append(f"bad_confidence:{claim.get('confidence')!r}->default")
        confidence = _DEFAULT_CONFIDENCE

    P_r = synthesize_relation_distribution(predicate, confidence, relation_space_size)
    decision = gw.admit_projection(P_r, p_illegal=0.0)

    structural_ok = bool(subject and predicate and obj)
    admissible = decision.admissible and structural_ok
    if decision.admissible and not structural_ok:
        errors.append("structural_invalid:empty_subject_predicate_or_object")
    if not decision.admissible:
        errors.append(f"blocked:{decision.emission_rule}:{decision.reason}")

    unit_id, projection_id = str(uuid.uuid4()), str(uuid.uuid4())
    cand = CanonicalClaimCandidate(
        subject=subject, predicate=predicate, object=obj,
        content=f"{subject} | {predicate} | {obj}",
        confidence=confidence, projection_entropy=decision.projection_entropy,
        emission_rule=decision.emission_rule, admissible=admissible,
        admission_reason=decision.reason, origin="benchmark_synth",
        claim_type=str(claim.get("claim_type", "")),
        unit_id=unit_id, projection_id=projection_id,
        source_ref=str(claim.get("source_ref", "desi_atomic_claim")), errors=errors)
    proj = CanonicalProjection(
        projection_id=projection_id, unit_id=unit_id, P_r=P_r,
        subject_candidates=[subject] if subject else [],
        object_candidates=[obj] if obj else [],
        h_norm=decision.projection_entropy or 0.0,
        emission_rule=decision.emission_rule, admissible=admissible)
    return cand, proj


__all__ = ["CanonicalProjection", "project_atomic_claim"]
