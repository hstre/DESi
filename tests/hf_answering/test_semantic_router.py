"""Targeted tests for the peripheral semantic pre-solver router.

The router must be deterministic, replay-stable, LLM-free, gold-free, and emit
only a solver policy (never a verdict). It projects through existing public DESi
components and must not require any API key or network.
"""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve()
_REPO = _HERE.parents[2]
sys.path.insert(0, str(_REPO / "src"))
sys.path.insert(0, str(_REPO / "benchmarks" / "hf_answering"))

from semantic_mode_router import MODES, RouteResult, SemanticModeRouter  # noqa: E402

# A plain factual pair: no frame markers, no authority, no explicit chain.
_PLAIN_CLAIM = "The Eiffel Tower is located in Paris."
_PLAIN_EVID = "Paris is the city that contains the Eiffel Tower."
# An authority-grounded claim: the logic layer refuses to promote authority.
_AUTH_CLAIM = "Napoleon said that the war had already been won."
_AUTH_EVID = "A general announced that the battle concluded in victory."


def test_modes_are_the_three_fixed_families():
    assert MODES == ("baseline", "evidence_strict", "entailment_direct")


def test_route_returns_valid_mode_and_shape():
    r = SemanticModeRouter()
    res = r.route(_PLAIN_CLAIM, _PLAIN_EVID)
    assert isinstance(res, RouteResult)
    assert res.mode in MODES
    assert isinstance(res.reason, str) and res.reason
    assert isinstance(res.features, dict) and res.features
    # features must be serialisable (no private enum objects leak out)
    assert not any(k.startswith("_") for k in res.features)
    for k in ("claim_frame", "frame_consistency", "claim_state", "chain_state"):
        assert k in res.features


def test_deterministic_same_input_same_mode():
    r = SemanticModeRouter()
    a = r.route(_AUTH_CLAIM, _AUTH_EVID)
    b = r.route(_AUTH_CLAIM, _AUTH_EVID)
    assert a.mode == b.mode and a.reason == b.reason and a.features == b.features
    # a fresh instance must agree (no cross-call state changes the decision)
    c = SemanticModeRouter().route(_AUTH_CLAIM, _AUTH_EVID)
    assert c.mode == a.mode


def test_authority_claim_routes_to_evidence_strict():
    # an authority-grounded claim is logically rejected -> require explicit evidence
    res = SemanticModeRouter().route(_AUTH_CLAIM, _AUTH_EVID)
    assert res.mode == "evidence_strict"
    assert res.features["claim_state"] == "logically_rejected"


def test_plain_unmarked_pair_routes_to_baseline():
    res = SemanticModeRouter().route(_PLAIN_CLAIM, _PLAIN_EVID)
    assert res.mode == "baseline"
    assert res.features["frame_consistency"] == "undecidable"


def test_router_can_produce_more_than_one_mode():
    r = SemanticModeRouter()
    modes = {r.route(_PLAIN_CLAIM, _PLAIN_EVID).mode,
             r.route(_AUTH_CLAIM, _AUTH_EVID).mode}
    assert len(modes) >= 2  # not a constant function


def test_route_needs_no_api_key(monkeypatch):
    # the router is offline: it must work with no DeepSeek/OpenRouter key present
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    res = SemanticModeRouter().route(_PLAIN_CLAIM, _PLAIN_EVID)
    assert res.mode in MODES


def test_empty_inputs_do_not_crash():
    res = SemanticModeRouter().route("", "")
    assert res.mode in MODES
