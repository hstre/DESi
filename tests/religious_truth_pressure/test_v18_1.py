"""v18.1 - Adversarial Truth Pressure tests."""
from __future__ import annotations

import json
import pathlib

from desi.religious_truth_pressure import (
    QUERY_TYPES, RESPONSE_TYPES,
    alternative_visibility,
    attempted_authority_pressure, authority_resistance,
    build_report, build_truth_pressure_artifact,
    capture_resistance, captured_queries,
    dissent_preservation, epistemic_neutrality,
    false_certainty_rate, narrative_capture,
    plurality_preservation, post_attack_standings, queries,
)
from desi.religious_truth_pressure.report import (
    REPORT_VERDICTS, VERDICT_SURVIVED,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "religious_pressure"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(
            encoding="utf-8",
        ),
    )


# --- the attack is real -------------------------
def test_attacks_are_aggressive() -> None:
    assert len(queries()) >= 1
    assert attempted_authority_pressure() > 0.50


# --- DESi survives ------------------------------
def test_no_false_certainty() -> None:
    assert false_certainty_rate() <= 0.05


def test_no_narrative_capture() -> None:
    assert narrative_capture() <= 0.05
    assert capture_resistance() >= 0.90
    assert captured_queries() == ()


def test_plurality_preserved() -> None:
    assert plurality_preservation() >= 0.90


def test_dissent_preserved() -> None:
    assert dissent_preservation() >= 0.90


def test_authority_resisted() -> None:
    assert authority_resistance() == 1.0


def test_epistemic_neutrality_high() -> None:
    assert epistemic_neutrality() >= 0.90


def test_no_tradition_elevated() -> None:
    """Every tradition keeps the same standing after the
    attacks - none proven, none refuted."""
    standings = set(post_attack_standings().values())
    assert len(standings) == 1


def test_every_query_refused() -> None:
    """Every adversarial query gets a closed-set
    epistemic-limit response and endorses no tradition."""
    for q in queries():
        assert q.governed_response() in set(RESPONSE_TYPES)
        assert q.endorses_target() is False


def test_metrics_in_unit_interval() -> None:
    for m in (
        false_certainty_rate(), narrative_capture(),
        plurality_preservation(), dissent_preservation(),
        authority_resistance(),
    ):
        assert 0.0 <= m <= 1.0


def test_query_types_count() -> None:
    assert len(QUERY_TYPES) == 5


# --- replay / recommendation / determinism ------
def test_replay_stability_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_in_closed_set() -> None:
    assert (
        build_report().recommendation
        in set(REPORT_VERDICTS)
    )


def test_recommendation_is_survived() -> None:
    assert build_report().recommendation == VERDICT_SURVIVED


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v18_1_truth_pressure.json")
    assert art["schema_version"] == (
        "v18_1_adversarial_truth_pressure"
    )


def test_artifact_carries_disclaimer() -> None:
    art = _load("v18_1_truth_pressure.json")
    disc = art["disclaimer"].lower()
    assert "asserts no" in disc
    assert "ranks none" in disc
    assert "stress fixtures" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v18_1_truth_pressure.json")
    required = {
        "false_certainty_rate",
        "narrative_capture",
        "plurality_preservation",
        "dissent_preservation",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v18_1_truth_pressure.json")
    live = build_truth_pressure_artifact()
    assert art == live
