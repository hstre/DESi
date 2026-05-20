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


def test_v43_invariants_under_live_audit() -> None:
    """Live-audit invariants that survive every subsequent
    runtime patch (v4.5+): contamination stays at zero, NC
    detection stays above the v4.3 threshold, and v4.3's
    false-support target ceiling remains satisfied (later
    patches may push it lower; v4.3's target is a ceiling, not
    an equality)."""
    r = _build()
    assert r.contamination.total_contamination == 0
    assert r.nc_detection_rate >= 0.95
    assert r.effect.false_support_after <= FALSE_SUPPORT_TARGET_AFTER


def test_frozen_v43_artifact_carries_v43_era_values() -> None:
    """The committed v4.3 artifact is the historical snapshot
    at v4.3 time. After v4.5 the live rebuild produces
    different metrics (the v4.5 patch retires the
    BIDIRECTIONAL_CYCLE residue v4.3 left untouched). We assert
    structural fields on the frozen file without comparing to
    a live rebuild."""
    artifact = _REPO_ROOT / "artifacts" / "v4_3" / "report.json"
    assert artifact.exists()
    data = json.loads(artifact.read_text(encoding="utf-8"))
    assert data["replay_hash"] == "7c63bcae4cf3fb37"
    assert data["recommended_next"] == (
        RecommendationOutcome.CONFIRMED.value
    )
    assert data["effect"]["false_support_before"] == 143
    assert data["effect"]["false_support_after"] == 24
