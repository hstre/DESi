"""v4.6 — residue selection + replay determinism."""
from __future__ import annotations

from desi.warrant_probe import (
    EXPECTED_RESIDUE_COUNT, collect_residue_cases, replay_all,
)


def test_v46_historical_residue_count_pinned() -> None:
    """The v4.6 frozen artifact holds the pre-v4.7 residue
    count of 19. After v4.7 the live ``collect_residue_cases``
    returns a smaller set (the v4.7 patch retires the
    CORRELATION_TO_CAUSATION and SAMPLE_TO_UNIVERSAL clusters
    v4.6 left untouched); we pin the historical v4.6 count
    via the frozen artifact and check that the live count has
    strictly dropped. See docs/memory/v4_7.md."""
    import json, pathlib
    p = (
        pathlib.Path(__file__).resolve().parents[2]
        / "artifacts" / "v4_6" / "report.json"
    )
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data["residue_count"] == EXPECTED_RESIDUE_COUNT == 19
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
    for r in records:
        assert r.originating_strategy, r.chain_id
