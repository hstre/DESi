"""v4.6 — residue selection + replay determinism."""
from __future__ import annotations

from desi.warrant_probe import (
    EXPECTED_RESIDUE_COUNT, collect_residue_cases, replay_all,
)


def test_residue_count_matches_v45_target() -> None:
    """v4.3 retired 119; v4.5 retired 5 more; the surviving
    residue is exactly 19."""
    cases = collect_residue_cases()
    assert len(cases) == EXPECTED_RESIDUE_COUNT == 19


def test_collect_is_deterministic() -> None:
    a = collect_residue_cases()
    b = collect_residue_cases()
    assert a == b


def test_replay_records_match_case_count() -> None:
    cases = collect_residue_cases()
    records = replay_all(cases)
    assert len(records) == len(cases)
    for c, r in zip(cases, records):
        assert r.chain_id == c.chain_id
        assert r.support_state == "logically_supported"


def test_replay_records_carry_originating_strategy() -> None:
    records = replay_all(collect_residue_cases())
    for r in records:
        assert r.originating_strategy, r.chain_id
