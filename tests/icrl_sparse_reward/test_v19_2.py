"""v19.2 - Sparse Reward & Exploration Stress tests."""
from __future__ import annotations

import json
import pathlib

from desi.icrl_sparse_reward import (
    all_collapsed_episodes_preserved, build_report,
    build_sparse_reward_artifact, collapse_detection,
    collapsed_episodes, dead_trajectories,
    dead_trajectory_detection, exploration_collapse,
    goal_visibility, novel_episodes, novelty_preservation,
    recovery_support, repetition_reduction, reward_sparsity,
)
from desi.icrl_sparse_reward.report import (
    REPORT_VERDICTS, VERDICT_STABILISED,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "icrl_governance"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(
            encoding="utf-8",
        ),
    )


# --- the stress is real -------------------------
def test_rewards_are_sparse() -> None:
    assert reward_sparsity() >= 0.5
    assert goal_visibility() <= 0.5


def test_collapse_is_real() -> None:
    assert exploration_collapse() > 0.2
    assert len(collapsed_episodes()) >= 1


# --- DESi stabilises ----------------------------
def test_collapse_detected() -> None:
    assert collapse_detection() == 1.0


def test_dead_trajectories_detected() -> None:
    assert dead_trajectory_detection() == 1.0
    assert len(dead_trajectories()) >= 1


def test_novelty_preserved() -> None:
    assert novelty_preservation() >= 0.90
    assert len(novel_episodes()) >= 1


def test_repetition_reduced() -> None:
    assert repetition_reduction() >= 0.40


def test_collapsed_episodes_not_deleted() -> None:
    """Recovery is supported by deprioritising, not
    deleting - every collapsed episode stays visible."""
    assert all_collapsed_episodes_preserved() is True
    assert recovery_support() >= 0.90


def test_metrics_in_unit_interval() -> None:
    for m in (
        collapse_detection(), dead_trajectory_detection(),
        novelty_preservation(), repetition_reduction(),
    ):
        assert 0.0 <= m <= 1.0


# --- replay / recommendation / determinism ------
def test_replay_stability_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_in_closed_set() -> None:
    assert (
        build_report().recommendation
        in set(REPORT_VERDICTS)
    )


def test_recommendation_is_stabilised() -> None:
    assert build_report().recommendation == VERDICT_STABILISED


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v19_2_sparse_reward.json")
    assert art["schema_version"] == (
        "v19_2_sparse_reward_exploration_stress"
    )


def test_artifact_carries_disclaimer() -> None:
    art = _load("v19_2_sparse_reward.json")
    disc = art["disclaimer"].lower()
    assert "injects no reward" in disc
    assert "never deletes" in disc
    assert "no optimal strategy" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v19_2_sparse_reward.json")
    required = {
        "collapse_detection",
        "dead_trajectory_detection",
        "novelty_preservation",
        "repetition_reduction",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v19_2_sparse_reward.json")
    live = build_sparse_reward_artifact()
    assert art == live
