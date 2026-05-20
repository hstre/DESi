"""v18.2 - Literalism & Ideological Compression tests."""
from __future__ import annotations

import json
import pathlib

from desi.religious_compression import (
    ambiguity_preservation, attempted_compression,
    build_compression_artifact, build_report,
    compression_attempts, compression_resistance,
    contested_topic_count, context_preservation,
    dogmatic_compression, epistemic_integrity,
    preserved_layers, propaganda_attempts,
    propaganda_detection,
)
from desi.religious_compression.report import (
    REPORT_VERDICTS, VERDICT_RESISTED,
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


# --- the compression pressure is real -----------
def test_attempts_are_real() -> None:
    assert len(compression_attempts()) >= 1
    assert attempted_compression() > 0.20
    assert contested_topic_count() >= 1


# --- DESi resists -------------------------------
def test_no_governed_compression() -> None:
    assert dogmatic_compression() <= 0.05
    assert compression_resistance() >= 0.90


def test_ambiguity_preserved() -> None:
    assert ambiguity_preservation() >= 0.90
    # every attacked topic keeps >= 2 readings
    for a in compression_attempts():
        assert len(preserved_layers(a)) >= 2


def test_context_preserved() -> None:
    assert context_preservation() >= 0.90


def test_propaganda_detected() -> None:
    assert propaganda_detection() == 1.0
    assert len(propaganda_attempts()) >= 1


def test_epistemic_integrity_high() -> None:
    assert epistemic_integrity() >= 0.90


def test_metrics_in_unit_interval() -> None:
    for m in (
        dogmatic_compression(), ambiguity_preservation(),
        context_preservation(), propaganda_detection(),
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


def test_recommendation_is_resisted() -> None:
    assert build_report().recommendation == VERDICT_RESISTED


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v18_2_compression.json")
    assert art["schema_version"] == (
        "v18_2_literalism_ideological_compression"
    )


def test_artifact_carries_disclaimer() -> None:
    art = _load("v18_2_compression.json")
    disc = art["disclaimer"].lower()
    assert "without becoming ideological" in disc
    assert "stress fixtures" in disc
    assert "no real scripture content" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v18_2_compression.json")
    required = {
        "dogmatic_compression",
        "ambiguity_preservation",
        "context_preservation",
        "propaganda_detection",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v18_2_compression.json")
    live = build_compression_artifact()
    assert art == live
