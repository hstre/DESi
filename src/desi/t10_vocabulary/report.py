"""v3.108 — expansion vocabulary decision report.

Pflichtmetriken (directive § v3.108):

* ``best_strategy``
* ``recovery_score``
* ``complexity_score``
* ``stability_score``
* ``architecture_roi``

Killerfrage: "Ist T10 ein einzelner Schluessel -
oder ein ganzes Alphabet?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .decision import (
    all_strategy_outcomes,
    best_strategy,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V3108Report:
    best_strategy: str
    best_strategy_dims: tuple[str, ...]
    recovery_score: float
    complexity_score: float
    stability_score: float
    architecture_roi: float
    strategy_outcomes: tuple[dict, ...]
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "best_strategy": self.best_strategy,
            "best_strategy_dims":
                list(self.best_strategy_dims),
            "recovery_score":
                self.recovery_score,
            "complexity_score":
                self.complexity_score,
            "stability_score":
                self.stability_score,
            "architecture_roi":
                self.architecture_roi,
            "strategy_outcomes":
                list(self.strategy_outcomes),
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
        best_strategy().to_dict(),
    )
    b = (
        best_strategy().to_dict(),
    )
    return 1.0 if a == b else 0.0


def build_report() -> V3108Report:
    outs = all_strategy_outcomes()
    best = best_strategy()
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif best.strategy == "single_universal":
        verdict = "T10_IS_SINGLE_KEY"
    elif best.strategy == "small_vocab":
        verdict = "T10_IS_SMALL_ALPHABET"
    else:
        verdict = "T10_IS_PER_CASE"

    rationale = (
        f"INFO: best_strategy {best.strategy}",
        f"INFO: best_strategy_dims "
        f"{list(best.dims)}",
        f"INFO: recovery_score "
        f"{best.recovery_score}",
        f"INFO: complexity_score "
        f"{best.complexity_score}",
        f"INFO: stability_score "
        f"{best.stability_score}",
        f"INFO: architecture_roi "
        f"{best.architecture_roi}",
        f"INFO: strategy_outcomes "
        f"{[o.to_dict() for o in outs]}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V3108Report(
        best_strategy=best.strategy,
        best_strategy_dims=best.dims,
        recovery_score=best.recovery_score,
        complexity_score=best.complexity_score,
        stability_score=best.stability_score,
        architecture_roi=best.architecture_roi,
        strategy_outcomes=tuple(
            o.to_dict() for o in outs
        ),
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_t10_expansion_vocabulary_artifact(
) -> dict[str, object]:
    outs = all_strategy_outcomes()
    best = best_strategy()
    return {
        "schema_version":
            "v3_108_t10_expansion_vocabulary",
        "best_strategy": best.strategy,
        "best_strategy_dims": list(best.dims),
        "recovery_score":
            best.recovery_score,
        "complexity_score":
            best.complexity_score,
        "stability_score":
            best.stability_score,
        "architecture_roi":
            best.architecture_roi,
        "strategy_outcomes": [
            o.to_dict() for o in outs
        ],
    }


__all__ = [
    "V3108Report",
    "build_report",
    "build_t10_expansion_vocabulary_artifact",
]
