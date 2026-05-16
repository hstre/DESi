"""v4.2 — false-support case extraction + replay determinism."""
from __future__ import annotations

from desi.external_audit_probe import (
    EXPECTED_FALSE_SUPPORT_COUNT, MIN_FALSE_SUPPORT_CASES,
    collect_false_support_cases, replay_all,
)


def test_case_count_meets_minimum_and_matches_v41() -> None:
    cases = collect_false_support_cases()
    assert len(cases) >= MIN_FALSE_SUPPORT_CASES
    assert len(cases) == EXPECTED_FALSE_SUPPORT_COUNT


def test_collect_is_deterministic() -> None:
    a = collect_false_support_cases()
    b = collect_false_support_cases()
    assert a == b


def test_replay_records_match_case_count() -> None:
    cases = collect_false_support_cases()
    records = replay_all(cases)
    assert len(records) == len(cases)
    for c, r in zip(cases, records):
        assert r.chain_id == c.chain_id
        assert r.domain == c.domain
        # support_state must be 'logically_supported' on every
        # case by construction.
        assert r.support_state == "logically_supported"


def test_replay_records_carry_strategy_origin() -> None:
    cases = collect_false_support_cases()
    records = replay_all(cases)
    seen_any = False
    for r in records:
        if r.frame_strategy_origin:
            seen_any = True
            for s in r.frame_strategy_origin:
                assert s.startswith("F")
    assert seen_any, "no case is unlocked by any v4.1 strategy"
