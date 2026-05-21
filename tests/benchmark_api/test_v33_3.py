"""v33.3 - Benchmark Harness & Blind Runner tests."""
from __future__ import annotations

import json
import pathlib

from desi.benchmark_api_harness import (
    anon_runs, blind_evaluation_integrity, blind_scores,
    build_harness_artifact, build_report, core_separation,
    harness_metrics, load_tasks, replay_stability, result_validation,
    run_all, scorecard_traceability, scorecards, sealed_map,
    validate, validation_failures,
)
from desi.benchmark_api_harness.report import (
    REPORT_VERDICTS, VERDICT_RAN,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__).resolve().parents[2]
    / "artifacts" / "benchmark_api"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(encoding="utf-8"),
    )


# --- harness runs -------------------------------
def test_harness_loads_tasks() -> None:
    tasks = load_tasks()
    assert len(tasks) >= 2
    names = {t.benchmark_name for t in tasks}
    assert "DRIFT_BENCHMARK" in names
    assert "SEARCH_COMPRESSION_BENCHMARK" in names


def test_every_task_produces_result() -> None:
    runs = run_all()
    assert len(runs) == len(load_tasks())
    for task, result in runs:
        assert result.task_id == task.task_id


# --- result validation --------------------------
def test_result_validation_full() -> None:
    assert result_validation() == 1.0
    assert validation_failures() == ()


def test_every_result_validates() -> None:
    for _, r in run_all():
        assert validate(r) is True


# --- blind evaluation ---------------------------
def test_blind_evaluation_integrity_full() -> None:
    assert blind_evaluation_integrity() == 1.0


def test_anon_runs_hide_benchmark_name() -> None:
    names = set(sealed_map().values())
    for run in anon_runs():
        blob = "|".join(str(v) for v in run.to_dict().values())
        for n in names:
            assert n not in blob
        assert run.anon_label.startswith("run_")


def test_blind_scores_objective() -> None:
    scores = blind_scores()
    assert scores
    for s in scores.values():
        assert s in (0.0, 1.0)


# --- core separation ----------------------------
def test_core_separation_full() -> None:
    assert core_separation() == 1.0


def test_running_does_not_change_core() -> None:
    from desi.peripheral_mutation import core_fingerprint
    before = core_fingerprint()
    run_all()
    assert core_fingerprint() == before


# --- scorecards ---------------------------------
def test_scorecard_traceability_full() -> None:
    assert scorecard_traceability() == 1.0


def test_scorecards_link_to_tasks() -> None:
    cards = scorecards()
    task_ids = {t.task_id for t in load_tasks()}
    assert {c.task_id for c in cards} == task_ids
    for c in cards:
        assert c.is_traceable()
        assert c.replay_hash


# --- replay -------------------------------------
def test_replay_stability_one() -> None:
    assert replay_stability() == 1.0


def test_metrics_in_unit_interval() -> None:
    for v in harness_metrics().values():
        assert 0.0 <= v <= 1.0


# --- report -------------------------------------
def test_recommendation_in_closed_set() -> None:
    assert build_report().recommendation in set(REPORT_VERDICTS)


def test_recommendation_is_ran_clean() -> None:
    assert build_report().recommendation == VERDICT_RAN


def test_report_not_halt() -> None:
    assert build_report().halt is False


def test_report_is_deterministic() -> None:
    assert build_report().to_dict() == build_report().to_dict()


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v33_3_harness.json")
    assert art["schema_version"] == "v33_3_benchmark_harness"


def test_artifact_carries_disclaimer() -> None:
    art = _load("v33_3_harness.json")
    disc = art["disclaimer"].lower()
    assert "never imports or mutates a protected core" in disc
    assert "cannot adapt its output to a known benchmark" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v33_3_harness.json")
    required = {
        "blind_evaluation_integrity", "core_separation",
        "result_validation", "scorecard_traceability",
        "replay_stability",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v33_3_harness.json")
    assert art == build_harness_artifact()
