"""v3.70 — counterfactual probe swap report.

Pflichtmetriken (directive § v3.70):

* ``swapped_coverage``
* ``coverage_loss``
* ``input_specificity``
* ``replay_stability``

Paper-11 historical gate #2: ``input_specificity > 0``.
"""
from __future__ import annotations

from dataclasses import dataclass
import json

from .counterfactual import (
    aggregate, mozart_baseline_score,
)
from .swap import (
    RANDOM_CONTROL_COUNT, SwapResult,
    deterministic_random_control_ids,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V370Report:
    mozart_coverage_score: float
    random_control_ids: tuple[str, ...]
    swap_results: tuple[dict, ...]
    swapped_coverage: dict[str, float]
    coverage_loss: dict[str, float]
    input_specificity: float
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "mozart_coverage_score":
                self.mozart_coverage_score,
            "random_control_ids":
                list(self.random_control_ids),
            "swap_results":
                list(self.swap_results),
            "swapped_coverage":
                dict(self.swapped_coverage),
            "coverage_loss":
                dict(self.coverage_loss),
            "input_specificity":
                self.input_specificity,
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
    a = [
        s.to_dict() for s in aggregate()[0]
    ]
    b = [
        s.to_dict() for s in aggregate()[0]
    ]
    if not a:
        return 1.0
    matches = sum(1 for x, y in zip(a, b) if x == y)
    return _round(matches / len(a))


def build_report() -> V370Report:
    swaps, mozart_score, spec = aggregate()
    swapped = {
        s.swap_id: s.coverage_score for s in swaps
    }
    losses = {
        s.swap_id: s.coverage_loss for s in swaps
    }
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif spec > 0:
        verdict = "MOZART_INPUT_SPECIFIC"
    elif spec == 0:
        verdict = "MOZART_NOT_INPUT_SPECIFIC"
    else:
        verdict = "MOZART_BELOW_CONTROLS"

    rationale = (
        f"INFO: mozart_coverage_score {mozart_score}",
        f"INFO: random_control_ids "
        f"{list(deterministic_random_control_ids())}",
        f"INFO: swapped_coverage "
        f"{sorted(swapped.items())}",
        f"INFO: coverage_loss "
        f"{sorted(losses.items())}",
        f"{'PASS' if spec > 0 else 'FAIL'}: "
        f"input_specificity {spec} > 0",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V370Report(
        mozart_coverage_score=mozart_score,
        random_control_ids=(
            deterministic_random_control_ids()
        ),
        swap_results=tuple(
            s.to_dict() for s in swaps
        ),
        swapped_coverage=swapped,
        coverage_loss=losses,
        input_specificity=spec,
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_mozart_counterfactual_artifact(
) -> dict[str, object]:
    swaps = aggregate()[0]
    return {
        "schema_version":
            "v3_70_mozart_counterfactual",
        "mozart_coverage_score":
            mozart_baseline_score(),
        "random_control_count":
            RANDOM_CONTROL_COUNT,
        "random_control_ids":
            list(deterministic_random_control_ids()),
        "swap_results":
            [s.to_dict() for s in swaps],
    }


__all__ = [
    "V370Report",
    "build_mozart_counterfactual_artifact",
    "build_report",
]
