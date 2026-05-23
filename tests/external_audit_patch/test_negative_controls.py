"""v4.3 — 80 synthetic NC fixtures, ≥0.95 detection."""
from __future__ import annotations

from desi.external_audit_patch import (
    MIN_NC_COUNT, MIN_NC_DETECTION, all_patch_ncs,
    build_v43_report,
)
from datetime import datetime, timezone


def test_at_least_80_ncs() -> None:
    assert len(all_patch_ncs()) >= MIN_NC_COUNT


def test_twenty_per_directive_class() -> None:
    from collections import Counter
    counts = Counter(nc.target_class for nc in all_patch_ncs())
    assert counts == {
        "HIDDEN_NEGATION":          20,
        "QUANTIFIER_DRIFT":         20,
        "AUTHORITY_CONTAMINATION":  20,
        "CYCLE_DISGUISE":           20,
    }


def test_nc_detection_rate_meets_threshold() -> None:
    when = datetime(2026, 5, 16, tzinfo=timezone.utc)
    r = build_v43_report(started_at=when, finished_at=when)
    assert r.nc_detection_rate >= MIN_NC_DETECTION


def test_every_patched_class_has_full_detection() -> None:
    when = datetime(2026, 5, 16, tzinfo=timezone.utc)
    r = build_v43_report(started_at=when, finished_at=when)
    for cluster in ("HIDDEN_NEGATION", "QUANTIFIER_DRIFT",
                    "AUTHORITY_CONTAMINATION"):
        stats = r.nc_by_class[cluster]
        assert stats["detected"] == stats["total"], (cluster, stats)
