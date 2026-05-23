"""Tests for the v3.0 replayer (Aufgabe 3)."""
from __future__ import annotations

import json
import pathlib

import pytest

from desi.self_audit import (
    ClaimKind,
    ClaimVerdict,
    ExplicitClaim,
    replay_claims,
)


def _make_artifact(tmp_path: pathlib.Path, name: str, body: dict) -> None:
    p = tmp_path / "artifacts" / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(body))


def _claim(**overrides) -> ExplicitClaim:
    base = dict(
        claim_id="cl_x", doc_id="doc_x", doc_path="x.md",
        line_number=1, line_text="",
        kind=ClaimKind.HASH, key="replay_hash",
        value="0" * 16,
    )
    base.update(overrides)
    return ExplicitClaim(**base)


def test_hash_claim_verified_when_found_in_artifact(tmp_path) -> None:
    _make_artifact(
        tmp_path, "v_x/report.json",
        {"replay_hash": "deadbeefdeadbeef"},
    )
    c = _claim(value="deadbeefdeadbeef")
    out = replay_claims((c,), artifact_root=tmp_path / "artifacts")
    assert out[0].verdict is ClaimVerdict.VERIFIED


def test_hash_claim_missing_artifact_when_absent(tmp_path) -> None:
    _make_artifact(tmp_path, "v_x/report.json", {"key": "other"})
    c = _claim(value="deadbeefdeadbeef")
    out = replay_claims((c,), artifact_root=tmp_path / "artifacts")
    assert out[0].verdict is ClaimVerdict.MISSING_ARTIFACT


def test_hash_claim_mismatch_when_referenced_artifact_disagrees(
    tmp_path,
) -> None:
    _make_artifact(
        tmp_path, "v_x/report.json",
        {"replay_hash": "actualactualact1"},
    )
    # The claim explicitly references the artifact but cites a
    # different hash that happens to appear in some OTHER file's
    # blob. Simulate that by writing both files; the claim's
    # referenced artifact must report the mismatch.
    _make_artifact(
        tmp_path, "v_y/other.json",
        {"random_field": "claimed_hash_15"},
    )
    c = _claim(
        value="claimed_hash_15",
        referenced_artifact="artifacts/v_x/report.json",
    )
    out = replay_claims((c,), artifact_root=tmp_path / "artifacts")
    assert out[0].verdict is ClaimVerdict.HASH_MISMATCH


def test_numeric_claim_verified_against_referenced_artifact(
    tmp_path,
) -> None:
    _make_artifact(
        tmp_path, "v_x/report.json",
        {"precision": 1.0, "recall": 1.0},
    )
    c = _claim(
        kind=ClaimKind.NUMERIC, key="precision", value="1.0",
        referenced_artifact="artifacts/v_x/report.json",
    )
    out = replay_claims((c,), artifact_root=tmp_path / "artifacts")
    assert out[0].verdict is ClaimVerdict.VERIFIED


def test_numeric_claim_value_mismatch(tmp_path) -> None:
    _make_artifact(
        tmp_path, "v_x/report.json",
        {"precision": 0.9},
    )
    c = _claim(
        kind=ClaimKind.NUMERIC, key="precision", value="1.0",
        referenced_artifact="artifacts/v_x/report.json",
    )
    out = replay_claims((c,), artifact_root=tmp_path / "artifacts")
    assert out[0].verdict is ClaimVerdict.VALUE_MISMATCH


def test_numeric_claim_ambiguous_when_no_artifact_carries_key(
    tmp_path,
) -> None:
    _make_artifact(tmp_path, "v_x/report.json", {"unrelated": 1.0})
    c = _claim(
        kind=ClaimKind.NUMERIC, key="precision", value="0.5",
    )
    out = replay_claims((c,), artifact_root=tmp_path / "artifacts")
    assert out[0].verdict is ClaimVerdict.AMBIGUOUS_REFERENCE


def test_phase_claim_verified_when_matches_referenced_artifact(
    tmp_path,
) -> None:
    _make_artifact(
        tmp_path, "v_x/report.json",
        {"phase": "complete"},
    )
    c = _claim(
        kind=ClaimKind.PHASE, key="phase", value="complete",
        referenced_artifact="artifacts/v_x/report.json",
    )
    out = replay_claims((c,), artifact_root=tmp_path / "artifacts")
    assert out[0].verdict is ClaimVerdict.VERIFIED


def test_phase_claim_value_mismatch_when_referenced(
    tmp_path,
) -> None:
    _make_artifact(
        tmp_path, "v_x/report.json",
        {"phase": "guard_synthesis"},
    )
    c = _claim(
        kind=ClaimKind.PHASE, key="phase", value="complete",
        referenced_artifact="artifacts/v_x/report.json",
    )
    out = replay_claims((c,), artifact_root=tmp_path / "artifacts")
    assert out[0].verdict is ClaimVerdict.VALUE_MISMATCH


def test_replay_is_deterministic_across_runs(tmp_path) -> None:
    _make_artifact(tmp_path, "v_x/report.json",
                    {"replay_hash": "deadbeefdeadbeef"})
    c = _claim(value="deadbeefdeadbeef")
    a = replay_claims((c,), artifact_root=tmp_path / "artifacts")
    b = replay_claims((c,), artifact_root=tmp_path / "artifacts")
    assert a == b
