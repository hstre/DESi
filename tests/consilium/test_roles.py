"""Tests for v1.3 ConsiliumRole — closed enum + canonical order."""
from __future__ import annotations

from desi.consilium import (
    CANONICAL_ROLE_ORDER,
    ConsiliumRole,
    ReviewContext,
    RoleReview,
    review_domain_examiner,
    review_integrator,
    review_logician,
    review_skeptic,
    run_role_reviews,
)
from desi.logic import LogicalAuditor


def _bridge_ctx():
    aud = LogicalAuditor()
    r = aud.audit("It is raining. Therefore the street is wet.")
    return ReviewContext(
        bridge=r.bridges[0],
        source_claim_id=r.audit_id,
        original_text=r.text,
    )


# ---------------------------------------------------------------------------
# Closed enum
# ---------------------------------------------------------------------------


def test_consilium_role_has_exactly_four_members() -> None:
    members = {m.value for m in ConsiliumRole}
    assert members == {
        "logician", "skeptic", "domain_examiner", "integrator",
    }


def test_canonical_role_order_lists_all_four() -> None:
    assert set(CANONICAL_ROLE_ORDER) == set(ConsiliumRole)
    assert len(CANONICAL_ROLE_ORDER) == 4


def test_canonical_role_order_is_a_tuple() -> None:
    """Order must be immutable so the audit-time stamp is stable."""
    assert isinstance(CANONICAL_ROLE_ORDER, tuple)


# ---------------------------------------------------------------------------
# Each role function returns a RoleReview with its own role label
# ---------------------------------------------------------------------------


def test_logician_returns_role_review_with_correct_role() -> None:
    rv = review_logician(_bridge_ctx())
    assert isinstance(rv, RoleReview)
    assert rv.role is ConsiliumRole.LOGICIAN


def test_skeptic_returns_role_review_with_correct_role() -> None:
    rv = review_skeptic(_bridge_ctx())
    assert rv.role is ConsiliumRole.SKEPTIC


def test_domain_examiner_returns_role_review_with_correct_role() -> None:
    rv = review_domain_examiner(_bridge_ctx())
    assert rv.role is ConsiliumRole.DOMAIN_EXAMINER


def test_integrator_returns_role_review_with_correct_role() -> None:
    rv = review_integrator(_bridge_ctx())
    assert rv.role is ConsiliumRole.INTEGRATOR


# ---------------------------------------------------------------------------
# run_role_reviews rejects malformed role orders
# ---------------------------------------------------------------------------


def test_run_role_reviews_rejects_duplicate_role() -> None:
    import pytest
    with pytest.raises(ValueError):
        run_role_reviews(
            _bridge_ctx(),
            role_order=(ConsiliumRole.LOGICIAN, ConsiliumRole.LOGICIAN,
                        ConsiliumRole.SKEPTIC, ConsiliumRole.INTEGRATOR),
        )


def test_run_role_reviews_rejects_missing_role() -> None:
    import pytest
    with pytest.raises(ValueError):
        run_role_reviews(
            _bridge_ctx(),
            role_order=(ConsiliumRole.LOGICIAN, ConsiliumRole.SKEPTIC,
                        ConsiliumRole.INTEGRATOR),  # missing DOMAIN_EXAMINER
        )


# ---------------------------------------------------------------------------
# RoleReview is frozen
# ---------------------------------------------------------------------------


def test_role_review_is_frozen() -> None:
    import pytest
    rv = review_logician(_bridge_ctx())
    with pytest.raises(Exception):
        rv.unresolved_gap = True  # type: ignore
