"""Targeted tests for the algorithmic micro-semantic pre-solver router.

Pure, deterministic, LLM-free, gold-free, dataset-name-free. Emits a routing mode
and a solver policy only -- never a verdict. No API key or network required.
"""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve()
_REPO = _HERE.parents[2]
sys.path.insert(0, str(_REPO / "benchmarks" / "hf_answering"))

from micro_semantic_router import MODES, POLICY, MicroSemanticRouter, RouteResult  # noqa: E402

R = MicroSemanticRouter()


def test_modes_and_policy_map():
    assert set(POLICY) == set(MODES)
    assert set(POLICY.values()) == {"baseline", "evidence_strict", "entailment_direct"}
    assert POLICY["direct_entailment_likely"] == "entailment_direct"
    assert POLICY["contradiction_likely"] == "baseline"
    assert POLICY["missing_linkage_risk"] == "evidence_strict"
    assert POLICY["partial_support_risk"] == "evidence_strict"
    assert POLICY["high_nei_risk"] == "evidence_strict"
    assert POLICY["ambiguous"] == "baseline"


def test_nobel_entailment_is_direct():
    # "won two Nobel Prizes" entails "received a Nobel Prize" (synonym won~received)
    res = R.route("received a Nobel Prize",
                  "Marie Curie won two Nobel Prizes in her career.")
    assert res.mode == "direct_entailment_likely"
    assert res.policy == "entailment_direct"


def test_explicit_negation_is_contradiction():
    res = R.route("The treaty was signed by both nations.",
                  "The treaty was not signed by both nations.")
    assert res.mode == "contradiction_likely"
    assert res.policy == "baseline"


def test_antonym_is_contradiction():
    res = R.route("Sales increased sharply last year.",
                  "Sales decreased sharply last year.")
    assert res.mode == "contradiction_likely"


def test_entity_mismatch_is_missing_linkage():
    res = R.route("Tokyo has a population of over nine million people.",
                  "Paris has a population of over nine million people.")
    assert res.mode == "missing_linkage_risk"
    assert res.policy == "evidence_strict"


def test_partial_lexical_support_is_partial():
    res = R.route("The company was founded in 1998 and employs thousands of people.",
                  "The company was founded in 1998.")
    assert res.mode == "partial_support_risk"
    assert res.policy == "evidence_strict"


def test_low_overlap_is_low_information():
    # no shared content, no proper-noun entities -> not enough info / ambiguous
    res = R.route("the device measures temperature inside the laboratory.",
                  "the festival attracts large crowds during the summer.")
    assert res.mode in ("high_nei_risk", "ambiguous")
    assert res.policy in ("evidence_strict", "baseline")


def test_numeric_mismatch_is_contradiction():
    res = R.route("The building has 50 floors.", "The building has 30 floors.")
    assert res.mode == "contradiction_likely"


def test_result_shape_and_serialisable_features():
    res = R.route("A short claim about cats.", "A passage that mentions cats briefly.")
    assert isinstance(res, RouteResult)
    assert res.mode in MODES and res.policy in set(POLICY.values())
    assert isinstance(res.reason, str) and res.reason
    for k in ("content_coverage_claim", "entity_overlap", "negation_claim",
              "quantifier_claim", "modality_claim", "numeric_claim",
              "temporal_claim", "antonym_hit", "contradiction_indicator",
              "missing_linkage_indicator", "direct_entailment_indicator"):
        assert k in res.features
    import json
    json.dumps(res.features)  # features must be JSON-serialisable (no enum leak)


def test_deterministic_replay():
    pairs = [
        ("received a Nobel Prize", "Marie Curie won two Nobel Prizes."),
        ("The treaty was signed.", "The treaty was not signed."),
        ("Tokyo is large.", "Paris is large."),
    ]
    for c, e in pairs:
        a = R.route(c, e)
        b = MicroSemanticRouter().route(c, e)
        assert a.mode == b.mode and a.policy == b.policy and a.reason == b.reason
        assert a.features == b.features


def test_no_api_key_needed(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    assert R.route("x covers y", "y is covered by x").mode in MODES


def test_empty_inputs_do_not_crash():
    assert R.route("", "").mode in MODES
