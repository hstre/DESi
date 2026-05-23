"""v27.2 - Research Convergence & Divergence tests."""
from __future__ import annotations

import json
import pathlib

from desi.research_convergence import (
    authority_marker_hits, build_convergence_artifact,
    build_report, conflict_lines, conflict_structure_visibility,
    convergence_visibility, converging_papers,
    emergent_trends, epistemic_neutrality, fragile_claims,
    method_cluster_visibility, reproducible_claims,
    replay_stability, shared_assumptions, shared_method_clusters,
)
from desi.research_convergence.report import (
    REPORT_VERDICTS, VERDICT_NEUTRAL,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "research_harvester"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(encoding="utf-8"),
    )


# --- convergence --------------------------------
def test_convergence_visibility_full() -> None:
    assert convergence_visibility() == 1.0


def test_emergent_trends_are_frequencies() -> None:
    trends = emergent_trends()
    assert trends
    for kind, name, freq in trends:
        assert kind in {"method", "assumption", "topic"}
        assert isinstance(freq, int) and freq >= 2


def test_shared_method_clusters_exist() -> None:
    clusters = shared_method_clusters()
    # generator/governor split is shared by H1 and H2
    assert "generator_governor_split" in clusters
    assert len(clusters["generator_governor_split"]) >= 2


def test_shared_assumptions_exist() -> None:
    assumptions = dict(shared_assumptions())
    assert "exploration_matters" in assumptions
    assert len(assumptions["exploration_matters"]) >= 2


# --- divergence ---------------------------------
def test_conflict_structure_visibility_full() -> None:
    assert conflict_structure_visibility() == 1.0


def test_conflict_lines_show_both_stances() -> None:
    lines = conflict_lines()
    assert len(lines) >= 1
    for l in lines:
        assert l.is_complete()
        assert l.stance_a and l.stance_b


def test_fragile_and_reproducible_marked_by_class() -> None:
    assert fragile_claims()
    assert reproducible_claims()


# --- clusters -----------------------------------
def test_method_cluster_visibility_full() -> None:
    assert method_cluster_visibility() == 1.0


# --- epistemic neutrality (core safety rule) ----
def test_epistemic_neutrality_full() -> None:
    assert epistemic_neutrality() >= 0.95


def test_no_authority_markers() -> None:
    assert authority_marker_hits() == ()


def test_report_has_no_ranking_or_score_fields() -> None:
    d = build_report().to_dict()
    forbidden = {
        "score", "rank", "ranking", "impact", "best", "winner",
        "quality",
    }
    assert forbidden.isdisjoint(set(d.keys()))


def test_artifact_structural_content_has_no_score() -> None:
    # the structural outputs carry no ranking/score - emergent
    # trends expose only kind/name/frequency (the disclaimer is
    # allowed to *name* what DESi does not do).
    art = _load("v27_2_convergence.json")
    for t in art["emergent_trends"]:
        assert set(t.keys()) == {"kind", "name", "frequency"}
    assert art["authority_marker_hits"] == []
    for line in art["conflict_lines"]:
        assert set(line.keys()) == {
            "paper_a", "paper_b", "stance_a", "stance_b",
        }


# --- replay -------------------------------------
def test_replay_stability_one() -> None:
    assert replay_stability() == 1.0


def test_metrics_in_unit_interval() -> None:
    for m in (
        convergence_visibility(),
        conflict_structure_visibility(),
        method_cluster_visibility(), epistemic_neutrality(),
        replay_stability(),
    ):
        assert 0.0 <= m <= 1.0


# --- report -------------------------------------
def test_recommendation_in_closed_set() -> None:
    assert build_report().recommendation in set(REPORT_VERDICTS)


def test_recommendation_is_neutral() -> None:
    assert build_report().recommendation == VERDICT_NEUTRAL


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v27_2_convergence.json")
    assert art["schema_version"] == "v27_2_research_convergence"


def test_artifact_carries_disclaimer() -> None:
    art = _load("v27_2_convergence.json")
    disc = art["disclaimer"].lower()
    assert "never evaluates them" in disc
    assert "right direction" in disc
    assert "frequencies, not scores" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v27_2_convergence.json")
    required = {
        "convergence_visibility",
        "conflict_structure_visibility",
        "method_cluster_visibility", "epistemic_neutrality",
        "replay_stability",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v27_2_convergence.json")
    live = build_convergence_artifact()
    assert art == live
