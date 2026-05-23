"""v3.116 — final T10 redeployment report.

Pflichtmetriken (directive § v3.116):

* ``canonical_score``
* ``proxy_score``
* ``structural_score``
* ``best_strategy``
* ``architecture_roi``
* ``replay_stability``

Killerfrage: "Kann T10 durch echte Struktur statt
Abkuerzungen ueberleben?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .decision import (
    RedeployStrategy,
    all_strategy_outcomes,
    best_strategy,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V3116Report:
    canonical_score: float
    proxy_score: float
    structural_score: float
    best_strategy: str
    best_strategy_dims: tuple[str, ...]
    architecture_roi: float
    strategy_outcomes: tuple[dict, ...]
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "canonical_score":
                self.canonical_score,
            "proxy_score": self.proxy_score,
            "structural_score":
                self.structural_score,
            "best_strategy":
                self.best_strategy,
            "best_strategy_dims":
                list(self.best_strategy_dims),
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


def _by_strategy(
    outs, name: str,
):
    return next(
        o for o in outs if o.strategy == name
    )


def build_report() -> V3116Report:
    outs = all_strategy_outcomes()
    canon = _by_strategy(
        outs, RedeployStrategy.CANONICAL_9D.value,
    )
    proxy = _by_strategy(
        outs,
        RedeployStrategy.PROXY_ALPHABET.value,
    )
    struct = _by_strategy(
        outs,
        RedeployStrategy.STRUCTURAL_ALPHABET.value,
    )
    best = best_strategy()
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif (
        best.strategy
        == RedeployStrategy
        .STRUCTURAL_ALPHABET.value
    ):
        verdict = "STRUCTURAL_REDEPLOYMENT"
    elif (
        best.strategy
        == RedeployStrategy.CANONICAL_9D.value
    ):
        verdict = "CANONICAL_HELD"
    else:
        verdict = "PROXY_RETAINED"

    rationale = (
        f"INFO: canonical_score "
        f"{canon.architecture_roi}",
        f"INFO: proxy_score "
        f"{proxy.architecture_roi}",
        f"INFO: structural_score "
        f"{struct.architecture_roi}",
        f"INFO: best_strategy {best.strategy}",
        f"INFO: best_strategy_dims "
        f"{list(best.dims)}",
        f"INFO: architecture_roi "
        f"{best.architecture_roi}",
        f"INFO: strategy_outcomes "
        f"{[o.to_dict() for o in outs]}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V3116Report(
        canonical_score=canon.architecture_roi,
        proxy_score=proxy.architecture_roi,
        structural_score=struct.architecture_roi,
        best_strategy=best.strategy,
        best_strategy_dims=best.dims,
        architecture_roi=best.architecture_roi,
        strategy_outcomes=tuple(
            o.to_dict() for o in outs
        ),
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_t10_structural_redeployment_artifact(
) -> dict[str, object]:
    outs = all_strategy_outcomes()
    best = best_strategy()
    return {
        "schema_version":
            "v3_116_t10_structural_redeployment",
        "best_strategy": best.strategy,
        "best_strategy_dims": list(best.dims),
        "architecture_roi":
            best.architecture_roi,
        "strategy_outcomes": [
            o.to_dict() for o in outs
        ],
    }


__all__ = [
    "V3116Report",
    "build_report",
    "build_t10_structural_redeployment_artifact",
]
