"""Tests for EvolutionLedgerJSONL — append-only file-backed persistence."""
from __future__ import annotations

import json
import pathlib

import pytest

from desi.evolution import (
    EvolutionLedger,
    EvolutionLedgerJSONL,
    LedgerEventType,
)


# ---------------------------------------------------------------------------
# v0.7 event types added
# ---------------------------------------------------------------------------


def test_v07_event_types_are_in_the_enum() -> None:
    values = {e.value for e in LedgerEventType}
    assert "config_activated" in values
    assert "metrics_delta" in values
    assert "evolution_cycle" in values


# ---------------------------------------------------------------------------
# JSONL persistence
# ---------------------------------------------------------------------------


def test_jsonl_ledger_writes_one_line_per_entry(tmp_path: pathlib.Path) -> None:
    p = tmp_path / "ledger.jsonl"
    led = EvolutionLedgerJSONL(p)
    led.append(LedgerEventType.PROPOSAL, {"mutation_id": "M-001"})
    led.append(LedgerEventType.CONFIG_ACTIVATED, {
        "mutation_id": "M-001",
        "clone_id": "clone_abc",
        "config_hash": "deadbeef",
        "active_knobs": ["guard_thresholds.branch_open_evidence_min"],
    })
    lines = p.read_text().splitlines()
    assert len(lines) == 2
    # Each line is valid JSON.
    for line in lines:
        json.loads(line)


def test_jsonl_ledger_lines_are_deterministic(tmp_path: pathlib.Path) -> None:
    a_path = tmp_path / "a.jsonl"
    b_path = tmp_path / "b.jsonl"
    a = EvolutionLedgerJSONL(a_path)
    b = EvolutionLedgerJSONL(b_path)
    # The wall-clock timestamps + uuids differ. To assert determinism
    # on the "payload bytes", we hand-construct identical entries with
    # identical payloads and compare the payload_hash.
    e1 = a.append(LedgerEventType.METRICS_DELTA, {
        "scenario_id": "ADV_BRANCH_EXPLOSION",
        "verdict": "improved",
        "branch_opened_delta": -1,
    })
    e2 = b.append(LedgerEventType.METRICS_DELTA, {
        "scenario_id": "ADV_BRANCH_EXPLOSION",
        "verdict": "improved",
        "branch_opened_delta": -1,
    })
    assert e1.payload_hash == e2.payload_hash


def test_jsonl_ledger_replays_on_reopen(tmp_path: pathlib.Path) -> None:
    p = tmp_path / "ledger.jsonl"
    led_a = EvolutionLedgerJSONL(p)
    a = led_a.append(LedgerEventType.PROPOSAL, {"mutation_id": "M-001"})
    led_a.append(LedgerEventType.METRICS_DELTA, {"verdict": "improved"})
    # Reopen the same file with a fresh instance.
    led_b = EvolutionLedgerJSONL(p)
    assert len(led_b.entries()) == 2
    assert led_b.entries()[0].ledger_id == a.ledger_id


def test_jsonl_ledger_is_append_only(tmp_path: pathlib.Path) -> None:
    p = tmp_path / "ledger.jsonl"
    led = EvolutionLedgerJSONL(p)
    baseline_count = 0
    for _ in range(5):
        led.append(LedgerEventType.METRICS_DELTA, {"verdict": "neutral"})
    # The file size only ever grows.
    sizes = []
    for _ in range(3):
        led.append(LedgerEventType.METRICS_DELTA, {"verdict": "improved"})
        sizes.append(p.stat().st_size)
    assert sizes == sorted(sizes)
    assert sizes[0] < sizes[-1]


def test_jsonl_ledger_replay_preserves_payload_hash(
    tmp_path: pathlib.Path,
) -> None:
    p = tmp_path / "ledger.jsonl"
    led = EvolutionLedgerJSONL(p)
    e = led.append(LedgerEventType.METRICS_DELTA, {
        "scenario_id": "S2",
        "verdict": "neutral",
    })
    h0 = e.payload_hash
    led2 = EvolutionLedgerJSONL(p)
    assert led2.entries()[0].payload_hash == h0


def test_jsonl_ledger_works_with_subdirectory_creation(
    tmp_path: pathlib.Path,
) -> None:
    p = tmp_path / "nested" / "subdir" / "ledger.jsonl"
    led = EvolutionLedgerJSONL(p)
    led.append(LedgerEventType.PROPOSAL, {"mutation_id": "M-001"})
    assert p.exists()
    assert p.parent.is_dir()
