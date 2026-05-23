"""v31.2 - Comparative Peripheral Evolution tests."""
from __future__ import annotations

import json
import pathlib

from desi.peripheral_mutation_comparison import (
    all_outputs_identical, baseline_recomputes,
    build_comparison_artifact, build_report, core_diff,
    core_identity, governance_identity, measured_improvement,
    mutated_recomputes, regression_survival, replay_stability,
)
from desi.peripheral_mutation_comparison.report import (
    REPORT_VERDICTS, VERDICT_REAL,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "peripheral_mutation"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(encoding="utf-8"),
    )


# --- measured improvement -----------------------
def test_measured_improvement_above_floor() -> None:
    assert measured_improvement() >= 0.20


def test_recomputes_reduced() -> None:
    assert mutated_recomputes() < baseline_recomputes()


# --- core / governance identity -----------------
def test_core_identity_full() -> None:
    assert core_identity() == 1.0
    assert core_diff() is False


def test_governance_identity_full() -> None:
    assert governance_identity() == 1.0


def test_outputs_identical() -> None:
    assert all_outputs_identical() is True


# --- regression / replay ------------------------
def test_regression_survival_full() -> None:
    assert regression_survival() == 1.0


def test_replay_stability_one() -> None:
    assert replay_stability() == 1.0


def test_metrics_in_unit_interval() -> None:
    for m in (
        measured_improvement(), core_identity(),
        governance_identity(), regression_survival(),
        replay_stability(),
    ):
        assert 0.0 <= m <= 1.0


# --- report -------------------------------------
def test_recommendation_in_closed_set() -> None:
    assert build_report().recommendation in set(REPORT_VERDICTS)


def test_recommendation_is_real() -> None:
    assert build_report().recommendation == VERDICT_REAL


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


def test_human_approval_required() -> None:
    assert build_report().human_approval_required is True


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v31_2_comparison.json")
    assert art["schema_version"] == "v31_2_peripheral_comparison"


def test_artifact_is_branch_isolated() -> None:
    art = _load("v31_2_comparison.json")
    assert art["branch"] == "proposal/peripheral_mutation_v1"


def test_artifact_carries_disclaimer() -> None:
    art = _load("v31_2_comparison.json")
    disc = art["disclaimer"].lower()
    assert "measured" in disc
    assert "not projected" in disc
    assert "byte-identical" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v31_2_comparison.json")
    required = {
        "measured_improvement", "core_identity",
        "governance_identity", "regression_survival",
        "replay_stability",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v31_2_comparison.json")
    live = build_comparison_artifact()
    assert art == live
