"""Tests for the v3.4 ClaimState additions (Aufgabe 5)."""
from __future__ import annotations

from desi.memory.claim import ClaimState


def test_four_new_claim_states_added() -> None:
    for name in (
        "FRAME_DECLARED", "FRAME_UNDECLARED",
        "FRAME_CONFLICT", "FRAME_MISMATCH",
    ):
        assert hasattr(ClaimState, name), name


def test_logically_supported_still_exists() -> None:
    """Aufgabe 5 — the new states must NOT replace LOGICALLY_SUPPORTED."""
    assert hasattr(ClaimState, "LOGICALLY_SUPPORTED")
    assert ClaimState.LOGICALLY_SUPPORTED.value == "logically_supported"


def test_v19_tool_states_still_intact() -> None:
    """v1.9 invariant: TOOL_* states must remain present."""
    for name in (
        "TOOL_REQUIRED", "TOOL_SUPPORTED",
        "TOOL_REFUTED", "TOOL_FAILED",
    ):
        assert hasattr(ClaimState, name)


def test_v12_audit_states_still_intact() -> None:
    """v1.2 invariant: audit states preserved."""
    for name in (
        "UNDER_LOGICAL_AUDIT", "GAP_DETECTED",
        "BRIDGE_REQUIRED", "LOGICALLY_SUPPORTED",
        "LOGICALLY_REJECTED",
    ):
        assert hasattr(ClaimState, name)


def test_frame_state_values_are_pre_audit_namespace() -> None:
    """All v3.4 additions use the 'frame_' prefix."""
    for s in (
        ClaimState.FRAME_DECLARED, ClaimState.FRAME_UNDECLARED,
        ClaimState.FRAME_CONFLICT, ClaimState.FRAME_MISMATCH,
    ):
        assert s.value.startswith("frame_")
