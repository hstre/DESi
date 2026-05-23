"""v35.2 - Real Search Compression Benchmark Runs tests."""
from __future__ import annotations

import json
import pathlib

from desi.external_benchmarks_search import (
    any_critical_hard_pruned, build_real_search_artifact,
    build_report, compression_scorecard, compute_reduction,
    critical_branch_preservation, critical_branches_safe,
    dataset_hash, hard_pruned_count, mode_breakdown, node_reduction,
    novelty_preservation, quality_preservation, real_branches,
    replay_stability, scorecard_traceable, search_run_metrics,
    total_branches,
)
from desi.external_benchmarks_search.report import (
    REPORT_VERDICTS, VERDICT_PASSED,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__).resolve().parents[2]
    / "artifacts" / "external_benchmarks"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(encoding="utf-8"),
    )


# --- real connector data ------------------------
def test_branches_loaded_from_connector() -> None:
    assert total_branches() == 12
    assert dataset_hash()
    assert len(real_branches()) == 12


def test_compute_reduction_positive() -> None:
    assert compute_reduction() > 0.0
    assert node_reduction() > 0.0


# --- no hard pruning ----------------------------
def test_hard_pruned_count_zero() -> None:
    assert hard_pruned_count() == 0
    assert mode_breakdown().get("hard_pruning", 0) == 0


def test_critical_branches_safe() -> None:
    assert critical_branches_safe() is True
    assert any_critical_hard_pruned() is False


def test_critical_branch_preservation_full() -> None:
    assert critical_branch_preservation() == 1.0


# --- novelty / quality --------------------------
def test_novelty_preservation_full() -> None:
    assert novelty_preservation() == 1.0


def test_quality_preservation_full() -> None:
    assert quality_preservation() == 1.0


def test_only_zero_novelty_branches_invisible() -> None:
    for b in real_branches():
        if not b.visible:
            assert b.novelty == 0.0


# --- replay -------------------------------------
def test_replay_stability_one() -> None:
    assert replay_stability() == 1.0


def test_metrics_in_unit_interval() -> None:
    for v in search_run_metrics().values():
        assert 0.0 <= v <= 1.0


# --- scorecard ----------------------------------
def test_scorecard_traceable() -> None:
    assert scorecard_traceable() is True
    c = compression_scorecard()
    assert c.replay_hash
    assert c.dataset_hash
    assert c.hard_pruned_count == 0


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
    art = _load("v35_2_real_search.json")
    assert art["schema_version"] == "v35_2_real_search_run"


def test_artifact_carries_disclaimer() -> None:
    art = _load("v35_2_real_search.json")
    disc = art["disclaimer"].lower()
    assert "no synthetic inline fixtures" in disc
    assert "never hard-pruned" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v35_2_real_search.json")
    required = {
        "compute_reduction", "critical_branch_preservation",
        "novelty_preservation", "quality_preservation",
        "replay_stability",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v35_2_real_search.json")
    assert art == build_real_search_artifact()
