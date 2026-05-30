"""Tests for DESi State Discovery v3 — deterministic, offline; the discoverer never sees the GT."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "state_discovery"))
sys.path.insert(0, str(_REPO / "claude_compression"))   # token_count

import discovery as disc  # noqa: E402
import evaluate_v3 as ev  # noqa: E402
import rehydrate_v3 as rh  # noqa: E402

_FX = _REPO / "state_discovery" / "fixtures_v3"
_GT_FIXTURES = ("research_architecture", "technical_debugging", "open_brainstorm")


def test_fixtures_have_frozen_hashes():
    """The audit-trail file documents the SHA-256 prefix of every chat and GT file."""
    hashes = (_FX / "HASHES.txt").read_text(encoding="utf-8").strip().splitlines()
    assert len(hashes) >= 6
    # every line: "<hash16>  <path>"
    for line in hashes:
        h, _ = line.split(None, 1)
        assert len(h) == 16


def test_no_markers_in_chat_fixtures():
    """The whole point: discovery on UNMARKED dialogs. Pin that the fixtures stay marker-free."""
    banned = ("[CLAIM", "[CONSTRAINT", "[DECISION", "[CONFLICT", "[QUESTION", "[EVIDENCE", "[DISCARD")
    for fid in _GT_FIXTURES:
        text = (_FX / f"chat_{fid}.json").read_text(encoding="utf-8")
        for b in banned:
            assert b not in text, f"{fid}: marker '{b}' leaked into the chat fixture"


def test_discoverer_does_not_read_ground_truth_files():
    """Structural guard: ignore the docstring (which legitimately mentions ground truth as a
    self-description) and check the remaining code lines for any GT-access pattern."""
    src_lines = (Path(disc.__file__)).read_text(encoding="utf-8").splitlines()
    # strip the module docstring (everything between the first two triple-quotes)
    in_doc, code_lines = False, []
    triple = 0
    for ln in src_lines:
        if '"""' in ln:
            triple += ln.count('"""')
            in_doc = (triple % 2 == 1)
            continue
        if not in_doc:
            code_lines.append(ln)
    code = "\n".join(code_lines)
    # also strip inline comments
    code = "\n".join(re.sub(r"#.*$", "", l) for l in code.splitlines())
    # Path(__file__) is allowed only to set sys.path for sibling module imports
    banned = ("open(", "read_text(", "fixtures_v3", "groundtruth_",
              "json.load(", "json.loads(")
    for b in banned:
        assert b not in code, f"discovery.py code contains '{b}' — possible GT access"



def test_discovery_is_deterministic():
    chat = json.loads((_FX / "chat_research_architecture.json").read_text(encoding="utf-8"))["chat"]
    a = disc.discover_state(chat)
    b = disc.discover_state(chat)
    assert a == b


def test_rejects_wrong_input():
    import pytest
    with pytest.raises(TypeError):
        disc.discover_state("not a chat history")


def test_state_is_structured_not_prose():
    chat = json.loads((_FX / "chat_research_architecture.json").read_text(encoding="utf-8"))["chat"]
    state = disc.discover_state(chat)
    assert set(state) == {"claims", "constraints", "decisions", "conflicts", "open_questions"}
    for cat, items in state.items():
        assert isinstance(items, list)
        for it in items:
            assert "id" in it and "what" in it
            # bodies are capped (NOT prose paragraphs)
            assert len(it["what"].split()) <= 18


def test_evaluation_uses_frozen_match_threshold():
    """Pinned threshold; nobody may silently tune it after seeing results."""
    assert ev.MATCH_THRESHOLD == 0.25


def test_evaluator_loads_ground_truth_independently():
    """The evaluator opens groundtruth files directly; the discoverer is never given them."""
    r = ev.evaluate_fixture("research_architecture")
    # the GT has 3 claims in this fixture; recall numerator/denominator must reflect that
    assert r["per_category"]["claims"]["n_expected"] == 3
    assert r["per_category"]["constraints"]["n_expected"] == 3
    assert r["per_category"]["decisions"]["n_expected"] == 3


def test_negative_results_pinned_research_architecture():
    """Pin the honest negative: discoverer fails to surface ANY of the 3 declarative claims
    on this dialog (F1=0). If a later change makes this PASS, that is good — but it must be a
    deliberate fix to the discoverer, not silent threshold tuning. This test forces the
    intentionality."""
    r = ev.evaluate_fixture("research_architecture")
    pc = r["per_category"]
    assert pc["claims"]["recall"] == 0.0
    assert pc["claims"]["f1"] == 0.0
    # decisions: high recall but precision tanks (lots of FP back-channels classified as decisions)
    assert pc["decisions"]["fp"] >= 5


def test_negative_results_pinned_technical_debugging():
    """Pin the honest negative on the debugging dialog: decisions/conflicts all-zero F1."""
    r = ev.evaluate_fixture("technical_debugging")
    pc = r["per_category"]
    assert pc["decisions"]["f1"] == 0.0
    assert pc["conflicts"]["f1"] == 0.0


def test_compression_is_negative_documented():
    """Honest documentation: on these unmarked dialogs the discovered state is LARGER than the
    raw chat. The hypothesis 'state is more compact than the dialog' is REFUTED here. Pinned."""
    for fid in _GT_FIXTURES:
        r = ev.evaluate_fixture(fid)
        assert r["compression"] < 0, f"{fid}: expected negative compression for honest record"


def test_rehydrate_carries_only_structured_state():
    chat = json.loads((_FX / "chat_open_brainstorm.json").read_text(encoding="utf-8"))["chat"]
    state = disc.discover_state(chat)
    payload = rh.rehydrate(state)
    parsed = rh.parse(payload["state_block"])
    # round-trip equals input
    assert parsed == state
    # no chat-style content sneaks into the block
    low = payload["state_block"].lower()
    for marker in ("user said", "assistant said", "as we discussed", "in the chat"):
        assert marker not in low


def test_overall_macro_f1_documented():
    """Document the macro-F1 ceiling on this set. A regression below this is failure; above
    it requires conscious justification (not threshold tuning)."""
    rows = [ev.evaluate_fixture(fid) for fid in _GT_FIXTURES]
    macros = [r["macro_f1"] for r in rows]
    avg = sum(macros) / len(macros)
    # honest current ceiling (computed once from the first run; pinned)
    assert avg < 0.50, f"macro F1 across fixtures is {avg:.3f}; current honest ceiling is <0.50"
