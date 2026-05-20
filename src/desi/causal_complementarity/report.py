"""v3.64 — causal complementarity report.

Pflichtmetriken (directive § v3.64):

* ``activation_after_ablation``
* ``causal_importance``
* ``necessary_factors``
* ``sufficient_factors``
* ``replay_stability``

Paper-11 v3 gate #5:
``at least one necessary_factor identified``.
"""
from __future__ import annotations

from dataclasses import dataclass
import json

from .ablation import (
    PROBE_RADIUS, all_pair_factors,
    baseline_pair_count, baseline_resonance,
    run_ablations,
)
from .causal import aggregate, rank_by_importance


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V364Report:
    probe_radius: float
    baseline_total: int
    baseline_resonant: int
    baseline_rate: float
    ablations: tuple[dict, ...]
    activation_after_ablation: dict[str, int]
    causal_importance: dict[str, float]
    necessary_factors: tuple[str, ...]
    sufficient_factors: tuple[str, ...]
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "probe_radius": self.probe_radius,
            "baseline_total": self.baseline_total,
            "baseline_resonant":
                self.baseline_resonant,
            "baseline_rate": self.baseline_rate,
            "ablations": list(self.ablations),
            "activation_after_ablation":
                dict(self.activation_after_ablation),
            "causal_importance":
                dict(self.causal_importance),
            "necessary_factors":
                list(self.necessary_factors),
            "sufficient_factors":
                list(self.sufficient_factors),
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
    a = [r.to_dict() for r in run_ablations()]
    b = [r.to_dict() for r in run_ablations()]
    if not a:
        return 1.0
    matches = sum(1 for x, y in zip(a, b) if x == y)
    return _round(matches / len(a))


def build_report() -> V364Report:
    total = baseline_pair_count()
    base_res = baseline_resonance()
    base_rate = (
        _round(base_res / total) if total else 0.0
    )
    results, necessary, sufficient = aggregate()
    ranked = rank_by_importance(results)
    activation = {
        r.factor: r.resonant_after for r in ranked
    }
    importance = {
        r.factor: r.causal_importance for r in ranked
    }
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif necessary:
        verdict = "NECESSARY_FACTOR_IDENTIFIED"
    else:
        verdict = "NO_NECESSARY_FACTOR"

    rationale = (
        f"INFO: probe_radius {PROBE_RADIUS}",
        f"INFO: baseline {base_res}/{total} pairs "
        f"resonant (rate {base_rate})",
        f"INFO: ablation results "
        f"{[r.to_dict() for r in ranked]}",
        f"INFO: activation_after_ablation "
        f"{sorted(activation.items())}",
        f"INFO: causal_importance "
        f"{sorted(importance.items())}",
        f"{'PASS' if necessary else 'FAIL'}: "
        f"necessary_factors {list(necessary)}",
        f"INFO: sufficient_factors "
        f"{list(sufficient)}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V364Report(
        probe_radius=PROBE_RADIUS,
        baseline_total=total,
        baseline_resonant=base_res,
        baseline_rate=base_rate,
        ablations=tuple(
            r.to_dict() for r in ranked
        ),
        activation_after_ablation=activation,
        causal_importance=importance,
        necessary_factors=necessary,
        sufficient_factors=sufficient,
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_causal_complementarity_artifact(
) -> dict[str, object]:
    return {
        "schema_version":
            "v3_64_causal_complementarity",
        "probe_radius": PROBE_RADIUS,
        "pair_factors": [
            p.to_dict() for p in all_pair_factors()
        ],
        "ablations": [
            r.to_dict() for r in run_ablations()
        ],
    }


__all__ = [
    "V364Report",
    "build_causal_complementarity_artifact",
    "build_report",
]
