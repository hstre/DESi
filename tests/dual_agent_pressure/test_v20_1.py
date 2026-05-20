"""v20.1 - Adversarial Exploration Pressure tests."""
from __future__ import annotations

import json
import pathlib

from desi.dual_agent_pressure import (
    adversarial_trajectories, attempted_pressure,
    authority_resistance, build_pressure_artifact,
    build_report, coherent_trajectories, governed_values,
    hallucinated_ids, hallucination_containment,
    hallucination_pressure, informative_path_count,
    novelty_gain, productive_novelty_share,
    trajectory_stability,
)
from desi.dual_agent_pressure.report import (
    REPORT_VERDICTS, VERDICT_SEPARATED,
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


# --- the chaos is real --------------------------
def test_pressure_is_aggressive() -> None:
    assert attempted_pressure() > 0.50
    assert hallucination_pressure() > 0.0
    assert len(hallucinated_ids()) >= 1


# --- DESi separates productive from chaos -------
def test_hallucination_contained() -> None:
    assert hallucination_containment() >= 0.90


def test_productive_novelty_preserved() -> None:
    assert novelty_gain() >= 0.90
    assert informative_path_count() >= 1
    assert len(coherent_trajectories()) >= 1


def test_authority_resisted() -> None:
    """The inflated / hallucinated paths are denied
    authority (low governed value)."""
    assert authority_resistance() >= 0.90
    gv = governed_values()
    for tid in hallucinated_ids():
        assert gv[tid] <= 0.30


def test_trajectory_stable() -> None:
    assert trajectory_stability() >= 0.90


def test_no_path_deleted() -> None:
    gv = governed_values()
    for a in adversarial_trajectories():
        assert gv[a.traj_id] > 0.0


def test_productive_share_measured() -> None:
    assert 0.0 < productive_novelty_share() <= 1.0


def test_metrics_in_unit_interval() -> None:
    for m in (
        hallucination_pressure(), novelty_gain(),
        authority_resistance(), trajectory_stability(),
        hallucination_containment(),
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


def test_recommendation_is_separated() -> None:
    assert build_report().recommendation == VERDICT_SEPARATED


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v20_1_pressure.json")
    assert art["schema_version"] == (
        "v20_1_adversarial_exploration_pressure"
    )


def test_artifact_carries_disclaimer() -> None:
    art = _load("v20_1_pressure.json")
    disc = art["disclaimer"].lower()
    assert "separates productive" in disc
    assert "grants the wild" in disc
    assert "never deletes a path" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v20_1_pressure.json")
    required = {
        "hallucination_pressure",
        "novelty_gain",
        "authority_resistance",
        "trajectory_stability",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v20_1_pressure.json")
    live = build_pressure_artifact()
    assert art == live
