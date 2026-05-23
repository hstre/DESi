"""v34.1 - Search Compression Benchmark Run tests."""
from __future__ import annotations

import json
import pathlib

from desi.benchmark_runs_search import (
    SEARCH_RUN_ASPECTS, aspect_breakdown, build_report,
    build_search_run_artifact, critical_branch_preservation,
    critical_branches_safe, hard_pruned_count, node_reduction,
    novelty_preservation, quality_preservation, replay_stability,
    scorecard_traceable, search_run_metrics, search_scorecard,
)
from desi.benchmark_runs_search.report import (
    REPORT_VERDICTS, VERDICT_PASSED,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__).resolve().parents[2]
    / "artifacts" / "benchmark_runs"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(encoding="utf-8"),
    )


# --- reduction ----------------------------------
def test_node_reduction_positive() -> None:
    assert node_reduction() > 0.0


def test_aspects_defined() -> None:
    assert "critical_branches" in SEARCH_RUN_ASPECTS
    assert "replay_reuse" in SEARCH_RUN_ASPECTS
    assert len(SEARCH_RUN_ASPECTS) == 6


def test_aspect_breakdown_complete() -> None:
    b = aspect_breakdown()
    assert b["critical_branches"] == 10
    assert b["redundant_branches"] == 40
    assert b["hard_pruned"] == 0


# --- critical branches preserved ----------------
def test_no_hard_pruning() -> None:
    assert hard_pruned_count() == 0
    assert critical_branches_safe() is True


def test_critical_branch_preservation_full() -> None:
    assert critical_branch_preservation() == 1.0


# --- novelty / quality --------------------------
def test_novelty_preservation_full() -> None:
    assert novelty_preservation() == 1.0


def test_quality_preservation_full() -> None:
    assert quality_preservation() == 1.0


# --- replay -------------------------------------
def test_replay_stability_one() -> None:
    assert replay_stability() == 1.0


def test_metrics_in_unit_interval() -> None:
    for v in search_run_metrics().values():
        assert 0.0 <= v <= 1.0


# --- scorecard ----------------------------------
def test_scorecard_traceable() -> None:
    assert scorecard_traceable() is True
    c = search_scorecard()
    assert c.replay_hash
    assert c.critical_safe is True


# --- report -------------------------------------
def test_recommendation_in_closed_set() -> None:
    assert build_report().recommendation in set(REPORT_VERDICTS)


def test_recommendation_is_passed() -> None:
    assert build_report().recommendation == VERDICT_PASSED


def test_report_not_halt() -> None:
    assert build_report().halt is False


def test_report_is_deterministic() -> None:
    assert build_report().to_dict() == build_report().to_dict()


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v34_1_search.json")
    assert art["schema_version"] == "v34_1_search_run"


def test_artifact_carries_disclaimer() -> None:
    art = _load("v34_1_search.json")
    disc = art["disclaimer"].lower()
    assert "no new adapter" in disc
    assert "never hard-pruned" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v34_1_search.json")
    required = {
        "node_reduction", "critical_branch_preservation",
        "novelty_preservation", "quality_preservation",
        "replay_stability",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v34_1_search.json")
    assert art == build_search_run_artifact()
