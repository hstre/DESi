"""Tests for desi.spl_core — the canonical SPL projection / admissibility layer.

Covers the public surface only: entropy, gateway admissibility (both modes),
candidate construction, atomic-claim projection, governance flags, and the
adapter from an existing desi.spl_adapter candidate. No benchmark or research
harness is involved — spl_core is self-contained (stdlib + a lazy spl_adapter
import used solely by from_desi_spl_candidate).
"""
from __future__ import annotations

import math

from desi.spl_core import (
    PROJECTION_HIGH_ENTROPY,
    PROJECTION_INVALID,
    PROJECTION_UNCERTAIN,
    CanonicalClaimCandidate,
    CanonicalGateway,
    CanonicalThresholds,
    from_desi_spl_candidate,
    normalized_shannon_entropy,
    project_atomic_claim,
    projection_flags,
    synthesize_relation_distribution,
)


# --------------------------------------------------------------------------- #
# entropy
# --------------------------------------------------------------------------- #
def test_entropy_single_key_is_zero() -> None:
    assert normalized_shannon_entropy({"a": 1.0}) == 0.0
    assert normalized_shannon_entropy({}) == 0.0


def test_entropy_uniform_two_is_one() -> None:
    assert normalized_shannon_entropy({"a": 0.5, "b": 0.5}) == 1.0


def test_entropy_peaked_below_uniform() -> None:
    h = normalized_shannon_entropy({"a": 0.9, "b": 0.05, "c": 0.05})
    assert 0.0 < h < 1.0


def test_synthesize_distribution_peaks_and_normalises() -> None:
    P_r = synthesize_relation_distribution("born_in", 0.9, relation_space_size=8)
    assert len(P_r) == 8
    assert abs(sum(P_r.values()) - 1.0) < 1e-9
    assert P_r["born_in"] == max(P_r.values())


def test_synthesize_distribution_clamps_extremes() -> None:
    # confidence 1.0 is clamped below 1.0 so residual mass stays > 0
    P_r = synthesize_relation_distribution("p", 1.0, relation_space_size=8)
    assert max(P_r.values()) < 1.0
    assert abs(sum(P_r.values()) - 1.0) < 1e-9


# --------------------------------------------------------------------------- #
# gateway admissibility — entropy model
# --------------------------------------------------------------------------- #
def test_gateway_invalid_thresholds_rejected() -> None:
    bad = CanonicalThresholds(tau_2=0.9, tau_3=0.5)  # tau_2 must be < tau_3
    try:
        CanonicalGateway(bad)
    except ValueError:
        return
    raise AssertionError("expected ValueError for invalid thresholds")


def test_gateway_high_confidence_admits_e1() -> None:
    gw = CanonicalGateway()
    P_r = synthesize_relation_distribution("p", 0.95)
    d = gw.admit_projection(P_r)
    assert d.admissible and d.emission_rule == "E1"


def test_gateway_mid_confidence_admits_e2() -> None:
    gw = CanonicalGateway()
    P_r = synthesize_relation_distribution("p", 0.7)
    d = gw.admit_projection(P_r)
    assert d.admissible and d.emission_rule == "E2"


def test_gateway_low_confidence_blocks_e3() -> None:
    gw = CanonicalGateway()
    P_r = synthesize_relation_distribution("p", 0.4)
    d = gw.admit_projection(P_r)
    assert (not d.admissible) and d.emission_rule == "E3"


def test_gateway_structural_violation_blocks_e0() -> None:
    gw = CanonicalGateway()
    d = gw.admit_projection({"p": 1.0}, p_illegal=0.99)
    assert (not d.admissible) and d.emission_rule == "E0"


# --------------------------------------------------------------------------- #
# gateway admissibility — flag model
# --------------------------------------------------------------------------- #
def test_gateway_flag_admits_confident() -> None:
    d = CanonicalGateway().admit_flag(confidence=0.9, ambiguous=False)
    assert d.admissible and d.emission_rule is None and d.model == "flag"


def test_gateway_flag_blocks_ambiguous() -> None:
    d = CanonicalGateway().admit_flag(confidence=0.9, ambiguous=True)
    assert (not d.admissible) and d.reason == "ambiguous_claim"


