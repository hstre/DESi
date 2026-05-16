"""v4.3 — report build + recommendation gate + artifact pin."""
from __future__ import annotations

import json
import pathlib
from datetime import datetime, timezone

from desi.external_audit_patch import (
    FALSE_SUPPORT_TARGET_AFTER, RecommendationOutcome,
    V40_PRE_V43_REPLAY_HASH, V41_PRE_V43_REPLAY_HASH,
    V42_PRE_V43_REPLAY_HASH, build_v43_report,
)


_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


def _build():
    when = datetime(2026, 5, 16, tzinfo=timezone.utc)
    return build_v43_report(started_at=when, finished_at=when)


def test_replay_hash_is_deterministic() -> None:
    a = _build()
    b = _build()
    assert a.replay_hash == b.replay_hash


def test_pre_v43_hashes_referenced() -> None:
    r = _build()
    assert r.v40_pre_v43_replay_hash == V40_PRE_V43_REPLAY_HASH
    assert r.v41_pre_v43_replay_hash == V41_PRE_V43_REPLAY_HASH
    assert r.v42_pre_v43_replay_hash == V42_PRE_V43_REPLAY_HASH


def test_recommendation_is_confirmed() -> None:
    r = _build()
    assert r.recommended_next == RecommendationOutcome.CONFIRMED.value
    assert r.effect.false_support_after <= FALSE_SUPPORT_TARGET_AFTER
    assert r.contamination.total_contamination == 0
    assert r.nc_detection_rate >= 0.95


def test_artifact_matches_built_report() -> None:
    artifact = _REPO_ROOT / "artifacts" / "v4_3" / "report.json"
    assert artifact.exists()
    data = json.loads(artifact.read_text(encoding="utf-8"))
    r = _build()
    assert data["replay_hash"] == r.replay_hash
    assert data["recommended_next"] == r.recommended_next
    assert (
        data["effect"]["false_support_after"]
        == r.effect.false_support_after
    )
