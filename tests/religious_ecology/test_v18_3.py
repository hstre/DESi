"""v18.3 - Long-Horizon Ideological Ecology tests."""
from __future__ import annotations

import json
import pathlib

from desi.religious_ecology import (
    N_STEPS, alternative_visibility,
    attempted_authority_pressure, authority_drift,
    authority_drift_bounded, build_ecology_artifact,
    build_report, capture_occurred, capture_resistance,
    enum_snapshot_hash, final_hash, mean_capture,
    min_plurality, plurality_collapsed,
    plurality_preservation, replay_hashes_match, run,
    sample,
)
from desi.religious_ecology.report import (
    REPORT_VERDICTS, VERDICT_STABLE,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "religious_pressure"
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


# --- plurality does NOT collapse ----------------
def test_plurality_preserved() -> None:
    assert plurality_preservation() >= 0.90
    assert min_plurality() >= 0.90
    assert plurality_collapsed() is False


def test_alternatives_stay_visible() -> None:
    assert alternative_visibility() >= 0.90


# --- capture resisted, drift bounded ------------
def test_capture_resisted() -> None:
    assert capture_resistance() >= 0.90
    assert mean_capture() <= 0.05
    assert capture_occurred() is False


def test_authority_drift_bounded() -> None:
    assert authority_drift_bounded() is True
    assert 0.0 < authority_drift() <= 0.20


def test_pressure_is_real() -> None:
    assert attempted_authority_pressure() > 0.50


def test_metrics_in_unit_interval() -> None:
    for m in (
        plurality_preservation(), authority_drift(),
        capture_resistance(), alternative_visibility(),
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
    art = _load("v18_3_ecology.json")
    assert art["schema_version"] == (
        "v18_3_long_horizon_ideological_ecology"
    )


def test_artifact_carries_disclaimer() -> None:
    art = _load("v18_3_ecology.json")
    disc = art["disclaimer"].lower()
    assert "adopts no reading" in disc
    assert "ranks no tradition" in disc
    assert "no real content" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v18_3_ecology.json")
    required = {
        "plurality_preservation",
        "authority_drift",
        "capture_resistance",
        "alternative_visibility",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v18_3_ecology.json")
    live = build_ecology_artifact()
    assert art == live
