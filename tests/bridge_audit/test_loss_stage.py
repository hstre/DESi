"""Tests for the v2.4 LossStage enum (Aufgabe 2)."""
from __future__ import annotations

from desi.bridge_audit import LossStage


_EXPECTED = {
    "no_loss",
    "parser_loss",
    "audit_reject_loss",
    "bridge_missing_loss",
    "consilium_veto_loss",
    "resolver_not_reached",
    "resolver_zero_depth",
    "cycle_not_recognized",
    "unknown_loss",
}


def test_nine_values_exactly() -> None:
    assert len(list(LossStage)) == 9


def test_value_set_matches_directive() -> None:
    assert {s.value for s in LossStage} == _EXPECTED


def test_each_directive_name_present() -> None:
    for name in (
        "NO_LOSS", "PARSER_LOSS", "AUDIT_REJECT_LOSS",
        "BRIDGE_MISSING_LOSS", "CONSILIUM_VETO_LOSS",
        "RESOLVER_NOT_REACHED", "RESOLVER_ZERO_DEPTH",
        "CYCLE_NOT_RECOGNIZED", "UNKNOWN_LOSS",
    ):
        assert hasattr(LossStage, name), name


def test_enum_is_string_compatible() -> None:
    assert isinstance(LossStage.NO_LOSS.value, str)
