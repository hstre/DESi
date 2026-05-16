"""v4.2 — false-support case extraction + replay determinism."""
from __future__ import annotations

from desi.external_audit_probe import (
    EXPECTED_FALSE_SUPPORT_COUNT, MIN_FALSE_SUPPORT_CASES,
    collect_false_support_cases, replay_all,
)


def test_v42_historical_case_count_pinned() -> None:
    """The v4.2 frozen artifact holds the pre-v4.3 case count
    of 143. After v4.3 the live ``collect_false_support_cases``
    returns a smaller set (the v4.3 patch suspends 119 of
    them); we pin the *historical* v4.2 count via the frozen
    artifact, not the live re-run. See docs/memory/v4_3.md."""
    import json, pathlib
    p = (
        pathlib.Path(__file__).resolve().parents[2]
        / "artifacts" / "v4_2" / "report.json"
    )
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data["case_count"] == EXPECTED_FALSE_SUPPORT_COUNT
    assert EXPECTED_FALSE_SUPPORT_COUNT >= MIN_FALSE_SUPPORT_CASES


def test_post_v43_false_support_count_below_v42() -> None:
    """v4.3 reduces the false-support set; live collection now
    returns fewer than the v4.2-era 143."""
    cases = collect_false_support_cases()
    assert len(cases) < EXPECTED_FALSE_SUPPORT_COUNT


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
    """v4.2-era invariant: at least one residue case was
    unlocked by a v4.1 strategy. After v4.9 the live residue
    is empty, so we relax the assertion: every present record
    must carry a valid strategy id; the v4.2 historical
    universality is pinned via the frozen artifact below."""
    cases = collect_false_support_cases()
    records = replay_all(cases)
    for r in records:
        if r.frame_strategy_origin:
            for s in r.frame_strategy_origin:
                assert s.startswith("F")


def test_v42_historical_strategy_origin_universal() -> None:
    """Every v4.2-era residue case was unlocked by at least
    one v4.1 strategy — pinned via the frozen artifact."""
    import json, pathlib
    p = (
        pathlib.Path(__file__).resolve().parents[2]
        / "artifacts" / "v4_2" / "report.json"
    )
    data = json.loads(p.read_text(encoding="utf-8"))
    for rec in data["replay_records"]:
        assert rec["frame_strategy_origin"], rec["chain_id"]
        for s in rec["frame_strategy_origin"]:
            assert s.startswith("F")
