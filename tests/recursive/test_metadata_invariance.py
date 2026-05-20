"""Tests for v1.4 INV-R6 — removing metadata does not change resolution.

Mirrors INV-L1/L2/L3 (v1.2) and INV-C2 (v1.3): the resolver
accepts ``source_metadata`` but immediately drops it. Authority
information cannot ever change a resolution outcome.
"""
from __future__ import annotations

from desi.recursive import RecursiveResolver, ResolutionState

from ._helpers import (
    ScriptedAuditor,
    ScriptedConsilium,
    needs_bridge,
)


def _resolver():
    auditor = ScriptedAuditor(script={
        "root": needs_bridge("root", "b1"),
        "b1":  needs_bridge("b1", "b2"),
    })
    return RecursiveResolver(
        auditor=auditor, consilium=ScriptedConsilium(),
    )


# ---------------------------------------------------------------------------
# Removing metadata does not change verdict
# ---------------------------------------------------------------------------


def test_no_metadata_matches_arbitrary_metadata() -> None:
    a = _resolver().resolve("root")
    b = _resolver().resolve("root", source_metadata={
        "author": "Nobel laureate",
        "title": "Important paper",
        "citation_count": 99999,
    })
    assert a.final_state == b.final_state
    assert a.replay_hash == b.replay_hash


def test_changing_author_does_not_change_resolution() -> None:
    a = _resolver().resolve("root", source_metadata={"author": "alice"})
    b = _resolver().resolve("root", source_metadata={"author": "bob"})
    assert a.final_state == b.final_state
    assert a.replay_hash == b.replay_hash


def test_changing_institution_does_not_change_resolution() -> None:
    a = _resolver().resolve("root", source_metadata={"institution": "MIT"})
    b = _resolver().resolve("root",
                              source_metadata={"institution": "anonymous_blog"})
    assert a.final_state == b.final_state
    assert a.replay_hash == b.replay_hash


# ---------------------------------------------------------------------------
# Authority storm cannot rescue a blocked resolution
# ---------------------------------------------------------------------------


def test_authority_storm_does_not_promote_blocked_root() -> None:
    """A vetoed grandchild stays blocked, even with absurd metadata."""
    from desi.consilium import Verdict
    auditor = ScriptedAuditor(script={
        "root": needs_bridge("root", "b1"),
        "b1":  needs_bridge("b1", "b2"),
    })
    cons = ScriptedConsilium(blocked_bridges={"b2": Verdict.VETO})
    metadata = {
        "author": "Nobel laureate",
        "h_index": 9999, "citation_count": 100000,
        "institution": "Cambridge", "source_reputation_score": 1.0,
    }
    res = RecursiveResolver(
        auditor=auditor, consilium=cons,
    ).resolve("root", source_metadata=metadata)
    assert res.final_state is ResolutionState.RESOLUTION_BLOCKED


# ---------------------------------------------------------------------------
# Real-component invariance (R1 with metadata bombs)
# ---------------------------------------------------------------------------


def test_r1_real_components_invariant_under_metadata() -> None:
    text = "It is raining. Therefore the street is wet."
    a = RecursiveResolver().resolve(text)
    b = RecursiveResolver().resolve(text, source_metadata={
        "author": "anonymous", "h_index": 0,
    })
    c = RecursiveResolver().resolve(text, source_metadata={
        "author": "Nobel laureate", "h_index": 9999,
        "citation_count": 99999,
    })
    assert a.replay_hash == b.replay_hash == c.replay_hash
    assert a.final_state == b.final_state == c.final_state
