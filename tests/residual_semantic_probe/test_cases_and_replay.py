"""v4.4 — residue case selection + replay determinism."""
from __future__ import annotations

from desi.residual_semantic_probe import (
    EXPECTED_RESIDUE_COUNT, collect_residue_cases, replay_all,
)


def test_residue_count_matches_v43_target() -> None:
    """v4.3 reduced 143 v4.2 false-supports to exactly the
    24 residue (5 CYCLE + 10 FRAME_SWITCH + 9 SEMANTIC)."""
    cases = collect_residue_cases()
    assert len(cases) == EXPECTED_RESIDUE_COUNT == 24


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
    # Every residue case is unlocked by at least one v4.1
    # strategy (the cases came from the v4.1 ingress probe).
    for r in records:
        assert r.originating_strategy, r.chain_id
