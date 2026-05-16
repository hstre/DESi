"""Tests for v3.6 enum + extraction (Aufgaben 1 + 2)."""
from __future__ import annotations

from desi.frame_failure_audit import (
    FrameFailureClass,
    extract_failures,
)


_EXPECTED = {
    "synonym_gap", "polysemy_collision", "marker_dropout",
    "multi_signal_conflict", "pipeline_routing_mismatch",
    "true_frame_shift", "unknown",
}


def test_failure_class_enum_has_seven_values() -> None:
    assert len(list(FrameFailureClass)) == 7


def test_failure_class_set_matches_directive() -> None:
    assert {f.value for f in FrameFailureClass} == _EXPECTED


def test_every_directive_name_present() -> None:
    for name in (
        "SYNONYM_GAP", "POLYSEMY_COLLISION", "MARKER_DROPOUT",
        "MULTI_SIGNAL_CONFLICT", "PIPELINE_ROUTING_MISMATCH",
        "TRUE_FRAME_SHIFT", "UNKNOWN",
    ):
        assert hasattr(FrameFailureClass, name)


def test_extract_returns_exactly_thirty_failures() -> None:
    """Aufgabe 1 hard expectation."""
    fs = extract_failures()
    assert len(fs) == 30


def test_every_extracted_record_has_required_fields() -> None:
    fs = extract_failures()
    for r in fs:
        for f in (
            "case_id", "canonical_group_id",
            "expected_frame", "detected_frame",
            "failure_type", "text",
            "explicit_marker_present",
            "paraphrase_variant",
        ):
            assert hasattr(r, f), f


def test_extraction_is_deterministic() -> None:
    a = extract_failures()
    b = extract_failures()
    assert tuple(r.case_id for r in a) == tuple(r.case_id for r in b)
