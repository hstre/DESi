"""v4.8 — residue selection + replay determinism."""
from __future__ import annotations

from desi.content_audit_probe import (
    EXPECTED_RESIDUE_COUNT, collect_residue_cases, replay_all,
)


def test_residue_count_matches_v47_target() -> None:
    """v4.3 + v4.5 + v4.7 cumulatively retire 134/143; the
    surviving residue is exactly 9, all MISSING_BRIDGE_RULE."""
    cases = collect_residue_cases()
    assert len(cases) == EXPECTED_RESIDUE_COUNT == 9


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
