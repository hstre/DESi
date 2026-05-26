"""Targeted tests for residual semantic escalation.

Algorithm-first: deterministic layers resolve clear cases; only the ambiguous
residue escalates to the lightweight semantic scorer. Deterministic, LLM-free,
gold-free, dataset-name-free, no API key/network.
"""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve()
_REPO = _HERE.parents[2]
sys.path.insert(0, str(_REPO / "benchmarks" / "hf_answering"))

from residual_semantic_escalation import (  # noqa: E402
    OUTCOMES, ResidualDecision, ResidualEscalationRouter, ResidualScorer, resolve,
)
from semantic_unfolding import SemanticUnfoldingDetector  # noqa: E402

R = ResidualEscalationRouter()
SC = ResidualScorer()
DET = SemanticUnfoldingDetector()


def _scores(c, e):
    return SC.score(c, e, DET.detect(c, e).signals)


def test_outcomes_present():
    assert set(OUTCOMES) == {
        "fold_safe_confirmed", "directional_entailment_confirmed",
        "semantic_divergence_confirmed", "partial_support_confirmed",
        "unresolved_high_risk",
    }


def test_semantic_near_epistemic_far():
    d = R.route("The author criticized the Nobel committee harshly.",
                "The author received a Nobel Prize.")
    assert d.escalated is True
    assert d.outcome == "semantic_divergence_confirmed"
    assert d.f_policy == "evidence_strict"


def test_directional_asymmetry():
    s = _scores("Paris is in France.",
                "Paris is the capital city of France, a large country in Europe.")
    out, pol = resolve(s)
    assert out == "directional_entailment_confirmed"
    assert pol == "entailment_direct"
    assert s["asym"] > 0  # claim contained in (and shorter than) the evidence


def test_partial_support():
    d = R.route("The company was founded in 1998 and employs thousands of people.",
                "The company was founded in 1998.")
    assert d.escalated is True
    assert d.outcome == "partial_support_confirmed"
    assert d.f_policy == "evidence_strict"


def test_residual_escalation_trigger():
    # ambiguous (same-topic / partial) escalates
    assert R.route("The author criticized the Nobel committee harshly.",
                   "The author received a Nobel Prize.").escalated is True
    # a clear contradiction is resolved deterministically (NOT escalated)
    assert R.route("The treaty was signed.", "The treaty was not signed.").escalated is False
    # a clear high-coverage fold is NOT escalated
    assert R.route("received a Nobel Prize", "Marie Curie won two Nobel Prizes.").escalated is False
    # a non-fold-candidate (low overlap) is NOT escalated
    assert R.route("the device measures temperature inside the lab.",
                   "the festival attracts crowds during the summer.").escalated is False


def test_outcome_policy_consistency():
    _MAP = {"fold_safe_confirmed": "entailment_direct",
            "directional_entailment_confirmed": "entailment_direct",
            "semantic_divergence_confirmed": "evidence_strict",
            "partial_support_confirmed": "evidence_strict",
            "unresolved_high_risk": "baseline"}
    for c, e in [("Russia is larger than Canada.", "Canada is larger than Russia."),
                 ("The author criticized the Nobel committee.", "The author received a Nobel Prize."),
                 ("The company was founded in 1998 and grew fast.", "The company was founded in 1998.")]:
        out, pol = resolve(_scores(c, e))
        assert _MAP[out] == pol


def test_dir_fwd_high_for_contained_claim():
    s = _scores("Cats are animals.", "Cats are small domestic animals kept as pets worldwide.")
    assert s["dir_fwd"] >= 0.5  # claim content largely contained in evidence


def test_deterministic_replay():
    pairs = [
        ("The author criticized the Nobel committee.", "The author received a Nobel Prize."),
        ("The company was founded in 1998 and grew.", "The company was founded in 1998."),
        ("Paris is in France.", "Paris is the capital of France in Europe."),
    ]
    for c, e in pairs:
        a = R.route(c, e)
        b = ResidualEscalationRouter().route(c, e)
        assert isinstance(a, ResidualDecision)
        assert (a.escalated, a.outcome, a.f_policy, a.e_policy) == \
               (b.escalated, b.outcome, b.f_policy, b.e_policy)
        assert a.scores == b.scores


def test_no_api_key_needed(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    d = R.route("x is bigger than y", "y is bigger than x")
    assert d.f_policy in ("baseline", "evidence_strict", "entailment_direct")
