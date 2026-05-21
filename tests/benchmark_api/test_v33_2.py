"""v33.2 - Search Compression Benchmark Adapter tests."""
from __future__ import annotations

import json
import pathlib

from desi.benchmark_api_search import (
    COMPRESSION_MODES, MODE_HARD_PRUNING, any_critical_hard_pruned,
    branch_compression, build_report, build_search_artifact,
    compression_measurement, compute_reduction,
    critical_branch_preservation, critical_branch_visibility,
    critical_branches, hard_pruned_count, mode_breakdown,
    node_reduction, novelty_preservation, quality_preservation,
    replay_stability, search_metrics, search_space, total_nodes,
)
from desi.benchmark_api_search.report import (
    REPORT_VERDICTS, VERDICT_MEASURED,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__).resolve().parents[2]
    / "artifacts" / "benchmark_api"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(encoding="utf-8"),
    )


# --- four compression modes distinguished -------
def test_five_modes_defined() -> None:
    assert set(COMPRESSION_MODES) == {
        "kept", "hard_pruning", "soft_reweighting",
        "replay_reuse", "redundant_branch_compression",
    }


def test_modes_partition_space() -> None:
    counts = mode_breakdown()
    assert sum(counts.values()) == total_nodes()


def test_compression_measurement_full() -> None:
    assert compression_measurement() == 1.0


def test_compression_metrics_positive() -> None:
    assert node_reduction() > 0.0
    assert branch_compression() > 0.0
    assert compute_reduction() > 0.0


# --- critical branches stay visible -------------
def test_no_hard_pruning_of_criticals() -> None:
    assert any_critical_hard_pruned() is False
    assert hard_pruned_count() == 0


def test_critical_branch_visibility_full() -> None:
    assert critical_branch_visibility() == 1.0
    assert critical_branch_preservation() == 1.0


def test_every_critical_visible() -> None:
    crit = critical_branches()
    assert crit
    for b in crit:
        assert b.visible
        assert b.mode != MODE_HARD_PRUNING


# --- novelty / quality --------------------------
def test_novelty_preservation_full() -> None:
    assert novelty_preservation() == 1.0


def test_quality_preservation_full() -> None:
    assert quality_preservation() == 1.0


def test_only_zero_novelty_branches_invisible() -> None:
    for b in search_space():
        if not b.visible:
            assert b.novelty == 0.0


# --- replay -------------------------------------
def test_replay_stability_one() -> None:
    assert replay_stability() == 1.0


def test_metrics_in_unit_interval() -> None:
    for v in search_metrics().values():
        assert 0.0 <= v <= 1.0


# --- report -------------------------------------
def test_recommendation_in_closed_set() -> None:
    assert build_report().recommendation in set(REPORT_VERDICTS)


def test_recommendation_is_measured() -> None:
    assert build_report().recommendation == VERDICT_MEASURED


def test_report_not_halt() -> None:
    assert build_report().halt is False


def test_report_is_deterministic() -> None:
    assert build_report().to_dict() == build_report().to_dict()


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v33_2_search_adapter.json")
    assert art["schema_version"] == "v33_2_search_adapter"


def test_artifact_carries_disclaimer() -> None:
    art = _load("v33_2_search_adapter.json")
    disc = art["disclaimer"].lower()
    assert "never hard-pruned" in disc
    assert "without hiding any load-bearing branch" in disc


def test_artifact_mode_breakdown() -> None:
    art = _load("v33_2_search_adapter.json")
    assert art["mode_breakdown"]["hard_pruning"] == 0
    assert sum(art["mode_breakdown"].values()) == art["total_nodes"]


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v33_2_search_adapter.json")
    required = {
        "compression_measurement", "critical_branch_visibility",
        "novelty_preservation", "quality_preservation",
        "replay_stability",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v33_2_search_adapter.json")
    assert art == build_search_artifact()
