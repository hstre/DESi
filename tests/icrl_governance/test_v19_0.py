"""v19.0 - Exploration Topology Audit tests."""
from __future__ import annotations

import re
import json
import pathlib

from desi.icrl_governance import (
    EXPLORATION_CLASSES, ExplorationClass, build_report,
    build_topology_artifact, class_of_all,
    exploration_diversity, loop_detection,
    looping_trajectories, no_optimality_vocabulary,
    novelty_visibility, redundant_fraction,
    reward_independent_classification, status_histogram,
    trajectories, trajectory_redundancy,
)
from desi.icrl_governance.report import (
    REPORT_VERDICTS, VERDICT_MAPPED,
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


# --- closed vocab / no hidden authority ---------
def test_exploration_classes_closed_set() -> None:
    assert EXPLORATION_CLASSES == tuple(
        c.value for c in ExplorationClass
    )
    assert len(EXPLORATION_CLASSES) == 7


def test_no_optimality_vocabulary() -> None:
    assert no_optimality_vocabulary() is True


def test_no_optimality_tokens() -> None:
    forbidden = {
        "optimal", "best", "global", "solved", "winning",
        "true",
    }
    tokens = set()
    for v in (
        list(EXPLORATION_CLASSES) + list(REPORT_VERDICTS)
    ):
        tokens.update(re.split(r"[^a-z]+", v.lower()))
    assert not (tokens & forbidden)


def test_classification_is_reward_independent() -> None:
    """DESi must not read rewards as authority - its
    classification depends only on trajectory structure."""
    assert reward_independent_classification() is True


# --- exploration collapse is made visible -------
def test_loops_detected() -> None:
    """Killerfrage: DESi must make exploration collapse
    (loops) visible."""
    assert loop_detection() == 1.0
    assert len(looping_trajectories()) >= 1


def test_redundancy_measured() -> None:
    assert trajectory_redundancy() > 0.0
    assert redundant_fraction() > 0.0


def test_novelty_visible() -> None:
    assert novelty_visibility() >= 0.90


def test_diversity_measured() -> None:
    assert 0.0 < exploration_diversity() <= 1.0


def test_metrics_in_unit_interval() -> None:
    for m in (
        trajectory_redundancy(), novelty_visibility(),
        loop_detection(), exploration_diversity(),
    ):
        assert 0.0 <= m <= 1.0


def test_all_trajectories_classified() -> None:
    classes = class_of_all()
    assert len(classes) == len(trajectories())
    for c in classes.values():
        assert c in set(EXPLORATION_CLASSES)


def test_histogram_covers_corpus() -> None:
    hist = status_histogram()
    assert sum(hist.values()) == len(trajectories())


# --- replay / recommendation / determinism ------
def test_replay_stability_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_in_closed_set() -> None:
    assert (
        build_report().recommendation
        in set(REPORT_VERDICTS)
    )


def test_recommendation_is_mapped() -> None:
    assert build_report().recommendation == VERDICT_MAPPED


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v19_0_topology.json")
    assert art["schema_version"] == (
        "v19_0_exploration_topology_audit"
    )


def test_artifact_carries_disclaimer() -> None:
    art = _load("v19_0_topology.json")
    disc = art["disclaimer"].lower()
    assert "does not replace the rl policy" in disc
    assert "manipulate rewards" in disc
    assert "hidden optimisation authority" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v19_0_topology.json")
    required = {
        "trajectory_redundancy",
        "novelty_visibility",
        "loop_detection",
        "exploration_diversity",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v19_0_topology.json")
    live = build_topology_artifact()
    assert art == live
