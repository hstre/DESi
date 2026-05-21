"""v35.3 - public scorecard export.

Turns each run summary into a public scorecard that carries its
score, provenance class and a replay anchor. A scorecard is traceable
iff it can be tied back to a run and a replay anchor - no score is
published without a trace.
"""
from __future__ import annotations

from dataclasses import dataclass

from .benchmark_summary import RunSummary, run_summaries


@dataclass(frozen=True)
class PublicScorecard:
    name: str
    family: str
    provenance_class: str
    score: float
    replay_anchor: str

    def is_traceable(self) -> bool:
        return (
            bool(self.name)
            and bool(self.family)
            and bool(self.provenance_class)
            and bool(self.replay_anchor)
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "family": self.family,
            "provenance_class": self.provenance_class,
            "score": self.score,
            "replay_anchor": self.replay_anchor,
        }


def _card(r: RunSummary) -> PublicScorecard:
    return PublicScorecard(
        name=r.name,
        family=r.family,
        provenance_class=r.provenance_class,
        score=r.score,
        replay_anchor=r.replay_anchor,
    )


def public_scorecards() -> tuple[PublicScorecard, ...]:
    return tuple(_card(r) for r in run_summaries())


def scorecard_traceability() -> float:
    cards = public_scorecards()
    if not cards:
        return 0.0
    ok = sum(1 for c in cards if c.is_traceable())
    return round(ok / len(cards), 6)


__all__ = [
    "PublicScorecard",
    "public_scorecards",
    "scorecard_traceability",
]
