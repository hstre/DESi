"""v4.9 — inversion vs content-preserving NCs."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone

from desi.content_inversion_patch import (
    MAX_FALSE_INVERSION, MIN_NC_COUNT, MIN_NC_DETECTION,
    all_inversion_ncs, build_v49_report,
)


def test_at_least_60_ncs() -> None:
    assert len(all_inversion_ncs()) >= MIN_NC_COUNT


def test_directive_minima_per_cohort() -> None:
    counts = Counter(n.cohort for n in all_inversion_ncs())
    assert counts["contradiction_pair"] >= 20
    assert counts["polarity_reversal"] >= 20
    assert counts["content_preserving"] >= 20


def test_nc_detection_rate_meets_threshold() -> None:
    when = datetime(2026, 5, 16, tzinfo=timezone.utc)
    r = build_v49_report(started_at=when, finished_at=when)
    assert r.nc_detection_rate >= MIN_NC_DETECTION


def test_false_inversion_rate_under_threshold() -> None:
    when = datetime(2026, 5, 16, tzinfo=timezone.utc)
    r = build_v49_report(started_at=when, finished_at=when)
    assert r.false_inversion_rate <= MAX_FALSE_INVERSION
