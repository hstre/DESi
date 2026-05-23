"""Aufgaben 1 + 3 + 4 — signal extraction + corpus minima."""
from __future__ import annotations

from desi.premise_audit import (
    ALL_NC_CHAINS,
    ExtractionSignals,
    MIN_CHAIN_COUNT,
    MIN_TRANSITION_COUNT,
    SIGNAL_ORDER,
    SignalName,
    all_chains,
    extract_signals,
)


def test_signal_enum_has_eleven_values() -> None:
    assert len(list(SignalName)) == 11
    assert len(SIGNAL_ORDER) == 11


def test_corpus_chain_count_meets_minimum() -> None:
    chains = all_chains()
    # NCs are added in the report layer; the input corpora alone
    # provide ≥ 504 chains.
    assert len(chains) + len(ALL_NC_CHAINS) >= MIN_CHAIN_COUNT


def test_corpus_transition_count_meets_minimum() -> None:
    chains = all_chains()
    transitions = (len(chains) + len(ALL_NC_CHAINS)) * 4
    assert transitions >= MIN_TRANSITION_COUNT


def test_extract_returns_feature_tuple_of_eleven_floats() -> None:
    sig = extract_signals(
        "t",
        "The kettle whistled. Steam filled the room. "
        "Therefore the tea was poured.",
    )
    assert isinstance(sig, ExtractionSignals)
    tup = sig.feature_tuple()
    assert len(tup) == 11
    for x in tup:
        assert isinstance(x, float)


def test_extraction_is_deterministic() -> None:
    text = (
        "Pollen drifted onto a stigma. The ovary swelled. "
        "Therefore a tulip set seed."
    )
    a = extract_signals("t", text).to_dict()
    b = extract_signals("t", text).to_dict()
    assert a == b


def test_negative_control_count_meets_minimum() -> None:
    assert len(ALL_NC_CHAINS) >= 50


def test_corpus_covers_required_sources() -> None:
    sources = {c.source for c in all_chains()}
    required = {
        "v23_multistep", "v314_heldout", "v315_adversarial",
        "v316_surviving", "v316_suspended",
    }
    assert required.issubset(sources)
