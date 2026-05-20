"""Tests for v1.4 INV-R4 — cycle detection (R4 scenario)."""
from __future__ import annotations

from desi.recursive import (
    RecursiveResolver,
    ResolutionState,
    check_for_cycle,
    node_id,
)

from ._helpers import (
    ScriptedAuditor,
    ScriptedConsilium,
    needs_bridge,
)


# ---------------------------------------------------------------------------
# check_for_cycle helper
# ---------------------------------------------------------------------------


def test_cycle_helper_returns_none_when_no_cycle() -> None:
    assert check_for_cycle("rn_x", ("rn_a", "rn_b")) is None


def test_cycle_helper_detects_self_revisit() -> None:
    hit = check_for_cycle("rn_a", ("rn_a", "rn_b", "rn_c"))
    assert hit is not None
    assert hit.repeated_node == "rn_a"
    assert hit.cycle_path == ("rn_a", "rn_b", "rn_c", "rn_a")


# ---------------------------------------------------------------------------
# R4: A → B → C → A
# ---------------------------------------------------------------------------


def test_r4_cycle_a_b_c_a_detected() -> None:
    auditor = ScriptedAuditor(script={
        "a": needs_bridge("a", "b"),
        "b": needs_bridge("b", "c"),
        "c": needs_bridge("c", "a"),  # cycles back to root
    })
    r = RecursiveResolver(
        auditor=auditor, consilium=ScriptedConsilium(),
    ).resolve("a")
    assert r.final_state is ResolutionState.RESOLUTION_CYCLE_DETECTED
    assert len(r.cycle_path) >= 4  # a → b → c → a (at least)
    # The repeated node id must equal the root.
    assert r.cycle_path[0] == r.cycle_path[-1] == node_id("a")


# ---------------------------------------------------------------------------
# A two-step cycle: A → B → A
# ---------------------------------------------------------------------------


def test_two_step_cycle_detected() -> None:
    auditor = ScriptedAuditor(script={
        "a": needs_bridge("a", "b"),
        "b": needs_bridge("b", "a"),
    })
    r = RecursiveResolver(
        auditor=auditor, consilium=ScriptedConsilium(),
    ).resolve("a")
    assert r.final_state is ResolutionState.RESOLUTION_CYCLE_DETECTED


# ---------------------------------------------------------------------------
# A non-cycle DAG with shared dependency does NOT trigger cycle.
# ---------------------------------------------------------------------------


def test_shared_dependency_is_not_a_cycle() -> None:
    """A → B, A → C, B → D, C → D. D appears twice but on different paths."""
    auditor = ScriptedAuditor(script={
        "a": needs_bridge("a", "b", "c"),
        "b": needs_bridge("b", "d"),
        "c": needs_bridge("c", "d"),
        "d": needs_bridge("d"),  # leaf with no bridges
    })
    # Strictly speaking d will produce no bridges; gap() default leaf-resolves.
    auditor.script["d"] = ScriptedAuditor(script={}).audit("d")
    r = RecursiveResolver(
        auditor=auditor, consilium=ScriptedConsilium(),
    ).resolve("a")
    assert r.final_state is not ResolutionState.RESOLUTION_CYCLE_DETECTED


# ---------------------------------------------------------------------------
# Cycle never silently truncates — R4 directive
# ---------------------------------------------------------------------------


def test_cycle_carries_inspectable_path() -> None:
    auditor = ScriptedAuditor(script={
        "a": needs_bridge("a", "b"),
        "b": needs_bridge("b", "a"),
    })
    r = RecursiveResolver(
        auditor=auditor, consilium=ScriptedConsilium(),
    ).resolve("a")
    # The cycle_path field is non-empty and the rationale mentions cycle.
    assert r.cycle_path
    assert "cycle" in r.rationale.lower()
