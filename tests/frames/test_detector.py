"""Tests for FrameDetector — Aufgaben 3 + 6 + 10."""
from __future__ import annotations

from desi.frames import DetectionMethod, FrameDetector, FrameKind


def _detect(text: str):
    return FrameDetector().detect(claim_id="X", source_text=text)


def test_explicit_marker_takes_precedence_over_rules() -> None:
    """Even when the text contains thermodynamic vocabulary, an
    explicit marker for information-theoretic wins."""
    d = _detect(
        "Frame: information-theoretic. Entropy is just one bit here."
    )
    assert d.frame_kind is FrameKind.INFORMATION_THEORETIC
    assert d.detection_method is DetectionMethod.EXPLICIT_MARKER


def test_explicit_thermodynamic_marker() -> None:
    d = _detect("Frame: thermodynamic. Heat conduction holds.")
    assert d.frame_kind is FrameKind.THERMODYNAMIC


def test_rule_based_metaphorical_via_as_if() -> None:
    d = _detect("He walked as if he owned the room.")
    assert d.frame_kind is FrameKind.METAPHORICAL
    assert d.detection_method is DetectionMethod.RULE_BASED


def test_rule_based_authority_speech() -> None:
    d = _detect("Professor X says the proof is complete.")
    assert d.frame_kind is FrameKind.AUTHORITY_SPEECH


def test_rule_based_tool_computable_arithmetic() -> None:
    d = _detect("What is 17 * 23 ?")
    assert d.frame_kind is FrameKind.TOOL_COMPUTABLE


def test_rule_based_tool_computable_date_arithmetic() -> None:
    d = _detect("How many days from 2020-01-01 to 2020-12-31 ?")
    assert d.frame_kind is FrameKind.TOOL_COMPUTABLE


def test_rule_based_empirical_causal() -> None:
    d = _detect("Heavy rainfall causes localised flooding.")
    assert d.frame_kind is FrameKind.EMPIRICAL_CAUSAL


def test_unframed_undeclared() -> None:
    d = _detect("The fox jumped over the lazy dog.")
    assert d.frame_kind is FrameKind.FRAME_UNDECLARED
    assert d.detection_method is DetectionMethod.DEFAULT_UNDECLARED


def test_entropy_alone_triggers_conflict() -> None:
    """Aufgabe 6 — bare 'entropy' fires both thermodynamic and
    information-theoretic buckets, so the detector emits
    FRAME_UNDECLARED with a 'frame conflict' rationale."""
    d = _detect("Entropy increases in any closed system over time.")
    assert d.frame_kind is FrameKind.FRAME_UNDECLARED
    assert "conflict" in d.rationale.lower()


def test_replay_hash_deterministic() -> None:
    a = _detect("Heavy rain causes flooding.")
    b = _detect("Heavy rain causes flooding.")
    assert a.replay_hash == b.replay_hash
    assert a.frame_id == b.frame_id


def test_replay_hash_changes_with_text() -> None:
    a = _detect("Heavy rain causes flooding.")
    b = _detect("Heavy snow causes flooding.")
    assert a.replay_hash != b.replay_hash


def test_declaration_carries_required_fields() -> None:
    d = _detect("Heavy rain causes flooding.")
    for f in (
        "frame_id", "claim_id", "frame_kind", "source_text",
        "detection_method", "confidence", "rationale", "replay_hash",
    ):
        assert hasattr(d, f)
