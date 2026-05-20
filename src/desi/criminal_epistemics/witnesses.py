"""v16.0 - witness statements and witness
conflicts.

Witness perception is genuinely divided in the
public record (notably on the perceived direction
of the shots). DESi marks the conflicts; it never
declares which witnesses were right. Encodes no new
testimony.
"""
from __future__ import annotations

from dataclasses import dataclass

from .claims import ClaimStatus


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class WitnessStatement:
    statement_id: str
    topic: str
    stance: str
    # how many witnesses (illustrative grouping)
    weight: int
    status: str

    def to_dict(self) -> dict[str, object]:
        return {
            "statement_id": self.statement_id,
            "topic": self.topic,
            "stance": self.stance,
            "weight": self.weight,
            "status": self.status,
        }


# Grouped witness perceptions from the public
# record. Stances on a shared topic that differ are
# genuine conflicts.
_STATEMENTS: tuple[WitnessStatement, ...] = (
    WitnessStatement(
        "W01", "shot_origin", "depository",
        weight=4, status=ClaimStatus.PLAUSIBLE.value,
    ),
    WitnessStatement(
        "W02", "shot_origin", "knoll",
        weight=2, status=ClaimStatus.PLAUSIBLE.value,
    ),
    WitnessStatement(
        "W03", "shot_count", "three",
        weight=3, status=ClaimStatus.PLAUSIBLE.value,
    ),
    WitnessStatement(
        "W04", "shot_count", "more_than_three",
        weight=1,
        status=ClaimStatus.CONTESTED.value,
    ),
    WitnessStatement(
        "W05", "shot_origin", "uncertain",
        weight=2, status=ClaimStatus.UNRESOLVED.value,
    ),
)


def statements() -> tuple[WitnessStatement, ...]:
    return _STATEMENTS


def _decisive(s: WitnessStatement) -> bool:
    # "uncertain" is not a competing stance; it is
    # preserved uncertainty, not a conflict.
    return s.stance != "uncertain"


def witness_conflict_topics() -> tuple[str, ...]:
    """Topics on which witnesses hold two or more
    distinct decisive stances."""
    by_topic: dict[str, set[str]] = {}
    for s in _STATEMENTS:
        if _decisive(s):
            by_topic.setdefault(
                s.topic, set(),
            ).add(s.stance)
    return tuple(
        sorted(
            t for t, st in by_topic.items()
            if len(st) >= 2
        )
    )


def witness_conflict_pairs() -> tuple[
    tuple[str, str], ...
]:
    """Pairs of witness statements that take
    different decisive stances on the same topic."""
    out: list[tuple[str, str]] = []
    rows = [s for s in _STATEMENTS if _decisive(s)]
    for i, a in enumerate(rows):
        for b in rows[i + 1:]:
            if (
                a.topic == b.topic
                and a.stance != b.stance
            ):
                out.append(
                    tuple(sorted(
                        (a.statement_id, b.statement_id),
                    )),
                )
    out.sort()
    return tuple(out)


def uncertainty_preserved() -> bool:
    """At least one witness stance is explicitly
    'uncertain' and is NOT collapsed into a
    decisive camp."""
    return any(
        s.stance == "uncertain" for s in _STATEMENTS
    )


__all__ = [
    "WitnessStatement",
    "statements",
    "uncertainty_preserved",
    "witness_conflict_pairs",
    "witness_conflict_topics",
]
