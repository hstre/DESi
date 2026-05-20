"""v4.11 — report build + recommendation gate + artifact
pin."""
from __future__ import annotations

import json
import pathlib
from datetime import datetime, timezone

from desi.repro_audit import (
    RecommendationOutcome, build_v411_report,
)


_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


def _build():
    when = datetime(2026, 5, 16, tzinfo=timezone.utc)
    return build_v411_report(started_at=when, finished_at=when)


def test_replay_hash_is_deterministic() -> None:
    a = _build()
    b = _build()
    assert a.replay_hash == b.replay_hash


def test_recommended_next_is_confirmed() -> None:
    r = _build()
    assert r.recommended_next == (
        RecommendationOutcome.CONFIRMED.value
    )


def test_v28_invariants() -> None:
    r = _build()
    assert r.v2_8_frozen_hash == "1f4d9dfe44cb16e1"
    assert r.v2_8_repro_class in (
        "LIVE_REPLAY_STABLE", "HISTORICAL_RUNTIME_DRIFT",
    )


def test_artifact_files_exist() -> None:
    """v4.11 writes the report.json artifact; the
    environment.json and replay_matrix.json files are
    snapshots written by the build runner."""
    artifact = (
        _REPO_ROOT / "artifacts" / "v4_11" / "report.json"
    )
    assert artifact.exists()
    data = json.loads(artifact.read_text(encoding="utf-8"))
    assert data["recommended_next"] == (
        RecommendationOutcome.CONFIRMED.value
    )


def test_environment_and_replay_matrix_artifacts_exist() -> None:
    base = _REPO_ROOT / "artifacts" / "v4_11"
    assert (base / "environment.json").exists()
    assert (base / "replay_matrix.json").exists()
