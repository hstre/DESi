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


def test_v48_recommendation_label_remains_closed() -> None:
    """v4.9 retires both v4.8 target clusters, so the live
    rebuild's recommendation label drifts from LOCALIZED to
    UNKNOWN (residue_count != EXPECTED). We assert closed-
    enum membership only."""
    r = _build()
    allowed = {v.value for v in RecommendationOutcome}
    assert r.recommended_next in allowed


def test_frozen_v48_artifact_carries_v48_era_values() -> None:
    """The committed v4.8 artifact is the v4.8-era snapshot.
    After v4.9 the live rebuild returns an empty residue; we
    pin the v4.8-era residue (nine cases) via the frozen
    file."""
    artifact = _REPO_ROOT / "artifacts" / "v4_8" / "report.json"
    assert artifact.exists()
    data = json.loads(artifact.read_text(encoding="utf-8"))
    assert data["replay_hash"] == "d0835b564453cfc0"
    assert data["recommended_next"] == (
        RecommendationOutcome.LOCALIZED.value
    )
    assert data["residue_count"] == 9
    assert data["distribution"]["largest_cluster"] >= (
        MIN_LARGEST_CLUSTER
    )
    assert data["distribution"]["unknown_fraction"] <= (
        MAX_UNKNOWN_FRACTION
    )
