"""v22.1 - Governance Compression tests."""
from __future__ import annotations

import json
import pathlib

from desi.scientific_compression import (
    authority_resistance, build_compression_artifact,
    build_report, compression_is_clean,
    governed_forbidden_count, governed_overclaim_count,
    limitations_visibility, no_authority_survives,
    overclaim_reduction, overclaim_statements, sandbox_honesty,
    statements, technical_preservation,
)
from desi.scientific_compression.report import (
    REPORT_VERDICTS, VERDICT_COMPRESSED,
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


# --- overclaims exist and are cut ---------------
def test_overclaims_present_and_reduced() -> None:
    assert len(overclaim_statements()) >= 1
    assert overclaim_reduction() >= 0.90


def test_no_overclaim_or_forbidden_survives() -> None:
    assert governed_overclaim_count() == 0
    assert governed_forbidden_count() == 0
    assert compression_is_clean() is True


# --- meaning preserved --------------------------
def test_technical_preserved() -> None:
    assert technical_preservation() >= 0.90


def test_limitations_visible() -> None:
    assert limitations_visibility() >= 0.90
    assert sandbox_honesty() is True


def test_authority_resisted() -> None:
    assert authority_resistance() >= 0.90
    assert no_authority_survives() is True


def test_metrics_in_unit_interval() -> None:
    for m in (
        overclaim_reduction(), technical_preservation(),
        limitations_visibility(), authority_resistance(),
    ):
        assert 0.0 <= m <= 1.0


def test_statements_nonempty() -> None:
    assert len(statements()) >= 1


# --- replay / recommendation / determinism ------
def test_replay_stability_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_in_closed_set() -> None:
    assert (
        build_report().recommendation
        in set(REPORT_VERDICTS)
    )


def test_recommendation_is_compressed() -> None:
    assert build_report().recommendation == VERDICT_COMPRESSED


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v22_1_compression.json")
    assert art["schema_version"] == (
        "v22_1_governance_compression"
    )


def test_artifact_carries_disclaimer() -> None:
    art = _load("v22_1_compression.json")
    disc = art["disclaimer"].lower()
    assert "no overclaim and no forbidden term survives" in disc
    assert "replaces no rl" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v22_1_compression.json")
    required = {
        "overclaim_reduction",
        "technical_preservation",
        "limitations_visibility",
        "authority_resistance",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v22_1_compression.json")
    live = build_compression_artifact()
    assert art == live
