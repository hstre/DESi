"""Tests for the v2.8 PatchPhase enum (Aufgabe 1)."""
from __future__ import annotations

from desi.rule_patch_protocol import PHASE_ORDER, PatchPhase


_EXPECTED = {
    "discovery", "risk_probe", "guard_synthesis",
    "implementation", "regression", "replay_verification", "complete",
}


def test_seven_phases_exactly() -> None:
    assert len(list(PatchPhase)) == 7


def test_value_set_matches_directive() -> None:
    assert {p.value for p in PatchPhase} == _EXPECTED


def test_each_directive_name_present() -> None:
    for name in (
        "DISCOVERY", "RISK_PROBE", "GUARD_SYNTHESIS",
        "IMPLEMENTATION", "REGRESSION", "REPLAY_VERIFICATION",
        "COMPLETE",
    ):
        assert hasattr(PatchPhase, name), name


def test_phase_order_covers_every_value_once() -> None:
    assert len(PHASE_ORDER) == 7
    assert tuple(p for p in PHASE_ORDER) == (
        PatchPhase.DISCOVERY,
        PatchPhase.RISK_PROBE,
        PatchPhase.GUARD_SYNTHESIS,
        PatchPhase.IMPLEMENTATION,
        PatchPhase.REGRESSION,
        PatchPhase.REPLAY_VERIFICATION,
        PatchPhase.COMPLETE,
    )


def test_phase_is_str_compatible() -> None:
    assert isinstance(PatchPhase.DISCOVERY.value, str)
