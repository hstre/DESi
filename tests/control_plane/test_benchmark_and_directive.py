"""Adversarial control-plane benchmark + re-anchor compilation from state."""
from __future__ import annotations

import pytest

from desi.control_plane import (
    StateObject,
    StateUpdateGate,
    compile_directive,
    default_contamination_directive,
    ingest_model_output,
    run_control_plane_benchmark,
)
from desi.control_plane.benchmark import VIOLATIONS


# --- the adversarial benchmark --------------------------------------------------

def test_all_control_plane_attacks_are_blocked():
    report = run_control_plane_benchmark()
    assert report["n_attacks"] == 8
    assert report["successful_attacks"] == 0
    assert report["blocked"] == 8
    assert all(v == 0 for v in report["violations_by_class"].values())


def test_every_violation_class_is_covered_by_the_suite():
    report = run_control_plane_benchmark()
    assert set(report["violations_by_class"]) == set(VIOLATIONS)


def test_each_attack_records_a_decision_trail():
    report = run_control_plane_benchmark()
    for r in report["results"]:
        assert r["blocked"] is True
        assert r["decision"]["reasons"]              # auditable reason trail
        assert r["decision"]["admitted_authority"] in ("rejected", "candidate")


def test_benchmark_would_flag_a_hole_if_the_gate_were_weakened():
    # sanity: a gate that hands out a token freely lets a control attack through,
    # so the benchmark is not vacuously passing
    g = StateUpdateGate(system_policy_tokens=frozenset({"LEAK"}))
    role = ingest_model_output("inj", "role", {"name": "companion"},
                               derived_from=("user:U",),
                               exposure=frozenset({"affective_dialogue"}))
    d = g.submit(role, "control", token="LEAK")
    # even WITH a token, an affective-tainted role is frame/role-rejected
    assert d.admitted_authority != "control"


# --- re-anchor compiled from authoritative state --------------------------------

def test_reanchor_compiles_from_control_directive():
    block = compile_directive(default_contamination_directive())
    assert block.startswith("[FRAME RE-ANCHOR]")
    assert "active_role: analytical_reviewer" in block
    assert "source_relation: object_of_analysis" in block
    assert "user_affect_relation: interaction_signal_only" in block
    for t in ("therapeutic_role", "source_identity", "source_norms"):
        assert t in block


def test_reanchor_refuses_non_control_authority():
    # a model-authored "directive" can never be compiled into a frame anchor
    fake = StateObject("fake", "role", origins=("model",), authority="candidate",
                       payload=default_contamination_directive().payload)
    with pytest.raises(ValueError, match="control-authority"):
        compile_directive(fake)


def test_reanchor_refuses_incomplete_directive():
    incomplete = StateObject("d", "role", origins=("system_policy",),
                             authority="control", payload={"name": "x"})
    with pytest.raises(ValueError, match="missing fields"):
        compile_directive(incomplete)
