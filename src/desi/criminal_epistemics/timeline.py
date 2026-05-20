"""v16.0 - public timeline backbone and timing
conflicts.

Encodes the well-established public sequence of
events (consistent by construction) plus a few
points where the public record carries CONTESTED
timing. DESi reports the contested points as
timeline inconsistencies; it does not adjudicate
them. No new factual claim is made.
"""
from __future__ import annotations

from dataclasses import dataclass

from .claims import ClaimStatus


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class TimelineEvent:
    event_id: str
    label: str
    # canonical offset in seconds from a reference
    # point (from the public timeline)
    offset_seconds: float
    status: str
    # True if the public record disputes this
    # event's timing
    contested_timing: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "event_id": self.event_id,
            "label": self.label,
            "offset_seconds": self.offset_seconds,
            "status": self.status,
            "contested_timing": self.contested_timing,
        }


# Established backbone (consistent), plus contested
# timing points. Offsets are illustrative ordinals
# from the public record, not new measurements.
_EVENTS: tuple[TimelineEvent, ...] = (
    TimelineEvent(
        "T01",
        "Motorcade enters Dealey Plaza",
        0.0, ClaimStatus.VERIFIED.value, False,
    ),
    TimelineEvent(
        "T02",
        "Shots are fired at the motorcade",
        8.0, ClaimStatus.VERIFIED.value, False,
    ),
    TimelineEvent(
        "T03",
        "Interval between first and last shot",
        # disputed across acoustic / film analyses
        14.0, ClaimStatus.CONTESTED.value, True,
    ),
    TimelineEvent(
        "T04",
        "Limousine accelerates toward the hospital",
        20.0, ClaimStatus.VERIFIED.value, False,
    ),
    TimelineEvent(
        "T05",
        "Arrival at Parkland Hospital",
        320.0, ClaimStatus.VERIFIED.value, False,
    ),
    TimelineEvent(
        "T06",
        "President pronounced dead",
        1920.0, ClaimStatus.VERIFIED.value, False,
    ),
    TimelineEvent(
        "T07",
        "Timing some witnesses assign to a "
        "knoll-area sound",
        # disputed relative to the shot sequence
        9.0, ClaimStatus.CONTESTED.value, True,
    ),
    TimelineEvent(
        "T08",
        "Oswald arrested",
        4500.0, ClaimStatus.VERIFIED.value, False,
    ),
    TimelineEvent(
        "T09",
        "Oswald killed by Ruby (two days later)",
        177000.0, ClaimStatus.VERIFIED.value, False,
    ),
)


def events() -> tuple[TimelineEvent, ...]:
    return _EVENTS


def _backbone() -> tuple[TimelineEvent, ...]:
    return tuple(
        e for e in _EVENTS if not e.contested_timing
    )


def backbone_is_ordered() -> bool:
    """The established (non-contested) events must
    be strictly increasing in offset - the
    backbone's internal consistency."""
    b = _backbone()
    return all(
        b[i].offset_seconds < b[i + 1].offset_seconds
        for i in range(len(b) - 1)
    )


def timeline_inconsistencies() -> tuple[
    TimelineEvent, ...
]:
    """The points the public record leaves with
    contested timing - surfaced, never resolved."""
    return tuple(
        e for e in _EVENTS if e.contested_timing
    )


def timeline_consistency() -> float:
    """Fraction of timeline events whose timing is
    settled in the public record (not contested),
    given that the established backbone is itself
    internally ordered. In [0, 1]."""
    if not _EVENTS:
        return 1.0
    if not backbone_is_ordered():
        # backbone contradiction would be a hard
        # epistemic failure
        return 0.0
    settled = sum(
        1 for e in _EVENTS if not e.contested_timing
    )
    return _round(settled / len(_EVENTS))


__all__ = [
    "TimelineEvent",
    "backbone_is_ordered",
    "events",
    "timeline_consistency",
    "timeline_inconsistencies",
]
