"""v4.6 — report build + recommendation gate + artifact pin."""
from __future__ import annotations

import json
import pathlib
from datetime import datetime, timezone

from desi.warrant_probe import (
    MAX_UNKNOWN_FRACTION, MIN_LARGEST_CLUSTER,
    RecommendationOutcome, V40_PRE_V43_REPLAY_HASH,
    V41_PRE_V43_REPLAY_HASH, V42_PRE_V43_REPLAY_HASH,
    V43_REPLAY_HASH, V44_REPLAY_HASH, V45_REPLAY_HASH,
    build_v46_report,
)


_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


def _build():
    when = datetime(2026, 5, 16, tzinfo=timezone.utc)
    return build_v46_report(started_at=when, finished_at=when)


def test_replay_hash_is_deterministic() -> None:
    a = _build()
    b = _build()
    assert a.replay_hash == b.replay_hash


def test_pre_v46_hashes_referenced() -> None:
    r = _build()
    assert r.v40_pre_v43_replay_hash == V40_PRE_V43_REPLAY_HASH
    assert r.v41_pre_v43_replay_hash == V41_PRE_V43_REPLAY_HASH
    assert r.v42_pre_v43_replay_hash == V42_PRE_V43_REPLAY_HASH
    assert r.v43_replay_hash == V43_REPLAY_HASH
    assert r.v44_replay_hash == V44_REPLAY_HASH
    assert r.v45_replay_hash == V45_REPLAY_HASH


def test_v46_invariants_under_live_audit() -> None:
    """Invariants that survive any later runtime patch:
    largest_cluster discipline and unknown_fraction
    discipline. The recommendation label drifts after v4.7
    (residue_count != EXPECTED_RESIDUE_COUNT will trigger
    UNKNOWN); we assert closed-enum membership."""
    r = _build()
    assert r.distribution.largest_cluster >= MIN_LARGEST_CLUSTER
    assert r.distribution.unknown_fraction <= MAX_UNKNOWN_FRACTION
    assert r.recommended_next in {
        v.value for v in RecommendationOutcome
    }


def test_frozen_v46_artifact_carries_v46_era_values() -> None:
    """The v4.6 artifact is the v4.6-era snapshot. After v4.7
    the live rebuild produces a smaller residue (the W3
    cluster is gone). We assert structural fields on the
    frozen file without comparing to a live rebuild."""
    artifact = _REPO_ROOT / "artifacts" / "v4_6" / "report.json"
    assert artifact.exists()
    data = json.loads(artifact.read_text(encoding="utf-8"))
    assert data["replay_hash"] == "58268fd9c4437e49"
    assert data["recommended_next"] == (
        RecommendationOutcome.LOCALIZED.value
    )
    assert data["residue_count"] == 19
