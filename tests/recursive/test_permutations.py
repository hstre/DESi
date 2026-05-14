"""Tests for v1.4 INV-R2 — recursion order does not change final_state (R6)."""
from __future__ import annotations

from desi.recursive import RecursiveResolver, ResolutionState

from ._helpers import (
    ScriptedAuditor,
    ScriptedConsilium,
    needs_bridge,
)


# ---------------------------------------------------------------------------
# Build a node with two siblings whose bridge order can be permuted.
# ---------------------------------------------------------------------------


def _two_sibling_auditor(child_a_first: bool):
    """Returns an auditor whose root has two bridges in the given order."""
    if child_a_first:
        return ScriptedAuditor(script={
            "root": needs_bridge("root", "child_a", "child_b"),
        })
    return ScriptedAuditor(script={
        "root": needs_bridge("root", "child_b", "child_a"),
    })


def test_two_siblings_resolve_to_same_final_state() -> None:
    a_first = RecursiveResolver(
        auditor=_two_sibling_auditor(True),
        consilium=ScriptedConsilium(),
    ).resolve("root")
    b_first = RecursiveResolver(
        auditor=_two_sibling_auditor(False),
        consilium=ScriptedConsilium(),
    ).resolve("root")
    assert a_first.final_state == b_first.final_state
    assert a_first.final_state is ResolutionState.RESOLUTION_COMPLETE


def test_two_siblings_resolve_to_same_replay_hash() -> None:
    """R6: child resolution order does not change replay_hash."""
    a_first = RecursiveResolver(
        auditor=_two_sibling_auditor(True),
        consilium=ScriptedConsilium(),
    ).resolve("root")
    b_first = RecursiveResolver(
        auditor=_two_sibling_auditor(False),
        consilium=ScriptedConsilium(),
    ).resolve("root")
    assert a_first.replay_hash == b_first.replay_hash


def test_two_siblings_resolved_set_is_identical() -> None:
    a = RecursiveResolver(
        auditor=_two_sibling_auditor(True),
        consilium=ScriptedConsilium(),
    ).resolve("root")
    b = RecursiveResolver(
        auditor=_two_sibling_auditor(False),
        consilium=ScriptedConsilium(),
    ).resolve("root")
    assert set(a.resolved_claims) == set(b.resolved_claims)


# ---------------------------------------------------------------------------
# Three siblings → 6 permutations all yield identical hash
# ---------------------------------------------------------------------------


def test_three_sibling_permutations_all_yield_same_hash() -> None:
    from itertools import permutations
    siblings = ("c1", "c2", "c3")
    hashes = set()
    for perm in permutations(siblings):
        auditor = ScriptedAuditor(script={
            "root": needs_bridge("root", *perm),
        })
        r = RecursiveResolver(
            auditor=auditor, consilium=ScriptedConsilium(),
        ).resolve("root")
        hashes.add(r.replay_hash)
    assert len(hashes) == 1


# ---------------------------------------------------------------------------
# Permutation invariance under a partial block
# ---------------------------------------------------------------------------


def test_blocking_outcome_is_permutation_invariant() -> None:
    """When one sibling is vetoed, both orderings still yield BLOCKED."""
    from desi.consilium import Verdict
    a = RecursiveResolver(
        auditor=_two_sibling_auditor(True),
        consilium=ScriptedConsilium(
            blocked_bridges={"child_a": Verdict.VETO},
        ),
    ).resolve("root")
    b = RecursiveResolver(
        auditor=_two_sibling_auditor(False),
        consilium=ScriptedConsilium(
            blocked_bridges={"child_a": Verdict.VETO},
        ),
    ).resolve("root")
    assert a.final_state == b.final_state == ResolutionState.RESOLUTION_BLOCKED
    assert set(a.blocked_claims) == set(b.blocked_claims)
