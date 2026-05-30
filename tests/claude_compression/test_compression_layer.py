"""Targeted tests for the DESi Compression Layer for Claude (deterministic, offline)."""
from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "claude_compression"))

import evaluate as ev  # noqa: E402
import extractor  # noqa: E402
import rehydrate as rh  # noqa: E402
import state as st  # noqa: E402
from fixtures import ALL_FIXTURES, FIXTURE_1  # noqa: E402


def test_empty_state_serializes_and_is_under_budget():
    s = st.DesiState()
    assert s.token_size() < st.MAX_STATE_TOKENS
    assert s.fits_budget()


def test_token_count_is_deterministic():
    text = "DESi compression layer for Claude — deterministic prototype."
    assert st.token_count(text) == st.token_count(text)
    assert st.token_count("") == 0


def test_extractor_rejects_wrong_input():
    import pytest
    with pytest.raises(TypeError):
        extractor.extract_state("not a chat history")


def test_extractor_is_deterministic():
    a = extractor.extract_state(FIXTURE_1["chat"])
    b = extractor.extract_state(FIXTURE_1["chat"])
    assert a.to_dict() == b.to_dict()


def test_extractor_captures_decisions_and_discards():
    s = extractor.extract_state(FIXTURE_1["chat"])
    joined = " ".join(s.architecture_decisions).lower()
    assert "jaccard" in joined
    assert any("embedding" in d.lower() for d in s.discarded_hypotheses)


def test_rehydration_roundtrip_preserves_state_fields():
    s = extractor.extract_state(FIXTURE_1["chat"])
    block = rh.render(s)
    parsed = rh.parse(block)
    for f in ("architecture_decisions", "discarded_hypotheses", "active_goals"):
        assert set(getattr(parsed, f)) == set(getattr(s, f))


def test_rehydrate_payload_shape():
    s = extractor.extract_state(FIXTURE_1["chat"])
    p = rh.rehydrate(s)
    assert set(p) >= {"system", "messages", "token_size", "state_block"}
    assert isinstance(p["messages"], list) and p["messages"][0]["role"] == "user"
    assert p["system"].startswith("You are continuing")


def test_state_carries_seven_fields_from_brief():
    assert set(st.FIELDS) == {"active_goals", "open_problems", "confirmed_findings",
                              "discarded_hypotheses", "architecture_decisions",
                              "open_conflicts", "references"}


def test_evaluation_marks_workability_as_untested():
    """The brief's 3rd success criterion (Claude workable in new chat) cannot be measured here.
    The evaluator MUST report it as UNTESTED, not silently inflated."""
    r = ev.evaluate_fixture(FIXTURE_1)
    assert r["success"]["claude_workable_in_new_chat"] == "UNTESTED_in_this_env"


def test_evaluation_runs_on_all_fixtures_and_is_consistent():
    rows = [ev.evaluate_fixture(fx) for fx in ALL_FIXTURES]
    assert len(rows) == len(ALL_FIXTURES)
    # rehydration round-trip must be consistent on every fixture
    assert all(r["consistency_roundtrip"] for r in rows)
    # at least one fixture must surface MISSING info -> the evaluator does not hide losses
    assert any(r["missing_info"] for r in rows)
