"""v3.104a — historical delta decomposition report.

Pflichtmetriken (directive § v3.104a):

* ``beneficial_flip_count``
* ``adverse_flip_count``
* ``neutral_count``
* ``historical_delta_map``
* ``replay_stability``

Killerfrage: "Sind die historischen Aenderungen
wirklich ausschliesslich nuetzlich?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .classify import (
    all_classified_outcomes,
)
from .delta import (
    adverse_auc_delta,
    adverse_flip_count,
    affected_sprint_ids,
    beneficial_auc_delta,
    beneficial_flip_count,
    historical_delta_map,
    neutral_count,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V3104aReport:
    classified_count: int
    beneficial_flip_count: int
    adverse_flip_count: int
    neutral_count: int
    adverse_auc_delta: float
    beneficial_auc_delta: float
    affected_sprint_ids: tuple[str, ...]
    historical_delta_map: dict[str, list[dict]]
    classified_outcomes: tuple[dict, ...]
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "classified_count":
                self.classified_count,
            "beneficial_flip_count":
                self.beneficial_flip_count,
            "adverse_flip_count":
                self.adverse_flip_count,
            "neutral_count": self.neutral_count,
            "adverse_auc_delta":
                self.adverse_auc_delta,
            "beneficial_auc_delta":
                self.beneficial_auc_delta,
            "affected_sprint_ids":
                list(self.affected_sprint_ids),
            "historical_delta_map":
                self.historical_delta_map,
            "classified_outcomes":
                list(self.classified_outcomes),
            "replay_stability":
                self.replay_stability,
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def _replay_stability() -> float:
    a = (
        adverse_flip_count(),
        beneficial_flip_count(),
        adverse_auc_delta(),
        beneficial_auc_delta(),
    )
    b = (
        adverse_flip_count(),
        beneficial_flip_count(),
        adverse_auc_delta(),
        beneficial_auc_delta(),
    )
    return 1.0 if a == b else 0.0


def build_report() -> V3104aReport:
    outs = all_classified_outcomes()
    a_count = adverse_flip_count()
    b_count = beneficial_flip_count()
    n_count = neutral_count()
    a_delta = adverse_auc_delta()
    b_delta = beneficial_auc_delta()
    affected = affected_sprint_ids()
    delta_map = historical_delta_map()
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif a_count == 0 and b_count > 0:
        verdict = "DELTA_PURELY_BENEFICIAL"
    elif a_count == 0:
        verdict = "DELTA_NEUTRAL"
    elif b_count == 0:
        verdict = "DELTA_PURELY_ADVERSE"
    else:
        verdict = "DELTA_MIXED"

    rationale = (
        f"INFO: classified_count {len(outs)}",
        f"INFO: beneficial_flip_count {b_count}",
        f"INFO: adverse_flip_count {a_count}",
        f"INFO: neutral_count {n_count}",
        f"INFO: adverse_auc_delta {a_delta}",
        f"INFO: beneficial_auc_delta {b_delta}",
        f"INFO: affected_sprint_ids "
        f"{list(affected)}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V3104aReport(
        classified_count=len(outs),
        beneficial_flip_count=b_count,
        adverse_flip_count=a_count,
        neutral_count=n_count,
        adverse_auc_delta=a_delta,
        beneficial_auc_delta=b_delta,
        affected_sprint_ids=affected,
        historical_delta_map=delta_map,
        classified_outcomes=tuple(
            o.to_dict() for o in outs
        ),
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_t10_delta_decomposition_artifact(
) -> dict[str, object]:
    outs = all_classified_outcomes()
    return {
        "schema_version":
            "v3_104a_t10_delta_decomposition",
        "classified_count": len(outs),
        "beneficial_flip_count":
            beneficial_flip_count(),
        "adverse_flip_count":
            adverse_flip_count(),
        "neutral_count": neutral_count(),
        "adverse_auc_delta":
            adverse_auc_delta(),
        "beneficial_auc_delta":
            beneficial_auc_delta(),
        "affected_sprint_ids":
            list(affected_sprint_ids()),
        "historical_delta_map":
            historical_delta_map(),
        "classified_outcomes": [
            o.to_dict() for o in outs
        ],
    }


__all__ = [
    "V3104aReport",
    "build_report",
    "build_t10_delta_decomposition_artifact",
]
