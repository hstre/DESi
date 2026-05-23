"""Tests for v2.6 CausalChainProbeReport (Aufgabe 7)."""
from __future__ import annotations

from datetime import datetime, timezone

from desi.causal_probe import (
    CausalChainProbeReport,
    CausalChainProbeRunner,
    RiskFlag,
    build_probe_report,
    compute_report_replay_hash,
)


def _report() -> CausalChainProbeReport:
    now = datetime.now(timezone.utc)
    return build_probe_report(
        CausalChainProbeRunner().run(),
        started_at=now, finished_at=now,
    )


def test_report_carries_all_required_fields() -> None:
    rep = _report()
    for f in (
        "total_cases", "triggered_multistep", "triggered_main",
        "triggered_known_false_positives", "dominant_risk_flags",
        "safe_to_implement", "required_guards_before_implementation",
        "replay_hash",
    ):
        assert hasattr(rep, f)


def test_safe_to_implement_is_a_bool() -> None:
    rep = _report()
    assert isinstance(rep.safe_to_implement, bool)


def test_dominant_risk_flags_are_in_enum() -> None:
    rep = _report()
    for f in rep.dominant_risk_flags:
        assert isinstance(f, RiskFlag)


def test_required_guards_is_nonempty_when_unsafe() -> None:
    """If safe_to_implement is False, at least one guard must be
    enumerated; if True, the field is informational."""
    rep = _report()
    if not rep.safe_to_implement:
        assert len(rep.required_guards_before_implementation) >= 1


def test_two_runs_produce_identical_replay_hash() -> None:
    now = datetime.now(timezone.utc)
    a = build_probe_report(
        CausalChainProbeRunner().run(),
        started_at=now, finished_at=now,
    )
    b = build_probe_report(
        CausalChainProbeRunner().run(),
        started_at=now, finished_at=now,
    )
    assert a.replay_hash == b.replay_hash


def test_replay_hash_independent_of_timestamps() -> None:
    early = datetime(2020, 1, 1, tzinfo=timezone.utc)
    late = datetime(2030, 1, 1, tzinfo=timezone.utc)
    run = CausalChainProbeRunner().run()
    a = build_probe_report(run, started_at=early, finished_at=early)
    b = build_probe_report(run, started_at=late, finished_at=late)
    assert a.replay_hash == b.replay_hash


def test_replay_hash_helper_is_sixteen_hex() -> None:
    h = compute_report_replay_hash({"total_cases": 80})
    assert len(h) == 16
    int(h, 16)


def test_safe_gate_requires_all_four_conditions() -> None:
    """Aufgabe 7 — gate semantics."""
    rep = _report()
    m = rep.metrics
    if rep.safe_to_implement:
        assert rep.triggered_multistep > 0
        assert rep.triggered_known_false_positives == 0
        assert m.authority_touch_rate == 0.0
        assert m.philosophy_touch_rate == 0.0


def test_total_cases_is_eighty() -> None:
    rep = _report()
    assert rep.total_cases == 80


def test_to_dict_round_trip_shape() -> None:
    rep = _report()
    d = rep.to_dict()
    for k in (
        "total_cases", "triggered_multistep", "triggered_main",
        "triggered_known_false_positives", "dominant_risk_flags",
        "safe_to_implement", "required_guards_before_implementation",
        "metrics", "candidates", "replay_hash",
    ):
        assert k in d
