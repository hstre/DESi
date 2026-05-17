"""v3.60 — crossed content/method resonance report.

Pflichtmetriken (directive § v3.60):

* ``resonance_by_condition``
* ``interaction_effect``
* ``crossed_transfer_rate``
* ``best_explanation_model``
* ``replay_stability``
"""
from __future__ import annotations

from dataclasses import dataclass
import json

from ..content_method.report import (
    build_report as v357_report,
)
from .conditions import (
    CROSSED_PROBE_RADIUS, ConditionResult,
    CrossedCondition, best_explanation_model,
    interaction_effect, per_condition_results,
)
from .transfer import (
    corpus_resonance_by_condition,
    crossed_transfer_rate, eligible_corpora,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V360Report:
    probe_radius: float
    condition_results: tuple[dict, ...]
    resonance_by_condition: dict[str, int]
    per_corpus_resonance: dict[str, dict[str, int]]
    interaction_effect: float
    crossed_transfer_rate: float
    best_explanation_model: str
    eligible_corpora: tuple[str, ...]
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "probe_radius": self.probe_radius,
            "condition_results":
                list(self.condition_results),
            "resonance_by_condition":
                dict(self.resonance_by_condition),
            "per_corpus_resonance": {
                c: dict(d)
                for c, d in self.per_corpus_resonance.items()
            },
            "interaction_effect":
                self.interaction_effect,
            "crossed_transfer_rate":
                self.crossed_transfer_rate,
            "best_explanation_model":
                self.best_explanation_model,
            "eligible_corpora":
                list(self.eligible_corpora),
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
    a = [r.to_dict() for r in per_condition_results()]
    b = [r.to_dict() for r in per_condition_results()]
    if not a:
        return 1.0
    matches = sum(1 for x, y in zip(a, b) if x == y)
    return _round(matches / len(a))


def build_report() -> V360Report:
    results = per_condition_results()
    resonance = {
        r.condition: r.resonant_pair_count
        for r in results
    }
    eligible = eligible_corpora()
    per_corpus = {
        c: corpus_resonance_by_condition(c)
        for c in eligible
    }
    interaction = interaction_effect(results)
    best = best_explanation_model(results)
    rate = crossed_transfer_rate()
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif rate > 0:
        verdict = "CROSSED_RESONANCE_TRANSFERS"
    elif any(v > 0 for v in resonance.values()):
        verdict = "CROSSED_RESONANCE_GLOBAL_ONLY"
    else:
        verdict = "CROSSED_RESONANCE_FALSIFIED"

    rationale = (
        f"INFO: probe_radius {CROSSED_PROBE_RADIUS}",
        f"INFO: resonance_by_condition "
        f"{sorted(resonance.items())}",
        f"INFO: per-corpus resonance "
        f"{[(c, dict(d)) for c, d in per_corpus.items()]}",
        f"INFO: interaction_effect {interaction} "
        f"(positive = method-matching contributes "
        f"more than content-matching)",
        f"INFO: best_explanation_model {best}",
        f"{'PASS' if rate > 0 else 'FAIL'}: "
        f"crossed_transfer_rate {rate} > 0",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V360Report(
        probe_radius=CROSSED_PROBE_RADIUS,
        condition_results=tuple(
            r.to_dict() for r in results
        ),
        resonance_by_condition=resonance,
        per_corpus_resonance=per_corpus,
        interaction_effect=interaction,
        crossed_transfer_rate=rate,
        best_explanation_model=best,
        eligible_corpora=eligible,
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_crossed_resonance_artifact(
) -> dict[str, object]:
    results = per_condition_results()
    eligible = eligible_corpora()
    return {
        "schema_version":
            "v3_60_crossed_resonance",
        "probe_radius": CROSSED_PROBE_RADIUS,
        "condition_results": [
            r.to_dict() for r in results
        ],
        "per_corpus_resonance": {
            c: corpus_resonance_by_condition(c)
            for c in eligible
        },
        "eligible_corpora": list(eligible),
    }


__all__ = [
    "V360Report", "build_crossed_resonance_artifact",
    "build_report",
]
