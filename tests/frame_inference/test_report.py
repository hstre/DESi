"""v4.1 — report build + safety gates + replay determinism."""
from __future__ import annotations

import json
import pathlib
from datetime import datetime, timezone

from desi.frame_inference import (
    InferenceStrategy, MAX_FRAME_FALSE_ASSIGNMENT,
    MIN_FRAME_PRECISION, MIN_FRAME_RECALL, MIN_NC_DETECTION,
    RecommendationOutcome, V40_REPLAY_HASH, build_v41_report,
)


_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


def _build():
    when = datetime(2026, 5, 16, tzinfo=timezone.utc)
    return build_v41_report(started_at=when, finished_at=when)


def test_replay_hash_is_deterministic() -> None:
    a = _build()
    b = _build()
    assert a.replay_hash == b.replay_hash


def test_report_carries_v40_pin() -> None:
    r = _build()
    assert r.v40_replay_hash == V40_REPLAY_HASH
    assert r.chain_count == 800
    assert r.transition_count == 3200
    assert r.nc_count == 100
    assert r.nc_contamination_count == 0


def test_recommended_next_is_closed_value() -> None:
    r = _build()
    allowed = {v.value for v in RecommendationOutcome}
    assert r.recommended_next in allowed


def test_strategies_present_with_safety_gates_evaluated() -> None:
    r = _build()
    strategies = {s.strategy for s in r.strategy_reports}
    assert strategies == {s.value for s in InferenceStrategy}
    for s in r.strategy_reports:
        # Safety-gate logic was actually applied:
        # invalid iff (false_support > 0) or (false_assign > 5%).
        expected_invalid = (
            s.pipeline_metrics.external_false_support > 0
            or s.frame_metrics.frame_false_assignment
            > MAX_FRAME_FALSE_ASSIGNMENT
        )
        assert s.valid == (not expected_invalid)


def test_artifact_matches_built_report() -> None:
    """The committed artifact must match the live report."""
    artifact_path = (
        _REPO_ROOT / "artifacts" / "v4_1" / "report.json"
    )
    assert artifact_path.exists()
    data = json.loads(artifact_path.read_text(encoding="utf-8"))
    r = _build()
    assert data["replay_hash"] == r.replay_hash
    assert data["recommended_next"] == r.recommended_next
    assert data["v40_replay_hash"] == V40_REPLAY_HASH
    assert data["chain_count"] == 800
    assert data["nc_contamination_count"] == 0


def test_thresholds_are_sane() -> None:
    assert 0.0 < MIN_FRAME_PRECISION <= 1.0
    assert 0.0 < MIN_FRAME_RECALL <= 1.0
    assert 0.0 <= MAX_FRAME_FALSE_ASSIGNMENT < 1.0
    assert 0.0 < MIN_NC_DETECTION <= 1.0
