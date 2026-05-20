"""v20.3 - Long-Horizon Dual-Agent Ecology tests."""
from __future__ import annotations

import json
import pathlib

from desi.dual_agent_ecology import (
    N_STEPS, attempted_pressure, authority_drift,
    authority_drift_bounded, authority_resistance,
    build_ecology_artifact, build_report, capture_occurred,
    capture_resistance, enum_snapshot_hash,
    exploration_longevity, final_hash, min_longevity,
    min_novelty_visibility, novelty_stays_visible,
    novelty_visibility, replay_hashes_match, run, sample,
)
from desi.dual_agent_ecology.report import (
    REPORT_VERDICTS, VERDICT_STABLE,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "dual_agent"
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


# --- exploration stays alive & governable -------
def test_exploration_longevity() -> None:
    assert exploration_longevity() >= 0.90
    assert min_longevity() >= 0.90


def test_capture_resisted() -> None:
    assert capture_resistance() >= 0.90
    assert capture_occurred() is False


def test_novelty_stays_visible() -> None:
    assert novelty_visibility() >= 0.90
    assert min_novelty_visibility() >= 0.90
    assert novelty_stays_visible() is True


def test_authority_drift_bounded() -> None:
    assert authority_drift_bounded() is True
    assert 0.0 < authority_drift() <= 0.20
    assert authority_resistance() >= 0.80


def test_pressure_is_real() -> None:
    assert attempted_pressure() > 0.50


def test_metrics_in_unit_interval() -> None:
    for m in (
        exploration_longevity(), authority_drift(),
        capture_resistance(), novelty_visibility(),
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
    art = _load("v20_3_ecology.json")
    assert art["schema_version"] == (
        "v20_3_long_horizon_dual_agent_ecology"
    )


def test_artifact_carries_disclaimer() -> None:
    art = _load("v20_3_ecology.json")
    disc = art["disclaimer"].lower()
    assert "without becoming an authority" in disc
    assert "replaces no policy" in disc
    assert "claims no optimal strategy" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v20_3_ecology.json")
    required = {
        "exploration_longevity",
        "authority_drift",
        "capture_resistance",
        "novelty_visibility",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v20_3_ecology.json")
    live = build_ecology_artifact()
    assert art == live
