"""v3.100 — compression vs information loss
report.

Pflichtmetriken (directive § v3.100):

* ``compression_gain``
* ``information_loss``
* ``reasoning_delta``
* ``predictive_delta``
* ``failure_class_delta``
* ``replay_stability``

Concept Gate conditions #4 (information_loss <=
0.10) and #5 (predictive_delta <= 0.10).
Killerfrage: "Ist Degeneracy effiziente Kompression
- oder blinder Informationsverlust?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from ..entangled.variance import (
    ENTANGLED_FAMILY_IDS,
)
from .compression import (
    collapsed_anchor_count,
    compression_gain,
    dim_a, dim_b,
    distinct_point_count_a,
    distinct_point_count_b,
)
from .loss import (
    downstream_diversity_a,
    downstream_diversity_b,
    downstream_failure_class_set_b,
    downstream_intervention_set_b,
    downstream_verdict_set_b,
    failure_class_delta,
    information_loss,
    predictive_delta,
    reasoning_delta,
)


INFORMATION_LOSS_THRESHOLD: float = 0.10
PREDICTIVE_DELTA_THRESHOLD: float = 0.10


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V3100Report:
    entangled_family_ids: tuple[str, ...]
    dim_a: int
    dim_b: int
    distinct_point_count_a: int
    distinct_point_count_b: int
    collapsed_anchor_count: int
    compression_gain: float
    information_loss: float
    reasoning_delta: float
    predictive_delta: float
    failure_class_delta: float
    downstream_diversity_a: dict[str, int]
    downstream_diversity_b: dict[str, int]
    downstream_verdict_set_b: tuple[str, ...]
    downstream_intervention_set_b: tuple[str, ...]
    downstream_failure_class_set_b: tuple[str, ...]
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "entangled_family_ids":
                list(self.entangled_family_ids),
            "dim_a": self.dim_a,
            "dim_b": self.dim_b,
            "distinct_point_count_a":
                self.distinct_point_count_a,
            "distinct_point_count_b":
                self.distinct_point_count_b,
            "collapsed_anchor_count":
                self.collapsed_anchor_count,
            "compression_gain":
                self.compression_gain,
            "information_loss":
                self.information_loss,
            "reasoning_delta":
                self.reasoning_delta,
            "predictive_delta":
                self.predictive_delta,
            "failure_class_delta":
                self.failure_class_delta,
            "downstream_diversity_a":
                self.downstream_diversity_a,
            "downstream_diversity_b":
                self.downstream_diversity_b,
            "downstream_verdict_set_b":
                list(self.downstream_verdict_set_b),
            "downstream_intervention_set_b":
                list(
                    self.downstream_intervention_set_b,
                ),
            "downstream_failure_class_set_b":
                list(
                    self
                    .downstream_failure_class_set_b,
                ),
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
        compression_gain(),
        information_loss(),
        reasoning_delta(),
        predictive_delta(),
        failure_class_delta(),
    )
    b = (
        compression_gain(),
        information_loss(),
        reasoning_delta(),
        predictive_delta(),
        failure_class_delta(),
    )
    return 1.0 if a == b else 0.0


def build_report() -> V3100Report:
    cg = compression_gain()
    il = information_loss()
    rd = reasoning_delta()
    pd = predictive_delta()
    fcd = failure_class_delta()
    da = downstream_diversity_a()
    db = downstream_diversity_b()
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif (
        il <= INFORMATION_LOSS_THRESHOLD
        and pd <= PREDICTIVE_DELTA_THRESHOLD
    ):
        verdict = "USEFUL_COMPRESSION"
    elif il <= INFORMATION_LOSS_THRESHOLD:
        verdict = "COMPRESSION_WITH_PREDICTIVE_COST"
    elif pd <= PREDICTIVE_DELTA_THRESHOLD:
        verdict = "COMPRESSION_WITH_INFORMATION_LOSS"
    else:
        verdict = "BLIND_INFORMATION_LOSS"

    rationale = (
        f"INFO: entangled_family_ids "
        f"{list(ENTANGLED_FAMILY_IDS)}",
        f"INFO: dim_a {dim_a()} dim_b {dim_b()}",
        f"INFO: distinct_point_count_a "
        f"{distinct_point_count_a()}",
        f"INFO: distinct_point_count_b "
        f"{distinct_point_count_b()}",
        f"INFO: collapsed_anchor_count "
        f"{collapsed_anchor_count()}",
        f"INFO: compression_gain {cg}",
        f"{'PASS' if il <= INFORMATION_LOSS_THRESHOLD else 'FAIL'}: "
        f"information_loss {il} "
        f"(threshold "
        f"{INFORMATION_LOSS_THRESHOLD})",
        f"INFO: reasoning_delta {rd}",
        f"{'PASS' if pd <= PREDICTIVE_DELTA_THRESHOLD else 'FAIL'}: "
        f"predictive_delta {pd} "
        f"(threshold "
        f"{PREDICTIVE_DELTA_THRESHOLD})",
        f"INFO: failure_class_delta {fcd}",
        f"INFO: downstream_diversity_a {da}",
        f"INFO: downstream_diversity_b {db}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V3100Report(
        entangled_family_ids=ENTANGLED_FAMILY_IDS,
        dim_a=dim_a(),
        dim_b=dim_b(),
        distinct_point_count_a=(
            distinct_point_count_a()
        ),
        distinct_point_count_b=(
            distinct_point_count_b()
        ),
        collapsed_anchor_count=(
            collapsed_anchor_count()
        ),
        compression_gain=cg,
        information_loss=il,
        reasoning_delta=rd,
        predictive_delta=pd,
        failure_class_delta=fcd,
        downstream_diversity_a=da,
        downstream_diversity_b=db,
        downstream_verdict_set_b=(
            downstream_verdict_set_b()
        ),
        downstream_intervention_set_b=(
            downstream_intervention_set_b()
        ),
        downstream_failure_class_set_b=(
            downstream_failure_class_set_b()
        ),
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_compression_vs_information_loss_artifact(
) -> dict[str, object]:
    return {
        "schema_version":
            "v3_100_compression_vs_information_loss",
        "entangled_family_ids":
            list(ENTANGLED_FAMILY_IDS),
        "dim_a": dim_a(),
        "dim_b": dim_b(),
        "distinct_point_count_a":
            distinct_point_count_a(),
        "distinct_point_count_b":
            distinct_point_count_b(),
        "collapsed_anchor_count":
            collapsed_anchor_count(),
        "compression_gain":
            compression_gain(),
        "information_loss":
            information_loss(),
        "reasoning_delta":
            reasoning_delta(),
        "predictive_delta":
            predictive_delta(),
        "failure_class_delta":
            failure_class_delta(),
        "downstream_diversity_a":
            downstream_diversity_a(),
        "downstream_diversity_b":
            downstream_diversity_b(),
        "downstream_verdict_set_b":
            list(downstream_verdict_set_b()),
        "downstream_intervention_set_b":
            list(
                downstream_intervention_set_b(),
            ),
        "downstream_failure_class_set_b":
            list(
                downstream_failure_class_set_b(),
            ),
    }


__all__ = [
    "INFORMATION_LOSS_THRESHOLD",
    "PREDICTIVE_DELTA_THRESHOLD",
    "V3100Report",
    "build_compression_vs_information_loss_artifact",
    "build_report",
]
