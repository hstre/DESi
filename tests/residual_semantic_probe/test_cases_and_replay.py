"""v4.4 — residue case selection + replay determinism."""
from __future__ import annotations

from desi.residual_semantic_probe import (
    EXPECTED_RESIDUE_COUNT, collect_residue_cases, replay_all,
)


def test_v44_historical_residue_count_pinned() -> None:
    """The v4.4 frozen artifact holds the pre-v4.5 residue
    count of 24. After v4.5 the live ``collect_residue_cases``
    returns a smaller set (the v4.5 patch suspends the 5
    BIDIRECTIONAL_CYCLE cases v4.4 left untouched); we pin the
    historical v4.4 count via the frozen artifact and check
    that the live count has strictly dropped.  See
    docs/memory/v4_5.md."""
    import json, pathlib
    p = (
        pathlib.Path(__file__).resolve().parents[2]
        / "artifacts" / "v4_4" / "report.json"
    )
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data["residue_count"] == EXPECTED_RESIDUE_COUNT == 24
    cases = collect_residue_cases()
    assert len(cases) < EXPECTED_RESIDUE_COUNT


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
