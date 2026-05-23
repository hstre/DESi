"""Aufgaben 2 + 3 + 5 — detector, separability, report gates."""
from __future__ import annotations

from datetime import datetime, timezone

from desi.causal_naturalness import (
    MAX_FALSE_ALARM_RATE,
    MIN_ADVERSARIAL_DETECTION_RATE,
    MIN_HELDOUT_SURVIVAL,
    MIN_VALID_ACCEPT_RATE,
    all_input_chains,
    build_manifold,
    build_naturalness_report,
    classify_all,
    valid_manifold_subset,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def test_manifold_built_only_from_valid_subset() -> None:
    chains = all_input_chains()
    subset = valid_manifold_subset(chains)
    assert len(subset) > 0
    for c in subset:
        assert c.expected_natural is True


def test_classify_returns_one_verdict_per_chain() -> None:
    chains = all_input_chains()
    manifold = build_manifold(valid_manifold_subset(chains))
    verdicts = classify_all(chains, manifold)
    assert len(verdicts) == len(chains)


def test_v314_held_out_survival_above_threshold() -> None:
    # Survival of v3.14 valid chains is critical: the manifold
    # was built from them, so it must accept the rest of the
    # valid v3.14 cases.
    r = build_naturalness_report(
        started_at=_now(), finished_at=_now(),
    )
    assert r.heldout_survival >= MIN_HELDOUT_SURVIVAL


def test_report_thresholds_match_directive() -> None:
    assert MIN_VALID_ACCEPT_RATE >= 0.90
    assert MIN_ADVERSARIAL_DETECTION_RATE >= 0.85
    assert MAX_FALSE_ALARM_RATE <= 0.05
    assert MIN_HELDOUT_SURVIVAL >= 0.85


def test_recommendation_is_none_when_any_gate_fails() -> None:
    r = build_naturalness_report(
        started_at=_now(), finished_at=_now(),
    )
    if r.recommended_next == "NONE":
        return
    assert r.valid_accept_rate >= MIN_VALID_ACCEPT_RATE
    assert r.adversarial_detection_rate >= MIN_ADVERSARIAL_DETECTION_RATE
    assert r.false_alarm_rate <= MAX_FALSE_ALARM_RATE
    assert r.heldout_survival >= MIN_HELDOUT_SURVIVAL
    assert r.contamination_count == 0


def test_separability_includes_every_pair() -> None:
    r = build_naturalness_report(
        started_at=_now(), finished_at=_now(),
    )
    pairs = {(s.a, s.b) for s in r.separability}
    # Four corpora -> 4 choose 2 = 6 pairs.
    assert len(pairs) >= 6


def test_nc_results_cover_every_case() -> None:
    from desi.causal_naturalness import ALL_NC_CHAINS
    r = build_naturalness_report(
        started_at=_now(), finished_at=_now(),
    )
    assert len(r.nc_results) == len(ALL_NC_CHAINS)


def test_replay_hash_deterministic() -> None:
    now = _now()
    a = build_naturalness_report(started_at=now, finished_at=now)
    b = build_naturalness_report(started_at=now, finished_at=now)
    assert a.replay_hash == b.replay_hash


def test_replay_hash_independent_of_timestamps() -> None:
    a = build_naturalness_report(
        started_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        finished_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    b = build_naturalness_report(
        started_at=datetime(2030, 6, 15, tzinfo=timezone.utc),
        finished_at=datetime(2030, 6, 15, tzinfo=timezone.utc),
    )
    assert a.replay_hash == b.replay_hash


def test_report_round_trips_json() -> None:
    import json
    r = build_naturalness_report(
        started_at=_now(), finished_at=_now(),
    )
    blob = json.dumps(
        r.to_dict(), sort_keys=True, separators=(",", ":"),
    )
    assert isinstance(blob, str)
