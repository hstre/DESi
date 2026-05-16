"""v4.8 — report build + recommendation gate + artifact pin."""
from __future__ import annotations

import json
import pathlib
from datetime import datetime, timezone

from desi.content_audit_probe import (
    MAX_UNKNOWN_FRACTION, MIN_LARGEST_CLUSTER,
    RecommendationOutcome, V40_PRE_V43_REPLAY_HASH,
    V41_PRE_V43_REPLAY_HASH, V42_PRE_V43_REPLAY_HASH,
    V43_REPLAY_HASH, V44_REPLAY_HASH, V45_REPLAY_HASH,
    V46_REPLAY_HASH, V47_REPLAY_HASH, build_v48_report,
)


_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


def _build():
    when = datetime(2026, 5, 16, tzinfo=timezone.utc)
    return build_v48_report(started_at=when, finished_at=when)


def test_replay_hash_is_deterministic() -> None:
    a = _build()
    b = _build()
    assert a.replay_hash == b.replay_hash


def test_pre_v48_hashes_referenced() -> None:
    r = _build()
    assert r.v40_pre_v43_replay_hash == V40_PRE_V43_REPLAY_HASH
    assert r.v41_pre_v43_replay_hash == V41_PRE_V43_REPLAY_HASH
    assert r.v42_pre_v43_replay_hash == V42_PRE_V43_REPLAY_HASH
    assert r.v43_replay_hash == V43_REPLAY_HASH
    assert r.v44_replay_hash == V44_REPLAY_HASH
    assert r.v45_replay_hash == V45_REPLAY_HASH
    assert r.v46_replay_hash == V46_REPLAY_HASH
    assert r.v47_replay_hash == V47_REPLAY_HASH


def test_recommendation_is_localized() -> None:
    r = _build()
    assert r.recommended_next == (
        RecommendationOutcome.LOCALIZED.value
    )
    assert r.distribution.largest_cluster >= MIN_LARGEST_CLUSTER
    assert r.distribution.unknown_fraction <= MAX_UNKNOWN_FRACTION


def test_artifact_matches_built_report() -> None:
    artifact = _REPO_ROOT / "artifacts" / "v4_8" / "report.json"
    assert artifact.exists()
    data = json.loads(artifact.read_text(encoding="utf-8"))
    r = _build()
    assert data["replay_hash"] == r.replay_hash
    assert data["recommended_next"] == r.recommended_next
    assert data["residue_count"] == r.residue_count
