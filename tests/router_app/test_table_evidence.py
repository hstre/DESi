"""The routing table as a living measurement: scores re-fit from ledger evidence, honestly.

Pins: only SCORED attempts move anything; a cell moves only at min_scored+; a refitted cell is
marked (score_source: ledger-refit + provenance block) and the policy surfaces that source; an
unmeasured pair appends as an explicitly provisional cell; unknown task classes are reported,
never created; dry-run by default.
"""
from __future__ import annotations

import json

from desi_router import table_evidence
from desi_router.ledger import Ledger

TABLE = {
    "schema_version": 1,
    "tasks": {
        "memory_recall": {"cells": [
            {"model": "small/model", "score": 0.56, "cost_per_item_usd": 0.0001},
        ]},
    },
}


def _ledger_with(tmp_path, attempts):
    led = Ledger(tmp_path / "l.db", instance_id="t")
    for task, model, score in attempts:
        led.record("pipeline_attempt",
                   {"task_class": task, "model": model, "attempt_idx": 0,
                    "confidence": "high", "escalate_bucket": False,
                    "answer": "x", "error": None, "cost_usd": 0.0002, "score": score})
    return led


def _table_file(tmp_path):
    p = tmp_path / "table.json"
    p.write_text(json.dumps(TABLE), encoding="utf-8")
    return p


def test_unscored_attempts_never_move_a_score(tmp_path):
    led = _ledger_with(tmp_path, [("memory_recall", "small/model", None)] * 50)
    out = table_evidence.refit(led, table_path=_table_file(tmp_path), min_scored=5)
    led.close()
    assert out["changes"] == []                       # production attempts without gold: no move


def test_below_min_scored_is_a_no_op(tmp_path):
    led = _ledger_with(tmp_path, [("memory_recall", "small/model", 1.0)] * 4)
    out = table_evidence.refit(led, table_path=_table_file(tmp_path), min_scored=5)
    led.close()
    assert out["changes"] == []


def test_dry_run_plans_but_does_not_write(tmp_path):
    led = _ledger_with(tmp_path, [("memory_recall", "small/model", 0.8)] * 30)
    tp = _table_file(tmp_path)
    out = table_evidence.refit(led, table_path=tp, min_scored=30)
    led.close()
    assert out["changes"][0]["action"] == "update"
    assert out["applied"] is False
    assert json.loads(tp.read_text())["tasks"]["memory_recall"]["cells"][0]["score"] == 0.56


def test_refit_updates_marks_and_keeps_provenance(tmp_path):
    led = _ledger_with(tmp_path, [("memory_recall", "small/model", 0.8)] * 30)
    tp = _table_file(tmp_path)
    out = table_evidence.refit(led, table_path=tp, min_scored=30, write=True)
    led.close()
    assert out["applied"] is True
    cell = json.loads(tp.read_text())["tasks"]["memory_recall"]["cells"][0]
    assert cell["score"] == 0.8
    assert cell["score_source"] == "ledger-refit"     # never poses as the benchmark measurement
    assert cell["refit"] == {"n_scored": 30, "prev_score": 0.56}


def test_an_unmeasured_pair_appends_a_provisional_cell(tmp_path):
    led = _ledger_with(tmp_path, [("memory_recall", "new/model", 0.9)] * 30)
    tp = _table_file(tmp_path)
    table_evidence.refit(led, table_path=tp, min_scored=30, write=True)
    led.close()
    cells = json.loads(tp.read_text())["tasks"]["memory_recall"]["cells"]
    new = next(c for c in cells if c["model"] == "new/model")
    assert new["provisional"] is True and new["score_source"] == "ledger-refit"
    assert cells[0]["score"] == 0.56                  # the benchmark row untouched


def test_an_unknown_task_class_is_reported_never_created(tmp_path):
    led = _ledger_with(tmp_path, [("poetry_critique", "small/model", 0.9)] * 30)
    tp = _table_file(tmp_path)
    out = table_evidence.refit(led, table_path=tp, min_scored=30, write=True)
    led.close()
    assert out["changes"][0]["action"] == "unknown_task"
    assert "poetry_critique" not in json.loads(tp.read_text())["tasks"]


def test_policy_surfaces_the_refit_source(monkeypatch, tmp_path):
    # a refitted number must not masquerade as 'measured' in the decision rationale
    from desi_router import policy, routing_table
    tp = tmp_path / "rt.json"
    tp.write_text(json.dumps({"tasks": {"scientific_claim": {"cells": [
        {"model": "m/x", "score": 0.9, "score_source": "ledger-refit"}]}}}), encoding="utf-8")
    monkeypatch.setattr(routing_table, "_TABLE_PATH", tp)
    routing_table._load.cache_clear()
    from desi_router.providers import ModelSpec
    score, src = policy._score(ModelSpec(id="m/x", locality="api"), "scientific_claim")
    routing_table._load.cache_clear()
    assert (score, src) == (0.9, "ledger-refit")
