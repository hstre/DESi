"""Aufgaben 10 + 11 — recommendation gate + final artifact."""
from __future__ import annotations

import json
import pathlib


_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


def _v4_10_artifact() -> dict:
    p = _REPO_ROOT / "artifacts" / "v4_10" / "report.json"
    return json.loads(p.read_text(encoding="utf-8"))


def test_recommended_next_is_v4_line_frozen() -> None:
    d = _v4_10_artifact()
    assert d["recommended_next"] == "V4_LINE_FROZEN"


def test_claim_count_meets_directive() -> None:
    d = _v4_10_artifact()
    assert d["claim_count"] >= 120


def test_failed_hypotheses_meets_directive() -> None:
    d = _v4_10_artifact()
    assert d["failed_hypotheses_count"] >= 10


def test_drift_contradiction_missing_all_zero() -> None:
    d = _v4_10_artifact()
    assert d["drift_findings"] == 0
    assert d["contradiction_count"] == 0
    assert d["missing_pin_count"] == 0


def test_final_false_support_is_zero() -> None:
    d = _v4_10_artifact()
    assert d["final_false_support_count"] == 0


def test_v40_and_v49_replay_hashes_pinned() -> None:
    d = _v4_10_artifact()
    assert d["v40_replay_hash"] == "aefa8f1e3429225a"
    assert d["v49_replay_hash"] == "51122b802bd257dc"


def test_replay_hash_present() -> None:
    d = _v4_10_artifact()
    assert "replay_hash" in d
    assert isinstance(d["replay_hash"], str)
    assert len(d["replay_hash"]) == 16
