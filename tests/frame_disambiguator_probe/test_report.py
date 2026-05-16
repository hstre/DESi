"""Tests for the v3.7 final report + recommendation (Aufgabe 9)."""
from __future__ import annotations

from datetime import datetime, timezone

from desi.frame_disambiguator_probe import build_disambiguator_report


def _report():
    now = datetime.now(timezone.utc)
    return build_disambiguator_report(started_at=now, finished_at=now)


def test_report_carries_required_fields() -> None:
    r = _report()
    for f in (
        "target_count", "counter_count", "candidate_count",
        "targets", "counters", "assessments",
        "recommended_next", "recommended_tokens", "replay_hash",
    ):
        assert hasattr(r, f), f


def test_target_count_is_fifteen() -> None:
    assert _report().target_count == 15


def test_counter_count_is_at_least_five() -> None:
    assert _report().counter_count >= 5


def test_candidate_count_is_at_least_ten() -> None:
    assert _report().candidate_count >= 10


def test_two_runs_produce_identical_replay_hash() -> None:
    a = _report()
    b = _report()
    assert a.replay_hash == b.replay_hash


def test_recommended_is_either_NONE_or_a_safe_candidate() -> None:
    r = _report()
    if r.recommended_next == "NONE":
        # No safe candidate exists — every assessment fails at
        # least one gate.
        assert not any(a.safe for a in r.assessments)
    else:
        # The recommendation must match a safe assessment.
        chosen = next(
            a for a in r.assessments
            if a.score.candidate.candidate_id == r.recommended_next
        )
        assert chosen.safe is True
        assert chosen.score.info_precision == 1.0
        assert chosen.score.coverage >= 0.30
        assert chosen.contamination.contamination_risk == 0.0
        assert chosen.negative_control_precision == 1.0


def test_at_least_one_safe_candidate_exists() -> None:
    """The v3.7 corpus must surface at least one safe disambiguator.
    If this fails, recommendation goes to NONE and the audit
    correctly reports no patch surface, but the test fails so the
    operator notices the regression."""
    r = _report()
    assert any(a.safe for a in r.assessments), (
        "no safe disambiguator candidate — recommendation = NONE"
    )


def test_recommended_tokens_include_anchor() -> None:
    r = _report()
    if r.recommended_next != "NONE":
        assert "entropy" in r.recommended_tokens
