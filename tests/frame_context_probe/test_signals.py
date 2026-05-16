"""ContextSignal enum is closed and exhaustive."""
from __future__ import annotations

from desi.frame_context_probe.signals import ContextSignal


def test_signal_enum_size() -> None:
    # Aufgabe 3: exactly the 7 enumerated signals — no plugin slots.
    assert len(list(ContextSignal)) == 7


def test_signal_enum_values() -> None:
    expected = {
        "section_header",
        "explicit_frame",
        "domain_repetition",
        "tool_route",
        "authority_context",
        "metaphor_context",
        "none",
    }
    assert {s.value for s in ContextSignal} == expected


def test_signal_enum_is_str() -> None:
    # Inherits from str for JSON-friendly serialisation.
    assert isinstance(ContextSignal.NONE, str)
    assert ContextSignal.NONE.value == "none"
