"""Tests for v0.8 ledger event types — MULTI_SEED_STARTED / RESULT / DECISION."""
from __future__ import annotations

import json
import pathlib

from desi.evolution import (
    EvolutionLedger,
    EvolutionLedgerJSONL,
    LedgerEventType,
)


# ---------------------------------------------------------------------------
# Enum additions
# ---------------------------------------------------------------------------


def test_v08_event_types_are_in_the_enum() -> None:
    values = {e.value for e in LedgerEventType}
    assert "multi_seed_started" in values
    assert "multi_seed_result" in values
    assert "significance_decision" in values


def test_v07_event_types_still_present() -> None:
    """v0.7 events must not have been removed by the v0.8 extension."""
    values = {e.value for e in LedgerEventType}
    for v in ("config_activated", "metrics_delta", "evolution_cycle"):
        assert v in values


# ---------------------------------------------------------------------------
# Append-only persistence on the new events
# ---------------------------------------------------------------------------


def test_multi_seed_event_chain_appends_three_lines(tmp_path: pathlib.Path) -> None:
    p = tmp_path / "ledger.jsonl"
    led = EvolutionLedgerJSONL(p, version="v0.8")
    led.append(LedgerEventType.MULTI_SEED_STARTED, {
        "mutation_id": "M-001",
        "scenario_ids": ["ADV_BRANCH_EXPLOSION", "S2", "S6"],
        "seeds": [42, 43, 44, 45, 46],
    })
    led.append(LedgerEventType.MULTI_SEED_RESULT, {
        "scenario_id": "ADV_BRANCH_EXPLOSION",
        "aggregated_metrics": {
            "mean_branch_delta": -1.0,
            "std_branch_delta": 0.0,
            "improved_seed_count": 5,
        },
        "verdict": "improved",
    })
    led.append(LedgerEventType.SIGNIFICANCE_DECISION, {
        "mutation_id": "M-001",
        "verdict": "improved",
        "supporting_seeds": [42, 43, 44, 45, 46],
        "failing_seeds": [],
    })
    lines = p.read_text().splitlines()
    assert len(lines) == 3
    for line in lines:
        json.loads(line)


def test_multi_seed_events_are_deterministic_across_processes(
    tmp_path: pathlib.Path,
) -> None:
    a = EvolutionLedgerJSONL(tmp_path / "a.jsonl", version="v0.8")
    b = EvolutionLedgerJSONL(tmp_path / "b.jsonl", version="v0.8")
    payload = {
        "mutation_id": "M-001",
        "verdict": "improved",
        "supporting_seeds": [42, 43, 44, 45, 46],
        "failing_seeds": [],
    }
    ea = a.append(LedgerEventType.SIGNIFICANCE_DECISION, payload)
    eb = b.append(LedgerEventType.SIGNIFICANCE_DECISION, payload)
    assert ea.payload_hash == eb.payload_hash


def test_jsonl_with_multi_seed_events_is_append_only(
    tmp_path: pathlib.Path,
) -> None:
    p = tmp_path / "ledger.jsonl"
    led = EvolutionLedgerJSONL(p, version="v0.8")
    sizes: list[int] = []
    for sid in ("ADV_BRANCH_EXPLOSION", "S2", "S6"):
        led.append(LedgerEventType.MULTI_SEED_RESULT, {
            "scenario_id": sid,
            "aggregated_metrics": {"mean_branch_delta": 0.0},
            "verdict": "neutral",
        })
        sizes.append(p.stat().st_size)
    assert sizes == sorted(sizes)
    assert sizes[0] < sizes[-1]


def test_multi_seed_event_replays_on_reopen(tmp_path: pathlib.Path) -> None:
    p = tmp_path / "ledger.jsonl"
    led_a = EvolutionLedgerJSONL(p, version="v0.8")
    led_a.append(LedgerEventType.MULTI_SEED_STARTED, {
        "mutation_id": "M-001",
        "scenario_ids": ["ADV_BRANCH_EXPLOSION"],
        "seeds": [42, 43, 44, 45, 46],
    })
    led_b = EvolutionLedgerJSONL(p, version="v0.8")
    assert len(led_b.entries()) == 1
    e = led_b.entries()[0]
    assert e.event_type is LedgerEventType.MULTI_SEED_STARTED
    assert e.payload["seeds"] == [42, 43, 44, 45, 46]


# ---------------------------------------------------------------------------
# Append-only-at-runtime invariant (in-memory ledger)
# ---------------------------------------------------------------------------


def test_in_memory_ledger_accepts_new_event_types() -> None:
    led = EvolutionLedger(version="v0.8")
    led.append(LedgerEventType.MULTI_SEED_STARTED,
               {"mutation_id": "M-001", "scenario_ids": [], "seeds": []})
    led.append(LedgerEventType.MULTI_SEED_RESULT,
               {"scenario_id": "S2", "aggregated_metrics": {},
                "verdict": "neutral"})
    led.append(LedgerEventType.SIGNIFICANCE_DECISION,
               {"mutation_id": "M-001", "verdict": "improved",
                "supporting_seeds": [42, 43, 44, 45, 46],
                "failing_seeds": []})
    assert len(led) == 3
