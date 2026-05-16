"""Tests for the v3.4 FrameKind + DetectionMethod enums (Aufgaben 1, 10)."""
from __future__ import annotations

from desi.frames import DetectionMethod, FrameKind


_EXPECTED = {
    "thermodynamic", "information_theoretic",
    "ontological_distinguishability", "metaphorical",
    "formal_logic", "empirical_causal", "authority_speech",
    "tool_computable", "frame_undeclared",
}


def test_nine_frame_kinds_exactly() -> None:
    assert len(list(FrameKind)) == 9


def test_value_set_matches_directive() -> None:
    assert {f.value for f in FrameKind} == _EXPECTED


def test_each_directive_name_present() -> None:
    for name in (
        "THERMODYNAMIC", "INFORMATION_THEORETIC",
        "ONTOLOGICAL_DISTINGUISHABILITY", "METAPHORICAL",
        "FORMAL_LOGIC", "EMPIRICAL_CAUSAL", "AUTHORITY_SPEECH",
        "TOOL_COMPUTABLE", "FRAME_UNDECLARED",
    ):
        assert hasattr(FrameKind, name), name


def test_detection_method_has_three_values() -> None:
    assert len(list(DetectionMethod)) == 3
    assert {m.value for m in DetectionMethod} == {
        "explicit_marker", "rule_based", "default_undeclared",
    }


def test_frame_kind_str_compatible() -> None:
    assert isinstance(FrameKind.METAPHORICAL.value, str)
