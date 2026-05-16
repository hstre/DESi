"""Tests for v3.7 extractor (Aufgaben 1 + 3)."""
from __future__ import annotations

from desi.frame_disambiguator_probe import (
    extract_polysemy_targets,
    extract_thermo_counter_set,
)
from desi.frames import FrameKind


def test_extract_polysemy_targets_returns_exactly_fifteen() -> None:
    targets = extract_polysemy_targets()
    assert len(targets) == 15


def test_every_target_is_information_theoretic() -> None:
    for t in extract_polysemy_targets():
        assert t.expected_frame is FrameKind.INFORMATION_THEORETIC


def test_every_target_contains_entropy_token() -> None:
    for t in extract_polysemy_targets():
        assert "entropy" in t.text.lower()


def test_target_tokens_are_lowercase() -> None:
    for t in extract_polysemy_targets():
        for tok in t.tokens:
            assert tok == tok.lower()
            assert len(tok) >= 3


def test_counter_set_has_at_least_five_cases() -> None:
    """Aufgabe 3 — fail closed if < 5."""
    counters = extract_thermo_counter_set()
    assert len(counters) >= 5


def test_no_counter_case_is_information_theoretic() -> None:
    for c in extract_thermo_counter_set():
        assert c.expected_frame is not FrameKind.INFORMATION_THEORETIC


def test_every_counter_text_contains_entropy() -> None:
    for c in extract_thermo_counter_set():
        assert "entropy" in c.text.lower()


def test_extraction_is_deterministic() -> None:
    a = extract_polysemy_targets()
    b = extract_polysemy_targets()
    assert tuple(t.case_id for t in a) == tuple(t.case_id for t in b)
    ca = extract_thermo_counter_set()
    cb = extract_thermo_counter_set()
    assert tuple(c.source for c in ca) == tuple(c.source for c in cb)
