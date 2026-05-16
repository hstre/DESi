"""v4.4 — report build + recommendation gate + artifact pin."""
from __future__ import annotations

import json
import pathlib
from datetime import datetime, timezone

from desi.residual_semantic_probe import (
    MAX_UNKNOWN_FRACTION, MIN_LARGEST_CLUSTER,
    RecommendationOutcome, V40_PRE_V43_REPLAY_HASH,
    V41_PRE_V43_REPLAY_HASH, V42_PRE_V43_REPLAY_HASH,
    V43_REPLAY_HASH, build_v44_report,
)


_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


def _build():
    when = datetime(2026, 5, 16, tzinfo=timezone.utc)
    return build_v44_report(started_at=when, finished_at=when)


def test_replay_hash_is_deterministic() -> None:
    a = _build()
    b = _build()
    assert a.replay_hash == b.replay_hash


def test_pre_v44_hashes_referenced() -> None:
    r = _build()
    assert r.v40_pre_v43_replay_hash == V40_PRE_V43_REPLAY_HASH
    assert r.v41_pre_v43_replay_hash == V41_PRE_V43_REPLAY_HASH
    assert r.v42_pre_v43_replay_hash == V42_PRE_V43_REPLAY_HASH
    assert r.v43_replay_hash == V43_REPLAY_HASH


def test_v44_invariants_under_live_audit() -> None:
    """Invariants that survive every subsequent runtime patch:
    the closed recommendation enum stays valid. Once v4.9
    retires every residue case the largest_cluster /
    unknown_fraction discipline is undefined, so we only
    assert it conditionally."""
    r = _build()
    if r.residue_count > 0:
        assert r.distribution.largest_cluster >= (
            MIN_LARGEST_CLUSTER
        )
        assert r.distribution.unknown_fraction <= (
            MAX_UNKNOWN_FRACTION
        )
    # Recommendation label may flip to UNKNOWN once
    # residue_count != EXPECTED_RESIDUE_COUNT; the label set
    # remains closed-enum either way.
    assert r.recommended_next in {
        v.value for v in RecommendationOutcome
    }


def test_frozen_v44_artifact_carries_v44_era_values() -> None:
    """The committed v4.4 artifact is the v4.4-era snapshot.
    After v4.5 the live rebuild produces a smaller residue
    (the BIDIRECTIONAL_CYCLE cluster is gone). We assert
    structural fields on the frozen file without comparing to
    a live rebuild."""
    artifact = _REPO_ROOT / "artifacts" / "v4_4" / "report.json"
    assert artifact.exists()
    data = json.loads(artifact.read_text(encoding="utf-8"))
    assert data["replay_hash"] == "bf4147b89f398224"
    assert data["recommended_next"] == (
        RecommendationOutcome.LOCALIZED.value
    )
    assert data["residue_count"] == 24
    assert data["classification_accuracy"] == 1.0
