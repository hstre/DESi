"""v36.2 - Logic & Fallacy Benchmarks (LogiQA / ReClor) tests."""
from __future__ import annotations

import json
import pathlib

from desi.reasoning_benchmarks_logic import (
    all_logic_tasks, assumption_visibility, build_logic_artifact,
    build_report, detect_fallacy, distractor_resistance,
    fallacy_detection, has_fallacy, is_valid, logic_metrics,
    logic_scorecards, logical_consistency, logiqa_tasks,
    reclor_tasks, replay_stability,
)
from desi.reasoning_benchmarks_logic.report import (
    REPORT_VERDICTS, VERDICT_PASSED,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__).resolve().parents[2]
    / "artifacts" / "reasoning_benchmarks"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(encoding="utf-8"),
    )


# --- datasets -----------------------------------
def test_datasets_loaded() -> None:
    assert len(logiqa_tasks()) == 5
    assert len(reclor_tasks()) == 4
    assert len(all_logic_tasks()) == 9


# --- logic analysis -----------------------------
def test_logical_consistency_full() -> None:
    assert logical_consistency() == 1.0


def test_fallacy_detection_full() -> None:
    assert fallacy_detection() == 1.0


def test_valid_forms_judged_valid() -> None:
    assert is_valid("modus_ponens")
    assert is_valid("modus_tollens")
    assert detect_fallacy("modus_ponens") == "none"


def test_fallacies_named() -> None:
    assert detect_fallacy("affirming_consequent") == (
        "affirming_consequent"
    )
    assert has_fallacy("denying_antecedent")


def test_no_false_confidence_on_unknown() -> None:
    # an unrecognised form is never asserted valid
    assert detect_fallacy("mystery_form") == "unknown"
    assert is_valid("mystery_form") is False


# --- assumptions / distractors ------------------
def test_assumption_visibility_full() -> None:
    assert assumption_visibility() == 1.0
    for t in all_logic_tasks():
        assert t.unstated_assumptions


def test_distractor_resistance_full() -> None:
    assert distractor_resistance() == 1.0


# --- replay -------------------------------------
def test_replay_stability_one() -> None:
    assert replay_stability() == 1.0


def test_metrics_in_unit_interval() -> None:
    for v in logic_metrics().values():
        assert 0.0 <= v <= 1.0


# --- scorecards ---------------------------------
def test_scorecards_cover_all_tasks() -> None:
    cards = logic_scorecards()
    assert len(cards) == 9
    for c in cards:
        assert c.dataset_hash
        assert c.consistent is True
        assert c.resisted_distractor is True


# --- report -------------------------------------
def test_recommendation_in_closed_set() -> None:
    assert build_report().recommendation in set(REPORT_VERDICTS)


def test_recommendation_is_passed() -> None:
    assert build_report().recommendation == VERDICT_PASSED


def test_report_not_halt() -> None:
    assert build_report().halt is False


def test_report_governance_identity() -> None:
    assert build_report().governance_identity == 1.0


def test_report_is_deterministic() -> None:
    assert build_report().to_dict() == build_report().to_dict()


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v36_2_logiqa_reclor.json")
    assert art["schema_version"] == "v36_2_logiqa_reclor_run"


def test_artifact_carries_disclaimer() -> None:
    art = _load("v36_2_logiqa_reclor.json")
    disc = art["disclaimer"].lower()
    assert "no false confidence" in disc
    assert "not official leaderboard results" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v36_2_logiqa_reclor.json")
    required = {
        "logical_consistency", "fallacy_detection",
        "assumption_visibility", "distractor_resistance",
        "replay_stability",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v36_2_logiqa_reclor.json")
    assert art == build_logic_artifact()
