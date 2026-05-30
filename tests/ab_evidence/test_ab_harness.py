"""Tests for the A/B-Evidence harness — deterministic, offline."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "ab_evidence"))
sys.path.insert(0, str(_REPO / "claude_compression"))

import backend  # noqa: E402
from build_state import load_chat, load_ground_truth, state_for_variant_B  # noqa: E402
from evaluate_response import MATCH_THRESHOLD, evaluate  # noqa: E402
from prompts import variant_A_messages, variant_B_messages  # noqa: E402

_FX = _REPO / "ab_evidence" / "fixtures"
_CASES = ("case1_architecture", "case2_research", "case3_debugging")


# ---- frozen ground truth audit trail -------------------------------------------------

def test_fixtures_have_frozen_hashes():
    hashes_text = (_FX / "HASHES.txt").read_text(encoding="utf-8")
    lines = [l for l in hashes_text.splitlines() if l.strip()]
    assert len(lines) >= 6  # 3 chats + 3 GT
    for line in lines:
        h = line.split()[0]
        assert len(h) == 16
    # spot-check: each declared hash matches the actual current file hash
    for line in lines:
        h, path = line.split(None, 1)
        actual = hashlib.sha256((_REPO / path).read_bytes()).hexdigest()[:16]
        assert h == actual, f"{path}: hash mismatch — fixture was mutated after freezing"


def test_chats_contain_no_markers():
    banned = ("[CLAIM", "[CONSTRAINT", "[DECISION", "[CONFLICT", "[QUESTION", "[EVIDENCE", "[DISCARD")
    for c in _CASES:
        text = (_FX / f"{c}_chat.json").read_text(encoding="utf-8")
        for b in banned:
            assert b not in text, f"{c}: marker {b} leaked into chat fixture"


# ---- backend honesty ----------------------------------------------------------------

def test_backend_refuses_when_no_api_key(monkeypatch):
    """No silent simulation: a call MUST raise if no API key is set."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert backend.is_available() is False
    import pytest
    with pytest.raises(RuntimeError):
        backend.call_messages("sys", [{"role": "user", "content": "hi"}])


def test_backend_status_reported_honestly_in_results():
    """The results JSON declares either REAL or UNAVAILABLE_in_this_env — no third option."""
    from run_ab import run
    out = run()
    assert isinstance(out["available"], bool)
    for c in out["cases"]:
        assert c["backend_status"] in ("REAL", "UNAVAILABLE_in_this_env")


# ---- prompt construction ------------------------------------------------------------

def test_variant_A_includes_full_chat_and_follow_up():
    p = variant_A_messages("case1_architecture")
    n_chat = len(load_chat("case1_architecture"))
    assert p["variant"] == "A_full_context"
    # exactly chat turns + 1 follow-up
    assert len(p["messages"]) == n_chat + 1
    # the last message is the follow-up question, not part of the chat
    assert p["messages"][-1]["content"] != load_chat("case1_architecture")[-1]["content"]


def test_variant_B_excludes_chat_includes_state():
    p = variant_B_messages("case1_architecture")
    assert p["variant"] == "B_desi_state"
    assert len(p["messages"]) == 1   # only the follow-up + state block, no history
    user = p["messages"][0]["content"]
    assert "DESi state" in user
    # variant B must contain category labels but NOT the original chat text
    assert "active_claims" in user and "decisions" in user
    chat_text = " ".join(m["content"] for m in load_chat("case1_architecture"))
    assert chat_text[:200] not in user


def test_prompts_are_deterministic():
    for c in _CASES:
        a1 = variant_A_messages(c); a2 = variant_A_messages(c)
        b1 = variant_B_messages(c); b2 = variant_B_messages(c)
        assert a1 == a2 and b1 == b2


# ---- state vs chat growth ------------------------------------------------------------

def test_state_growth_signal_recorded_for_all_cases():
    from run_ab import _state_growth_table
    for c in _CASES:
        g = _state_growth_table(c)
        assert g["chat_tokens"] > 0 and g["state_tokens"] > 0
        assert "ratio_state_over_chat" in g and g["n_chat_turns"] > 0


# ---- evaluation function -------------------------------------------------------------

def test_evaluation_matches_pinned_threshold():
    """The Jaccard match threshold MUST stay 0.25; any change requires intentional review."""
    assert MATCH_THRESHOLD == 0.25


def test_evaluation_recall_uses_ground_truth_bodies():
    gt = load_ground_truth("case1_architecture")
    # a response that reproduces each GT body AS ITS OWN SENTENCE should yield recall = 1.0
    # everywhere. (Splitting on '. ' is how a real Claude response is shaped.)
    response = ". ".join([x["what"] for cat in
                          ("active_claims", "active_constraints", "decisions",
                           "open_conflicts", "open_questions") for x in gt[cat]]) + "."
    ev = evaluate(response, gt)
    assert ev["claim_preservation"]["recall"] == 1.0
    assert ev["constraint_preservation"]["recall"] == 1.0
    assert ev["decision_preservation"]["recall"] == 1.0
    assert ev["conflict_visibility"]["recall"] == 1.0
    assert ev["open_question_preservation"]["recall"] == 1.0


def test_evaluation_detects_zero_recall_for_empty_response():
    gt = load_ground_truth("case2_research")
    ev = evaluate("", gt)
    assert ev["decision_preservation"]["recall"] == 0.0
    assert ev["constraint_preservation"]["recall"] == 0.0


def test_evaluation_detects_hallucinations():
    gt = load_ground_truth("case3_debugging")
    # a sentence completely unrelated to the case
    response = "The Eiffel Tower is 330 meters tall and was built in 1889 for the world exhibition."
    ev = evaluate(response, gt)
    assert ev["hallucinations"]["count"] >= 1


# ---- methodological commitments pinned ----------------------------------------------

def test_no_simulation_disclaimer_present_when_unavailable(monkeypatch):
    """When the backend is unavailable, the report explicitly says A/B was NOT run."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    from run_ab import run
    out = run()
    if not out["available"]:
        report = (_REPO / "ab_evidence" / "reports" / "ab_evidence_report.md").read_text()
        assert "UNAVAILABLE_in_this_env" in report
        assert "no simulation, no mock" in report.lower() or "no simulation" in report.lower()
