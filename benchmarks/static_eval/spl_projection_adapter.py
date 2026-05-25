#!/usr/bin/env python3
"""DESi-side adapter onto the vendored Alexandria Semantic Projection Layer (SPL).

THIS FILE IS DESi GLUE, NOT ORIGINAL SPL.
-----------------------------------------
The unmodified original SPL lives in ``vendor/alexandria_spl/`` (spl.py,
spl_gateway.py — MIT, Copyright Steffen Rentschler; see vendor/.../VENDOR.md).
This module is the DESi adapter that drives that code. It does NOT reimplement
any SPL logic; it only constructs the SPL's own data objects and calls the
SPL's own gateway.

What it does
------------
Takes a DESi *atomic claim* (a plain ``{subject, predicate, object,
confidence?}`` dict produced by the P2/P3 extraction stages) and pushes it
through the SPL's pre-protocol path:

    atomic claim
        -> SemanticUnit          (spl.SemanticUnit.new)
        -> SemanticProjection    (spl.SemanticProjection, P_r synthesized here)
        -> SPLGateway.submit      -> SPLResult (E0-E3 emission)
        -> ClaimCandidate         (result.top_candidate(), rank 1)

This enforces the SPL invariant for the DESi pipeline: a raw S/P/O triple is
NEVER treated as a canonical claim directly. It must first become a
SemanticUnit, be projected, and survive the gateway's emission rules before any
DESi conflict / graph stage may compare it.

What it deliberately does NOT do
--------------------------------
It does not call ``SPLGateway.emit_claim_nodes()``. That method routes through
``ClaimCandidateConverter.convert()``, which does ``from .schema import
ClaimNode`` — the *protocol-side* schema that is intentionally not vendored
(DESi has its own ClaimNode/Claim layer in ``src/desi/memory``). So the SPL's
"only legal path to a ClaimNode" terminates, for DESi, at a *validated
ClaimCandidate*; the DESi memory layer is the converter on the other side of
that boundary. ``gateway_valid`` below reflects whether the candidate would pass
the gateway's own candidate-validation gate (rule / confidence / entropy /
evidence), i.e. everything ``emit_claim_nodes`` checks before the protocol
conversion.

The P_r synthesis is an adapter HEURISTIC, not measured SPL output
------------------------------------------------------------------
The real SPL derives P_r from an NLP relation matrix (WP2 §3.3); we have no such
backend here. We synthesize a peaked relational distribution from the single
extracted predicate plus its scalar confidence: the predicate gets mass =
confidence, and the residual (1 - confidence) is spread *uniformly* (maximum
entropy given only the peak is known) over ``relation_space_size - 1`` synthetic
alternative-relation slots. Consequently ``h_norm`` here is a deterministic,
monotone function of the extractor's confidence — it is a *confidence-shaped
entropy*, NOT a semantic entropy measured over a real relation space. This is
documented honestly so nobody mistakes the gateway pass/block for a semantic
judgement; it is a confidence gate wearing the SPL's emission machinery.

No network, no secrets. stdlib + vendored stdlib-only SPL only.
"""
from __future__ import annotations

import sys
import uuid
from pathlib import Path

_VENDOR = Path(__file__).resolve().parent / "vendor" / "alexandria_spl"
if str(_VENDOR) not in sys.path:
    # spl_gateway.py does `from spl import ...`, so the vendor dir must be on
    # sys.path as a flat module location (not imported as a package).
    sys.path.insert(0, str(_VENDOR))

from spl import (  # noqa: E402  (original SPL, vendored)
    SemanticProjection,
    SemanticUnit,
    SPLThresholds,
)
from spl_gateway import (  # noqa: E402  (original SPL, vendored)
    CandidateRejectedError,
    SPLGateway,
)

