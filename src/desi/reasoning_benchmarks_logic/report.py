"""v36.2 - Logic & Fallacy Benchmarks (LogiQA / ReClor) report.

Pflichtmetriken (directive § v36.2):

* logical_consistency
* fallacy_detection
* assumption_visibility
* distractor_resistance
* replay_stability

Killerfrage: "Kann DESi logische Fehler sichtbar machen, ohne falsche
Sicherheit zu erzeugen?"

Runs locally-vendored LogiQA and ReClor reference datasets through
DESi's deterministic logical-form analyzer: valid forms are judged
valid, fallacies are named, unstated assumptions are surfaced, and
distractor options are resisted. Unknown forms are never asserted
valid.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from desi.reasoning_benchmarks import (
    core_identity, core_replay_stable, governance_identity,
)
from desi.self_improvement import HUMAN_APPROVAL_REQUIRED

from .fallacy_detector import detect_fallacy, has_fallacy
from .logic_scorecard import (
    all_logic_tasks, logic_scorecards, selected_option,
)

VERDICT_PASSED = "LOGIQA_RECLOR_RUN_PASSED"
VERDICT_PARTIAL = "LOGIQA_RECLOR_RUN_PARTIAL"
VERDICT_HALT = "LOGIQA_RECLOR_RUN_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_PASSED, VERDICT_PARTIAL, VERDICT_HALT,
)

_FLOOR = 0.80


def logical_consistency() -> float:
    cards = logic_scorecards()
    if not cards:
        return 0.0
    ok = sum(1 for c in cards if c.consistent)
    return round(ok / len(cards), 6)


def fallacy_detection() -> float:
    fallacious = [t for t in all_logic_tasks() if has_fallacy(t.form)]
    if not fallacious:
        return 0.0
    ok = sum(
        1 for t in fallacious if detect_fallacy(t.form) == t.form
    )
    return round(ok / len(fallacious), 6)


def assumption_visibility() -> float:
    tasks = all_logic_tasks()
    if not tasks:
        return 0.0
    ok = sum(1 for t in tasks if t.unstated_assumptions)
    return round(ok / len(tasks), 6)


def distractor_resistance() -> float:
    tasks = all_logic_tasks()
    if not tasks:
        return 0.0
    ok = sum(
        1 for t in tasks
        if selected_option(t) != t.distractor_option
    )
    return round(ok / len(tasks), 6)


def replay_stability() -> float:
    a = [(t.task_id, detect_fallacy(t.form)) for t in all_logic_tasks()]
    b = [(t.task_id, detect_fallacy(t.form)) for t in all_logic_tasks()]
    if a != b:
        return 0.0
    return 1.0 if core_replay_stable() else 0.0


def logic_metrics() -> dict[str, float]:
    return {
        "logical_consistency": logical_consistency(),
        "fallacy_detection": fallacy_detection(),
        "assumption_visibility": assumption_visibility(),
        "distractor_resistance": distractor_resistance(),
        "replay_stability": replay_stability(),
    }


def _signature() -> str:
    m = logic_metrics()
    parts = [f"{k}={m[k]}" for k in sorted(m)]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


def _recommendation() -> str:
    m = logic_metrics()
    if m["replay_stability"] < 1.0 or governance_identity() < 1.0:
        return VERDICT_HALT
    if all(v >= _FLOOR for v in m.values()):
        return VERDICT_PASSED
    return VERDICT_PARTIAL


@dataclass(frozen=True)
class V362Report:
    task_count: int
    logical_consistency: float
    fallacy_detection: float
    assumption_visibility: float
    distractor_resistance: float
    replay_stability: float
    governance_identity: float
    core_identity: float
    human_approval_required: bool
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "task_count": self.task_count,
            "logical_consistency": self.logical_consistency,
            "fallacy_detection": self.fallacy_detection,
            "assumption_visibility": self.assumption_visibility,
            "distractor_resistance": self.distractor_resistance,
            "replay_stability": self.replay_stability,
            "governance_identity": self.governance_identity,
            "core_identity": self.core_identity,
            "human_approval_required": self.human_approval_required,
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True, separators=(",", ":"),
        )


def build_report() -> V362Report:
    m = logic_metrics()
    replay = m["replay_stability"]
    halt = replay < 1.0
    rationale = (
        f"INFO: analysed {len(all_logic_tasks())} LogiQA/ReClor "
        f"tasks with the deterministic logical-form analyzer; no LLM "
        f"and no false-confidence (unknown forms are not asserted "
        f"valid)",
        f"{'PASS' if m['logical_consistency'] >= _FLOOR else 'FAIL'}: "
        f"logical_consistency {m['logical_consistency']} >= 0.80",
        f"{'PASS' if m['fallacy_detection'] >= _FLOOR else 'FAIL'}: "
        f"fallacy_detection {m['fallacy_detection']} >= 0.80",
        f"{'PASS' if m['assumption_visibility'] >= _FLOOR else 'FAIL'}"
        f": assumption_visibility {m['assumption_visibility']} "
        f">= 0.80 (unstated assumptions surfaced)",
        f"{'PASS' if m['distractor_resistance'] >= _FLOOR else 'FAIL'}"
        f": distractor_resistance {m['distractor_resistance']} "
        f">= 0.80",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: replay_stability "
        f"{replay} == 1.0; governance_identity "
        f"{governance_identity()}; core_identity {core_identity()}; "
        f"HUMAN_APPROVAL_REQUIRED={HUMAN_APPROVAL_REQUIRED}",
    )
    return V362Report(
        task_count=len(all_logic_tasks()),
        logical_consistency=m["logical_consistency"],
        fallacy_detection=m["fallacy_detection"],
        assumption_visibility=m["assumption_visibility"],
        distractor_resistance=m["distractor_resistance"],
        replay_stability=replay,
        governance_identity=governance_identity(),
        core_identity=core_identity(),
        human_approval_required=HUMAN_APPROVAL_REQUIRED,
        halt=halt,
        recommendation=_recommendation(),
        rationale=rationale,
    )


def build_logic_artifact() -> dict[str, object]:
    m = logic_metrics()
    return {
        "schema_version": "v36_2_logiqa_reclor_run",
        "disclaimer": (
            "Logic & fallacy run over locally-vendored LogiQA and "
            "ReClor reference datasets. DESi classifies each "
            "canonical logical form deterministically: valid forms "
            "(modus ponens / tollens) are judged valid, fallacies "
            "(affirming the consequent, denying the antecedent, "
            "hasty generalization, false dichotomy) are named, "
            "unstated assumptions are surfaced and distractor "
            "options are resisted. An unrecognised form is reported "
            "as 'unknown' rather than asserted valid - no false "
            "confidence. This tests deterministic logical-form "
            "governance, not LLM accuracy; the datasets are NOT live "
            "downloads and the scores are NOT official leaderboard "
            "results. Human approval is mandatory."
        ),
        "report_verdicts": list(REPORT_VERDICTS),
        "scorecards": [c.to_dict() for c in logic_scorecards()],
        "logical_consistency": m["logical_consistency"],
        "fallacy_detection": m["fallacy_detection"],
        "assumption_visibility": m["assumption_visibility"],
        "distractor_resistance": m["distractor_resistance"],
        "replay_stability": m["replay_stability"],
        "governance_identity": governance_identity(),
        "core_identity": core_identity(),
        "human_approval_required": HUMAN_APPROVAL_REQUIRED,
        "signature": _signature(),
        "recommendation": _recommendation(),
    }


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_PARTIAL",
    "VERDICT_PASSED",
    "V362Report",
    "assumption_visibility",
    "build_logic_artifact",
    "build_report",
    "distractor_resistance",
    "fallacy_detection",
    "logic_metrics",
    "logical_consistency",
    "replay_stability",
]
