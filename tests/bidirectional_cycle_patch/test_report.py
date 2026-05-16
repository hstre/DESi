"""v4.5 — report build + recommendation gate + artifact pin."""
from __future__ import annotations

import json
import pathlib
from datetime import datetime, timezone

from desi.bidirectional_cycle_patch import (
    RecommendationOutcome, V40_PRE_V43_REPLAY_HASH,
    V41_PRE_V43_REPLAY_HASH, V42_PRE_V43_REPLAY_HASH,
    V43_REPLAY_HASH, V44_REPLAY_HASH, build_v45_report,
)


_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


def _build():
    when = datetime(2026, 5, 16, tzinfo=timezone.utc)
    return build_v45_report(started_at=when, finished_at=when)


def test_replay_hash_is_deterministic() -> None:
    a = _build()
    b = _build()
    assert a.replay_hash == b.replay_hash


def test_pre_v45_hashes_referenced() -> None:
    r = _build()
    assert r.v40_pre_v43_replay_hash == V40_PRE_V43_REPLAY_HASH
    assert r.v41_pre_v43_replay_hash == V41_PRE_V43_REPLAY_HASH
    assert r.v42_pre_v43_replay_hash == V42_PRE_V43_REPLAY_HASH
    assert r.v43_replay_hash == V43_REPLAY_HASH
    assert r.v44_replay_hash == V44_REPLAY_HASH


def test_v45_recommendation_label_set_remains_closed() -> None:
    """Under any later runtime patch, the v4.5 report builder
    must still emit one of the closed recommendation labels.
    The CONFIRMED label is a v4.5-era property — later
    patches that change false_support_after will shift the
    label. We assert the closed-enum membership invariant."""
    r = _build()
    allowed = {v.value for v in RecommendationOutcome}
    assert r.recommended_next in allowed


def test_frozen_v45_artifact_carries_v45_era_values() -> None:
    """The committed v4.5 artifact is the v4.5-era snapshot.
    After v4.7 the live rebuild produces different metrics
    (the v4.7 patch retires the MODALITY clusters v4.5 left
    untouched). We assert structural fields on the frozen
    file without comparing to a live rebuild."""
    artifact = _REPO_ROOT / "artifacts" / "v4_5" / "report.json"
    assert artifact.exists()
    data = json.loads(artifact.read_text(encoding="utf-8"))
    assert data["replay_hash"] == "86418c9d976cc147"
    assert data["recommended_next"] == (
        RecommendationOutcome.CONFIRMED.value
    )
    assert data["effect"]["false_support_after"] == 19
    assert data["effect"]["reduction"] == 5
