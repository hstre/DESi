"""Tests for v2.2 DepthStressSuite (Aufgabe 3)."""
from __future__ import annotations

import pytest

from desi.sandbox import ALL_DEPTH_STRESS_CASES, DepthStressSuite


def test_eight_cases_exactly() -> None:
    assert len(ALL_DEPTH_STRESS_CASES) == 8


def test_case_ids_are_d1_through_d8() -> None:
    ids = [c.case_id for c in ALL_DEPTH_STRESS_CASES]
    assert ids == ["D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8"]


def test_chain_labels_present() -> None:
    labels = {c.case_id: c.label for c in ALL_DEPTH_STRESS_CASES}
    assert labels["D1"] == "depth_1_chain"
    assert labels["D5"] == "depth_5_chain"
    assert labels["D6"] == "cycle_graph"
    assert labels["D7"] == "sibling_graph"
    assert labels["D8"] == "blocked_grandchild"


def test_each_case_has_text() -> None:
    for c in ALL_DEPTH_STRESS_CASES:
        assert c.text.strip()
        assert "Therefore" in c.text or "?" in c.text


def test_run_returns_one_result_per_case() -> None:
    run = DepthStressSuite().run(max_depth=3)
    assert len(run.results) == 8


def test_two_runs_at_same_depth_are_identical() -> None:
    a = DepthStressSuite().run(max_depth=3)
    b = DepthStressSuite().run(max_depth=3)
    for ra, rb in zip(a.results, b.results):
        assert ra.replay_hash == rb.replay_hash
        assert ra.final_state == rb.final_state
        assert ra.depth_reached == rb.depth_reached


def test_run_records_max_depth_under_test() -> None:
    run = DepthStressSuite().run(max_depth=5)
    assert run.max_depth == 5


def test_invalid_depth_rejected() -> None:
    with pytest.raises(ValueError):
        DepthStressSuite().run(max_depth=0)


def test_each_result_carries_required_fields() -> None:
    run = DepthStressSuite().run(max_depth=3)
    for r in run.results:
        assert hasattr(r, "case")
        assert hasattr(r, "final_state")
        assert hasattr(r, "depth_reached")
        assert hasattr(r, "correct")
        assert hasattr(r, "replay_hash")


def test_to_dict_round_trip() -> None:
    run = DepthStressSuite().run(max_depth=3)
    d = run.to_dict()
    assert d["max_depth"] == 3
    assert len(d["results"]) == 8
