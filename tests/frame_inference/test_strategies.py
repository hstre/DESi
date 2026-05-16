"""v4.1 — per-strategy unit + smoke tests.

These tests fix the behaviour of each strategy so a future
refactor cannot silently change the inference output.
"""
from __future__ import annotations

from desi.external_probe.corpus import ExternalChain
from desi.external_probe.enums import Domain, GroundTruth
from desi.frame_inference import (
    InferenceStrategy, f1_marker_lexical, f2_nearest_neighbor,
    f3_sentence_cooccurrence, f4_context_window,
    is_context_strategy, stateless_strategy, synthetic_marker,
)
from desi.frames import FrameKind


def _chain(text: str) -> ExternalChain:
    return ExternalChain(
        chain_id="T001", domain=Domain.D1_SCIENTIFIC_ABSTRACTS,
        text=text, ground_truth=GroundTruth.VALID, rationale="t",
    )


def test_strategy_registry_covers_three_stateless() -> None:
    expected_stateless = {
        InferenceStrategy.F1_MARKER_LEXICAL,
        InferenceStrategy.F2_NEAREST_NEIGHBOR,
        InferenceStrategy.F3_SENTENCE_COOCCURRENCE,
    }
    for s in expected_stateless:
        assert callable(stateless_strategy(s))
    assert is_context_strategy(InferenceStrategy.F4_CONTEXT_WINDOW)


def test_synthetic_marker_round_trip() -> None:
    for kind in FrameKind:
        if kind is FrameKind.FRAME_UNDECLARED:
            continue
        marker = synthetic_marker(kind)
        assert marker.startswith("Frame: ")


def test_synthetic_marker_rejects_undeclared() -> None:
    import pytest
    with pytest.raises(ValueError):
        synthetic_marker(FrameKind.FRAME_UNDECLARED)


def test_f2_returns_none_on_short_text() -> None:
    # No vocabulary terms match the empty domain text.
    assert f2_nearest_neighbor(_chain("Hello world.")) is None


def test_f2_picks_empirical_for_medical_text() -> None:
    text = (
        "The patient presented with fever. Blood cultures grew "
        "Staphylococcus aureus in the hospital lab. The clinical "
        "picture supports infection."
    )
    assert f2_nearest_neighbor(_chain(text)) is FrameKind.EMPIRICAL_CAUSAL


def test_f3_picks_formal_for_proof_text() -> None:
    text = (
        "Suppose n is an integer. Then n is rational by definition. "
        "Therefore the sequence of integers is convergent in the "
        "extended real line."
    )
    assert (
        f3_sentence_cooccurrence(_chain(text))
        is FrameKind.FORMAL_LOGIC
    )


def test_f4_inherits_when_own_signal_is_silent() -> None:
    silent = ExternalChain(
        chain_id="T010", domain=Domain.D1_SCIENTIFIC_ABSTRACTS,
        text="A short note follows here.", ground_truth=GroundTruth.VALID,
        rationale="silent",
    )
    history = (
        ("scientific_abstracts", FrameKind.EMPIRICAL_CAUSAL),
        ("scientific_abstracts", FrameKind.EMPIRICAL_CAUSAL),
        ("scientific_abstracts", FrameKind.EMPIRICAL_CAUSAL),
        ("scientific_abstracts", FrameKind.EMPIRICAL_CAUSAL),
    )
    assert (
        f4_context_window(silent, prior_history=history)
        is FrameKind.EMPIRICAL_CAUSAL
    )


def test_f4_does_not_inherit_across_domains() -> None:
    silent = ExternalChain(
        chain_id="T011", domain=Domain.D4_MATHEMATICAL_PROOFS,
        text="Short note.", ground_truth=GroundTruth.VALID,
        rationale="silent",
    )
    history = (
        ("scientific_abstracts", FrameKind.EMPIRICAL_CAUSAL),
        ("scientific_abstracts", FrameKind.EMPIRICAL_CAUSAL),
        ("scientific_abstracts", FrameKind.EMPIRICAL_CAUSAL),
        ("scientific_abstracts", FrameKind.EMPIRICAL_CAUSAL),
    )
    assert f4_context_window(silent, prior_history=history) is None


def test_f1_returns_none_on_undeclared() -> None:
    text = "An entirely neutral sentence with no markers at all."
    assert f1_marker_lexical(_chain(text)) is None
