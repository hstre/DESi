"""v4.8 — residue selection + replay determinism."""
from __future__ import annotations

from desi.content_audit_probe import (
    EXPECTED_RESIDUE_COUNT, collect_residue_cases, replay_all,
)


def test_v48_historical_residue_count_pinned() -> None:
    """The v4.8 frozen artifact pins the pre-v4.9 residue
    count of 9. After v4.9 the live ``collect_residue_cases``
    returns an empty set (the v4.9 patch retires both v4.8
    target clusters); we pin the historical v4.8 count via
    the frozen artifact and check the live count has strictly
    dropped. See docs/memory/v4_9.md."""
    import json, pathlib
    p = (
        pathlib.Path(__file__).resolve().parents[2]
        / "artifacts" / "v4_8" / "report.json"
    )
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data["residue_count"] == EXPECTED_RESIDUE_COUNT == 9
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
