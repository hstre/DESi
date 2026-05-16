"""Negative control — the three deliberately-wrong claims in
``docs/reviewer_bundle/fake_reproduction.md`` must each be rejected
by the validator with the correct verdict.
"""
from __future__ import annotations

import json
import pathlib

import pytest


_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
_FAKE_FIXTURE = (
    _REPO_ROOT / "tests" / "reviewer_bundle" / "fake_claims.json"
)
_FAKE_DOC = (
    _REPO_ROOT / "docs" / "reviewer_bundle" / "fake_reproduction.md"
)


def _validate(claim: dict) -> str:
    """Return the verdict for a single (intentionally wrong) claim."""
    art_path = _REPO_ROOT / claim["artifact_path"]
    if not art_path.exists():
        return "missing_artifact"
    payload = json.loads(art_path.read_text())
    cur = payload
    for seg in claim["field_path"].split("."):
        if isinstance(cur, dict):
            cur = cur.get(seg)
        else:
            return "missing_field"
    if cur is None:
        return "missing_field"
    if cur == claim["expected_value"]:
        return "verified"
    return "value_mismatch"


def _load_fakes() -> list[dict]:
    return json.loads(_FAKE_FIXTURE.read_text())["fake_claims"]


def test_fake_reproduction_md_exists() -> None:
    assert _FAKE_DOC.exists()


def test_three_fakes_present() -> None:
    fakes = _load_fakes()
    assert len(fakes) == 3


@pytest.mark.parametrize(
    "fake", _load_fakes(), ids=lambda f: f["id"],
)
def test_each_fake_is_rejected_with_expected_verdict(
    fake: dict,
) -> None:
    verdict = _validate(fake)
    assert verdict == fake["expected_verdict"], (
        f"{fake['id']}: expected verdict {fake['expected_verdict']!r}, "
        f"got {verdict!r}"
    )


def test_no_fake_resolves_to_verified() -> None:
    for fake in _load_fakes():
        verdict = _validate(fake)
        assert verdict != "verified", (
            f"{fake['id']} unexpectedly verified — "
            "the reviewer bundle's negative control is broken"
        )


def test_negative_control_catches_all_three_fakes() -> None:
    verdicts = {fake["id"]: _validate(fake) for fake in _load_fakes()}
    # Each fake must surface with the documented failure mode.
    assert verdicts == {
        "FAKE-001-wrong-hash": "value_mismatch",
        "FAKE-002-wrong-value": "value_mismatch",
        "FAKE-003-missing-artifact": "missing_artifact",
    }
