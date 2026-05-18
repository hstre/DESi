"""v3.120b — bootstrap stability report.

Pflichtmetriken (directive § v3.120b):

* ``threshold_mean``
* ``threshold_ci``
* ``threshold_drift``
* ``seed_invariance``
* ``replay_stability``

Killerfrage: "Ist der Threshold real - oder
Zufall?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .bootstrap import (
    BOOTSTRAP_SEEDS,
    all_bootstrap_draws,
)
from .stability import (
    seed_invariance,
    threshold_ci,
    threshold_drift,
    threshold_mean,
)


DRIFT_CEILING: float = 0.05


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V3120bReport:
    bootstrap_seed_count: int
    threshold_mean: float
    threshold_ci: tuple[float, float]
    threshold_drift: float
    seed_invariance: float
    bootstrap_draws: tuple[dict, ...]
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "bootstrap_seed_count":
                self.bootstrap_seed_count,
            "threshold_mean":
                self.threshold_mean,
            "threshold_ci":
                list(self.threshold_ci),
            "threshold_drift":
                self.threshold_drift,
            "seed_invariance":
                self.seed_invariance,
            "bootstrap_draws":
                list(self.bootstrap_draws),
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
        threshold_mean(),
        threshold_ci(),
        threshold_drift(),
        seed_invariance(),
    )
    b = (
        threshold_mean(),
        threshold_ci(),
        threshold_drift(),
        seed_invariance(),
    )
    return 1.0 if a == b else 0.0


def build_report() -> V3120bReport:
    draws = all_bootstrap_draws()
    tm = threshold_mean()
    ci = threshold_ci()
    td = threshold_drift()
    si = seed_invariance()
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif td <= DRIFT_CEILING:
        verdict = "THRESHOLD_STABLE"
    elif si >= 0.50:
        verdict = "THRESHOLD_MODE_STABLE"
    else:
        verdict = "THRESHOLD_DRIFTS"

    rationale = (
        f"INFO: bootstrap_seed_count "
        f"{len(BOOTSTRAP_SEEDS)}",
        f"INFO: threshold_mean {tm}",
        f"INFO: threshold_ci {list(ci)}",
        f"{'PASS' if td <= DRIFT_CEILING else 'FAIL'}: "
        f"threshold_drift {td} "
        f"(ceiling {DRIFT_CEILING})",
        f"INFO: seed_invariance {si}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V3120bReport(
        bootstrap_seed_count=len(
            BOOTSTRAP_SEEDS,
        ),
        threshold_mean=tm,
        threshold_ci=ci,
        threshold_drift=td,
        seed_invariance=si,
        bootstrap_draws=tuple(
            d.to_dict() for d in draws
        ),
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_pre_t10_bootstrap_artifact(
) -> dict[str, object]:
    draws = all_bootstrap_draws()
    return {
        "schema_version":
            "v3_120b_pre_t10_bootstrap",
        "bootstrap_seed_count":
            len(BOOTSTRAP_SEEDS),
        "threshold_mean": threshold_mean(),
        "threshold_ci":
            list(threshold_ci()),
        "threshold_drift":
            threshold_drift(),
        "seed_invariance":
            seed_invariance(),
        "bootstrap_draws": [
            d.to_dict() for d in draws
        ],
    }


__all__ = [
    "DRIFT_CEILING",
    "V3120bReport",
    "build_pre_t10_bootstrap_artifact",
    "build_report",
]
