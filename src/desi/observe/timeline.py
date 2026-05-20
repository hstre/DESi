"""TimelineEvent + exporters.

Events are ordered by a monotonic ``tick`` field, not by wall-clock
time, because two runs of the same scenario must produce identical
timelines. Wall-clock ``ts`` is recorded as metadata only and is
deliberately not part of the equality contract.
"""
from __future__ import annotations

import csv
import io
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Iterable


class EventType(str, Enum):
    """Closed enumeration of observable event kinds.

    Adding a new kind requires a code change here so that the timeline
    exporters and the harness assertions stay in sync.
    """

    # Run lifecycle
    RUN_STARTED = "run_started"
    RUN_ENDED = "run_ended"

    # Operator + guard
    OPERATOR_STARTED = "operator_started"
    GUARD_PASSED = "guard_passed"
    GUARD_BLOCKED = "guard_blocked"
    OPERATOR_ENDED = "operator_ended"

    # Claims
    CLAIM_CREATED = "claim_created"
    CLAIM_REVISED = "claim_revised"
    CLAIM_REJECTED = "claim_rejected"

    # Relations
    RELATION_CREATED = "relation_created"

    # Branches
    BRANCH_OPENED = "branch_opened"
    BRANCH_CLOSED = "branch_closed"
    BRANCH_MERGED = "branch_merged"

    # Memory hook surface (when a recorder write fails non-strictly)
    HOOK_ERROR = "hook_error"


@dataclass(frozen=True)
class TimelineEvent:
    """One observable event during a DESi run.

    Equality / hashing is by (tick, event_type, payload-as-tuple).
    ``ts`` is metadata only.
    """

    tick: int
    event_type: EventType
    payload: dict[str, Any] = field(default_factory=dict)
    ts: datetime = field(default_factory=lambda: datetime.now(timezone.utc),
                          compare=False, hash=False)

    def to_dict(self) -> dict[str, Any]:
        return {
            "tick": self.tick,
            "event_type": self.event_type.value,
            "payload": dict(self.payload),
            "ts": self.ts.isoformat(),
        }


# ---------------------------------------------------------------------------
# Exporters
# ---------------------------------------------------------------------------


def timeline_to_json(events: Iterable[TimelineEvent], *, indent: int = 2) -> str:
    return json.dumps([e.to_dict() for e in events], indent=indent,
                      default=_json_default, sort_keys=False)


def timeline_to_markdown(events: Iterable[TimelineEvent]) -> str:
    """Render a markdown table-style timeline.

    Format chosen to be diff-friendly: one row per event, fixed-order
    columns, no ASCII art that depends on terminal width.
    """
    lines = ["| tick | event_type | summary |",
             "|---:  |---         |---      |"]
    for ev in events:
        summary = _summarise_payload(ev.event_type, ev.payload)
        lines.append(f"| {ev.tick} | `{ev.event_type.value}` | {summary} |")
    return "\n".join(lines) + "\n"


def timeline_to_csv(events: Iterable[TimelineEvent]) -> str:
    """Emit a CSV with columns: tick, event_type, payload_json."""
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(["tick", "event_type", "payload_json"])
    for ev in events:
        writer.writerow([
            ev.tick,
            ev.event_type.value,
            json.dumps(ev.payload, default=_json_default, sort_keys=True),
        ])
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _summarise_payload(event_type: EventType, payload: dict[str, Any]) -> str:
    """Compact one-line description suitable for a markdown cell."""
    if event_type is EventType.RUN_STARTED:
        return f"trajectory_id={payload.get('trajectory_id')!r}, " \
               f"steps={payload.get('n_steps')}"
    if event_type is EventType.RUN_ENDED:
        return f"report={payload.get('report_type', '?')}"
    if event_type in (EventType.OPERATOR_STARTED, EventType.OPERATOR_ENDED):
        return f"op={payload.get('operator')!r}, " \
               f"loop={payload.get('loop_index')}"
    if event_type in (EventType.GUARD_PASSED, EventType.GUARD_BLOCKED):
        return f"op={payload.get('operator')!r}, " \
               f"guard={payload.get('guard_result', '')!r}"
    if event_type is EventType.CLAIM_CREATED:
        return f"claim_id={payload.get('claim_id')!r}, " \
               f"method={payload.get('method')!r}"
    if event_type is EventType.CLAIM_REVISED:
        return f"claim_id={payload.get('claim_id')!r}, " \
               f"version={payload.get('version')}"
    if event_type is EventType.CLAIM_REJECTED:
        return f"claim_id={payload.get('claim_id')!r}"
    if event_type is EventType.RELATION_CREATED:
        return f"{payload.get('source')!r} -[{payload.get('rel_type')}]-> " \
               f"{payload.get('target')!r}"
    if event_type is EventType.BRANCH_OPENED:
        return f"branch_id={payload.get('branch_id')!r}, " \
               f"focus={payload.get('focus_claim_id')!r}"
    if event_type is EventType.BRANCH_CLOSED:
        return f"branch_id={payload.get('branch_id')!r}"
    if event_type is EventType.BRANCH_MERGED:
        return f"branches={payload.get('source_branches')!r} -> " \
               f"{payload.get('target_branch')!r}"
    if event_type is EventType.HOOK_ERROR:
        return f"stage={payload.get('stage')!r}, " \
               f"err={payload.get('error_class')!r}"
    return ""


def _json_default(o: Any) -> Any:
    if isinstance(o, datetime):
        return o.isoformat()
    if isinstance(o, Enum):
        return o.value
    if isinstance(o, (set, tuple)):
        return list(o)
    raise TypeError(f"object of type {type(o).__name__} is not JSON-serialisable")
