"""v3.104a — historical delta classification.

For every gate outcome recorded by v3.103
(``HistoricalGateOutcome``) we classify the
stored → counterfactual transition into one of
four closed cells:

* ``BENEFICIAL_FLIP`` - stored=FAIL, cf=PASS.
* ``ADVERSE_FLIP``    - stored=PASS, cf=FAIL.
* ``NEUTRAL_PASS``    - stored=PASS, cf=PASS.
* ``NEUTRAL_FAIL``    - stored=FAIL, cf=FAIL.

Direction-aware gates use this taxonomy to
decide whether to block.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from functools import lru_cache

from ..t10_compat.replay import (
    HistoricalGateOutcome,
    all_historical_gate_outcomes,
)


class DeltaKind(str, Enum):
    BENEFICIAL_FLIP = "beneficial_flip"
    ADVERSE_FLIP    = "adverse_flip"
    NEUTRAL_PASS    = "neutral_pass"
    NEUTRAL_FAIL    = "neutral_fail"


def classify_outcome(
    outcome: HistoricalGateOutcome,
) -> str:
    if outcome.stored_pass and outcome.counterfactual_pass:
        return DeltaKind.NEUTRAL_PASS.value
    if (
        not outcome.stored_pass
        and not outcome.counterfactual_pass
    ):
        return DeltaKind.NEUTRAL_FAIL.value
    if (
        not outcome.stored_pass
        and outcome.counterfactual_pass
    ):
        return DeltaKind.BENEFICIAL_FLIP.value
    return DeltaKind.ADVERSE_FLIP.value


@dataclass(frozen=True)
class ClassifiedOutcome:
    sprint_id: str
    gate_metric: str
    kind: str
    stored_value: float
    counterfactual_value: float
    value_delta: float

    def to_dict(self) -> dict[str, object]:
        return {
            "sprint_id": self.sprint_id,
            "gate_metric": self.gate_metric,
            "kind": self.kind,
            "stored_value": self.stored_value,
            "counterfactual_value":
                self.counterfactual_value,
            "value_delta": self.value_delta,
        }


@lru_cache(maxsize=1)
def all_classified_outcomes() -> tuple[
    ClassifiedOutcome, ...,
]:
    return tuple(
        ClassifiedOutcome(
            sprint_id=o.sprint_id,
            gate_metric=o.gate_metric,
            kind=classify_outcome(o),
            stored_value=o.stored_value,
            counterfactual_value=(
                o.counterfactual_value
            ),
            value_delta=o.value_delta,
        )
        for o in all_historical_gate_outcomes()
    )


__all__ = [
    "ClassifiedOutcome",
    "DeltaKind",
    "all_classified_outcomes",
    "classify_outcome",
]
