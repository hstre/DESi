"""Tests for TimelineEvent + exporters."""
from __future__ import annotations

import csv
import io
import json

from desi.observe import (
    EventType,
    TimelineEvent,
    timeline_to_csv,
    timeline_to_json,
    timeline_to_markdown,
)


def _events() -> list[TimelineEvent]:
    return [
        TimelineEvent(tick=0, event_type=EventType.RUN_STARTED,
                      payload={"trajectory_id": "t1", "n_steps": 2}),
        TimelineEvent(tick=1, event_type=EventType.OPERATOR_STARTED,
                      payload={"operator": "T6", "loop_index": 0,
                                "focus_claim_id": "C001"}),
        TimelineEvent(tick=2, event_type=EventType.CLAIM_CREATED,
                      payload={"claim_id": "C001", "method": "T6",
                                "loop_index": 0, "state": "proposed"}),
        TimelineEvent(tick=3, event_type=EventType.RUN_ENDED,
                      payload={"trajectory_id": "t1",
                                "report_type": "DeterministicMetrics"}),
    ]


def test_event_equality_excludes_wallclock_ts() -> None:
    a = TimelineEvent(tick=0, event_type=EventType.RUN_STARTED,
                      payload={"x": 1})
    b = TimelineEvent(tick=0, event_type=EventType.RUN_STARTED,
                      payload={"x": 1})
    assert a == b
    # ts is metadata only — different wall-clock instants must not break eq.
    assert a.ts != b.ts or a.ts == b.ts  # tautology; documents intent


def test_event_to_dict_contains_all_fields() -> None:
    ev = _events()[0]
    d = ev.to_dict()
    assert d["tick"] == 0
    assert d["event_type"] == "run_started"
    assert d["payload"] == {"trajectory_id": "t1", "n_steps": 2}
    assert "ts" in d


def test_to_json_is_parseable() -> None:
    s = timeline_to_json(_events())
    parsed = json.loads(s)
    assert len(parsed) == 4
    assert parsed[0]["event_type"] == "run_started"
    assert parsed[2]["payload"]["claim_id"] == "C001"


def test_to_markdown_has_one_row_per_event() -> None:
    md = timeline_to_markdown(_events())
    rows = [line for line in md.splitlines() if line.startswith("|")]
    # 1 header + 1 separator + 4 data rows
    assert len(rows) == 6
    # And the data rows include each tick value.
    assert any("| 0 |" in r for r in rows)
    assert any("| 3 |" in r for r in rows)


def test_to_csv_round_trips() -> None:
    s = timeline_to_csv(_events())
    reader = csv.reader(io.StringIO(s))
    rows = list(reader)
    assert rows[0] == ["tick", "event_type", "payload_json"]
    assert len(rows) == 5
    payload = json.loads(rows[3][2])
    assert payload["claim_id"] == "C001"


def test_event_types_enum_is_closed() -> None:
    # The 13 v0.4 event kinds.
    assert {et.value for et in EventType} == {
        "run_started", "run_ended",
        "operator_started", "guard_passed", "guard_blocked", "operator_ended",
        "claim_created", "claim_revised", "claim_rejected",
        "relation_created",
        "branch_opened", "branch_closed", "branch_merged",
        "hook_error",
    }
