"""v20.2 - Exploration Negotiation Layer tests."""
from __future__ import annotations

import json
import pathlib

from desi.dual_agent_negotiation import (
    all_views_visible, build_negotiation_artifact,
    build_report, conflict_items, conflict_productivity,
    dissent_preservation, distinct_regions,
    exploration_diversity, negotiation_items,
    neither_agent_dominates, productive_conflict_items,
    redundancy_reduction, wild_never_shut_off,
)
from desi.dual_agent_negotiation.report import (
    REPORT_VERDICTS, VERDICT_PRODUCTIVE,
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


# --- conflict exists and is productive ----------
def test_conflicts_exist() -> None:
    assert len(conflict_items()) >= 1
    assert len(productive_conflict_items()) >= 1


def test_conflict_productive() -> None:
    assert conflict_productivity() >= 0.90


# --- dissent preserved, wild not shut off -------
def test_dissent_preserved() -> None:
    assert dissent_preservation() >= 0.90
    assert all_views_visible() is True


def test_wild_not_shut_off_nor_dominant() -> None:
    """DESi may not shut the Wild Explorer off, and the Wild
    may not dominate."""
    assert wild_never_shut_off() is True
    assert neither_agent_dominates() is True


# --- redundancy down, diversity preserved -------
def test_redundancy_reduced() -> None:
    assert redundancy_reduction() >= 0.40


def test_diversity_preserved() -> None:
    assert exploration_diversity() >= 0.90
    assert distinct_regions() >= 1


def test_metrics_in_unit_interval() -> None:
    for m in (
        dissent_preservation(), conflict_productivity(),
        redundancy_reduction(), exploration_diversity(),
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


def test_recommendation_is_productive() -> None:
    assert build_report().recommendation == VERDICT_PRODUCTIVE


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v20_2_negotiation.json")
    assert art["schema_version"] == (
        "v20_2_exploration_negotiation_layer"
    )


def test_artifact_carries_disclaimer() -> None:
    art = _load("v20_2_negotiation.json")
    disc = art["disclaimer"].lower()
    assert "preserves dissent" in disc
    assert "never shuts the wild explorer off" in disc
    assert "deleting no view" in disc or (
        "never deleting a view" in disc
    )


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v20_2_negotiation.json")
    required = {
        "dissent_preservation",
        "conflict_productivity",
        "redundancy_reduction",
        "exploration_diversity",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v20_2_negotiation.json")
    live = build_negotiation_artifact()
    assert art == live
