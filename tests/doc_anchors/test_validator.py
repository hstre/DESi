"""Tests for v3.1 anchor validator (Aufgabe 7)."""
from __future__ import annotations

import json
import pathlib

import pytest

from desi.doc_anchors import (
    AnchorVerdict,
    ClaimAnchor,
    validate_anchor,
)


def _anchor(**ov):
    base = dict(
        artifact="artifacts/x.json", field="precision",
        expected="1.0", doc_path="t.md", line_number=1, raw="",
    )
    base.update(ov)
    return ClaimAnchor(**base)


def _setup_artifact(
    tmp_path: pathlib.Path, name: str, body: dict,
) -> None:
    p = tmp_path / "artifacts" / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(body))


def test_verified_when_artifact_and_field_match(tmp_path) -> None:
    _setup_artifact(tmp_path, "x.json", {"precision": 1.0})
    out = validate_anchor(_anchor(), repo_root=tmp_path)
    assert out.verdict is AnchorVerdict.VERIFIED


def test_missing_artifact_when_file_absent(tmp_path) -> None:
    out = validate_anchor(_anchor(), repo_root=tmp_path)
    assert out.verdict is AnchorVerdict.MISSING_ARTIFACT


def test_missing_field_when_artifact_present_but_no_key(
    tmp_path,
) -> None:
    _setup_artifact(tmp_path, "x.json", {"other": 1.0})
    out = validate_anchor(_anchor(), repo_root=tmp_path)
    assert out.verdict is AnchorVerdict.MISSING_FIELD


def test_value_mismatch(tmp_path) -> None:
    _setup_artifact(tmp_path, "x.json", {"precision": 0.5})
    out = validate_anchor(_anchor(expected="1.0"), repo_root=tmp_path)
    assert out.verdict is AnchorVerdict.VALUE_MISMATCH


def test_dotted_field_resolves(tmp_path) -> None:
    _setup_artifact(
        tmp_path, "x.json", {"metrics": {"precision": 1.0}},
    )
    out = validate_anchor(
        _anchor(field="metrics.precision"), repo_root=tmp_path,
    )
    assert out.verdict is AnchorVerdict.VERIFIED


def test_len_prefix_resolves_list_length(tmp_path) -> None:
    _setup_artifact(
        tmp_path, "x.json", {"steps": [1, 2, 3]},
    )
    out = validate_anchor(
        _anchor(field="len:steps", expected="3"),
        repo_root=tmp_path,
    )
    assert out.verdict is AnchorVerdict.VERIFIED


def test_string_field_exact_match(tmp_path) -> None:
    _setup_artifact(
        tmp_path, "x.json", {"phase": "complete"},
    )
    out = validate_anchor(
        _anchor(field="phase", expected="complete"),
        repo_root=tmp_path,
    )
    assert out.verdict is AnchorVerdict.VERIFIED


def test_malformed_when_expected_missing(tmp_path) -> None:
    _setup_artifact(tmp_path, "x.json", {"precision": 1.0})
    out = validate_anchor(_anchor(expected=""), repo_root=tmp_path)
    assert out.verdict is AnchorVerdict.MALFORMED


def test_validator_is_deterministic(tmp_path) -> None:
    _setup_artifact(tmp_path, "x.json", {"precision": 1.0})
    a = validate_anchor(_anchor(), repo_root=tmp_path)
    b = validate_anchor(_anchor(), repo_root=tmp_path)
    assert a == b
