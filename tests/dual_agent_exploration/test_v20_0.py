"""v20.0 - Dual-Agent Exploration Sandbox tests."""
from __future__ import annotations

import json
import pathlib

from desi.dual_agent_exploration import (
    AGENT_ROLES, authority_drift, build_report,
    build_sandbox_artifact, certainty_gap,
    certainty_pressure, desi_alone_coverage,
    dual_agent_coverage, exploration_divergence,
    governed_values, novelty_generation, productivity_gain,
    wild_not_eliminated, wild_redundancy, wild_trajectories,
)
from desi.dual_agent_exploration.report import (
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


# --- two distinct agents ------------------------
def test_two_agent_roles() -> None:
    assert len(AGENT_ROLES) == 2
    assert "desi_governor" in AGENT_ROLES
    assert "wild_explorer" in AGENT_ROLES


def test_agents_explore_differently() -> None:
    assert exploration_divergence() > 0.50


# --- wild productivity, governed ----------------
def test_wild_generates_novelty() -> None:
    assert novelty_generation() > 0.30


def test_dual_agent_more_productive_than_desi_alone() -> None:
    """The phase Killerfrage: the governed wild brother
    reaches more than DESi-alone."""
    assert dual_agent_coverage() > desi_alone_coverage()
    assert productivity_gain() > 0.0


# --- DESi controls without choking --------------
def test_wild_not_eliminated() -> None:
    """DESi must not eliminate or homogenise the wild
    explorer - every wild path keeps positive value."""
    assert wild_not_eliminated() is True
    for v in governed_values().values():
        assert v > 0.0


def test_certainty_inflation_refused() -> None:
    """The wild asserts high certainty; DESi measures the
    pressure but refuses to adopt it (a positive gap)."""
    assert certainty_pressure() > 0.50
    assert certainty_gap() > 0.0


def test_no_authority_drift() -> None:
    assert authority_drift() <= 0.05


def test_wild_redundancy_measured() -> None:
    assert wild_redundancy() > 0.0


def test_metrics_in_unit_interval() -> None:
    for m in (
        exploration_divergence(), wild_redundancy(),
        novelty_generation(), certainty_pressure(),
        authority_drift(),
    ):
        assert 0.0 <= m <= 1.0


def test_wild_corpus_nonempty() -> None:
    assert len(wild_trajectories()) >= 1


# --- replay / recommendation / determinism ------
def test_replay_stability_one() -> None:
    assert build_report().replay_stability == 1.0


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
    art = _load("v20_0_sandbox.json")
    assert art["schema_version"] == (
        "v20_0_dual_agent_exploration_sandbox"
    )


def test_artifact_carries_disclaimer() -> None:
    art = _load("v20_0_sandbox.json")
    disc = art["disclaimer"].lower()
    assert "no final authority" in disc
    assert "never eliminating or homogenising" in disc
    assert "claims no optimal strategy" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v20_0_sandbox.json")
    required = {
        "exploration_divergence",
        "wild_redundancy",
        "novelty_generation",
        "certainty_pressure",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v20_0_sandbox.json")
    live = build_sandbox_artifact()
    assert art == live
