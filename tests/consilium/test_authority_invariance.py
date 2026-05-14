"""Tests for v1.3 INV-C2 — authority metadata must never change the verdict.

C4 scenario: same invalid bridge proposed by Nobel laureate,
university institute, and anonymous blogger → identical verdict.
"""
from __future__ import annotations

from desi.consilium import (
    BridgeConsilium,
    Verdict,
)
from desi.logic import LogicalAuditor


# ---------------------------------------------------------------------------
# C4: prestige trap
# ---------------------------------------------------------------------------


def _build_offtopic_consilium():
    """An off-topic bridge proposed against the rain/street audit."""
    from desi.logic.bridge_claims import BridgeClaim, BRIDGE_METHOD
    from desi.memory.claim import Claim, ClaimState, Provenance
    audit = LogicalAuditor().audit(
        "It is raining. Therefore the street is wet."
    )
    bridge = BridgeClaim(
        bridge_id="br_prestige_trap",
        text="thunder is loud during storms",
        claim=Claim(
            content="thunder is loud during storms",
            method=BRIDGE_METHOD,
            state=ClaimState.PROPOSED,
            provenance=Provenance(source="x", run_id="r1"),
        ),
        rationale="testing the prestige trap",
    )
    return BridgeConsilium(), bridge, audit


def test_c4_prestige_trap_same_verdict_across_authors() -> None:
    cons, bridge, audit = _build_offtopic_consilium()
    sources = [
        {"author": "Nobel laureate", "institution": "Karolinska"},
        {"author": "University Institute"},
        {"author": "anonymous blogger"},
        {"author": "alice", "citation_count": 9999, "h_index": 142},
    ]
    verdicts = set()
    for src in sources:
        res = cons.deliberate(
            bridge, source_claim_id=audit.audit_id,
            original_text=audit.text,
            source_metadata=src,
        )
        verdicts.add(res.verdict.verdict)
    assert len(verdicts) == 1


# ---------------------------------------------------------------------------
# INV-C2: metadata never changes the verdict
# ---------------------------------------------------------------------------


def test_inv_c2_changing_author_does_not_change_verdict() -> None:
    cons, bridge, audit = _build_offtopic_consilium()
    a = cons.deliberate(
        bridge, source_claim_id=audit.audit_id,
        original_text=audit.text,
        source_metadata={"author": "alice"},
    )
    b = cons.deliberate(
        bridge, source_claim_id=audit.audit_id,
        original_text=audit.text,
        source_metadata={"author": "bob"},
    )
    assert a.verdict.verdict == b.verdict.verdict


def test_inv_c2_changing_institution_does_not_change_verdict() -> None:
    cons, bridge, audit = _build_offtopic_consilium()
    a = cons.deliberate(
        bridge, source_claim_id=audit.audit_id,
        original_text=audit.text,
        source_metadata={"institution": "MIT"},
    )
    b = cons.deliberate(
        bridge, source_claim_id=audit.audit_id,
        original_text=audit.text,
        source_metadata={"institution": "anonymous_blog"},
    )
    assert a.verdict.verdict == b.verdict.verdict


def test_inv_c2_no_metadata_is_equivalent_to_arbitrary_metadata() -> None:
    cons, bridge, audit = _build_offtopic_consilium()
    a = cons.deliberate(
        bridge, source_claim_id=audit.audit_id,
        original_text=audit.text,
    )
    b = cons.deliberate(
        bridge, source_claim_id=audit.audit_id,
        original_text=audit.text,
        source_metadata={
            "author": "Nobel laureate",
            "title": "Definitive treatment",
            "citation_count": 99999,
        },
    )
    assert a.verdict.verdict == b.verdict.verdict
    assert a.replay_hash == b.replay_hash


# ---------------------------------------------------------------------------
# An authority storm cannot promote a vetoed bridge
# ---------------------------------------------------------------------------


def test_authority_storm_cannot_overturn_a_counterexample_veto() -> None:
    audit = LogicalAuditor().audit(
        "It is raining. Therefore the street is wet."
    )
    metadata = {
        "author": "Nobel laureate",
        "title": "Definitive treatise",
        "h_index": 9999,
        "citation_count": 100000,
        "institution": "Cambridge",
        "source_reputation_score": 1.0,
    }
    res = BridgeConsilium().deliberate(
        audit.bridges[0],
        source_claim_id=audit.audit_id,
        original_text=audit.text,
        additional_conditions=("the street has a roof",),
        source_metadata=metadata,
    )
    assert res.verdict.verdict is Verdict.VETO


# ---------------------------------------------------------------------------
# Clean P1 bridge still gets ACCEPT regardless of metadata
# ---------------------------------------------------------------------------


def test_clean_bridge_accept_invariant_under_metadata() -> None:
    audit = LogicalAuditor().audit(
        "It is raining. Therefore the street is wet."
    )
    cons = BridgeConsilium()
    for src in (
        {"author": "alice"},
        {"author": "Nobel laureate", "h_index": 9999},
        {"institution": "anonymous_blog"},
        None,
    ):
        res = cons.deliberate(
            audit.bridges[0],
            source_claim_id=audit.audit_id,
            original_text=audit.text,
            source_metadata=src,
        )
        assert res.verdict.verdict is Verdict.ACCEPT_AS_BRIDGE
