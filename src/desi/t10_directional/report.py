"""v3.104b — directional gate simulation report.

Pflichtmetriken (directive § v3.104b):

* ``old_gate_result``
* ``directional_gate_result``
* ``false_block_rate``
* ``false_pass_rate``
* ``replay_stability``

Killerfrage: "Blockiert das neue Gate nur echten
Schaden?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .gate import (
    GateInput, GateResult,
    directional_gate, old_gate,
)
from .simulate import (
    ScenarioKind,
    all_scenario_outcomes,
    false_block_rate,
    false_pass_rate,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V3104bReport:
    scenario_count: int
    old_gate_result_on_actual: dict
    directional_gate_result_on_actual: dict
    false_block_rate_old: float
    false_block_rate_directional: float
    false_pass_rate_old: float
    false_pass_rate_directional: float
    scenario_outcomes: tuple[dict, ...]
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "scenario_count":
                self.scenario_count,
            "old_gate_result_on_actual":
                self.old_gate_result_on_actual,
            "directional_gate_result_on_actual":
                self
                .directional_gate_result_on_actual,
            "false_block_rate_old":
                self.false_block_rate_old,
            "false_block_rate_directional":
                self
                .false_block_rate_directional,
            "false_pass_rate_old":
                self.false_pass_rate_old,
            "false_pass_rate_directional":
                self
                .false_pass_rate_directional,
            "scenario_outcomes":
                list(self.scenario_outcomes),
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
        false_block_rate(False),
        false_block_rate(True),
        false_pass_rate(False),
        false_pass_rate(True),
    )
    b = (
        false_block_rate(False),
        false_block_rate(True),
        false_pass_rate(False),
        false_pass_rate(True),
    )
    return 1.0 if a == b else 0.0


def build_report() -> V3104bReport:
    outs = all_scenario_outcomes()
    actual = next(
        o for o in outs
        if o.scenario
        == ScenarioKind.ACTUAL_T10.value
    )
    fbr_old = false_block_rate(False)
    fbr_dir = false_block_rate(True)
    fpr_old = false_pass_rate(False)
    fpr_dir = false_pass_rate(True)
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif fbr_dir == 0.0 and fpr_dir == 0.0:
        verdict = (
            "DIRECTIONAL_GATE_DOMINANT"
        )
    elif fbr_dir < fbr_old and fpr_dir == 0.0:
        verdict = (
            "DIRECTIONAL_GATE_IMPROVES"
        )
    else:
        verdict = (
            "DIRECTIONAL_GATE_INCONCLUSIVE"
        )

    rationale = (
        f"INFO: scenario_count {len(outs)}",
        f"INFO: old_gate on actual = "
        f"{actual.old_gate}",
        f"INFO: directional_gate on actual = "
        f"{actual.directional_gate}",
        f"INFO: false_block_rate_old {fbr_old}",
        f"INFO: false_block_rate_directional "
        f"{fbr_dir}",
        f"INFO: false_pass_rate_old {fpr_old}",
        f"INFO: false_pass_rate_directional "
        f"{fpr_dir}",
        f"INFO: scenario_outcomes "
        f"{[o.to_dict() for o in outs]}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V3104bReport(
        scenario_count=len(outs),
        old_gate_result_on_actual=actual.old_gate,
        directional_gate_result_on_actual=(
            actual.directional_gate
        ),
        false_block_rate_old=fbr_old,
        false_block_rate_directional=fbr_dir,
        false_pass_rate_old=fpr_old,
        false_pass_rate_directional=fpr_dir,
        scenario_outcomes=tuple(
            o.to_dict() for o in outs
        ),
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_t10_directional_gate_artifact(
) -> dict[str, object]:
    outs = all_scenario_outcomes()
    return {
        "schema_version":
            "v3_104b_t10_directional_gate",
        "scenario_count": len(outs),
        "scenarios": [
            o.to_dict() for o in outs
        ],
        "false_block_rate_old":
            false_block_rate(False),
        "false_block_rate_directional":
            false_block_rate(True),
        "false_pass_rate_old":
            false_pass_rate(False),
        "false_pass_rate_directional":
            false_pass_rate(True),
    }


__all__ = [
    "V3104bReport",
    "build_report",
    "build_t10_directional_gate_artifact",
]
