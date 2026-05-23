"""Tests for v1.9 ToolDetector — pattern dispatch + Cat-E rejection."""
from __future__ import annotations

import pytest

from desi.tools import ToolDetector, ToolKind


@pytest.mark.parametrize("text, expected_kind", [
    ("What is 2 + 2?", ToolKind.PYTHON_DECIMAL),
    ("Compute 17 * 23", ToolKind.PYTHON_DECIMAL),
    ("Calculate 100 / 4", ToolKind.PYTHON_DECIMAL),
    ("Is 144 = 12 * 12?", ToolKind.PYTHON_DECIMAL),
    ("How many days between 2020-01-01 and 2020-12-31?",
     ToolKind.PYTHON_DATETIME),
    ("What weekday was 2024-07-04?", ToolKind.PYTHON_DATETIME),
    ("Add 30 days to 2025-01-15", ToolKind.PYTHON_DATETIME),
    ("How many vowels in 'mississippi'?", ToolKind.PYTHON_COLLECTIONS),
    ("How many s's in 'mississippi'?", ToolKind.PYTHON_COLLECTIONS),
    ("How many distinct letters in 'banana'?", ToolKind.PYTHON_COLLECTIONS),
    ("Solve x^2 - 4 = 0 for x", ToolKind.SYMPY),
    ("Is {1, 2} subset of {1, 2, 3}?", ToolKind.SET_THEORY),
    ("Intersection of {1, 2} and {2, 3}", ToolKind.SET_THEORY),
])
def test_detector_dispatches_known_patterns(text, expected_kind) -> None:
    p = ToolDetector().detect(text)
    assert p is not None, f"detector failed to fire on: {text!r}"
    assert p.tool_kind is expected_kind


@pytest.mark.parametrize("text", [
    # Cat E false-temptation: detector must NOT fire.
    "Compute the consciousness of a rock.",
    "What is love + happiness?",
    "Solve God for x",
    "How many truths in the universe?",
    # Existing main-benchmark inputs — detector must NOT fire.
    "All men are mortal. Socrates is a man. Therefore Socrates is mortal.",
    "Professor X says quantum gravity is solved.",
    "It is raining. Therefore the street is wet.",
    "The market is nervous.",
    "What is the meaning of life?",
])
def test_detector_returns_none_for_non_computable(text) -> None:
    assert ToolDetector().detect(text) is None, (
        f"detector falsely fired on non-computable input: {text!r}"
    )


def test_detector_returns_proposal_with_input_hash() -> None:
    p = ToolDetector().detect("What is 2 + 2?")
    assert p is not None
    assert p.input_hash.startswith("ih_")
    assert p.input_payload["expression"] == "2 + 2"


def test_detector_is_deterministic() -> None:
    a = ToolDetector().detect("What is 2 + 2?")
    b = ToolDetector().detect("What is 2 + 2?")
    assert a is not None and b is not None
    assert a.input_hash == b.input_hash
    assert a.tool_kind == b.tool_kind


def test_detector_rejects_empty_input() -> None:
    assert ToolDetector().detect("") is None
    assert ToolDetector().detect("   ") is None
