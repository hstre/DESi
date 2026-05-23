"""v3.124 - artifact-comparison tests for the
full-regression validation.

These tests assert that the pinned artifact at
``artifacts/v3_124/full_regression_validation.json``
matches what the live build produces, and that
the deployment decision is the expected
``DEPLOYED_ARCHITECTURE_RULE``."""
from __future__ import annotations

import json
import pathlib

from desi.pre_t10_v2_validation import (
    build_full_regression_validation_artifact,
    full_regression_passed,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "v3_124"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(
            encoding="utf-8",
        ),
    )


def test_regression_status_committed() -> None:
    """The status JSON must be present so future
    replays read the same value (otherwise the
    artifact-vs-live test below would drift)."""
    assert (
        _ARTIFACT_ROOT
        / "_regression_status.json"
    ).exists()


def test_regression_status_passed_true() -> None:
    status = _load("_regression_status.json")
    assert status["passed"] is True
    assert status["failed_count"] == 0
    assert status["error_count"] == 0


def test_full_regression_passed_live() -> None:
    assert full_regression_passed() is True


def test_artifact_present() -> None:
    art = _load(
        "full_regression_validation.json",
    )
    assert art["schema_version"] == (
        "v3_124_full_regression_validation"
    )


def test_artifact_historical_tpr() -> None:
    art = _load(
        "full_regression_validation.json",
    )
    assert art["historical_tpr"] == 1.0


def test_artifact_historical_far() -> None:
    art = _load(
        "full_regression_validation.json",
    )
    assert art["historical_far"] == 0.0


def test_artifact_no_adverse_flips() -> None:
    art = _load(
        "full_regression_validation.json",
    )
    assert art["adverse_flip_count"] == 0


def test_artifact_hash_stability() -> None:
    art = _load(
        "full_regression_validation.json",
    )
    assert art["hash_stability"] == 1.0


def test_artifact_rule_roi_positive() -> None:
    art = _load(
        "full_regression_validation.json",
    )
    assert art["rule_roi"] > 0.0


def test_artifact_full_regression_passed() -> None:
    art = _load(
        "full_regression_validation.json",
    )
    assert art["full_regression_passed"] is True


def test_artifact_deployment_decision_is_deployed() -> (
    None
):
    """Killerfrage: ist Pre-T10 v2 wirklich
    architekturreif? Verdict pinned in the
    artifact: DEPLOYED_ARCHITECTURE_RULE."""
    art = _load(
        "full_regression_validation.json",
    )
    assert art["deployment_decision"] == (
        "DEPLOYED_ARCHITECTURE_RULE"
    )
    assert art["failing_conditions"] == []


def test_artifact_matches_live_build() -> None:
    art = _load(
        "full_regression_validation.json",
    )
    live = (
        build_full_regression_validation_artifact()
    )
    # ``regression_summary`` is the pytest tail
    # string; the COUNTS are what matter and are
    # checked above. ``matrix_drift_entries`` is
    # informational and its ordering / contents
    # depend on which v4.x artifacts are present
    # on disk at replay time.
    volatile = {
        "regression_summary",
        "matrix_drift_entries",
    }
    art_stable = {
        k: v for k, v in art.items()
        if k not in volatile
    }
    live_stable = {
        k: v for k, v in live.items()
        if k not in volatile
    }
    assert art_stable == live_stable


def test_decision_document_present() -> None:
    doc = (
        _ARTIFACT_ROOT
        / "full_regression_validation.md"
    ).read_text(encoding="utf-8")
    assert "DEPLOYED_ARCHITECTURE_RULE" in doc
    assert "5024" in doc
    assert "members_per_family" in doc
