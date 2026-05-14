"""Tests for the v1.2 authority-independence invariants L1 / L2 / L3.

INV-L1: changing author / title / source must never change logical state.
INV-L2: adding ten identical documents must never change logical state.
INV-L3: removing all source metadata while keeping the logic identical
        must preserve logical state.
"""
from __future__ import annotations

from desi.logic import LogicalAuditor, LogicalState
from desi.spl_adapter import SourceDocument, SPLAdapter


def _aud() -> LogicalAuditor:
    return LogicalAuditor()


# ---------------------------------------------------------------------------
# Directive's required scenarios
# ---------------------------------------------------------------------------


def test_p1_complete_syllogism_is_logically_supported() -> None:
    r = _aud().audit(
        "All men are mortal. Socrates is a man. "
        "Therefore Socrates is mortal."
    )
    assert r.state == LogicalState.LOGICALLY_SUPPORTED


def test_p2_authority_trap_is_gap_detected() -> None:
    r = _aud().audit("Professor X says quantum gravity is solved.")
    assert r.state == LogicalState.GAP_DETECTED


def test_p3_hidden_assumption_is_bridge_required() -> None:
    r = _aud().audit("It is raining. Therefore the street is wet.")
    assert r.state == LogicalState.BRIDGE_REQUIRED


def test_p5_invalid_transitivity_is_logically_rejected() -> None:
    r = _aud().audit("a -> b. b -> c. Therefore a -> d.")
    assert r.state == LogicalState.LOGICALLY_REJECTED


# ---------------------------------------------------------------------------
# INV-L1: changing author / title / source must never change verdict
# ---------------------------------------------------------------------------


_TEXT = (
    "Professor X says quantum gravity is solved."
)


def test_inv_l1_changing_author_does_not_change_verdict() -> None:
    a = _aud().audit(_TEXT, source_metadata={"author": "alice"})
    b = _aud().audit(_TEXT, source_metadata={"author": "bob"})
    assert a.state == b.state


def test_inv_l1_changing_title_does_not_change_verdict() -> None:
    a = _aud().audit(_TEXT, source_metadata={"title": "Modest blog post"})
    b = _aud().audit(_TEXT, source_metadata={"title": "Nature 2026"})
    assert a.state == b.state


def test_inv_l1_changing_source_label_does_not_change_verdict() -> None:
    a = _aud().audit(_TEXT, source_metadata={"source": "spl_llm"})
    b = _aud().audit(_TEXT, source_metadata={"source": "human"})
    assert a.state == b.state


# ---------------------------------------------------------------------------
# INV-L2: ten identical documents → identical state (P4 prestige trap)
# ---------------------------------------------------------------------------


def test_inv_l2_ten_identical_documents_yield_same_verdict() -> None:
    """The directive's P4: same unsupported claim in blog, university
    PDF, peer-reviewed article. Logical state must not change with
    document count or document type."""
    auditor = _aud()
    sources = [
        {"document_id": "blog_post", "content_type": "text/html"},
        {"document_id": "uni_pdf", "content_type": "application/pdf"},
        {"document_id": "peer_review", "content_type": "text/plain"},
    ]
    sources += [
        {"document_id": f"copy_{i}", "content_type": "text/plain"}
        for i in range(7)
    ]
    verdicts = [
        auditor.audit(_TEXT, source_metadata=src).state
        for src in sources
    ]
    assert len(set(verdicts)) == 1, f"verdicts diverged: {verdicts}"


def test_inv_l2_identical_logic_p1_is_supported_for_all_sources() -> None:
    auditor = _aud()
    text = ("All men are mortal. Socrates is a man. "
            "Therefore Socrates is mortal.")
    for src in (
        {"author": "alice"},
        {"author": "bob", "title": "high prestige journal"},
        {"document_count": 1000, "citation_count": 9999},
    ):
        r = auditor.audit(text, source_metadata=src)
        assert r.state == LogicalState.LOGICALLY_SUPPORTED


# ---------------------------------------------------------------------------
# INV-L3: removing all source metadata preserves verdict
# ---------------------------------------------------------------------------


def test_inv_l3_dropping_metadata_preserves_verdict() -> None:
    auditor = _aud()
    with_meta = auditor.audit(_TEXT, source_metadata={
        "author": "alice", "title": "x", "source": "y",
        "document_count": 17,
    })
    without_meta = auditor.audit(_TEXT)
    assert with_meta.state == without_meta.state


def test_inv_l3_replay_hash_is_independent_of_metadata() -> None:
    text = ("All men are mortal. Socrates is a man. "
            "Therefore Socrates is mortal.")
    a = _aud().audit(text, source_metadata={"author": "alice"})
    b = _aud().audit(text, source_metadata={"author": "bob"})
    assert a.proof_chain is not None and b.proof_chain is not None
    assert a.proof_chain.replay_hash == b.proof_chain.replay_hash


# ---------------------------------------------------------------------------
# Integration with SPL: P4-style prestige trap on real SPL claims
# ---------------------------------------------------------------------------


def test_p4_multi_source_prestige_trap_via_spl_adapter() -> None:
    """Same authority claim emitted by three different SPL document
    types yields the same audit verdict (GAP_DETECTED). The SPL
    metadata is *available* on the Claim's provenance but the
    auditor never reads it."""
    adapter = SPLAdapter()
    text = "Professor X says quantum gravity is solved."
    sources = [
        SourceDocument(document_id="blog", content=text,
                       content_type="text/html",
                       author="anonymous_blog"),
        SourceDocument(document_id="uni_paper", content=text,
                       content_type="text/plain",
                       author="university_press"),
        SourceDocument(document_id="peer_review", content=text,
                       content_type="text/markdown",
                       author="nature_2026"),
    ]
    # The SPL deterministic backend may or may not produce a claim
    # for the surface text; what we assert is invariance of the
    # logical verdict on the *text*.
    auditor = _aud()
    verdicts = [auditor.audit(d.content,
                              source_metadata={"document_id": d.document_id,
                                                "author": d.author})
                .state
                for d in sources]
    assert len(set(verdicts)) == 1
    assert verdicts[0] == LogicalState.GAP_DETECTED


# ---------------------------------------------------------------------------
# Bonus: an absurdly authoritative metadata blob does not flip a
# rejected verdict to supported.
# ---------------------------------------------------------------------------


def test_authority_storm_does_not_promote_invalid_inference() -> None:
    auditor = _aud()
    text = "a -> b. b -> c. Therefore a -> d."
    metadata = {
        "author": "Nobel laureate",
        "title": "PNAS replication of replication",
        "document_count": 10000,
        "citation_count": 999999,
        "source_reputation_score": 1.0,
    }
    r = auditor.audit(text, source_metadata=metadata)
    assert r.state == LogicalState.LOGICALLY_REJECTED
