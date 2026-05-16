"""Aufgaben 5 + 6 + 10 + 11 — runner + metrics + recommendation."""
from __future__ import annotations

from datetime import datetime, timezone

from desi.external_probe import (
    Domain,
    MIN_NC_DETECTION,
    MIN_EXTERNAL_PRECISION,
    MIN_EXTERNAL_RECALL,
    RecommendationOutcome,
    all_chains,
    build_external_probe_report,
    run_all,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def test_runner_emits_one_outcome_per_chain() -> None:
    chains = all_chains()
    outs = run_all(chains)
    assert len(outs) == len(chains)


def test_runner_is_deterministic() -> None:
    chains = all_chains()
    a = [o.to_dict() for o in run_all(chains)]
    b = [o.to_dict() for o in run_all(chains)]
    assert a == b


def test_report_emits_per_domain_metrics() -> None:
    r = build_external_probe_report(
        started_at=_now(), finished_at=_now(),
    )
    for d in (
        Domain.D1_SCIENTIFIC_ABSTRACTS,
        Domain.D2_LEGAL_REASONING,
        Domain.D3_MEDICAL_CASE_REPORTS,
        Domain.D4_MATHEMATICAL_PROOFS,
        Domain.D5_ADVERSARIAL_REAL_WORLD,
    ):
        assert d.value in r.domain_metrics, d.value


def test_nc_detection_meets_threshold() -> None:
    r = build_external_probe_report(
        started_at=_now(), finished_at=_now(),
    )
    assert r.nc_detection_rate >= MIN_NC_DETECTION


def test_no_external_false_support_at_baseline() -> None:
    # The directive's hardest gate: external_false_support == 0.
    r = build_external_probe_report(
        started_at=_now(), finished_at=_now(),
    )
    assert r.global_metrics.external_false_support == 0


def test_recommendation_in_allowed_set() -> None:
    r = build_external_probe_report(
        started_at=_now(), finished_at=_now(),
    )
    allowed = {ro.value for ro in RecommendationOutcome}
    assert r.recommended_next in allowed


def test_confirmation_only_when_all_gates_pass() -> None:
    r = build_external_probe_report(
        started_at=_now(), finished_at=_now(),
    )
    if r.recommended_next == RecommendationOutcome.CONFIRMED.value:
        assert r.contamination.exact_overlap_count == 0
        assert r.contamination.semantic_overlap_count == 0
        assert r.nc_detection_rate >= MIN_NC_DETECTION
        assert r.global_metrics.external_precision >= MIN_EXTERNAL_PRECISION
        assert r.global_metrics.external_recall >= MIN_EXTERNAL_RECALL
        assert r.global_metrics.external_false_support == 0


def test_failure_classes_use_closed_enum() -> None:
    r = build_external_probe_report(
        started_at=_now(), finished_at=_now(),
    )
    allowed = {
        "FRAME_FAILURE", "CHAIN_FAILURE",
        "SUSPENSION_FAILURE", "ROUTING_FAILURE",
        "GROUND_TRUTH_MISMATCH", "UNKNOWN",
    }
    for cls in r.failure_class_counts:
        assert cls in allowed


def test_replay_hash_deterministic() -> None:
    now = _now()
    a = build_external_probe_report(started_at=now, finished_at=now)
    b = build_external_probe_report(started_at=now, finished_at=now)
    assert a.replay_hash == b.replay_hash


def test_replay_hash_independent_of_timestamps() -> None:
    a = build_external_probe_report(
        started_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        finished_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    b = build_external_probe_report(
        started_at=datetime(2030, 6, 15, tzinfo=timezone.utc),
        finished_at=datetime(2030, 6, 15, tzinfo=timezone.utc),
    )
    assert a.replay_hash == b.replay_hash


def test_report_round_trips_json() -> None:
    import json
    r = build_external_probe_report(
        started_at=_now(), finished_at=_now(),
    )
    blob = json.dumps(
        r.to_dict(), sort_keys=True, separators=(",", ":"),
    )
    assert isinstance(blob, str)
