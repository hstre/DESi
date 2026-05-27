"""Targeted tests for the small-LLM unfolding gate.

These tests are OFFLINE: they exercise the gate's pure parsing / policy logic and
its key requirement, without any network call. The gate must ONLY ever produce
UNFOLD / DO_NOT_UNFOLD / UNCERTAIN -- never a SUPPORTS/REFUTES/NEI verdict.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve()
_REPO = _HERE.parents[2]
sys.path.insert(0, str(_REPO / "src"))
sys.path.insert(0, str(_REPO / "benchmarks" / "hf_answering"))

from llm_unfold_gate import DECISIONS, GateResult, LLMUnfoldGate, gate_policy  # noqa: E402


def test_decisions_constant():
    assert DECISIONS == ("UNFOLD", "DO_NOT_UNFOLD", "UNCERTAIN")


def test_gate_policy_mapping():
    assert gate_policy("UNFOLD", "baseline") == "evidence_strict"
    assert gate_policy("DO_NOT_UNFOLD", "baseline") == "entailment_direct"
    # UNCERTAIN defers to the supplied deterministic route
    assert gate_policy("UNCERTAIN", "evidence_strict") == "evidence_strict"
    assert gate_policy("UNCERTAIN", "baseline") == "baseline"


def test_gate_requires_key(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(RuntimeError):
        LLMUnfoldGate()


def _gate(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "dummy-test-key")
    return LLMUnfoldGate()


def test_parse_valid_json(monkeypatch):
    g = _gate(monkeypatch)
    d, reason, ok = g._parse('{"decision": "UNFOLD", "reason": "missing link"}')
    assert d == "UNFOLD" and ok is True and reason == "missing link"
    d2, _, ok2 = g._parse('here: {"decision":"DO_NOT_UNFOLD","reason":"direct"} done')
    assert d2 == "DO_NOT_UNFOLD" and ok2 is True


def test_parse_invalid_returns_uncertain(monkeypatch):
    g = _gate(monkeypatch)
    d, _, ok = g._parse("this is not json at all")
    assert d == "UNCERTAIN" and ok is False


def test_parse_never_emits_a_verdict(monkeypatch):
    g = _gate(monkeypatch)
    # even if the model rambles about SUPPORTS/REFUTES, the gate only ever yields a DECISION
    for text in ('{"decision": "SUPPORTS"}', "SUPPORTS REFUTES NOT_ENOUGH_INFO",
                 '{"verdict": "REFUTES"}', "the claim is clearly supported"):
        d, _, _ = g._parse(text)
        assert d in DECISIONS
        assert d not in ("SUPPORTS", "REFUTES", "NOT_ENOUGH_INFO")


def test_parse_case_insensitive(monkeypatch):
    g = _gate(monkeypatch)
    d, _, ok = g._parse('{"decision": "unfold", "reason": "x"}')
    assert d == "UNFOLD" and ok is True


def test_gateresult_shape(monkeypatch):
    g = _gate(monkeypatch)
    d, reason, ok = g._parse('{"decision":"UNCERTAIN","reason":"cannot tell"}')
    r = GateResult(d, reason, ok, False, 0, 0)
    assert r.decision in DECISIONS and isinstance(r.reason, str)


def test_price_available(monkeypatch):
    g = _gate(monkeypatch)
    pr = g.price()
    assert isinstance(pr, tuple) and len(pr) == 2
