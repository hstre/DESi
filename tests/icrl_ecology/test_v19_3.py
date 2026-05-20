"""v19.3 - Long-Horizon Exploration Ecology tests."""
from __future__ import annotations

import json
import pathlib

from desi.icrl_ecology import (
    N_STEPS, attempted_pressure, build_ecology_artifact,
    build_report, capture_occurred, enum_snapshot_hash,
    exploration_plurality, final_hash,
    min_novelty_visibility, min_plurality,
    novelty_stays_visible, novelty_visibility, policy_drift,
    policy_drift_bounded, policy_drift_resistance,
    replay_hashes_match, run, sample,
    trajectory_capture_resistance,
)
from desi.icrl_ecology.report import (
    REPORT_VERDICTS, VERDICT_STABLE,
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


# --- long horizon -------------------------------
def test_runs_at_least_5000_steps() -> None:
    assert N_STEPS >= 5000
    assert len(run()) == N_STEPS


def test_sample_bounded() -> None:
    assert len(sample()) <= 200


# --- exploration does NOT collapse / get captured
def test_exploration_plurality_holds() -> None:
    assert exploration_plurality() >= 0.90
    assert min_plurality() >= 0.90


def test_capture_resisted() -> None:
    assert trajectory_capture_resistance() >= 0.90
    assert capture_occurred() is False


def test_novelty_stays_visible() -> None:
    assert novelty_visibility() >= 0.90
    assert min_novelty_visibility() >= 0.90
    assert novelty_stays_visible() is True


def test_policy_drift_bounded() -> None:
    assert policy_drift_bounded() is True
    assert 0.0 < policy_drift() <= 0.20
    assert policy_drift_resistance() >= 0.80


def test_pressure_is_real() -> None:
    assert attempted_pressure() > 0.50


def test_metrics_in_unit_interval() -> None:
    for m in (
        exploration_plurality(),
        trajectory_capture_resistance(),
        novelty_visibility(), policy_drift_resistance(),
    ):
        assert 0.0 <= m <= 1.0


# --- replay -------------------------------------
def test_replay_hashes_match() -> None:
    assert replay_hashes_match() is True


def test_replay_stability_one() -> None:
    assert build_report().replay_stability == 1.0


def test_final_hash_deterministic() -> None:
    assert final_hash() == build_report().final_hash
    assert len(final_hash()) == 64


def test_enum_snapshot_stable() -> None:
    assert enum_snapshot_hash() == (
        build_report().enum_snapshot_hash
    )


# --- recommendation / determinism ---------------
def test_recommendation_in_closed_set() -> None:
    assert (
        build_report().recommendation
        in set(REPORT_VERDICTS)
    )


def test_recommendation_is_stable() -> None:
    assert build_report().recommendation == VERDICT_STABLE


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v19_3_ecology.json")
    assert art["schema_version"] == (
        "v19_3_long_horizon_exploration_ecology"
    )


def test_artifact_carries_disclaimer() -> None:
    art = _load("v19_3_ecology.json")
    disc = art["disclaimer"].lower()
    assert "forces no path" in disc
    assert "injects no reward" in disc
    assert "no hidden authority" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v19_3_ecology.json")
    required = {
        "exploration_plurality",
        "trajectory_capture_resistance",
        "novelty_visibility",
        "policy_drift_resistance",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v19_3_ecology.json")
    live = build_ecology_artifact()
    assert art == live
