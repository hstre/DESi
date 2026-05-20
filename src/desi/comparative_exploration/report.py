"""v21.0 - Comparative Exploration Governance report.

Pflichtmetriken (directive § v21.0):

* delta_novelty_gain
* delta_exploration_diversity
* delta_redundancy_reduction
* delta_hallucination_pressure
* delta_authority_drift
* delta_replay_stability
* paper_readiness_score

Killerfrage: "Liefert Dual-Agent-Exploration gegenueber
DESi-alone einen echten epistemischen Mehrwert?"

Concept gate (dual-agent is better iff): delta_novelty_gain
> 0, delta_exploration_diversity > 0,
delta_hallucination_pressure <= 0.10, delta_authority_drift
<= 0.05, delta_replay_stability == 0, paper_readiness_score
>= 0.80.

Thesis on pass: "Controlled wild exploration improves
ICRL-governed exploration without breaking epistemic
safety."
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .comparison import (
    comparison_table, delta_authority_drift,
    delta_exploration_diversity, delta_hallucination_pressure,
    delta_novelty_gain, delta_redundancy_reduction,
    delta_replay_stability, desi_alone, dual_agent,
    productivity_gain,
)
from .paper_readiness import (
    paper_readiness_score, readiness_checklist,
)

VERDICT_DUAL_BETTER = "DUAL_AGENT_ADDS_EPISTEMIC_VALUE"
VERDICT_NO_GAIN = "DUAL_AGENT_NO_CLEAR_GAIN"
VERDICT_HALT = "REPLAY_DRIFT_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_DUAL_BETTER, VERDICT_NO_GAIN, VERDICT_HALT,
)

THESIS = (
    "Controlled wild exploration improves ICRL-governed "
    "exploration without breaking epistemic safety."
)

_HALLUCINATION_CEILING = 0.10
_AUTHORITY_CEILING = 0.05
_PAPER_FLOOR = 0.80


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class GateCondition:
    name: str
    value: float
    threshold: float
    comparator: str
    passed: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "value": self.value,
            "threshold": self.threshold,
            "comparator": self.comparator,
            "passed": self.passed,
        }


def gate_conditions() -> tuple[GateCondition, ...]:
    dng = delta_novelty_gain()
    ded = delta_exploration_diversity()
    dhp = delta_hallucination_pressure()
    dad = delta_authority_drift()
    drs = delta_replay_stability()
    prs = paper_readiness_score()
    raw = [
        ("delta_novelty_gain", dng, 0.0, ">", dng > 0.0),
        ("delta_exploration_diversity", ded, 0.0, ">", ded > 0.0),
        (
            "delta_hallucination_pressure", dhp,
            _HALLUCINATION_CEILING, "<=",
            dhp <= _HALLUCINATION_CEILING,
        ),
        (
            "delta_authority_drift", dad, _AUTHORITY_CEILING,
            "<=", dad <= _AUTHORITY_CEILING,
        ),
        (
            "delta_replay_stability", drs, 0.0, "==", drs == 0.0,
        ),
        (
            "paper_readiness_score", prs, _PAPER_FLOOR, ">=",
            prs >= _PAPER_FLOOR,
        ),
    ]
    return tuple(
        GateCondition(
            name=n, value=_round(v), threshold=t,
            comparator=c, passed=p,
        )
        for (n, v, t, c, p) in raw
    )


def gate_passes_all() -> bool:
    return all(c.passed for c in gate_conditions())


def gate_failing_conditions() -> tuple[str, ...]:
    return tuple(
        c.name for c in gate_conditions() if not c.passed
    )


def _replay_stability() -> float:
    # both phases are replay-exact and this layer only reads
    # them; verify the comparison is itself deterministic.
    a = comparison_table()
    b = comparison_table()
    desi_replay = desi_alone()["replay_stability"]
    dual_replay = dual_agent()["replay_stability"]
    if desi_replay < 1.0 or dual_replay < 1.0:
        return 0.0
    return 1.0 if a == b else 0.0


@dataclass(frozen=True)
class V210Report:
    delta_novelty_gain: float
    delta_exploration_diversity: float
    delta_redundancy_reduction: float
    delta_hallucination_pressure: float
    delta_authority_drift: float
    delta_replay_stability: float
    paper_readiness_score: float
    productivity_gain: float
    gate_conditions: tuple[dict, ...]
    gate_passes_all: bool
    gate_failing_conditions: tuple[str, ...]
    thesis: str
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "delta_novelty_gain": self.delta_novelty_gain,
            "delta_exploration_diversity":
                self.delta_exploration_diversity,
            "delta_redundancy_reduction":
                self.delta_redundancy_reduction,
            "delta_hallucination_pressure":
                self.delta_hallucination_pressure,
            "delta_authority_drift": self.delta_authority_drift,
            "delta_replay_stability":
                self.delta_replay_stability,
            "paper_readiness_score": self.paper_readiness_score,
            "productivity_gain": self.productivity_gain,
            "gate_conditions": list(self.gate_conditions),
            "gate_passes_all": self.gate_passes_all,
            "gate_failing_conditions":
                list(self.gate_failing_conditions),
            "thesis": self.thesis,
            "replay_stability": self.replay_stability,
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def _recommendation(*, replay: float, passes: bool) -> str:
    if replay < 1.0:
        return VERDICT_HALT
    return VERDICT_DUAL_BETTER if passes else VERDICT_NO_GAIN


def build_report() -> V210Report:
    conds = gate_conditions()
    passes = gate_passes_all()
    failing = gate_failing_conditions()
    replay = _replay_stability()
    halt = replay < 1.0
    verdict = _recommendation(replay=replay, passes=passes)
    rationale = (
        "INFO: compares v19 (DESi-alone ICRL governance) with "
        "v20 (DESi + Wild Explorer); numbers read directly "
        "from both phases' modules",
        "INFO: DESi-alone has no Wild Explorer, so contributes "
        "no wild-driven novelty and no hallucination pressure "
        "by construction",
        f"INFO: productivity_gain {productivity_gain()} "
        f"(dual-agent reaches more distinct states than "
        f"DESi-alone)",
        *[
            f"{'PASS' if c.passed else 'FAIL'}: "
            f"{c.name} {c.value} {c.comparator} {c.threshold}"
            for c in conds
        ],
        f"INFO: gate_passes_all {passes}",
        f"INFO: Killerfrage answer "
        f"{'JA' if passes else 'OFFEN'}: dual-agent "
        f"exploration delivers real epistemic value over "
        f"DESi-alone",
        f"INFO: thesis -> {THESIS}" if passes else (
            "INFO: thesis not yet established"
        ),
    )
    return V210Report(
        delta_novelty_gain=delta_novelty_gain(),
        delta_exploration_diversity=delta_exploration_diversity(),
        delta_redundancy_reduction=delta_redundancy_reduction(),
        delta_hallucination_pressure=(
            delta_hallucination_pressure()
        ),
        delta_authority_drift=delta_authority_drift(),
        delta_replay_stability=delta_replay_stability(),
        paper_readiness_score=paper_readiness_score(),
        productivity_gain=productivity_gain(),
        gate_conditions=tuple(c.to_dict() for c in conds),
        gate_passes_all=passes,
        gate_failing_conditions=failing,
        thesis=THESIS if passes else "",
        replay_stability=replay,
        halt=halt,
        recommendation=verdict,
        rationale=rationale,
    )


def build_comparison_artifact() -> dict[str, object]:
    return {
        "schema_version":
            "v21_0_comparative_exploration_governance",
        "disclaimer": (
            "Comparison of DESi-alone ICRL governance (v19) "
            "with DESi + Wild Explorer dual-agent governance "
            "(v20). Numbers are read directly from both "
            "phases' modules. No RL is replaced, no reward "
            "injected, no optimal strategy claimed. The thesis "
            "is an empirical claim on this synthetic corpus, "
            "not an AGI or world-model claim. Replay-exact."
        ),
        "report_verdicts": list(REPORT_VERDICTS),
        "desi_alone": desi_alone(),
        "dual_agent": dual_agent(),
        "comparison_table": comparison_table(),
        "readiness_checklist": readiness_checklist(),
        "delta_novelty_gain": delta_novelty_gain(),
        "delta_exploration_diversity":
            delta_exploration_diversity(),
        "delta_redundancy_reduction":
            delta_redundancy_reduction(),
        "delta_hallucination_pressure":
            delta_hallucination_pressure(),
        "delta_authority_drift": delta_authority_drift(),
        "delta_replay_stability": delta_replay_stability(),
        "paper_readiness_score": paper_readiness_score(),
        "productivity_gain": productivity_gain(),
        "gate_passes_all": gate_passes_all(),
        "thesis": THESIS if gate_passes_all() else "",
        "recommendation": build_report().recommendation,
    }


__all__ = [
    "REPORT_VERDICTS",
    "THESIS",
    "VERDICT_DUAL_BETTER",
    "VERDICT_HALT",
    "VERDICT_NO_GAIN",
    "GateCondition",
    "V210Report",
    "build_comparison_artifact",
    "build_report",
    "gate_conditions",
    "gate_failing_conditions",
    "gate_passes_all",
]
