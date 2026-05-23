"""v3.99 — counterfactual divergence report.

Pflichtmetriken (directive § v3.99):

* ``perturbation_divergence``
* ``separation_rate``
* ``coupling_stability``
* ``chaos_threshold``
* ``replay_stability``

Concept Gate condition #3: separation_rate <
0.20. Killerfrage: "Sind es stabile Doppelgaenger
- oder nur im Gleichgewicht?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from ..entangled.variance import (
    ENTANGLED_FAMILY_IDS,
)
from .counterfactual import (
    NO_CHAOS_SENTINEL,
    SEPARATION_THRESHOLD,
    all_perturbation_outcomes,
    baseline_auc,
    chaos_threshold,
    coupling_stability,
    perturbation_divergence,
    separation_rate,
)
from .perturb import (
    MAGNITUDE_GRID, PERTURBATION_KINDS,
)


SEPARATION_RATE_THRESHOLD: float = 0.20


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V399Report:
    entangled_family_ids: tuple[str, ...]
    perturbation_kinds: tuple[str, ...]
    magnitude_grid: tuple[float, ...]
    cell_count: int
    baseline_auc: float
    perturbation_divergence: float
    separation_rate: float
    coupling_stability: float
    chaos_threshold: float
    perturbation_outcomes: tuple[dict, ...]
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "entangled_family_ids":
                list(self.entangled_family_ids),
            "perturbation_kinds":
                list(self.perturbation_kinds),
            "magnitude_grid":
                list(self.magnitude_grid),
            "cell_count": self.cell_count,
            "baseline_auc": self.baseline_auc,
            "perturbation_divergence":
                self.perturbation_divergence,
            "separation_rate":
                self.separation_rate,
            "coupling_stability":
                self.coupling_stability,
            "chaos_threshold":
                self.chaos_threshold,
            "perturbation_outcomes":
                list(self.perturbation_outcomes),
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
        baseline_auc(),
        perturbation_divergence(),
        separation_rate(),
        chaos_threshold(),
    )
    b = (
        baseline_auc(),
        perturbation_divergence(),
        separation_rate(),
        chaos_threshold(),
    )
    return 1.0 if a == b else 0.0


def build_report() -> V399Report:
    base = baseline_auc()
    pd = perturbation_divergence()
    sr = separation_rate()
    cs = coupling_stability()
    ct = chaos_threshold()
    outs = all_perturbation_outcomes()
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif sr < SEPARATION_RATE_THRESHOLD:
        verdict = "DOPPELGAENGER_STABLE"
    elif ct != NO_CHAOS_SENTINEL:
        verdict = "DOPPELGAENGER_FRAGILE"
    else:
        verdict = "DOPPELGAENGER_INCONCLUSIVE"

    rationale = (
        f"INFO: entangled_family_ids "
        f"{list(ENTANGLED_FAMILY_IDS)}",
        f"INFO: perturbation_kinds "
        f"{list(PERTURBATION_KINDS)}",
        f"INFO: magnitude_grid "
        f"{list(MAGNITUDE_GRID)}",
        f"INFO: cell_count {len(outs)}",
        f"INFO: baseline_auc {base}",
        f"INFO: perturbation_divergence {pd}",
        f"{'PASS' if sr < SEPARATION_RATE_THRESHOLD else 'FAIL'}: "
        f"separation_rate {sr} "
        f"(threshold "
        f"{SEPARATION_RATE_THRESHOLD})",
        f"INFO: coupling_stability {cs}",
        f"INFO: chaos_threshold {ct} "
        f"({'no threshold' if ct == NO_CHAOS_SENTINEL else 'magnitude'})",
        f"INFO: perturbation_outcomes "
        f"{[o.to_dict() for o in outs]}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V399Report(
        entangled_family_ids=ENTANGLED_FAMILY_IDS,
        perturbation_kinds=PERTURBATION_KINDS,
        magnitude_grid=MAGNITUDE_GRID,
        cell_count=len(outs),
        baseline_auc=base,
        perturbation_divergence=pd,
        separation_rate=sr,
        coupling_stability=cs,
        chaos_threshold=ct,
        perturbation_outcomes=tuple(
            o.to_dict() for o in outs
        ),
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_counterfactual_divergence_artifact(
) -> dict[str, object]:
    outs = all_perturbation_outcomes()
    return {
        "schema_version":
            "v3_99_counterfactual_divergence",
        "entangled_family_ids":
            list(ENTANGLED_FAMILY_IDS),
        "perturbation_kinds":
            list(PERTURBATION_KINDS),
        "magnitude_grid":
            list(MAGNITUDE_GRID),
        "baseline_auc": baseline_auc(),
        "perturbation_divergence":
            perturbation_divergence(),
        "separation_rate": separation_rate(),
        "coupling_stability":
            coupling_stability(),
        "chaos_threshold": chaos_threshold(),
        "perturbation_outcomes": [
            o.to_dict() for o in outs
        ],
    }


__all__ = [
    "SEPARATION_RATE_THRESHOLD",
    "V399Report",
    "build_counterfactual_divergence_artifact",
    "build_report",
]
