"""Negative control — Aufgabe 8.

Construct a fake anchor that points at a non-existent artefact and
verify the validator rejects it with the correct verdict.
"""
from __future__ import annotations

import pathlib

from desi.doc_anchors import (
    AnchorVerdict,
    ClaimAnchor,
    validate_anchor,
)


_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


def _fake(**ov) -> ClaimAnchor:
    base = dict(
        artifact="artifacts/this_does_not_exist/report.json",
        field="precision", expected="1.0",
        doc_path="negative_fixture.md", line_number=1, raw="",
    )
    base.update(ov)
    return ClaimAnchor(**base)


def test_fake_anchor_with_missing_artifact_rejected() -> None:
    out = validate_anchor(_fake(), repo_root=_REPO_ROOT)
    assert out.verdict is AnchorVerdict.MISSING_ARTIFACT
    assert "does not exist" in out.reason


def test_fake_anchor_with_wrong_value_rejected() -> None:
    """Use a real artefact but a value that does not match."""
    out = validate_anchor(
        _fake(
            artifact="artifacts/v2_8/reconstruction.json",
            field="phase", expected="not_a_real_phase",
        ),
        repo_root=_REPO_ROOT,
    )
    assert out.verdict is AnchorVerdict.VALUE_MISMATCH


def test_fake_anchor_with_unknown_field_rejected() -> None:
    out = validate_anchor(
        _fake(
            artifact="artifacts/v2_8/reconstruction.json",
            field="this.field.does.not.exist",
            expected="anything",
        ),
        repo_root=_REPO_ROOT,
    )
    assert out.verdict is AnchorVerdict.MISSING_FIELD


def test_validator_rejects_every_fake_anchor_variant() -> None:
    """Aufgabe 8 success criterion: the negative fixture must fail
    with either MISSING_ARTIFACT or VALUE_MISMATCH."""
    cases = (
        _fake(),
        _fake(
            artifact="artifacts/v2_8/reconstruction.json",
            field="phase", expected="not_a_real_phase",
        ),
    )
    for c in cases:
        out = validate_anchor(c, repo_root=_REPO_ROOT)
        assert out.verdict in (
            AnchorVerdict.MISSING_ARTIFACT,
            AnchorVerdict.VALUE_MISMATCH,
        )
