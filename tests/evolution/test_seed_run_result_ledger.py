"""Tests for v0.9 LedgerEventType.SEED_RUN_RESULT — append-only per-seed audit."""
from __future__ import annotations

import json
import pathlib

from desi.evolution import (
    EvolutionLedger,
    EvolutionLedgerJSONL,
    LedgerEventType,
)


# ---------------------------------------------------------------------------
# Enum addition
# ---------------------------------------------------------------------------


def test_seed_run_result_is_in_the_enum() -> None:
    values = {e.value for e in LedgerEventType}
    assert "seed_run_result" in values


def test_v07_v08_event_types_still_present() -> None:
    values = {e.value for e in LedgerEventType}
    for v in ("config_activated", "metrics_delta", "evolution_cycle",
              "multi_seed_started", "multi_seed_result",
              "significance_decision"):
        assert v in values


# ---------------------------------------------------------------------------
# JSONL persistence + replay
# ---------------------------------------------------------------------------


def test_seed_run_result_jsonl_appends_one_line(tmp_path: pathlib.Path) -> None:
    p = tmp_path / "ledger.jsonl"
    led = EvolutionLedgerJSONL(p, version="v0.9")
    led.append(LedgerEventType.SEED_RUN_RESULT, {
        "scenario_id": "ADV_BRANCH_EXPLOSION",
        "seed": 43,
        "permutation_id": "perm_93f1",
        "verdict": "improved",
        "metrics": {"branch_opened_delta": -1},
    })
    lines = p.read_text().splitlines()
    assert len(lines) == 1
    rec = json.loads(lines[0])
    assert rec["event_type"] == "seed_run_result"
    assert rec["payload"]["seed"] == 43
    assert rec["payload"]["permutation_id"] == "perm_93f1"


def test_multiple_seed_run_results_keep_append_order(
    tmp_path: pathlib.Path,
) -> None:
    p = tmp_path / "ledger.jsonl"
    led = EvolutionLedgerJSONL(p, version="v0.9")
    for s in (42, 43, 44, 45, 46):
        led.append(LedgerEventType.SEED_RUN_RESULT, {
            "scenario_id": "ADV_BRANCH_EXPLOSION",
            "seed": s,
            "permutation_id": f"perm_{s:04x}",
            "verdict": "improved",
            "metrics": {},
        })
    lines = p.read_text().splitlines()
    assert len(lines) == 5
    seeds_in_order = [json.loads(line)["payload"]["seed"] for line in lines]
    assert seeds_in_order == [42, 43, 44, 45, 46]


def test_seed_run_result_replays_on_reopen(tmp_path: pathlib.Path) -> None:
    p = tmp_path / "ledger.jsonl"
    led_a = EvolutionLedgerJSONL(p, version="v0.9")
    led_a.append(LedgerEventType.SEED_RUN_RESULT, {
        "scenario_id": "S2", "seed": 42,
        "permutation_id": "perm_a3f8",
        "verdict": "neutral",
        "metrics": {},
    })
    led_b = EvolutionLedgerJSONL(p, version="v0.9")
    assert len(led_b.entries()) == 1
    e = led_b.entries()[0]
    assert e.event_type is LedgerEventType.SEED_RUN_RESULT


# ---------------------------------------------------------------------------
# In-memory ledger accepts the new type
# ---------------------------------------------------------------------------


def test_in_memory_ledger_accepts_seed_run_result() -> None:
    led = EvolutionLedger(version="v0.9")
    led.append(LedgerEventType.SEED_RUN_RESULT, {
        "scenario_id": "S6", "seed": 43, "permutation_id": "perm_b5e7",
        "verdict": "neutral", "metrics": {},
    })
    assert len(led) == 1


def test_seed_run_result_payload_hash_is_deterministic(
    tmp_path: pathlib.Path,
) -> None:
    a = EvolutionLedgerJSONL(tmp_path / "a.jsonl", version="v0.9")
    b = EvolutionLedgerJSONL(tmp_path / "b.jsonl", version="v0.9")
    payload = {
        "scenario_id": "ADV_BRANCH_EXPLOSION",
        "seed": 42,
        "permutation_id": "perm_3f345ab3",
        "verdict": "improved",
        "metrics": {"branch_opened_delta": -1},
    }
    ea = a.append(LedgerEventType.SEED_RUN_RESULT, payload)
    eb = b.append(LedgerEventType.SEED_RUN_RESULT, payload)
    assert ea.payload_hash == eb.payload_hash
