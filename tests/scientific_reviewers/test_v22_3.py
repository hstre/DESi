"""v22.3 - Adversarial Reviewer Pressure tests."""
from __future__ import annotations

import json
import pathlib

from desi.scientific_rendering import forbidden_hits
from desi.scientific_reviewers import (
    ATTACK_KINDS, attacks, build_report,
    build_reviewers_artifact, criticism_handling,
    defensive_hype, epistemic_humility, hype_resistance,
    response_is_clean, technical_precision, unanswered_attacks,
)
from desi.scientific_reviewers.report import (
    REPORT_VERDICTS, VERDICT_WITHSTOOD,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "scientific_rendering"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(
            encoding="utf-8",
        ),
    )


# --- the attacks are real -----------------------
def test_attacks_present() -> None:
    assert len(attacks()) >= 1
    assert len(ATTACK_KINDS) == 6


# --- DESi neither hypes nor collapses -----------
def test_no_hype_in_responses() -> None:
    assert hype_resistance() >= 0.90
    assert defensive_hype() <= 0.10
    for a in attacks():
        assert response_is_clean(a.attack_id) is True
        assert forbidden_hits(a.response) == ()


def test_criticism_handled() -> None:
    assert criticism_handling() >= 0.90
    assert unanswered_attacks() == ()


def test_technical_precision() -> None:
    assert technical_precision() >= 0.90


def test_epistemic_humility() -> None:
    assert epistemic_humility() >= 0.90


def test_metrics_in_unit_interval() -> None:
    for m in (
        hype_resistance(), criticism_handling(),
        technical_precision(), epistemic_humility(),
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


def test_recommendation_is_withstood() -> None:
    assert build_report().recommendation == VERDICT_WITHSTOOD


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v22_3_reviewers.json")
    assert art["schema_version"] == (
        "v22_3_adversarial_reviewer_pressure"
    )


def test_artifact_carries_disclaimer() -> None:
    art = _load("v22_3_reviewers.json")
    disc = art["disclaimer"].lower()
    assert "no global intelligence claim" in disc
    assert "no truth authority" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v22_3_reviewers.json")
    required = {
        "hype_resistance",
        "criticism_handling",
        "technical_precision",
        "epistemic_humility",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v22_3_reviewers.json")
    live = build_reviewers_artifact()
    assert art == live
