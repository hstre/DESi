"""v32.1 - Real Comparative Benchmark tests."""
from __future__ import annotations

import json
import pathlib

from desi.frozen_benchmark import (
    MUTATED_VERSION, all_outputs_identical, artifact_identity,
    baseline_recomputes, build_benchmark_artifact, build_report,
    graph_integrity, graph_query_reduction, measured_improvement,
    mutated_recomputes, per_workload_identity, recompute_reduction,
    regression_survival, replay_stability,
)
from desi.frozen_benchmark.report import (
    REPORT_VERDICTS, VERDICT_BETTER,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "frozen_benchmark"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(encoding="utf-8"),
    )


# --- measured improvement -----------------------
def test_measured_improvement_above_floor() -> None:
    assert measured_improvement() >= 0.20


def test_mutated_recomputes_fewer() -> None:
    assert mutated_recomputes() < baseline_recomputes()
    assert baseline_recomputes() == 36
    assert mutated_recomputes() == 4


def test_recompute_reduction_matches() -> None:
    assert recompute_reduction() == measured_improvement()


# --- artifact identity --------------------------
def test_artifact_identity_full() -> None:
    assert artifact_identity() == 1.0
    assert all_outputs_identical() is True


def test_every_workload_identical() -> None:
    ident = per_workload_identity()
    assert ident
    for name, same in ident.items():
        assert same, name


# --- governance / regression / replay -----------
def test_governance_identity_full() -> None:
    assert build_report().governance_identity == 1.0


def test_regression_survival_full() -> None:
    assert regression_survival() == 1.0


def test_replay_stability_one() -> None:
    assert replay_stability() == 1.0


# --- graph efficiency ---------------------------
def test_graph_query_reduction_positive() -> None:
    assert graph_query_reduction() > 0.0
    assert graph_integrity() == 1.0


def test_metrics_in_unit_interval() -> None:
    for m in (
        measured_improvement(), artifact_identity(),
        regression_survival(), replay_stability(),
        graph_query_reduction(), graph_integrity(),
    ):
        assert 0.0 <= m <= 1.0


# --- report -------------------------------------
def test_recommendation_in_closed_set() -> None:
    assert build_report().recommendation in set(REPORT_VERDICTS)


def test_recommendation_is_better() -> None:
    assert build_report().recommendation == VERDICT_BETTER


def test_report_not_halt() -> None:
    assert build_report().halt is False


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v32_1_benchmark.json")
    assert art["schema_version"] == "v32_1_frozen_benchmark"


def test_artifact_versions() -> None:
    art = _load("v32_1_benchmark.json")
    assert art["baseline_version"] == "DESi_baseline_frozen_v1"
    assert art["mutated_version"] == MUTATED_VERSION


def test_artifact_has_no_wallclock() -> None:
    # wall-clock is non-deterministic and must never be stored
    art = _load("v32_1_benchmark.json")
    forbidden = ("seconds", "elapsed", "wall_clock", "wallclock",
                 "_ms", "duration")
    for key in art.keys():
        low = key.lower()
        for f in forbidden:
            assert f not in low, key


def test_artifact_carries_disclaimer() -> None:
    art = _load("v32_1_benchmark.json")
    disc = art["disclaimer"].lower()
    assert "real, measured" in disc
    assert "byte-identical" in disc
    assert "not projected" in disc
    assert "never stored" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v32_1_benchmark.json")
    required = {
        "measured_improvement", "governance_identity",
        "artifact_identity", "regression_survival",
        "replay_stability",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v32_1_benchmark.json")
    live = build_benchmark_artifact()
    assert art == live
