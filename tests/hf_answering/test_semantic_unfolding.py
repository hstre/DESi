"""Targeted tests for the semantic UNFOLDING detector.

Deterministic, LLM-free, gold-free, dataset-name-free. Detects superficially
similar but epistemically dangerous differences (protects against false folding).
No API key or network required.
"""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve()
_REPO = _HERE.parents[2]
sys.path.insert(0, str(_REPO / "benchmarks" / "hf_answering"))

from semantic_unfolding import CATEGORIES, SemanticUnfoldingDetector, UnfoldResult  # noqa: E402

D = SemanticUnfoldingDetector()


def test_categories_present():
    assert set(CATEGORIES) == {
        "fold_safe", "contradiction_masking", "directional_divergence",
        "operator_divergence", "semantic_near_epistemic_far", "partial_support_masking",
    }


def test_fold_safe_synonym():
    # "won two Nobel Prizes" ~ "received a Nobel Prize": safe to fold
    r = D.detect("received a Nobel Prize", "Marie Curie won two Nobel Prizes in her career.")
    assert r.category == "fold_safe"
    assert r.unfold is False and r.applicable is True


def test_directional_reversal():
    r = D.detect("Russia is larger than Canada.", "Canada is larger than Russia.")
    assert r.category == "directional_divergence"
    assert r.unfold is True
    assert r.signals["directional_mismatch"] is True


def test_quantifier_divergence():
    r = D.detect("All swans are white birds.", "Some swans are white birds.")
    assert r.category == "operator_divergence"
    assert r.unfold is True
    assert r.signals["operator_mismatch"] is True


def test_semantic_near_epistemic_far():
    # same topic (Nobel) but a different relation (criticized vs received)
    r = D.detect("The author criticized the Nobel committee harshly.",
                 "The author received a Nobel Prize.")
    assert r.category == "semantic_near_epistemic_far"
    assert r.unfold is True
    assert r.signals["same_topic_different_relation"] is True


def test_contradiction_masking():
    r = D.detect("The treaty was signed by both nations.",
                 "The treaty was not signed by both nations.")
    assert r.category == "contradiction_masking"
    assert r.unfold is True


def test_low_similarity_defers():
    # not a fold candidate -> applicable False, defers (fold_safe sentinel)
    r = D.detect("the device measures temperature inside the laboratory.",
                 "the festival attracts large crowds during the summer.")
    assert r.applicable is False
    assert r.unfold is False


def test_result_shape_serialisable():
    import json
    r = D.detect("A covers B.", "B is covered by A.")
    assert isinstance(r, UnfoldResult)
    assert r.category in CATEGORIES
    json.dumps(r.signals)  # signals must be JSON-serialisable
    for k in ("directional_mismatch", "operator_mismatch", "negation_asymmetry",
              "semantic_near_epistemic_far", "surface_similarity_masking_contradiction"):
        assert k in r.signals


def test_deterministic_replay():
    pairs = [
        ("Russia is larger than Canada.", "Canada is larger than Russia."),
        ("All swans are white.", "Some swans are white."),
        ("The treaty was signed.", "The treaty was not signed."),
        ("received a Nobel Prize", "won two Nobel Prizes"),
    ]
    for c, e in pairs:
        a = D.detect(c, e)
        b = SemanticUnfoldingDetector().detect(c, e)
        assert a.category == b.category and a.unfold == b.unfold
        assert a.applicable == b.applicable and a.signals == b.signals


def test_no_api_key_needed(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    assert D.detect("x is bigger than y", "y is bigger than x").category in CATEGORIES
