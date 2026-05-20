"""Aufgabe 7 — runtime benchmark: 40/40 expected."""
from __future__ import annotations

from collections import Counter

from desi.frame_tension import (
    ALL_LAYER_CASES,
    FrameConsistency,
    FrameTensionLayer,
)


def test_benchmark_has_at_least_forty_cases() -> None:
    assert len(ALL_LAYER_CASES) >= 40


def test_benchmark_has_ten_per_category() -> None:
    counts = Counter(c.expected.value for c in ALL_LAYER_CASES)
    for cls in FrameConsistency:
        assert counts[cls.value] >= 10, (
            f"category {cls.value} has {counts[cls.value]} cases, "
            "need >= 10"
        )


def test_layer_reaches_perfect_accuracy() -> None:
    layer = FrameTensionLayer()
    wrong = []
    for case in ALL_LAYER_CASES:
        d = layer.gate(
            claim_id=case.case_id,
            claim_text=case.claim_text,
            inherited_context_text=case.inherited_context_text,
        )
        if d.consistency is not case.expected:
            wrong.append((case.case_id, case.expected.value,
                          d.consistency.value))
    assert wrong == [], (
        f"{len(wrong)} mismatches on layer benchmark: {wrong}"
    )


def test_confirmed_cases_are_allowed() -> None:
    layer = FrameTensionLayer()
    for c in ALL_LAYER_CASES:
        if c.expected is FrameConsistency.CONFIRMED:
            d = layer.gate(
                claim_id=c.case_id,
                claim_text=c.claim_text,
                inherited_context_text=c.inherited_context_text,
            )
            assert d.inherited_allowed is True, c.case_id


def test_tension_cases_are_blocked() -> None:
    layer = FrameTensionLayer()
    for c in ALL_LAYER_CASES:
        if c.expected is FrameConsistency.TENSION:
            d = layer.gate(
                claim_id=c.case_id,
                claim_text=c.claim_text,
                inherited_context_text=c.inherited_context_text,
            )
            assert d.inherited_allowed is False, c.case_id
            assert d.event.value == "frame_inheritance_blocked", (
                c.case_id
            )


def test_conflict_cases_are_blocked() -> None:
    layer = FrameTensionLayer()
    for c in ALL_LAYER_CASES:
        if c.expected is FrameConsistency.CONFLICT:
            d = layer.gate(
                claim_id=c.case_id,
                claim_text=c.claim_text,
                inherited_context_text=c.inherited_context_text,
            )
            assert d.inherited_allowed is False, c.case_id
            assert d.event.value == "frame_conflict_blocked", c.case_id


def test_undecidable_cases_are_blocked() -> None:
    layer = FrameTensionLayer()
    for c in ALL_LAYER_CASES:
        if c.expected is FrameConsistency.UNDECIDABLE:
            d = layer.gate(
                claim_id=c.case_id,
                claim_text=c.claim_text,
                inherited_context_text=c.inherited_context_text,
            )
            assert d.inherited_allowed is False, c.case_id
            assert d.event.value == "frame_undecidable_blocked", (
                c.case_id
            )


def test_layer_records_one_ledger_entry_per_gate_call() -> None:
    layer = FrameTensionLayer()
    for c in ALL_LAYER_CASES:
        layer.gate(
            claim_id=c.case_id,
            claim_text=c.claim_text,
            inherited_context_text=c.inherited_context_text,
        )
    assert len(layer.ledger.entries) == len(ALL_LAYER_CASES)
