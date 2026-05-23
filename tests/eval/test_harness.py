"""Tests for EvaluationHarness — end-to-end runs + reproducibility."""
from __future__ import annotations

import pytest

from desi.eval import EvaluationHarness, list_scenarios, scenario_by_id


@pytest.fixture()
def harness() -> EvaluationHarness:
    return EvaluationHarness(model="claude-opus-4-7", config={"version": "v0.4"})


# ---------------------------------------------------------------------------
# Per-scenario: each one passes its own expectations
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("scenario", list_scenarios(),
                          ids=lambda s: s.scenario_id)
def test_scenario_passes_its_own_expectations(harness, scenario) -> None:
    result = harness.run_scenario(scenario, seed=42)
    assert result.passed, (
        f"{scenario.scenario_id} failed: {result.expectations_detail}"
    )


def test_run_all_returns_one_result_per_scenario(harness) -> None:
    results = harness.run_all(seed=0)
    assert len(results) == 7
    assert {r.scenario_id for r in results} == {
        "S1", "S2", "S3", "S4", "S5", "S6", "S7",
    }


def test_evaluation_result_carries_full_audit(harness) -> None:
    result = harness.run_scenario(scenario_by_id("S2"), seed=1)
    assert result.evaluation_id.startswith("eval_")
    assert result.scenario_id == "S2"
    assert result.seed == 1
    assert result.model == "claude-opus-4-7"
    assert result.config_hash
    assert result.report.trajectory_id == "s2_contradictions"
    assert result.timeline
    assert result.snapshots
    assert result.hook_errors == []


# ---------------------------------------------------------------------------
# Specific scenario verifications used in the v0.4 acceptance report
# ---------------------------------------------------------------------------


def test_s2_records_contradicts_relation(harness) -> None:
    result = harness.run_scenario(scenario_by_id("S2"))
    end = result.snapshots[-1]
    contradicts = [r for r in end.relations if r["rel_type"] == "CONTRADICTS"]
    assert len(contradicts) == 2  # bidirectional
    pairs = {(r["source_claim_id"], r["target_claim_id"])
             for r in contradicts}
    assert pairs == {("C002", "C003"), ("C003", "C002")}


def test_s5_opens_two_branches(harness) -> None:
    result = harness.run_scenario(scenario_by_id("S5"))
    branch_opened = [e for e in result.timeline
                     if e.event_type.value == "branch_opened"]
    focuses = [e.payload["focus_claim_id"] for e in branch_opened]
    assert focuses == ["B_left", "B_right"]


def test_s6_records_no_merged_into(harness) -> None:
    result = harness.run_scenario(scenario_by_id("S6"))
    end = result.snapshots[-1]
    rel_types = {r["rel_type"] for r in end.relations}
    assert "MERGED_INTO" not in rel_types
    # And exactly one guard_blocked event was emitted.
    blocked = [e for e in result.timeline
               if e.event_type.value == "guard_blocked"]
    assert len(blocked) == 1


def test_s7_does_not_collapse_legacy_and_new_claim(harness) -> None:
    result = harness.run_scenario(scenario_by_id("S7"))
    end = result.snapshots[-1]
    methods = sorted(c["method"] for c in end.claims
                     if c["content"] == "C_legacy")
    # Two distinct claims share content "C_legacy" but different methods.
    assert "hearsay" in methods
    assert "T6" in methods


# ---------------------------------------------------------------------------
# Reproducibility / regression
# ---------------------------------------------------------------------------


def test_same_seed_produces_identical_timeline(harness) -> None:
    a = harness.run_scenario(scenario_by_id("S1"), seed=11)
    b = harness.run_scenario(scenario_by_id("S1"), seed=11)
    # Wall-clock timestamps differ; tick + event_type + payload do not.
    assert a.timeline == b.timeline


def test_same_seed_produces_identical_snapshots(harness) -> None:
    a = harness.run_scenario(scenario_by_id("S2"), seed=3)
    b = harness.run_scenario(scenario_by_id("S2"), seed=3)
    # Compare claim/relation/event content (snapshots ignore wall-clock).
    a_payload = [s.to_dict() for s in a.snapshots]
    b_payload = [s.to_dict() for s in b.snapshots]
    # Strip wall-clock / uuid-derived fields. Determinism is asserted on
    # structure (claims/relations/events sets, not on per-uuid identity
    # of OperatorEvent records or wall-clock timestamps).
    def _strip(d: dict) -> dict:
        for col in ("claims", "relations", "runs", "events"):
            for item in d.get(col, []):
                for k in ("prov_timestamp", "created_at",
                          "started_at", "finished_at", "timestamp",
                          "event_id", "run_id", "prov_run_id"):
                    item.pop(k, None)
        return d
    a_payload = [_strip(x) for x in a_payload]
    b_payload = [_strip(x) for x in b_payload]
    assert a_payload == b_payload


def test_same_seed_produces_identical_diagnostic_report(harness) -> None:
    a = harness.run_scenario(scenario_by_id("S4"), seed=99)
    b = harness.run_scenario(scenario_by_id("S4"), seed=99)
    assert a.report == b.report


# ---------------------------------------------------------------------------
# Optionality / no DESi-source change
# ---------------------------------------------------------------------------


def test_diagnostic_report_matches_compute_all(harness) -> None:
    """v0.4 must not change DESi behaviour: report must equal compute_all."""
    from desi.diagnostics import compute_all
    sc = scenario_by_id("S1")
    plain = compute_all(sc.trajectory_factory())
    via_harness = harness.run_scenario(sc, seed=0).report
    assert plain == via_harness