# Adapter calibration (DESi-side, documented heuristic — NOT SPL defaults).
DEFAULT_RELATION_SPACE_SIZE = 8
"""Size |R| of the synthetic relation space. Chosen so a moderately-confident
extraction (confidence 0.7) yields h_norm ~= 0.57, comfortably below tau_3=0.65
(=> E2 emission, candidate usable), while confidence <= ~0.5 maps above tau_3
(=> E3 ambiguity block). Larger => more lenient (lower entropy per peak)."""

DEFAULT_CONFIDENCE = 0.7
"""Used when an atomic claim carries no explicit confidence (matches the
benchmark runner's record_claim confidence)."""

_CONF_LO, _CONF_HI = 0.01, 0.99
"""Confidence is clamped into this open-ish interval so P_r stays a proper
distribution (no degenerate 0/1 point mass that would distort h_norm)."""

ADAPTER_MATRIX_VERSION = "desi-spl-adapter-v1-synthetic-Pr"
"""Recorded in the projection so audit trails never mistake this synthetic P_r
for a real sealed SPL relation matrix."""


def _synthesize_relation_distribution(
    predicate: str, confidence: float, relation_space_size: int
) -> dict[str, float]:
    """Peaked P_r over a synthetic relation space (see module docstring).

    Peak (= the extracted predicate) gets ``confidence``; the residual is split
    uniformly over ``relation_space_size - 1`` placeholder slots. Placeholder
    keys only shape entropy; only the rank-1 (peak) candidate is ever consumed.
    """
    conf = min(_CONF_HI, max(_CONF_LO, float(confidence)))
    peak_key = predicate or "<empty-relation>"
    n_alt = max(0, int(relation_space_size) - 1)
    if n_alt == 0:
        return {peak_key: 1.0}
    residual = (1.0 - conf) / n_alt
    P_r: dict[str, float] = {peak_key: conf}
    if residual > 0:
        for i in range(n_alt):
            P_r[f"<alt-relation:{i + 1}>"] = residual
    return P_r


def _candidate_passes_gate(gateway: SPLGateway, candidate) -> tuple[bool, str]:
    """Run the SPL gateway's OWN candidate-validation gate (the same checks
    ``emit_claim_nodes`` applies before protocol conversion), without crossing
    into the protocol-side ClaimNode conversion that DESi owns.

    We call the gateway's own ``_validate_candidate`` so the gate criteria stay
    a single source of truth (re-implementing them here would risk drifting from
    the vendored SPL)."""
    try:
        gateway._validate_candidate(candidate, jsd=None, evidence_count=1)
        return True, ""
    except CandidateRejectedError as e:
        return False, str(e)