def test_gateway_flag_blocks_below_floor() -> None:
    d = CanonicalGateway().admit_flag(confidence=0.4, ambiguous=False)
    assert (not d.admissible) and d.reason == "ambiguous_claim"


# --------------------------------------------------------------------------- #
# candidate construction
# --------------------------------------------------------------------------- #
def test_candidate_as_conflict_claim() -> None:
    c = CanonicalClaimCandidate(subject="s", predicate="p", object="o")
    cc = c.as_conflict_claim(_id="x1", state="proposed")
    assert cc == {"_id": "x1", "subject": "s", "predicate": "p",
                  "object": "o", "state": "proposed"}


def test_candidate_to_dict_roundtrip_keys() -> None:
    c = CanonicalClaimCandidate(subject="s", predicate="p", object="o",
                                content="s | p | o", admissible=True)
    d = c.to_dict()
    for k in ("subject", "predicate", "object", "content", "admissible",
              "projection_entropy", "emission_rule", "origin", "candidate_id"):
        assert k in d


# --------------------------------------------------------------------------- #
# projection from atomic claim
# --------------------------------------------------------------------------- #
def test_projection_admits_confident_triple() -> None:
    cand, proj = project_atomic_claim(
        {"subject": "Lincoln", "predicate": "born_in", "object": "1809",
         "confidence": 0.95})
    assert cand.admissible
    assert cand.emission_rule in ("E1", "E2")
    assert cand.subject == "Lincoln" and cand.predicate == "born_in"
    assert proj.projection_id == cand.projection_id
    assert math.isclose(sum(proj.P_r.values()), 1.0, abs_tol=1e-9)


def test_projection_blocks_low_confidence() -> None:
    cand, _ = project_atomic_claim(
        {"subject": "x", "predicate": "y", "object": "z", "confidence": 0.4})
    assert not cand.admissible
    assert cand.emission_rule == "E3"


def test_projection_blocks_empty_triple() -> None:
    cand, _ = project_atomic_claim(
        {"subject": "", "predicate": "", "object": "", "confidence": 0.9})
    assert not cand.admissible
    assert any(e.startswith("empty_") for e in cand.errors)


# --------------------------------------------------------------------------- #
# governance flags
# --------------------------------------------------------------------------- #
def test_flags_e2_is_uncertain() -> None:
    cand, _ = project_atomic_claim(
        {"subject": "a", "predicate": "p", "object": "b", "confidence": 0.7})
    assert PROJECTION_UNCERTAIN in projection_flags(cand)


def test_flags_e3_is_invalid_and_high_entropy() -> None:
    cand, _ = project_atomic_claim(
        {"subject": "a", "predicate": "p", "object": "b", "confidence": 0.4})
    flags = projection_flags(cand)
    assert PROJECTION_INVALID in flags and PROJECTION_HIGH_ENTROPY in flags


def test_flags_clean_e1_has_none() -> None:
    cand, _ = project_atomic_claim(
        {"subject": "a", "predicate": "p", "object": "b", "confidence": 0.99})
    assert projection_flags(cand) == []


# --------------------------------------------------------------------------- #
# adapter from an existing desi.spl_adapter candidate (flag model)
# --------------------------------------------------------------------------- #
def test_adapter_from_desi_spl_candidate_admits_confident() -> None:
    from desi.spl_adapter.mapping import ClaimCandidate
    from desi.spl_adapter.provenance import make_deterministic_provenance
    dc = ClaimCandidate(content="water boils at 100C",
                        method="deterministic_semantic_projection",
                        spl_provenance=make_deterministic_provenance(),
                        confidence=0.9, ambiguous=False)
    can = from_desi_spl_candidate(dc)
    assert can.admissible
    assert can.origin == "desi_spl_adapter"
    assert can.projection_entropy is None  # flag model has no entropy


def test_adapter_from_desi_spl_candidate_blocks_ambiguous() -> None:
    from desi.spl_adapter.mapping import ClaimCandidate
    from desi.spl_adapter.provenance import make_deterministic_provenance
    dc = ClaimCandidate(content="maybe true",
                        method="deterministic_semantic_projection",
                        spl_provenance=make_deterministic_provenance(),
                        confidence=0.4, ambiguous=True)
    can = from_desi_spl_candidate(dc)
    assert not can.admissible
    assert can.admission_reason == "ambiguous_claim"
