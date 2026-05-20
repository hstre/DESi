"""v4.5 — structural NCs: cycles vs token-rich non-cycles."""
from __future__ import annotations

from collections import Counter

from desi.bidirectional_cycle_patch import (
    MAX_FALSE_CYCLE_RATE, MIN_NC_COUNT, MIN_NC_DETECTION,
    all_structural_ncs, build_v45_report,
)
from datetime import datetime, timezone


def test_at_least_50_ncs() -> None:
    assert len(all_structural_ncs()) >= MIN_NC_COUNT


def test_directive_minima_per_cohort() -> None:
    counts = Counter(
        n.is_cycle for n in all_structural_ncs()
    )
    assert counts[True] >= 25
    assert counts[False] >= 25


def test_nc_detection_rate_meets_threshold() -> None:
    when = datetime(2026, 5, 16, tzinfo=timezone.utc)
    r = build_v45_report(started_at=when, finished_at=when)
    assert r.nc_detection_rate >= MIN_NC_DETECTION


def test_false_cycle_rate_under_threshold() -> None:
    when = datetime(2026, 5, 16, tzinfo=timezone.utc)
    r = build_v45_report(started_at=when, finished_at=when)
    assert r.false_cycle_rate <= MAX_FALSE_CYCLE_RATE