def project_atomic_claim_to_candidate(
    claim: dict,
    *,
    relation_space_size: int = DEFAULT_RELATION_SPACE_SIZE,
    thresholds: SPLThresholds | None = None,
    k: int = 3,
) -> dict:
    """Project one DESi atomic claim through the vendored SPL pre-protocol path.

    Parameters
    ----------
    claim
        ``{"subject", "predicate", "object", "confidence"?, "source_ref"?}``.
    relation_space_size
        Size of the synthetic relation space for P_r (calibration knob).
    thresholds
        Optional SPL ``SPLThresholds``; defaults to WP2 recommended values.
    k
        Top-k for E2 multiple emission (only rank-1 is consumed downstream).

    Returns
    -------
    dict with keys:
        semantic_unit       SemanticUnit.to_dict()
        semantic_projection SemanticProjection.to_dict() (status, emission_rule,
                            h_norm included)
        claim_candidate     ClaimCandidate.to_dict() of the rank-1 candidate, or
                            None if the projection was blocked (E0/E3)
        projection_entropy  h_norm of the projection (float)
        projection_method   "spl_adapter"
        gateway_valid       True iff a rank-1 candidate exists AND passes the
                            gateway candidate-validation gate
        errors              list[str] of issues (empty inputs, block/reject
                            reasons) — empty on a clean E1/E2 emission
        emission_status     projection status value ("ready_for_claim",
                            "ambiguous", ...)
        emission_rule       "E0".."E4" or None
    """
    errors: list[str] = []
    subject = str(claim.get("subject", "") or "").strip()
    predicate = str(claim.get("predicate", "") or "").strip()
    obj = str(claim.get("object", "") or "").strip()
    if not subject:
        errors.append("empty_subject")
    if not predicate:
        errors.append("empty_predicate")
    if not obj:
        errors.append("empty_object")
    confidence = claim.get("confidence", DEFAULT_CONFIDENCE)
    try:
        confidence = float(confidence)
    except (TypeError, ValueError):
        errors.append(f"bad_confidence:{confidence!r}->default")
        confidence = DEFAULT_CONFIDENCE

    source_text = " ".join(p for p in (subject, predicate, obj) if p)
    unit = SemanticUnit.new(
        source_text=source_text or "<empty>",
        source_ref=str(claim.get("source_ref", "desi_atomic_claim")),
        fragmentation_signal="desi_spl_adapter",
    )

    P_r = _synthesize_relation_distribution(predicate, confidence, relation_space_size)
    projection = SemanticProjection(
        projection_id=str(uuid.uuid4()),
        unit_id=unit.unit_id,
        builder_origin="alpha",
        matrix_version=ADAPTER_MATRIX_VERSION,
        P_r=P_r,
        subject_candidates=[subject] if subject else [],
        object_candidates=[obj] if obj else [],
        P_modality={"asserted": 1.0},
        P_category={"dynamic": 1.0},
        p_illegal=0.0,
    )

    gateway = SPLGateway(thresholds=thresholds, audit_log_path=None)
    result = gateway.submit(projection, k=k)

    candidate = result.top_candidate()
    gateway_valid = False
    if candidate is None:
        # E0 (structural) or E3 (ambiguity) — no candidate emitted.
        errors.append(
            f"blocked:{projection.status.value}"
            f"({projection.emission_rule.value if projection.emission_rule else '-'})"
            f"@h_norm={projection.h_norm:.3f}"
        )
    else:
        gateway_valid, reason = _candidate_passes_gate(gateway, candidate)
        if not gateway_valid:
            errors.append(f"gateway_reject:{reason}")
        # The full emit_claim_nodes path also runs validate_claim_node (non-empty
        # subject/relation/object). A structurally-empty candidate could never
        # become a valid ClaimNode, so it is not gateway-valid either.
        elif not (candidate.subject.strip() and candidate.relation.strip()
                  and candidate.object.strip()):
            gateway_valid = False
            errors.append("structural_invalid:empty_subject_relation_or_object")

    return {
        "semantic_unit": unit.to_dict(),
        "semantic_projection": projection.to_dict(),
        "claim_candidate": candidate.to_dict() if candidate else None,
        "projection_entropy": projection.h_norm,
        "projection_method": "spl_adapter",
        "gateway_valid": gateway_valid,
        "errors": errors,
        "emission_status": projection.status.value,
        "emission_rule": projection.emission_rule.value if projection.emission_rule else None,
    }


def _smoke() -> int:
    samples = [
        {"subject": "Abraham Lincoln", "predicate": "birth year", "object": "1809", "confidence": 0.9},
        {"subject": "the Earth", "predicate": "is", "object": "flat", "confidence": 0.7},
        {"subject": "the suspect", "predicate": "was in", "object": "London", "confidence": 0.45},
        {"subject": "", "predicate": "", "object": "", "confidence": 0.7},
    ]
    print(f"relation_space_size={DEFAULT_RELATION_SPACE_SIZE}")
    for c in samples:
        r = project_atomic_claim_to_candidate(c)
        cand = r["claim_candidate"]
        rel = cand["relation"] if cand else "-"
        print(
            f"  conf={c.get('confidence'):.2f} '{c['subject']}|{c['predicate']}|{c['object']}'"
            f" -> status={r['emission_status']} rule={r['emission_rule']}"
            f" h_norm={r['projection_entropy']:.3f} gateway_valid={r['gateway_valid']}"
            f" rel={rel!r} errors={r['errors']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(_smoke())
