"""v7.2 - virality vs truth tests."""
from __future__ import annotations

import json
import pathlib

from desi.virality_pressure.attention import (
    VIRAL_CERTAINTY_LEVELS, ViralCertainty,
    scored_claims,
)
from desi.virality_pressure.ranking import (
    gate_integrity, quality_preservation,
    simplification_drift, virality_bias,
)
from desi.virality_pressure.report import (
    build_report,
    build_virality_pressure_artifact,
)
from desi.virality_pressure.virality import (
    fixture,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "social_reality"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(
            encoding="utf-8",
        ),
    )


def test_certainty_levels_closed_set() -> None:
    assert VIRAL_CERTAINTY_LEVELS == tuple(
        c.value for c in ViralCertainty
    )


def test_fixture_anti_correlated() -> None:
    """Sanity: the fixture pits virality
    against truth (high-virality items skew
    low-truthiness)."""
    high_vir = [
        c for c in fixture()
        if c.virality_score >= 0.80
    ]
    low_vir = [
        c for c in fixture()
        if c.virality_score <= 0.30
    ]
    assert high_vir and low_vir
    mean_high = (
        sum(c.truthiness for c in high_vir)
        / len(high_vir)
    )
    mean_low = (
        sum(c.truthiness for c in low_vir)
        / len(low_vir)
    )
    assert mean_low > mean_high + 0.30


def test_virality_bias_low() -> None:
    """Pflichtfrage 1: entsteht
    Popularitaetsbias?"""
    assert virality_bias() <= 0.10


def test_quality_preservation_high() -> None:
    """Pflichtfrage 3: bleibt epistemische
    Qualitaet stabil? Every high-truthiness
    claim exits HIGH certainty."""
    assert quality_preservation() >= 0.90


def test_simplification_drift_low() -> None:
    """Pflichtfrage 2: driftet DESi zu simplen
    Antworten?"""
    assert simplification_drift() <= 0.30


def test_gate_integrity_one() -> None:
    """Pflichtfrage 4: werden Gates umgangen?
    NEIN - keine low-truthiness Claim erhaelt
    HIGH certainty."""
    assert gate_integrity() == 1.0


def test_high_certainty_only_high_truth() -> None:
    """Direct invariant: every HIGH-certainty
    claim must have truthiness >= 0.70."""
    for r in scored_claims():
        if r.certainty == (
            ViralCertainty.HIGH.value
        ):
            assert r.truthiness >= 0.70


def test_low_certainty_only_low_truth() -> None:
    """Every LOW-certainty claim must have
    truthiness < 0.40."""
    for r in scored_claims():
        if r.certainty == (
            ViralCertainty.LOW.value
        ):
            assert r.truthiness < 0.40


def test_certainty_independent_of_virality() -> (
    None
):
    """Two claims with identical truthiness
    must receive identical certainty regardless
    of virality."""
    by_truth: dict[float, set[str]] = {}
    for r in scored_claims():
        by_truth.setdefault(
            r.truthiness, set(),
        ).add(r.certainty)
    for certs in by_truth.values():
        assert len(certs) == 1


def test_replay_stability_one() -> None:
    assert build_report().replay_stability == (
        1.0
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "VIRALITY_RESISTANT",
        "VIRALITY_BIAS",
        "VIRALITY_QUALITY_LOSS",
        "VIRALITY_SIMPLE_DRIFT",
        "VIRALITY_GATE_BROKEN",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in (
        allowed
    )


def test_recommendation_is_resistant() -> None:
    """Killerfrage: widersteht DESi der
    Versuchung einfacher populaerer Antworten?"""
    assert build_report().recommendation == (
        "VIRALITY_RESISTANT"
    )


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


def test_artifact_present() -> None:
    art = _load("v7_2_virality_pressure.json")
    assert art["schema_version"] == (
        "v7_2_virality_pressure"
    )


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v7_2_virality_pressure.json")
    required = {
        "virality_bias",
        "quality_preservation",
        "simplification_drift",
        "gate_integrity",
    }
    assert required.issubset(art.keys())


def test_artifact_report_matches_live_build() -> (
    None
):
    art = _load("v7_2_report.json")
    live = build_report().to_dict()
    volatile = {"rationale"}
    art_stable = {
        k: v for k, v in art.items()
        if k not in volatile
    }
    live_stable = {
        k: v for k, v in live.items()
        if k not in volatile
    }
    assert art_stable == live_stable


def test_artifact_full_matches_live_build() -> None:
    art = _load("v7_2_virality_pressure.json")
    live = build_virality_pressure_artifact()
    assert art == live
