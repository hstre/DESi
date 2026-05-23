"""Aufgabe 9 — two complete pipeline runs must produce identical
state hashes."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

from desi.frame_tension_integration import (
    FrameTensionRouter,
    build_integration_benchmark,
)


_FIXED = datetime(2026, 5, 16, 0, 0, 0, tzinfo=timezone.utc)


def _run_once() -> str:
    router = FrameTensionRouter()
    decisions = []
    for case in build_integration_benchmark():
        d = router.route(
            claim_id=case.case_id,
            claim_text=case.claim_text,
            inherited_context_text=case.inherited_context_text,
            recorded_at=_FIXED,
        )
        decisions.append(d.to_dict())
    state = {
        "decisions": decisions,
        "ledger": router.ledger.to_list(),
    }
    raw = json.dumps(
        state, sort_keys=True, separators=(",", ":"), default=str,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def test_two_complete_runs_identical() -> None:
    a = _run_once()
    b = _run_once()
    assert a == b, f"replay drifted: {a} != {b}"


def test_ledger_event_ids_are_zero_based_sequential() -> None:
    router = FrameTensionRouter()
    for case in build_integration_benchmark():
        router.route(
            claim_id=case.case_id,
            claim_text=case.claim_text,
            inherited_context_text=case.inherited_context_text,
            recorded_at=_FIXED,
        )
    for i, e in enumerate(router.ledger.entries):
        assert e.event_id == f"frl_{i:06d}"
