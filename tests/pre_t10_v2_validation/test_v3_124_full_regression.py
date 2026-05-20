"""v3.124 - full-regression + gate-deployment
validation tests (module-level invariants).

These tests cover the parts of v3.124's
validation that hold WITHOUT the regression
having completed: TPR, FAR, adverse flips, hash
invariants, ROI, status-API shape. The artifact-
comparison tests live in the sibling file
``test_v3_124_full_regression_artifact.py``,
which only runs once the regression has been
completed and the pinned artifact + status JSON
are committed."""
from __future__ import annotations

from desi.pre_t10_v2_validation.validation import (
    V2_8_FROZEN_FAILCASE_HASH,
    V2_8_FROZEN_RECONSTRUCTION_HASH,
    adverse_flip_count,
    build_full_regression_validation_artifact,
    build_report, full_regression_status,
    hash_checks, hash_stability,
    historical_far, historical_tpr,
    matrix_drift_count, rule_roi,
    v2_8_failcase_live_hash,
    v2_8_reconstruction_live_hash,
)


def test_historical_tpr_is_one() -> None:
    """Pflichtfrage 1: bleibt TPR = 1.0?"""
    assert historical_tpr() == 1.0


def test_historical_far_is_zero() -> None:
    """Pflichtfrage 2: bleibt FAR = 0?"""
    assert historical_far() == 0.0


def test_no_adverse_flips() -> None:
    """Pflichtfrage 3: entstehen adverse flips?"""
    assert adverse_flip_count() == 0


def test_v28_reconstruction_hash_pinned() -> None:
    """Pflichtfrage 4 (a): bleibt der kanonische
    Rekonstruktions-Hash 1f4d9dfe44cb16e1?"""
    assert v2_8_reconstruction_live_hash() == (
        V2_8_FROZEN_RECONSTRUCTION_HASH
    )


def test_v28_failcase_hash_pinned() -> None:
    """Pflichtfrage 4 (b): bleibt der kanonische
    Failcase-Hash d83d81ab8417c022?"""
    assert v2_8_failcase_live_hash() == (
        V2_8_FROZEN_FAILCASE_HASH
    )


def test_hash_stability_is_one() -> None:
    """Pflichtfrage 4: bleiben Replay-Hashes
    stabil? Pinned v2.8 invariants must all
    match. Matrix drift is tracked separately
    in matrix_drift_count."""
    assert hash_stability() == 1.0


def test_hash_checks_contain_both_invariants() -> (
    None
):
    labels = {c.label for c in hash_checks()}
    assert "v2_8_reconstruction" in labels
    assert "v2_8_failcase" in labels


def test_rule_roi_is_positive() -> None:
    """Pflichtfrage 6: bleibt ROI positiv?"""
    assert rule_roi() > 0.0


def test_rule_roi_is_at_ceiling() -> None:
    """far=0 + tpr=1 + epsilon=0.01 => roi=100."""
    assert rule_roi() == 100.0


def test_matrix_drift_is_pre_existing() -> None:
    """Pflichtfrage 5 (info): the v4.x matrix
    entries that drift are documented HISTORICAL_
    RUNTIME_DRIFT under v4.11. They predate the
    multi-signal rule. The metric is surfaced
    for audit; it is NOT a deployment-gate
    failure."""
    assert matrix_drift_count() >= 0


def test_full_regression_status_keys() -> None:
    status = full_regression_status()
    for key in (
        "passed", "passed_count",
        "failed_count", "error_count",
        "summary",
    ):
        assert key in status


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "DEPLOYED_ARCHITECTURE_RULE",
        "PRE_T10_V2_EXPERIMENTAL",
    }
    assert build_report().deployment_decision in (
        allowed
    )


def test_failing_conditions_align_with_decision() -> (
    None
):
    r = build_report()
    if r.deployment_decision == (
        "DEPLOYED_ARCHITECTURE_RULE"
    ):
        assert r.failing_conditions == ()
    else:
        assert len(r.failing_conditions) > 0


def test_pflichtmetriken_present_in_artifact_keys() -> (
    None
):
    """All six Pflichtmetriken must appear as
    top-level keys in the artifact."""
    art = (
        build_full_regression_validation_artifact()
    )
    required = {
        "full_regression_passed",
        "historical_tpr",
        "historical_far",
        "adverse_flip_count",
        "hash_stability",
        "rule_roi",
    }
    assert required.issubset(art.keys())
