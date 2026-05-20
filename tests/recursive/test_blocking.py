"""Tests for v1.4 INV-R3 — a blocked child blocks every ancestor (R3)."""
from __future__ import annotations

from desi.consilium import Verdict
from desi.recursive import RecursiveResolver, ResolutionState

from ._helpers import (
    ScriptedAuditor,
    ScriptedConsilium,
    needs_bridge,
)


# ---------------------------------------------------------------------------
# R3: B2 vetoed → root not upgraded
# ---------------------------------------------------------------------------


def test_r3_vetoed_grandchild_blocks_root() -> None:
    auditor = ScriptedAuditor(script={
        "root":  needs_bridge("root", "b1"),
        "b1":   needs_bridge("b1", "b2"),
    })
    consilium = ScriptedConsilium(blocked_bridges={"b2": Verdict.VETO})
    r = RecursiveResolver(
        auditor=auditor, consilium=consilium,
    ).resolve("root")
    assert r.final_state is ResolutionState.RESOLUTION_BLOCKED
    # Root is not in resolved_claims (because the cascade blocked it).
    from desi.recursive import node_id
    root_id = node_id("root")
    assert root_id not in r.resolved_claims


def test_r3_blocked_child_appears_in_blocked_set() -> None:
    auditor = ScriptedAuditor(script={
        "root": needs_bridge("root", "b1"),
        "b1":   needs_bridge("b1", "b2"),
    })
    consilium = ScriptedConsilium(blocked_bridges={"b2": Verdict.VETO})
    r = RecursiveResolver(
        auditor=auditor, consilium=consilium,
    ).resolve("root")
    from desi.recursive import node_id
    assert node_id("b2") in r.blocked_claims


def test_r3_open_gaps_propagate_to_root() -> None:
    auditor = ScriptedAuditor(script={
        "root": needs_bridge("root", "b1"),
        "b1":   needs_bridge("b1", "b2"),
    })
    consilium = ScriptedConsilium(blocked_bridges={"b2": Verdict.VETO})
    r = RecursiveResolver(
        auditor=auditor, consilium=consilium,
    ).resolve("root")
    # Root's id appears in open_gaps because at least one descendant
    # is unresolved.
    from desi.recursive import node_id
    assert node_id("root") in r.open_gaps


# ---------------------------------------------------------------------------
# Direct child block also blocks root
# ---------------------------------------------------------------------------


def test_directly_vetoed_child_blocks_root() -> None:
    auditor = ScriptedAuditor(script={
        "root": needs_bridge("root", "child"),
    })
    consilium = ScriptedConsilium(blocked_bridges={"child": Verdict.VETO})
    r = RecursiveResolver(
        auditor=auditor, consilium=consilium,
    ).resolve("root")
    assert r.final_state is ResolutionState.RESOLUTION_BLOCKED


def test_needs_more_premises_also_blocks_root() -> None:
    """A NEEDS_MORE_PREMISES verdict from consilium is not an
    acceptance — it must block the parent."""
    auditor = ScriptedAuditor(script={
        "root": needs_bridge("root", "child"),
    })
    consilium = ScriptedConsilium(
        blocked_bridges={"child": Verdict.NEEDS_MORE_PREMISES},
    )
    r = RecursiveResolver(
        auditor=auditor, consilium=consilium,
    ).resolve("root")
    assert r.final_state is ResolutionState.RESOLUTION_BLOCKED


# ---------------------------------------------------------------------------
# Sibling block: with two bridges, ONE blocked is enough to fail the parent
# ---------------------------------------------------------------------------


def test_one_blocked_sibling_blocks_parent() -> None:
    auditor = ScriptedAuditor(script={
        "root": needs_bridge("root", "good", "bad"),
    })
    consilium = ScriptedConsilium(blocked_bridges={"bad": Verdict.VETO})
    r = RecursiveResolver(
        auditor=auditor, consilium=consilium,
    ).resolve("root")
    assert r.final_state is ResolutionState.RESOLUTION_BLOCKED
    from desi.recursive import node_id
    assert node_id("bad") in r.blocked_claims
