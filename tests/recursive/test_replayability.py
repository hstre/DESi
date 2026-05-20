"""Tests for v1.4 INV-R1 — same graph → same replay_hash."""
from __future__ import annotations

import time

from desi.recursive import (
    RecursiveResolver,
    ResolutionReplay,
    ResolutionState,
    node_id,
)

from ._helpers import (
    ScriptedAuditor,
    ScriptedConsilium,
    needs_bridge,
)


# ---------------------------------------------------------------------------
# Direct API determinism
# ---------------------------------------------------------------------------


def test_resolution_replay_hash_is_deterministic() -> None:
    a = ResolutionReplay(
        root_node_id="rn_root",
        sorted_node_ids=("rn_a", "rn_b"),
        sorted_edges=(("rn_root", "rn_a"), ("rn_root", "rn_b")),
        final_state="resolution_complete",
        depth_reached=1,
    )
    b = ResolutionReplay(
        root_node_id="rn_root",
        sorted_node_ids=("rn_a", "rn_b"),
        sorted_edges=(("rn_root", "rn_a"), ("rn_root", "rn_b")),
        final_state="resolution_complete",
        depth_reached=1,
    )
    assert a.replay_hash == b.replay_hash


def test_replay_hash_changes_with_final_state() -> None:
    base_kwargs = dict(
        root_node_id="x", sorted_node_ids=("x",),
        sorted_edges=(), depth_reached=0,
    )
    a = ResolutionReplay(final_state="resolution_complete", **base_kwargs)
    b = ResolutionReplay(final_state="resolution_blocked", **base_kwargs)
    assert a.replay_hash != b.replay_hash


def test_replay_hash_changes_with_node_set() -> None:
    base = dict(root_node_id="x", final_state="resolution_complete",
                depth_reached=0)
    a = ResolutionReplay(sorted_node_ids=("x",), sorted_edges=(), **base)
    b = ResolutionReplay(sorted_node_ids=("x", "y"),
                          sorted_edges=(("x", "y"),), **base)
    assert a.replay_hash != b.replay_hash


# ---------------------------------------------------------------------------
# Resolver determinism
# ---------------------------------------------------------------------------


def test_two_resolutions_same_input_same_replay_hash() -> None:
    a = RecursiveResolver().resolve(
        "It is raining. Therefore the street is wet."
    )
    b = RecursiveResolver().resolve(
        "It is raining. Therefore the street is wet."
    )
    assert a.replay_hash == b.replay_hash


def test_replay_hash_independent_of_wall_clock() -> None:
    a = RecursiveResolver().resolve(
        "It is raining. Therefore the street is wet."
    )
    time.sleep(0.01)
    b = RecursiveResolver().resolve(
        "It is raining. Therefore the street is wet."
    )
    assert a.replay_hash == b.replay_hash


# ---------------------------------------------------------------------------
# Scripted resolution: identical graph → identical hash
# ---------------------------------------------------------------------------


def test_scripted_resolution_hash_is_stable_across_calls() -> None:
    auditor = ScriptedAuditor(script={
        "root":  needs_bridge("root", "b1"),
        "b1":   needs_bridge("b1", "b2"),
    })
    r1 = RecursiveResolver(
        auditor=auditor, consilium=ScriptedConsilium(),
    ).resolve("root")
    r2 = RecursiveResolver(
        auditor=auditor, consilium=ScriptedConsilium(),
    ).resolve("root")
    assert r1.replay_hash == r2.replay_hash


# ---------------------------------------------------------------------------
# node_id helper is deterministic
# ---------------------------------------------------------------------------


def test_node_id_is_deterministic_on_canonical_text() -> None:
    a = node_id("Hello World.")
    b = node_id("  hello world  ")
    assert a == b


def test_node_id_is_distinct_for_distinct_text() -> None:
    assert node_id("hello") != node_id("world")
