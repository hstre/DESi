"""spl_core ↔ spl_adapter parity: the canonical layer must never admit a
candidate the layer it consolidates rejects (closed method set, S7)."""
from __future__ import annotations

from desi.spl_adapter import (
    ClaimCandidate,
    SPLGateway,
    make_deterministic_provenance,
)
from desi.spl_core import from_desi_spl_candidate


def _cand(**kw) -> ClaimCandidate:
    defaults = dict(
        content="water boils at 100°C",
        method="deterministic_semantic_projection",
        spl_provenance=make_deterministic_provenance(),
        confidence=0.9,
        ambiguous=False,
    )
    defaults.update(kw)
    return ClaimCandidate(**defaults)


def test_invalid_method_rejected_like_spl_gateway() -> None:
    cand = _cand(method="totally_invented_method")
    admitted, rejected = SPLGateway().admit((cand,), run_id="run_x")
    assert admitted == () and rejected[0][1] == "invalid_method"
    canonical = from_desi_spl_candidate(cand)
    assert canonical.admissible is False
    assert canonical.admission_reason == "invalid_method"
    assert "invalid_method" in canonical.errors


def test_legal_method_admitted_like_spl_gateway() -> None:
    cand = _cand()
    admitted, _ = SPLGateway().admit((cand,), run_id="run_x")
    assert len(admitted) == 1
    canonical = from_desi_spl_candidate(cand)
    assert canonical.admissible is True
    assert canonical.admission_reason == ""
    assert canonical.claim_type == "deterministic_semantic_projection"


def test_flag_rules_match_spl_gateway_precedence() -> None:
    # empty content outranks everything
    c = from_desi_spl_candidate(_cand(content=""))
    assert (c.admissible, c.admission_reason) == (False, "empty_content")
    # ambiguity / low confidence outrank invalid_method (gateway order)
    c = from_desi_spl_candidate(_cand(ambiguous=True, method="hearsay"))
    assert (c.admissible, c.admission_reason) == (False, "ambiguous_claim")
    c = from_desi_spl_candidate(_cand(confidence=0.1, method="hearsay"))
    assert (c.admissible, c.admission_reason) == (False, "ambiguous_claim")
