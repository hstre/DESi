"""v32.2 - Blind Evolution Evaluation tests."""
from __future__ import annotations

import json
import pathlib

from desi.frozen_benchmark_blind import (
    BLIND_EVALUATION, TRUE_BASELINE, TRUE_MUTATED, anon_observations,
    bias_resistance, blind_ranking, blind_winner,
    blind_winner_is_mutated, blindness_integrity,
    build_blind_artifact, build_report, margin, observed_labels,
    replay_stability, sealed_map,
)
from desi.frozen_benchmark_blind.report import (
    REPORT_VERDICTS, VERDICT_BLIND_BETTER,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "frozen_benchmark"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(encoding="utf-8"),
    )


# --- blindness ----------------------------------
def test_blind_evaluation_flag() -> None:
    assert BLIND_EVALUATION is True
    assert build_report().blind_evaluation is True


def test_blindness_integrity_full() -> None:
    assert blindness_integrity() == 1.0


def test_observations_carry_no_true_name() -> None:
    for o in anon_observations():
        blob = "|".join(str(v) for v in o.to_dict().values())
        assert TRUE_BASELINE not in blob
        assert TRUE_MUTATED not in blob
        assert o.anon_label.startswith("version_")


def test_two_anonymous_versions() -> None:
    labels = observed_labels()
    assert len(labels) == 2
    assert set(labels) == {"version_0", "version_1"}


# --- bias resistance ----------------------------
def test_bias_resistance_full() -> None:
    assert bias_resistance() == 1.0


def test_sealed_map_covers_both() -> None:
    sm = sealed_map()
    assert set(sm.values()) == {TRUE_BASELINE, TRUE_MUTATED}
    assert set(sm.keys()) == {"version_0", "version_1"}


# --- the blind outcome --------------------------
def test_blind_winner_is_mutated() -> None:
    assert blind_winner_is_mutated() is True
    assert sealed_map()[blind_winner()] == TRUE_MUTATED


def test_blind_ranking_orders_winner_first() -> None:
    ranking = blind_ranking()
    assert ranking[0] == blind_winner()
    assert len(ranking) == 2


def test_margin_is_recompute_gap() -> None:
    assert margin() == 32


# --- replay -------------------------------------
def test_replay_stability_one() -> None:
    assert replay_stability() == 1.0


def test_metrics_in_unit_interval() -> None:
    for m in (
        blindness_integrity(), bias_resistance(),
        replay_stability(),
    ):
        assert 0.0 <= m <= 1.0


# --- report -------------------------------------
def test_recommendation_in_closed_set() -> None:
    assert build_report().recommendation in set(REPORT_VERDICTS)


def test_recommendation_is_blind_better() -> None:
    assert build_report().recommendation == VERDICT_BLIND_BETTER


def test_report_not_halt() -> None:
    assert build_report().halt is False


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v32_2_blind.json")
    assert art["schema_version"] == "v32_2_blind_evaluation"
    assert art["blind_evaluation"] is True


def test_artifact_carries_disclaimer() -> None:
    art = _load("v32_2_blind.json")
    disc = art["disclaimer"].lower()
    assert "no version-aware scoring" in disc
    assert "no mutation favouritism" in disc
    assert "no branch bias" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v32_2_blind.json")
    required = {
        "blindness_integrity", "bias_resistance",
        "artifact_identity", "governance_identity",
        "replay_stability",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v32_2_blind.json")
    live = build_blind_artifact()
    assert art == live
