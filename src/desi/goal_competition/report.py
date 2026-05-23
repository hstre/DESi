"""v8.2 — goal-competition report.

Five Pflichtmetriken:

* ``goal_balance``
* ``goodhart_risk``
* ``hidden_reweighting``
* ``tradeoff_transparency``
* ``replay_stability``

Killerfrage: "Kann DESi konkurrierende Ziele
balancieren, ohne epistemisch zu tricksen?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .goal_conflicts import (
    GOAL_WEIGHTS, OPTIMIZATION_GOALS, fixture,
)
from .optimization import (
    optimised, selected_top_k,
)
from .priority import (
    goal_balance, goodhart_risk,
    hidden_reweighting,
    tradeoff_transparency,
)


@dataclass(frozen=True)
class V82Report:
    item_count: int
    goal_balance: float
    goodhart_risk: float
    hidden_reweighting: float
    tradeoff_transparency: float
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "item_count": self.item_count,
            "goal_balance": self.goal_balance,
            "goodhart_risk":
                self.goodhart_risk,
            "hidden_reweighting":
                self.hidden_reweighting,
            "tradeoff_transparency":
                self.tradeoff_transparency,
            "replay_stability":
                self.replay_stability,
            "halt": self.halt,
            "recommendation":
                self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def _replay_stability() -> float:
    a = (
        goal_balance(), goodhart_risk(),
        hidden_reweighting(),
        tradeoff_transparency(),
    )
    b = (
        goal_balance(), goodhart_risk(),
        hidden_reweighting(),
        tradeoff_transparency(),
    )
    return 1.0 if a == b else 0.0


def _recommendation(
    *, replay: float, gb: float, gr: float,
    hr: float, tt: float,
) -> str:
    if replay < 1.0:
        return "HALT_REPLAY_DRIFT"
    if hr > 0.0:
        return "GOAL_HIDDEN_REWEIGHTING"
    if gr > 0.10:
        return "GOAL_GOODHART"
    if gb < 0.80:
        return "GOAL_COLLAPSE"
    if tt < 0.90:
        return "GOAL_OPAQUE"
    return "GOAL_BALANCED"


def build_report() -> V82Report:
    gb = goal_balance()
    gr = goodhart_risk()
    hr = hidden_reweighting()
    tt = tradeoff_transparency()
    replay = _replay_stability()
    halt = replay < 1.0
    verdict = _recommendation(
        replay=replay, gb=gb, gr=gr,
        hr=hr, tt=tt,
    )
    rationale = (
        f"INFO: item_count {len(fixture())}",
        f"INFO: goal_weights {dict(GOAL_WEIGHTS)}",
        f"INFO: top_3 "
        f"{[t.item_id for t in selected_top_k()]}",
        f"{'PASS' if gb >= 0.80 else 'FAIL'}: "
        f"goal_balance {gb} >= 0.80",
        f"{'PASS' if gr <= 0.10 else 'FAIL'}: "
        f"goodhart_risk {gr} <= 0.10",
        f"{'PASS' if hr == 0.0 else 'FAIL'}: "
        f"hidden_reweighting {hr} == 0.0",
        f"{'PASS' if tt >= 0.90 else 'FAIL'}: "
        f"tradeoff_transparency {tt} >= 0.90",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )
    return V82Report(
        item_count=len(fixture()),
        goal_balance=gb, goodhart_risk=gr,
        hidden_reweighting=hr,
        tradeoff_transparency=tt,
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_goal_competition_artifact(
) -> dict[str, object]:
    return {
        "schema_version":
            "v8_2_goal_competition",
        "optimization_goals":
            list(OPTIMIZATION_GOALS),
        "goal_weights": dict(GOAL_WEIGHTS),
        "item_count": len(fixture()),
        "items": [
            c.to_dict() for c in fixture()
        ],
        "optimised": [
            o.to_dict() for o in optimised()
        ],
        "top_3": [
            t.to_dict()
            for t in selected_top_k()
        ],
        "goal_balance": goal_balance(),
        "goodhart_risk": goodhart_risk(),
        "hidden_reweighting":
            hidden_reweighting(),
        "tradeoff_transparency":
            tradeoff_transparency(),
    }


__all__ = [
    "V82Report",
    "build_goal_competition_artifact",
    "build_report",
]
