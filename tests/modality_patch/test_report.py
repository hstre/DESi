"""v4.7 — report build + recommendation + artifact pin."""
from __future__ import annotations

import json
import pathlib
from datetime import datetime, timezone

from desi.modality_patch import (
    RecommendationOutcome, V40_PRE_V43_REPLAY_HASH,
    V41_PRE_V43_REPLAY_HASH, V42_PRE_V43_REPLAY_HASH,
    V43_REPLAY_HASH, V44_REPLAY_HASH, V45_REPLAY_HASH,
    V46_REPLAY_HASH, build_v47_report,
)


_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


def _build():
    when = datetime(2026, 5, 16, tzinfo=timezone.utc)
    return build_v47_report(started_at=when, finished_at=when)


def test_replay_hash_is_deterministic() -> None:
    a = _build()
    b = _build()
    assert a.replay_hash == b.replay_hash


def test_pre_v47_hashes_referenced() -> None:
    r = _build()
    assert r.v40_pre_v43_replay_hash == V40_PRE_V43_REPLAY_HASH
    assert r.v41_pre_v43_replay_hash == V41_PRE_V43_REPLAY_HASH
    assert r.v42_pre_v43_replay_hash == V42_PRE_V43_REPLAY_HASH
    assert r.v43_replay_hash == V43_REPLAY_HASH
    assert r.v44_replay_hash == V44_REPLAY_HASH
    assert r.v45_replay_hash == V45_REPLAY_HASH
    assert r.v46_replay_hash == V46_REPLAY_HASH


def test_v47_recommendation_label_remains_closed() -> None:
    """Under any later runtime patch the v4.7 report builder
    must still emit one of the closed recommendation labels.
    The CONFIRMED label is a v4.7-era property; v4.9 retires
    additional clusters and the live rebuild drifts."""
    r = _build()
    allowed = {v.value for v in RecommendationOutcome}
    assert r.recommended_next in allowed


def test_frozen_v47_artifact_carries_v47_era_values() -> None:
    """The committed v4.7 artifact is the v4.7-era snapshot.
    After v4.9 the live rebuild produces a smaller
    false_support_after (zero). We assert structural fields
    on the frozen file."""
    artifact = _REPO_ROOT / "artifacts" / "v4_7" / "report.json"
    assert artifact.exists()
    data = json.loads(artifact.read_text(encoding="utf-8"))
    assert data["replay_hash"] == "2774818766a8035a"
    assert data["recommended_next"] == (
        RecommendationOutcome.CONFIRMED.value
    )
    assert data["effect"]["false_support_after"] == 9
    assert data["effect"]["reduction"] == 10
