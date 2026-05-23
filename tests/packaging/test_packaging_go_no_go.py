"""Tests for the packaging migration GO/NO-GO assessment."""
from __future__ import annotations

import pathlib

from desi.packaging_audit import (
    assessment, build_go_no_go, importability, is_go,
    nondeterminism_hits, replay_drift_count,
)

_ROOT = pathlib.Path(__file__).resolve().parents[2]


def test_no_replay_drift() -> None:
    assert replay_drift_count() == 0


def test_no_hidden_state() -> None:
    assert nondeterminism_hits() == ()


def test_importability_full() -> None:
    assert importability() == 1.0


def test_assessment_is_go() -> None:
    a = assessment()
    assert a["packaging_replay_drift"] == 0
    assert a["hidden_state_introduced"] is False
    assert a["core_identity"] == 1.0
    assert a["governance_intact"] is True
    assert a["determinism_clean"] is True
    assert is_go() is True


def test_go_no_go_artifact_written_and_go() -> None:
    art = _ROOT / "artifacts" / "packaging" / (
        "desi_packaging_go_no_go.md"
    )
    assert art.exists()
    text = art.read_text(encoding="utf-8")
    assert "`GO`" in text
    assert "does not modify the replay kernel" in text


def test_go_no_go_matches_live_build() -> None:
    art = _ROOT / "artifacts" / "packaging" / (
        "desi_packaging_go_no_go.md"
    )
    assert art.read_text(encoding="utf-8") == build_go_no_go()
