"""v4.2 — report build + recommendation gate + replay
determinism + artifact pin."""
from __future__ import annotations

import json
import pathlib
from datetime import datetime, timezone

from desi.external_audit_probe import (
    RecommendationOutcome, V40_REPLAY_HASH, V41_REPLAY_HASH,
    build_v42_report,
)


_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


def _build():
    when = datetime(2026, 5, 16, tzinfo=timezone.utc)
    return build_v42_report(started_at=when, finished_at=when)


def test_replay_hash_is_deterministic() -> None:
    a = _build()
    b = _build()
    assert a.replay_hash == b.replay_hash


def test_report_pins_v40_and_v41_hashes() -> None:
    r = _build()
    assert r.v40_replay_hash == V40_REPLAY_HASH
    assert r.v41_replay_hash == V41_REPLAY_HASH


def test_recommended_next_is_closed_value() -> None:
    r = _build()
    allowed = {v.value for v in RecommendationOutcome}
    assert r.recommended_next in allowed


def test_success_criteria_hold() -> None:
    r = _build()
    assert r.case_count >= 100
    assert r.nc_count >= 50
    assert r.classification_accuracy >= 0.95
    assert r.total_contamination == 0


def test_artifact_matches_built_report() -> None:
    artifact = _REPO_ROOT / "artifacts" / "v4_2" / "report.json"
    assert artifact.exists()
    data = json.loads(artifact.read_text(encoding="utf-8"))
    r = _build()
    assert data["replay_hash"] == r.replay_hash
    assert data["recommended_next"] == r.recommended_next
    assert data["case_count"] == r.case_count
    assert data["total_contamination"] == 0
    assert data["v40_replay_hash"] == V40_REPLAY_HASH
    assert data["v41_replay_hash"] == V41_REPLAY_HASH
