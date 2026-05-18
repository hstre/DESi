"""v3.124 — pre-T10 v2 go/no-go report.

Pflichtmetriken (directive § v3.124):

* ``best_strategy``
* ``false_activation_rate``
* ``true_case_recall``
* ``architecture_roi``
* ``replay_stability``

Killerfrage: "Welche Pre-T10 Variante geht in
Produktion - oder gar keine?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .decision import (
    STRATEGIES, all_strategy_metrics,
    best_strategy, disqualified_strategies,
    metrics_multi_signal, metrics_no_precheck,
    metrics_single_threshold,
)


_FAR_CEILING: float = 0.10
_TPR_FLOOR: float = 1.0


@dataclass(frozen=True)
class V3124Report:
    best_strategy: str
    false_activation_rate: float
    true_case_recall: float
    architecture_roi: float
    rule_complexity: int
    disqualified: tuple[str, ...]
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "best_strategy": self.best_strategy,
            "false_activation_rate":
                self.false_activation_rate,
            "true_case_recall":
                self.true_case_recall,
            "architecture_roi":
                self.architecture_roi,
            "rule_complexity":
                self.rule_complexity,
            "disqualified":
                list(self.disqualified),
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
    a = tuple(
        m.to_dict() for m in
        all_strategy_metrics()
    )
    b = tuple(
        m.to_dict() for m in
        all_strategy_metrics()
    )
    if a != b:
        return 0.0
    if best_strategy() != best_strategy():
        return 0.0
    return 1.0


def _metrics_for(name: str):
    if name == "no_precheck":
        return metrics_no_precheck()
    if name == "single_threshold":
        return metrics_single_threshold()
    if name == "multi_signal":
        return metrics_multi_signal()
    return None


def _recommendation(
    chosen: str, replay: float,
) -> str:
    if replay < 1.0:
        return "HALT_REPLAY_DRIFT"
    if chosen == "BEST_STRATEGY_NONE":
        return "DEPLOY_NONE"
    if chosen == "multi_signal":
        return "DEPLOY_MULTI_SIGNAL"
    if chosen == "single_threshold":
        return "DEPLOY_SINGLE_THRESHOLD"
    return "DEPLOY_NO_PRECHECK"


def build_report() -> V3124Report:
    chosen = best_strategy()
    chosen_m = _metrics_for(chosen)
    replay = _replay_stability()
    disq = disqualified_strategies()
    halt = replay < 1.0

    if chosen_m is None:
        far = 1.0
        tpr = 0.0
        roi = 0.0
        complexity = 0
    else:
        far = chosen_m.false_activation_rate
        tpr = chosen_m.true_case_recall
        roi = chosen_m.architecture_roi
        complexity = chosen_m.rule_complexity

    verdict = _recommendation(chosen, replay)

    lines: list[str] = []
    for m in all_strategy_metrics():
        lines.append(
            f"INFO: {m.strategy} "
            f"far={m.false_activation_rate} "
            f"tpr={m.true_case_recall} "
            f"complexity={m.rule_complexity} "
            f"roi={m.architecture_roi} "
            f"qualifies={m.qualifies}",
        )
    lines.append(
        f"INFO: best_strategy {chosen}",
    )
    lines.append(
        f"INFO: disqualified {list(disq)}",
    )
    lines.append(
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )
    rationale = tuple(lines)

    return V3124Report(
        best_strategy=chosen,
        false_activation_rate=far,
        true_case_recall=tpr,
        architecture_roi=roi,
        rule_complexity=complexity,
        disqualified=disq,
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_pre_t10_v2_go_no_go_artifact(
) -> dict[str, object]:
    return {
        "schema_version":
            "v3_124_pre_t10_v2_go_no_go",
        "strategies": list(STRATEGIES),
        "metrics": [
            m.to_dict()
            for m in all_strategy_metrics()
        ],
        "best_strategy": best_strategy(),
        "disqualified":
            list(disqualified_strategies()),
        "far_ceiling": _FAR_CEILING,
        "tpr_floor": _TPR_FLOOR,
    }


__all__ = [
    "V3124Report",
    "build_pre_t10_v2_go_no_go_artifact",
    "build_report",
]
