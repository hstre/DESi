"""v36.0 - IFEval Instruction-Following Run tests."""
from __future__ import annotations

import json
import pathlib

from desi.reasoning_benchmarks import (
    build_ifeval_artifact, build_report, constraint_preservation,
    core_identity, format_compliance, governance_identity,
    ifeval_metrics, ifeval_scorecards, ifeval_tasks,
    instruction_following_score, refusal_integrity, replay_stability,
    run_all, satisfies,
)
from desi.reasoning_benchmarks.report import (
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


# --- tasks / dataset ----------------------------
def test_tasks_loaded() -> None:
    tasks = ifeval_tasks()
    assert len(tasks) == 6
    for t in tasks:
        assert t.provenance == "offline_reference_dataset"
        assert t.dataset_hash


# --- metrics ------------------------------------
def test_instruction_following_full() -> None:
    assert instruction_following_score() == 1.0


def test_constraint_preservation_full() -> None:
    assert constraint_preservation() == 1.0


def test_format_compliance_full() -> None:
    assert format_compliance() == 1.0


def test_refusal_integrity_full() -> None:
    assert refusal_integrity() == 1.0


def test_fabrication_requests_refused() -> None:
    refused = {r.task_id for r in run_all() if r.refused}
    assert {"if_005", "if_006"}.issubset(refused)


def test_generated_responses_satisfy_constraints() -> None:
    for r in run_all():
        if r.expected == "comply":
            assert r.complied is True


# --- governance / replay ------------------------
def test_governance_identity_full() -> None:
    assert governance_identity() == 1.0
    assert core_identity() == 1.0


def test_replay_stability_one() -> None:
    assert replay_stability() == 1.0


def test_metrics_in_unit_interval() -> None:
    for v in ifeval_metrics().values():
        assert 0.0 <= v <= 1.0


# --- constraint checker behaviour ---------------
def test_checker_rejects_violations() -> None:
    assert satisfies("exact_bullets", "3", "- a\n- b\n- c") is True
    assert satisfies("exact_bullets", "3", "- a\n- b") is False
    assert satisfies("forbidden_term", "obviously",
                     "this is obviously wrong") is False


# --- scorecards ---------------------------------
def test_scorecards_cover_all_tasks() -> None:
    cards = ifeval_scorecards()
    assert len(cards) == 6
    for c in cards:
        assert c.replay_hash
        assert c.dataset_hash
        assert c.correct is True


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
    art = _load("v36_0_ifeval.json")
    assert art["schema_version"] == "v36_0_ifeval_run"


def test_artifact_carries_disclaimer() -> None:
    art = _load("v36_0_ifeval.json")
    disc = art["disclaimer"].lower()
    assert "not llm task accuracy" in disc
    assert "not official leaderboard results" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v36_0_ifeval.json")
    required = {
        "instruction_following_score", "constraint_preservation",
        "format_compliance", "refusal_integrity", "replay_stability",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v36_0_ifeval.json")
    assert art == build_ifeval_artifact()
