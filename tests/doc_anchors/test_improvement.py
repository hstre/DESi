"""Verify v3.1 improvement gates — Aufgabe 5 + 6.

Re-runs the v3.0 self-audit and pins:

* self_deception_rate < 0.20
* verified_claims > v3.0 baseline (321)
* drift_findings_count == 0
"""
from __future__ import annotations

from desi.self_audit import SelfAuditRunner


_V30_BASELINE_VERIFIED: int = 321
_V30_BASELINE_DECEPTION_RATE: float = 0.314103


def test_self_deception_rate_below_target() -> None:
    rep = SelfAuditRunner().run()
    assert rep.self_deception_rate < 0.20, (
        f"self_deception_rate = {rep.self_deception_rate} "
        f"is not below the 0.20 hard target"
    )


def test_verified_claims_exceed_baseline() -> None:
    rep = SelfAuditRunner().run()
    assert rep.verified_claims > _V30_BASELINE_VERIFIED, (
        f"verified_claims = {rep.verified_claims} "
        f"did not improve on the v3.0 baseline of "
        f"{_V30_BASELINE_VERIFIED}"
    )


def test_drift_findings_remain_zero() -> None:
    rep = SelfAuditRunner().run()
    assert rep.drift_findings_count == 0


def test_improvement_factor_at_least_one_point_five() -> None:
    """v3.1 must reduce self_deception_rate by >= 1.5x."""
    rep = SelfAuditRunner().run()
    factor = (
        _V30_BASELINE_DECEPTION_RATE / max(rep.self_deception_rate, 1e-9)
    )
    assert factor >= 1.5, (
        f"improvement factor {factor:.2f} < 1.5"
    )


def test_total_claims_still_above_one_hundred() -> None:
    rep = SelfAuditRunner().run()
    assert rep.total_claims >= 100
