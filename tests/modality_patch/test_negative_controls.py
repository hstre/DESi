"""v4.7 — modality NCs: tense-consistent valid vs leaps."""
from __future__ import annotations

from collections import Counter

from desi.modality_patch import (
    MAX_FALSE_MODALITY, MIN_NC_COUNT, MIN_NC_DETECTION,
    all_modality_ncs, build_v47_report,
)
from datetime import datetime, timezone


def test_at_least_60_ncs() -> None:
    assert len(all_modality_ncs()) >= MIN_NC_COUNT


def test_directive_minima_per_cohort() -> None:
    counts = Counter(n.cohort for n in all_modality_ncs())
    assert counts["tense_consistent_valid"] >= 20
    assert counts["correlation_leap"] >= 20
    assert counts["sample_to_universal_leap"] >= 20


def test_nc_detection_rate_meets_threshold() -> None:
    when = datetime(2026, 5, 16, tzinfo=timezone.utc)
    r = build_v47_report(started_at=when, finished_at=when)
    assert r.nc_detection_rate >= MIN_NC_DETECTION


def test_false_modality_rate_under_threshold() -> None:
    when = datetime(2026, 5, 16, tzinfo=timezone.utc)
    r = build_v47_report(started_at=when, finished_at=when)
    assert r.false_modality_rate <= MAX_FALSE_MODALITY
