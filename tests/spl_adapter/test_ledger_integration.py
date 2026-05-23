"""Tests for the three v1.0 SEMANTIC_PROJECTION_* ledger events."""
from __future__ import annotations

import json
import pathlib

from desi.evolution import EvolutionLedger, EvolutionLedgerJSONL, LedgerEventType
from desi.spl_adapter import (
    LLMSemanticBackend,
    SPLAdapter,
)


# ---------------------------------------------------------------------------
# Enum membership
# ---------------------------------------------------------------------------


def test_three_semantic_event_types_in_enum() -> None:
    values = {e.value for e in LedgerEventType}
    assert "semantic_projection_started" in values
    assert "semantic_candidate_emitted" in values
    assert "semantic_projection_rejected" in values


# ---------------------------------------------------------------------------
# Adapter writes the expected events
# ---------------------------------------------------------------------------


def test_started_event_is_emitted_on_entry() -> None:
    led = EvolutionLedger(version="v1.0")
    SPLAdapter(ledger=led).project_text("Water boils at 100C.")
    started = led.filter(LedgerEventType.SEMANTIC_PROJECTION_STARTED)
    assert len(started) == 1
    assert started[0].payload["backend"] == "deterministic_semantic_projection"


def test_candidate_emitted_per_backend_candidate() -> None:
    led = EvolutionLedger(version="v1.0")
    SPLAdapter(ledger=led).project_text("Water boils at 100C.")
    emitted = led.filter(LedgerEventType.SEMANTIC_CANDIDATE_EMITTED)
    assert len(emitted) == 1
    assert emitted[0].payload["method"] == "deterministic_semantic_projection"


def test_rejected_event_on_ambiguous_input() -> None:
    led = EvolutionLedger(version="v1.0")
    SPLAdapter(ledger=led).project_text(
        "Water might possibly boil somewhere around 100 degrees."
    )
    rejected = led.filter(LedgerEventType.SEMANTIC_PROJECTION_REJECTED)
    assert len(rejected) == 1
    assert rejected[0].payload["reason"] == "ambiguous_claim"


def test_rejected_event_on_no_backend_output() -> None:
    led = EvolutionLedger(version="v1.0")
    SPLAdapter(ledger=led).project_text("The cat sat on the mat.")
    rejected = led.filter(LedgerEventType.SEMANTIC_PROJECTION_REJECTED)
    assert any(r.payload["reason"] == "no_backend_output" for r in rejected)


def test_rejected_event_on_cost_guard_exhaustion() -> None:
    def _ok(prompt: str) -> str:
        return json.dumps({
            "units": [{
                "canonical_content": "water boils at 100°C",
                "raw_span": "Water boils at 100C.",
                "confidence": 0.9, "ambiguous": False,
                "proposed_relations": [],
            }]
        })
    led = EvolutionLedger(version="v1.0")
    adapter = SPLAdapter(
        backend=LLMSemanticBackend(llm_call=_ok), ledger=led,
        llm_projection_budget=2,
    )
    for _ in range(3):
        adapter.project_text("Water boils at 100C.")
    rejected = led.filter(LedgerEventType.SEMANTIC_PROJECTION_REJECTED)
    assert any(r.payload["reason"] == "cost_guard_exhausted"
               for r in rejected)


# ---------------------------------------------------------------------------
# JSONL persistence + replay
# ---------------------------------------------------------------------------


def test_jsonl_persists_semantic_events(tmp_path: pathlib.Path) -> None:
    p = tmp_path / "ledger.jsonl"
    led = EvolutionLedgerJSONL(p, version="v1.0")
    SPLAdapter(ledger=led).project_text("Water boils at 100C.")
    lines = p.read_text().splitlines()
    assert len(lines) >= 2  # at least STARTED + CANDIDATE_EMITTED
    for line in lines:
        rec = json.loads(line)
        assert rec["event_type"].startswith("semantic_")


def test_jsonl_semantic_events_replay_on_reopen(
    tmp_path: pathlib.Path,
) -> None:
    p = tmp_path / "ledger.jsonl"
    led_a = EvolutionLedgerJSONL(p, version="v1.0")
    SPLAdapter(ledger=led_a).project_text("Water boils at 100C.")
    n_before = len(led_a.entries())
    led_b = EvolutionLedgerJSONL(p, version="v1.0")
    assert len(led_b.entries()) == n_before


# ---------------------------------------------------------------------------
# Adapter without a ledger does NOT log
# ---------------------------------------------------------------------------


def test_adapter_without_ledger_does_not_crash() -> None:
    """Ledger is optional; when omitted, nothing is logged but the
    adapter still returns the right claims."""
    adapter = SPLAdapter()  # no ledger
    result = adapter.project_text("Water boils at 100C.")
    assert len(result.claims) == 1
