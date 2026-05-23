"""v28.3 - Comparative Evolution Benchmark tests."""
from __future__ import annotations

import json
import pathlib

from desi.self_improvement_comparison import (
    DIMENSIONS, SAFETY_INVARIANTS, authority_resistance,
    build_comparison_artifact, build_report,
    candidate_vector, comparative_improvement, comparison_table,
    current_vector, degraded_safety_dimensions,
    governance_preservation, improved_dimensions,
    is_genuine_improvement, regression_survival_preserved,
    replay_stability, safety_invariant_preservation,
)
from desi.self_improvement_comparison.report import (
    REPORT_VERDICTS, VERDICT_EVOLVED,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "self_improvement"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(encoding="utf-8"),
    )


# --- the nine dimensions ------------------------
def test_nine_dimensions() -> None:
    assert len(DIMENSIONS) == 9


def test_comparison_table_covers_all_dimensions() -> None:
    dims = {r.dimension for r in comparison_table()}
    assert dims == set(DIMENSIONS)


# --- safety invariants never degrade ------------
def test_safety_invariant_preservation_full() -> None:
    assert safety_invariant_preservation() == 1.0
    assert degraded_safety_dimensions() == ()


def test_every_safety_invariant_held() -> None:
    cur, cand = current_vector(), candidate_vector()
    for d in SAFETY_INVARIANTS:
        assert cand[d] == cur[d]


def test_no_dimension_degrades() -> None:
    for r in comparison_table():
        assert r.verdict in {"improved", "held"}


# --- genuine improvement ------------------------
def test_comparative_improvement_full() -> None:
    assert comparative_improvement() == 1.0


def test_is_genuine_improvement() -> None:
    assert is_genuine_improvement() is True
    assert improved_dimensions()  # at least one improved


def test_only_quality_dimensions_improved() -> None:
    for d in improved_dimensions():
        assert d not in SAFETY_INVARIANTS


# --- governance / authority ---------------------
def test_governance_preservation_full() -> None:
    assert governance_preservation() == 1.0


def test_authority_resistance_full() -> None:
    assert authority_resistance() == 1.0


def test_regression_survival_preserved() -> None:
    assert regression_survival_preserved() is True


# --- replay -------------------------------------
def test_replay_stability_one() -> None:
    assert replay_stability() == 1.0


def test_metrics_in_unit_interval() -> None:
    for m in (
        comparative_improvement(), governance_preservation(),
        safety_invariant_preservation(), authority_resistance(),
        replay_stability(),
    ):
        assert 0.0 <= m <= 1.0


# --- report -------------------------------------
def test_recommendation_in_closed_set() -> None:
    assert build_report().recommendation in set(REPORT_VERDICTS)


def test_recommendation_is_evolved() -> None:
    assert build_report().recommendation == VERDICT_EVOLVED


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v28_3_comparison.json")
    assert art["schema_version"] == "v28_3_comparative_evolution"


def test_artifact_carries_disclaimer() -> None:
    art = _load("v28_3_comparison.json")
    disc = art["disclaimer"].lower()
    assert "projection" in disc
    assert "not a measurement of a built system" in disc
    assert "no safety degradation" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v28_3_comparison.json")
    required = {
        "comparative_improvement", "governance_preservation",
        "safety_invariant_preservation", "authority_resistance",
        "replay_stability",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v28_3_comparison.json")
    live = build_comparison_artifact()
    assert art == live
