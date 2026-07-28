from __future__ import annotations

import hashlib
import json
from dataclasses import asdict

from .models import CandidateUpdate, ItemType, ValidationDecision, ValidationResult

RULESET_VERSION = "desi-validation-v0.1"


def _canonical_hash(candidate: CandidateUpdate) -> str:
    payload = json.dumps(
        asdict(candidate),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=lambda value: value.value,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def validate_candidate(candidate: CandidateUpdate) -> ValidationResult:
    """Validate a proposed state update without mutating external state.

    The rules are intentionally closed and deterministic. This first reference
    implementation is conservative: it accepts only candidates whose claim,
    provenance, evidence anchors, typed decomposition, and applicability are
    structurally complete and not contradicted.
    """

    reasons: list[str] = []
    required: list[str] = []
    evidence_by_id = {anchor.anchor_id: anchor for anchor in candidate.evidence}
    support_ids = sorted(
        anchor.anchor_id for anchor in candidate.evidence if anchor.polarity == "support"
    )
    counter_ids = sorted(
        anchor.anchor_id for anchor in candidate.evidence if anchor.polarity == "counter"
    )

    fatal = False
    if not candidate.candidate_id.strip():
        reasons.append("missing_candidate_id")
        fatal = True
    if not candidate.claim.strip():
        reasons.append("missing_claim")
        fatal = True
    if not candidate.source_trace_ids:
        reasons.append("missing_source_trace_provenance")
        fatal = True
    if not candidate.items:
        reasons.append("missing_typed_decomposition")
        fatal = True

    duplicate_item_ids = len({item.item_id for item in candidate.items}) != len(candidate.items)
    duplicate_anchor_ids = len(evidence_by_id) != len(candidate.evidence)
    if duplicate_item_ids:
        reasons.append("duplicate_item_id")
        fatal = True
    if duplicate_anchor_ids:
        reasons.append("duplicate_evidence_anchor_id")
        fatal = True

    has_observation = False
    has_inference = False
    has_assumption = False
    unsupported_items: list[str] = []

    for item in candidate.items:
        if not item.item_id.strip() or not item.text.strip():
            reasons.append("incomplete_epistemic_item")
            fatal = True
            continue

        missing_refs = sorted(ref for ref in item.evidence_ids if ref not in evidence_by_id)
        if missing_refs:
            reasons.append(f"unknown_evidence_reference:{item.item_id}")
            fatal = True

        if item.item_type is ItemType.OBSERVATION:
            has_observation = True
            if not item.evidence_ids:
                unsupported_items.append(item.item_id)
        elif item.item_type is ItemType.INFERENCE:
            has_inference = True
            if not item.evidence_ids:
                unsupported_items.append(item.item_id)
        elif item.item_type is ItemType.ASSUMPTION:
            has_assumption = True
            if not item.evidence_ids:
                required.append(f"verify_assumption:{item.item_id}")

    for anchor in candidate.evidence:
        if not anchor.anchor_id or not anchor.source_id or not anchor.content_hash:
            reasons.append("incomplete_evidence_anchor")
            fatal = True
        if anchor.polarity not in {"support", "counter"}:
            reasons.append(f"invalid_evidence_polarity:{anchor.anchor_id}")
            fatal = True

    if unsupported_items:
        reasons.append("unsupported_observation_or_inference")
        required.extend(f"attach_evidence:{item_id}" for item_id in sorted(unsupported_items))

    if not has_observation:
        reasons.append("no_typed_observation")
        required.append("provide_observation")
    if not has_inference and candidate.proposed_target.upper() == "L3":
        reasons.append("no_explicit_inference_for_L3_update")
        required.append("provide_inference")
    if not candidate.applicability_boundary.strip():
        reasons.append("missing_applicability_boundary")
        required.append("define_applicability_boundary")

    if fatal:
        decision = ValidationDecision.REJECTED
    elif counter_ids:
        decision = ValidationDecision.CONTRADICTED
        reasons.append("counterevidence_present")
    elif unsupported_items or not has_observation or not candidate.applicability_boundary.strip():
        decision = ValidationDecision.REQUIRES_VERIFICATION
    elif has_assumption:
        decision = ValidationDecision.HYPOTHESIS
        reasons.append("contains_assumption")
    elif not support_ids:
        decision = ValidationDecision.REQUIRES_VERIFICATION
        reasons.append("no_supporting_evidence")
        required.append("attach_supporting_evidence")
    else:
        decision = ValidationDecision.ADMISSIBLE
        reasons.append("structurally_supported_and_uncontradicted")

    return ValidationResult(
        candidate_id=candidate.candidate_id,
        decision=decision,
        reasons=tuple(sorted(set(reasons))),
        required_verification=tuple(sorted(set(required))),
        supporting_evidence_ids=tuple(support_ids),
        counterevidence_ids=tuple(counter_ids),
        input_hash=_canonical_hash(candidate),
        ruleset_version=RULESET_VERSION,
    )
