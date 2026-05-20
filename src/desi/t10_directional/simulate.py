"""v3.104b — gate behaviour under realistic and
synthetic scenarios.

Three closed scenarios:

* ``ACTUAL_T10``         - the live numbers from
  v3.101-v3.104.
* ``SYNTHETIC_ADVERSE``  - same as ACTUAL_T10
  but with an injected ADVERSE flip (purity 0.9
  -> 0.5 on a previously passing sprint). Both
  gates SHOULD block this.
* ``SYNTHETIC_BENEFICIAL_ONLY`` - same as
  ACTUAL_T10 but with one extra beneficial flip
  and no adverse flips. The old gate may block
  it; the directional gate should not.

False-block rate = fraction of scenarios where
gate blocks but adverse_flip_count == 0 and
adverse_auc_delta <= 0.05 (i.e. nothing is
actually broken).

False-pass rate = fraction of scenarios where
gate passes but adverse_flip_count > 0 or
adverse_auc_delta > 0.05.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from functools import lru_cache

from ..t10_compat.replay import (
    historical_auc_delta as v3103_historical_delta,
)
from ..t10_gate.delta import (
    adverse_auc_delta as v3104a_adverse_auc,
    adverse_flip_count as v3104a_adverse_flips,
    beneficial_auc_delta as v3104a_ben_auc,
    beneficial_flip_count as v3104a_ben_flips,
)
from .gate import (
    GateInput, GateResult,
    directional_gate, old_gate,
)


class ScenarioKind(str, Enum):
    ACTUAL_T10                  = "actual_t10"
    SYNTHETIC_ADVERSE           = "synthetic_adverse"
    SYNTHETIC_BENEFICIAL_ONLY   = (
        "synthetic_beneficial_only"
    )


@lru_cache(maxsize=1)
def _actual_t10_input() -> GateInput:
    return GateInput(
        candidate_auc=1.0,
        injected_purity=1.0,
        injected_auc=1.0,
        adverse_flip_count=v3104a_adverse_flips(),
        beneficial_flip_count=v3104a_ben_flips(),
        adverse_auc_delta=v3104a_adverse_auc(),
        beneficial_auc_delta=v3104a_ben_auc(),
        historical_auc_delta=(
            v3103_historical_delta()
        ),
        replay_stability=1.0,
    )


@lru_cache(maxsize=1)
def _synthetic_adverse_input() -> GateInput:
    base = _actual_t10_input()
    return GateInput(
        candidate_auc=base.candidate_auc,
        injected_purity=base.injected_purity,
        injected_auc=base.injected_auc,
        adverse_flip_count=1,
        beneficial_flip_count=(
            base.beneficial_flip_count
        ),
        adverse_auc_delta=0.40,
        beneficial_auc_delta=(
            base.beneficial_auc_delta
        ),
        historical_auc_delta=max(
            base.historical_auc_delta, 0.40,
        ),
        replay_stability=base.replay_stability,
    )


@lru_cache(maxsize=1)
def _synthetic_beneficial_only_input() -> GateInput:
    base = _actual_t10_input()
    return GateInput(
        candidate_auc=base.candidate_auc,
        injected_purity=base.injected_purity,
        injected_auc=base.injected_auc,
        adverse_flip_count=0,
        beneficial_flip_count=(
            base.beneficial_flip_count + 1
        ),
        adverse_auc_delta=0.0,
        beneficial_auc_delta=max(
            base.beneficial_auc_delta, 0.60,
        ),
        historical_auc_delta=max(
            base.historical_auc_delta, 0.60,
        ),
        replay_stability=base.replay_stability,
    )


_SCENARIO_INPUTS: dict[str, "callable"] = {
    ScenarioKind.ACTUAL_T10.value:
        _actual_t10_input,
    ScenarioKind.SYNTHETIC_ADVERSE.value:
        _synthetic_adverse_input,
    ScenarioKind.SYNTHETIC_BENEFICIAL_ONLY.value:
        _synthetic_beneficial_only_input,
}


@dataclass(frozen=True)
class ScenarioOutcome:
    scenario: str
    gate_input: dict
    old_gate: dict
    directional_gate: dict
    real_damage: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "scenario": self.scenario,
            "gate_input": self.gate_input,
            "old_gate": self.old_gate,
            "directional_gate":
                self.directional_gate,
            "real_damage": self.real_damage,
        }


def _real_damage(g: GateInput) -> bool:
    return (
        g.adverse_flip_count > 0
        or g.adverse_auc_delta > 0.05
    )


@lru_cache(maxsize=1)
def all_scenario_outcomes() -> tuple[
    ScenarioOutcome, ...,
]:
    out: list[ScenarioOutcome] = []
    for kind in ScenarioKind:
        gi = _SCENARIO_INPUTS[kind.value]()
        out.append(ScenarioOutcome(
            scenario=kind.value,
            gate_input=gi.to_dict(),
            old_gate=old_gate(gi).to_dict(),
            directional_gate=(
                directional_gate(gi).to_dict()
            ),
            real_damage=_real_damage(gi),
        ))
    return tuple(out)


def false_block_rate(use_directional: bool) -> float:
    """Rate of scenarios the gate blocks even
    though no real damage occurred."""
    outs = all_scenario_outcomes()
    total = len(outs)
    if total == 0:
        return 0.0
    false_blocks = 0
    for o in outs:
        if o.real_damage:
            continue
        result = (
            o.directional_gate
            if use_directional
            else o.old_gate
        )
        if not result["passed"]:
            false_blocks += 1
    return round(false_blocks / total, 6)


def false_pass_rate(use_directional: bool) -> float:
    """Rate of scenarios the gate passes even
    though real damage occurred."""
    outs = all_scenario_outcomes()
    total = len(outs)
    if total == 0:
        return 0.0
    false_passes = 0
    for o in outs:
        if not o.real_damage:
            continue
        result = (
            o.directional_gate
            if use_directional
            else o.old_gate
        )
        if result["passed"]:
            false_passes += 1
    return round(false_passes / total, 6)


__all__ = [
    "ScenarioKind",
    "ScenarioOutcome",
    "all_scenario_outcomes",
    "false_block_rate",
    "false_pass_rate",
]
