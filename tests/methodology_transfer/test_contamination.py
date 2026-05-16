"""v5.0 — contamination audit against protected pool."""
from __future__ import annotations

from desi.methodology_transfer.contamination import (
    _protected_pool, audit_probes,
)
from desi.methodology_transfer.report import build_report


def test_protected_pool_nonempty() -> None:
    pool = _protected_pool()
    assert len(pool) > 0


def test_protected_pool_is_currently_supported_only() -> None:
    """Every text in the protected pool must currently
    audit as LOGICALLY_SUPPORTED. v5.0 reuses the v4.5/v4.7
    protected-pool definition; if this regresses, the
    contamination audit is comparing against the wrong
    baseline."""
    from desi.logic.audit import LogicalAuditor, LogicalState
    aud = LogicalAuditor()
    pool = _protected_pool()
    for text in pool:
        st = aud.audit(text).state
        assert st is LogicalState.LOGICALLY_SUPPORTED, text[:80]


def test_safe_probe_count_meets_threshold() -> None:
    r = build_report()
    assert r.safe_probe_count >= 3


def test_every_probe_outcome_has_known_cluster() -> None:
    r = build_report()
    cluster_names = {t.taxonomy_name for t in r.taxonomy}
    for o in r.probe_outcomes:
        assert o.cluster_name in cluster_names


def test_safe_flag_matches_contamination_zero() -> None:
    r = build_report()
    for o in r.probe_outcomes:
        assert o.safe == (o.contamination == 0)
