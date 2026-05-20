"""Tests for the frame-compatibility checker — Aufgabe 4."""
from __future__ import annotations

from desi.frames import (
    FrameKind,
    allowed_pipelines,
    blocked_pipelines,
    check_compatibility,
)


def test_metaphor_blocks_literal_physical_inference() -> None:
    blocked = blocked_pipelines(FrameKind.METAPHORICAL)
    assert "literal_physical_inference" in blocked
    assert "tool_gate" in blocked


def test_metaphor_requires_consilium() -> None:
    allowed = allowed_pipelines(FrameKind.METAPHORICAL)
    assert "consilium" in allowed
    assert "metaphor_audit" in allowed


def test_authority_speech_blocks_authority_boost() -> None:
    blocked = blocked_pipelines(FrameKind.AUTHORITY_SPEECH)
    assert "authority_boost" in blocked


def test_tool_computable_routes_to_tool_gate() -> None:
    allowed = allowed_pipelines(FrameKind.TOOL_COMPUTABLE)
    blocked = blocked_pipelines(FrameKind.TOOL_COMPUTABLE)
    assert allowed == ("tool_gate",)
    assert "linguistic_proof" in blocked


def test_thermodynamic_allows_tool_and_logical_audit() -> None:
    allowed = allowed_pipelines(FrameKind.THERMODYNAMIC)
    assert "tool_gate" in allowed
    assert "logical_audit" in allowed
    blocked = blocked_pipelines(FrameKind.THERMODYNAMIC)
    assert "metaphor_audit" in blocked


def test_information_theoretic_blocks_thermodynamic_inference() -> None:
    blocked = blocked_pipelines(FrameKind.INFORMATION_THEORETIC)
    assert "thermodynamic_inference" in blocked


def test_ontological_blocks_causal_chain() -> None:
    blocked = blocked_pipelines(FrameKind.ONTOLOGICAL_DISTINGUISHABILITY)
    assert "causal_chain" in blocked
    allowed = allowed_pipelines(FrameKind.ONTOLOGICAL_DISTINGUISHABILITY)
    assert "identity_audit" in allowed


def test_formal_logic_blocks_authority_boost() -> None:
    assert "authority_boost" in blocked_pipelines(FrameKind.FORMAL_LOGIC)


def test_empirical_causal_blocks_syllogism() -> None:
    assert "syllogism" in blocked_pipelines(FrameKind.EMPIRICAL_CAUSAL)
    assert "causal_chain" in allowed_pipelines(FrameKind.EMPIRICAL_CAUSAL)


def test_undeclared_blocks_every_pipeline() -> None:
    allowed = allowed_pipelines(FrameKind.FRAME_UNDECLARED)
    assert allowed == ()


def test_undeclared_compatibility_is_false() -> None:
    out = check_compatibility(declared_frame=FrameKind.FRAME_UNDECLARED)
    assert out.compatible is False


def test_compatible_when_requested_pipeline_allowed() -> None:
    out = check_compatibility(
        declared_frame=FrameKind.TOOL_COMPUTABLE,
        requested_pipeline="tool_gate",
    )
    assert out.compatible is True


def test_incompatible_when_requested_pipeline_blocked() -> None:
    out = check_compatibility(
        declared_frame=FrameKind.METAPHORICAL,
        requested_pipeline="tool_gate",
    )
    assert out.compatible is False
    assert "blocked" in out.reason


def test_compatibility_replay_hash_deterministic() -> None:
    a = check_compatibility(declared_frame=FrameKind.THERMODYNAMIC)
    b = check_compatibility(declared_frame=FrameKind.THERMODYNAMIC)
    assert a.replay_hash == b.replay_hash
