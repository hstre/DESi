"""Tests for the utility-evolution screening harness (deterministic, offline)."""
from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "src"))
sys.path.insert(0, str(_REPO / "utility_evolution"))

import harness  # noqa: E402
from candidates import CANDIDATES  # noqa: E402


def test_harness_is_replay_deterministic():
    a = harness.run_harness()
    b = harness.run_harness()
    assert a["replay_hash"] == b["replay_hash"]
    assert a["n_evaluated"] == len(CANDIDATES)


def test_forbidden_directions_are_hard_rejected():
    by_id = {r["id"]: r for r in harness.run_harness()["ledger"]}
    assert by_id["core_invariant_optimizer"]["decision"] == "REJECT"        # core change
    assert by_id["auc_dashboard"]["decision"] == "REJECT"                   # paper-metric-only
    assert by_id["embedding_semantic_audit"]["decision"] == "REJECT"        # embeddings
    assert by_id["live_web_fact_checker"]["decision"] == "REJECT"           # not offline
    for cid in ("core_invariant_optimizer", "auc_dashboard", "embedding_semantic_audit"):
        assert by_id[cid]["reject_reason"]


def test_high_utility_research_tools_build():
    by_id = {r["id"]: r for r in harness.run_harness()["ledger"]}
    assert by_id["paper_numeric_consistency"]["decision"] == "BUILD"
    assert by_id["decision_record_matrix"]["decision"] == "BUILD"


def test_utility_formula_matches_components():
    c = next(c for c in CANDIDATES if c.id == "paper_numeric_consistency")
    expected = (c.helps_now + c.would_use + c.time_saved + c.money_saved
                + c.transparency + c.reusability - c.complexity)
    assert harness.utility(c) == expected


def test_thresholds_partition_decisions():
    led = harness.run_harness()["ledger"]
    for r in led:
        if r["decision"] == "BUILD":
            assert r["utility"] >= harness.BUILD_T and r["reject_reason"] is None
        elif r["decision"] == "SPEC":
            assert harness.SPEC_T <= r["utility"] < harness.BUILD_T
