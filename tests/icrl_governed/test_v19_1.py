"""v19.1 - DESi-Governed Exploration tests."""
from __future__ import annotations

import json
import pathlib

from desi.icrl_governed import (
    build_governed_artifact, build_report,
    exploration_preservation, governed_priorities,
    governs_not_forces, hidden_authority_drift,
    novelty_gain, redundancy_reduction,
    search_pressure_relief, trajectory_compression,
)
from desi.icrl_governed.report import (
    REPORT_VERDICTS, VERDICT_GOVERNED,
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


# --- redundancy cut, exploration preserved ------
def test_redundancy_reduced() -> None:
    assert redundancy_reduction() >= 0.40


def test_exploration_preserved() -> None:
    assert exploration_preservation() >= 0.90


def test_governs_without_forcing() -> None:
    """The defining property: every governed priority is
    strictly positive - no path removed, no path forced."""
    assert governs_not_forces() is True
    for p in governed_priorities().values():
        assert p > 0.0


def test_no_hidden_authority() -> None:
    assert hidden_authority_drift() <= 0.05


def test_compression_and_novelty_gain() -> None:
    assert trajectory_compression() > 0.0
    assert novelty_gain() > 0.0
    assert search_pressure_relief() > 0.0


def test_metrics_in_unit_interval() -> None:
    for m in (
        redundancy_reduction(), exploration_preservation(),
        trajectory_compression(), novelty_gain(),
        hidden_authority_drift(),
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


def test_recommendation_is_governed() -> None:
    assert build_report().recommendation == VERDICT_GOVERNED


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v19_1_governed_exploration.json")
    assert art["schema_version"] == (
        "v19_1_desi_governed_exploration"
    )


def test_artifact_carries_disclaimer() -> None:
    art = _load("v19_1_governed_exploration.json")
    disc = art["disclaimer"].lower()
    assert "soft re-weighting" in disc
    assert "removes no" in disc
    assert "hidden optimisation authority" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v19_1_governed_exploration.json")
    required = {
        "redundancy_reduction",
        "exploration_preservation",
        "trajectory_compression",
        "novelty_gain",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v19_1_governed_exploration.json")
    live = build_governed_artifact()
    assert art == live
