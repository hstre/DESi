"""The single, unified ClaimCandidate for DESi SPL-core.

Before consolidation there were three incompatible candidate shapes:

* Alexandria SPL — a triple `(subject, relation, object)` + `relation_score`
  + `h_norm` + an emission rule.
* `desi.spl_adapter` — a `content` *string* + boolean `ambiguous` + confidence,
  with **no triple** and **no entropy**.
* the P8 benchmark adapter — Alexandria's, serialised to a dict.

`CanonicalClaimCandidate` is the union that both native shapes map onto without
losing information: it carries the triple **and** the canonical proposition
string, an optional `projection_entropy` (None for the flag model), and the
admissibility verdict. Two adapter constructors (`from_alexandria_candidate`,
`from_desi_spl_candidate`) sit here; the third adapter — atomic-claim →
candidate — is `spl_core.projection.project_atomic_claim`.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

_ORIGINS = ("alexandria_spl", "desi_spl_adapter", "benchmark_synth", "canonical")


@dataclass
class CanonicalClaimCandidate:
    """Unified candidate consumed by the conflict engine / claim graph."""
    subject:            str = ""
    predicate:          str = ""
    object:             str = ""
    content:            str = ""          # canonical proposition ("s | p | o" for triples)
    confidence:         float = 1.0
    projection_entropy: Optional[float] = None   # h_norm; None for the flag model
    ambiguous:          bool = False
    emission_rule:      Optional[str] = None      # "E0".."E4" or None (flag model)
    admissible:         bool = False
    admission_reason:   str = ""
    origin:             str = "canonical"
    claim_type:         str = ""
    modality_hint:      str = "asserted"
    unit_id:            str = ""
    projection_id:      str = ""
    candidate_id:       str = field(default_factory=lambda: str(uuid.uuid4()))
    source_ref:         str = ""
    errors:             list[str] = field(default_factory=list)

    def as_conflict_claim(self, _id: str | None = None,
                          state: str | None = None) -> dict[str, Any]:
        """The dict shape the conflict engine consumes — built from the
        *validated candidate*, never from a raw triple."""
        return {"_id": _id or self.candidate_id, "subject": self.subject,
                "predicate": self.predicate, "object": self.object, "state": state}

    def to_dict(self) -> dict[str, Any]:
        return {
            "subject": self.subject, "predicate": self.predicate, "object": self.object,
            "content": self.content, "confidence": self.confidence,
            "projection_entropy": self.projection_entropy, "ambiguous": self.ambiguous,
            "emission_rule": self.emission_rule, "admissible": self.admissible,
            "admission_reason": self.admission_reason, "origin": self.origin,
            "claim_type": self.claim_type, "modality_hint": self.modality_hint,
            "unit_id": self.unit_id, "projection_id": self.projection_id,
            "candidate_id": self.candidate_id, "source_ref": self.source_ref,
            "errors": list(self.errors),
        }


def from_alexandria_candidate(cand: Any, *, admissible: bool,
                              admission_reason: str = "") -> CanonicalClaimCandidate:
    """Adapter: a vendored Alexandria `ClaimCandidate` → canonical.

    `cand` has subject / relation / object / relation_score / rank / emission_rule
    / h_norm / modality_hint / semantic_category_hint. Admissibility is decided by
    the caller (the Alexandria gateway) and passed in."""
    rule = getattr(cand, "emission_rule", None)
    rule_str = rule.value if hasattr(rule, "value") else (str(rule) if rule else None)
    subj, rel, obj = cand.subject, cand.relation, cand.object
    return CanonicalClaimCandidate(
        subject=subj, predicate=rel, object=obj,
        content=f"{subj} | {rel} | {obj}",
        confidence=getattr(cand, "relation_score", 1.0),
        projection_entropy=getattr(cand, "h_norm", None),
        emission_rule=rule_str, admissible=admissible, admission_reason=admission_reason,
        origin="alexandria_spl",
        claim_type=getattr(cand, "semantic_category_hint", ""),
        modality_hint=getattr(cand, "modality_hint", "asserted"),
        unit_id=getattr(cand, "unit_id", ""), projection_id=getattr(cand, "projection_id", ""),
        candidate_id=getattr(cand, "candidate_id", str(uuid.uuid4())),
        source_ref=getattr(cand, "source_ref", ""))


def from_desi_spl_candidate(cand: Any, *, gateway: Any = None) -> CanonicalClaimCandidate:
    """Adapter: a `desi.spl_adapter.mapping.ClaimCandidate` → canonical.

    The flag model: `content` string, boolean `ambiguous`, confidence,
    `proposed_relations`. There is no triple and no entropy, so `subject /
    predicate / object` stay empty and `projection_entropy` stays None. The
    admissibility decision mirrors `desi.spl_adapter.SPLGateway` precedence
    (empty_content → hallucinated_relation → ambiguous/confidence →
    invalid_method, the closed-set check `candidate_to_claim` applies last)."""
    from desi.spl_adapter.mapping import LEGAL_METHODS

    from .gateway import CanonicalGateway
    gw = gateway or CanonicalGateway()
    errors: list[str] = []
    content = getattr(cand, "content", "") or ""
    proposed = getattr(cand, "proposed_relations", ()) or ()
    method = getattr(cand, "method", "") or ""
    if not content:
        admissible, reason = False, "empty_content"
    elif proposed:
        admissible, reason = False, "hallucinated_relation"
    else:
        d = gw.admit_flag(confidence=getattr(cand, "confidence", 1.0),
                          ambiguous=getattr(cand, "ambiguous", False))
        admissible, reason = d.admissible, d.reason
        if admissible and method not in LEGAL_METHODS:
            # S7 closed method set: SPLGateway rejects any method outside
            # LEGAL_METHODS; the canonical layer must never admit what the
            # layer it consolidates rejects.
            admissible, reason = False, "invalid_method"
    if not admissible:
        errors.append(reason)
    return CanonicalClaimCandidate(
        content=content, confidence=getattr(cand, "confidence", 1.0),
        ambiguous=getattr(cand, "ambiguous", False),
        projection_entropy=None, emission_rule=None,
        admissible=admissible, admission_reason=reason,
        origin="desi_spl_adapter", claim_type=method,
        errors=errors)


__all__ = ["CanonicalClaimCandidate", "from_alexandria_candidate",
           "from_desi_spl_candidate"]
