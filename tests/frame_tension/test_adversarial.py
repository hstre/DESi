"""Aufgabe 9 — adversarial probe using the v3.9 manipulation set."""
from __future__ import annotations

from desi.frame_consistency_probe.manipulation import MANIPULATIONS
from desi.frame_tension import FrameTensionLayer, FrameTensionLedgerEvent


def _run_all() -> list:
    layer = FrameTensionLayer()
    out = []
    for m in MANIPULATIONS:
        d = layer.gate(
            claim_id=f"manip:{m.case_id}",
            claim_text=m.text,
            inherited_context_text=m.ctx_3,
        )
        out.append((m.case_id, d))
    return out


def test_no_manipulated_case_receives_inheritance_allowed() -> None:
    # Aufgabe 9 hard requirement: 0 manipulation cases may carry
    # the FRAME_INHERITANCE_ALLOWED ledger event.
    for case_id, d in _run_all():
        assert d.event is not FrameTensionLedgerEvent.FRAME_INHERITANCE_ALLOWED, (
            f"manipulation {case_id} leaked through as allowed"
        )


def test_manipulation_detection_rate_meets_threshold() -> None:
    results = _run_all()
    detected = sum(
        1 for _, d in results
        if d.event is not FrameTensionLedgerEvent.FRAME_INHERITANCE_ALLOWED
    )
    rate = detected / len(results)
    assert rate >= 0.95, f"manipulation_detection_rate={rate} < 0.95"


def test_every_manipulation_lands_in_block_event() -> None:
    block_events = {
        FrameTensionLedgerEvent.FRAME_INHERITANCE_BLOCKED,
        FrameTensionLedgerEvent.FRAME_CONFLICT_BLOCKED,
        FrameTensionLedgerEvent.FRAME_UNDECIDABLE_BLOCKED,
    }
    for case_id, d in _run_all():
        assert d.event in block_events, case_id
