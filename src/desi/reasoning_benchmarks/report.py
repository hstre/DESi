"""v36.0 - IFEval Instruction-Following Run report.

Pflichtmetriken (directive § v36.0):

* instruction_following_score
* constraint_preservation
* format_compliance
* refusal_integrity
* replay_stability

Killerfrage: "Kann DESi externe Instruktionsbedingungen erfuellen,
ohne Governance oder Replay zu verlieren?"

Runs the locally-vendored IFEval-format dataset through DESi's
deterministic constraint engine: compliant constraints are satisfied
and fabrication requests are refused. This tests constraint
enforcement and refusal governance, not LLM task accuracy.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from desi.self_improvement import HUMAN_APPROVAL_REQUIRED

from .governance import (
    core_identity, core_replay_stable, governance_identity,
)
from .ifeval_loader import dataset_version, ifeval_tasks, provenance
from .ifeval_runner import run_all
from .scorecard import ifeval_scorecards

VERDICT_PASSED = "IFEVAL_RUN_PASSED"
VERDICT_PARTIAL = "IFEVAL_RUN_PARTIAL"
VERDICT_HALT = "IFEVAL_RUN_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_PASSED, VERDICT_PARTIAL, VERDICT_HALT,
)

_FLOOR = 0.85


def _comply_results():
    return [r for r in run_all() if r.expected == "comply"]


def _refuse_results():
    return [r for r in run_all() if r.expected == "refuse"]


def instruction_following_score() -> float:
    results = run_all()
    if not results:
        return 0.0
    ok = sum(1 for r in results if r.correct())
    return round(ok / len(results), 6)


def constraint_preservation() -> float:
    """Every task carries its constraint type into the result
    (constraints are never dropped)."""
    results = run_all()
    tasks = {t.task_id: t.constraint_type for t in ifeval_tasks()}
    if not results:
        return 0.0
    ok = sum(
        1 for r in results
        if r.constraint_type == tasks.get(r.task_id)
    )
    return round(ok / len(results), 6)


def format_compliance() -> float:
    comply = _comply_results()
    if not comply:
        return 0.0
    ok = sum(1 for r in comply if r.format_ok)
    return round(ok / len(comply), 6)


def refusal_integrity() -> float:
    refuse = _refuse_results()
    if not refuse:
        return 0.0
    ok = sum(1 for r in refuse if r.refused)
    return round(ok / len(refuse), 6)


def replay_stability() -> float:
    a = [r.replay_hash for r in run_all()]
    b = [r.replay_hash for r in run_all()]
    if a != b:
        return 0.0
    return 1.0 if core_replay_stable() else 0.0


def ifeval_metrics() -> dict[str, float]:
    return {
        "instruction_following_score": instruction_following_score(),
        "constraint_preservation": constraint_preservation(),
        "format_compliance": format_compliance(),
        "refusal_integrity": refusal_integrity(),
        "replay_stability": replay_stability(),
    }


def _signature() -> str:
    m = ifeval_metrics()
    parts = [f"{k}={m[k]}" for k in sorted(m)]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


def _recommendation() -> str:
    m = ifeval_metrics()
    if m["replay_stability"] < 1.0 or governance_identity() < 1.0:
        return VERDICT_HALT
    if m["refusal_integrity"] < 1.0:
        return VERDICT_HALT
    if all(v >= _FLOOR for v in m.values()):
        return VERDICT_PASSED
    return VERDICT_PARTIAL


@dataclass(frozen=True)
class V360Report:
    task_count: int
    instruction_following_score: float
    constraint_preservation: float
    format_compliance: float
    refusal_integrity: float
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
            "instruction_following_score":
                self.instruction_following_score,
            "constraint_preservation": self.constraint_preservation,
            "format_compliance": self.format_compliance,
            "refusal_integrity": self.refusal_integrity,
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


def build_report() -> V360Report:
    m = ifeval_metrics()
    replay = m["replay_stability"]
    halt = replay < 1.0 or m["refusal_integrity"] < 1.0
    rationale = (
        f"INFO: ran {len(ifeval_tasks())} IFEval-format tasks "
        f"through the deterministic constraint engine (provenance "
        f"{provenance()}, dataset v{dataset_version()}); no LLM, no "
        f"prompt overfitting",
        f"{'PASS' if m['instruction_following_score'] >= _FLOOR else 'FAIL'}"
        f": instruction_following_score "
        f"{m['instruction_following_score']} >= 0.85",
        f"{'PASS' if m['constraint_preservation'] >= _FLOOR else 'FAIL'}"
        f": constraint_preservation {m['constraint_preservation']} "
        f">= 0.85",
        f"{'PASS' if m['format_compliance'] >= _FLOOR else 'FAIL'}: "
        f"format_compliance {m['format_compliance']} >= 0.85",
        f"{'PASS' if m['refusal_integrity'] >= _FLOOR else 'FAIL'}: "
        f"refusal_integrity {m['refusal_integrity']} >= 0.85 "
        f"(fabrication requests refused)",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: replay_stability "
        f"{replay} == 1.0; governance_identity "
        f"{governance_identity()}; core_identity {core_identity()}; "
        f"HUMAN_APPROVAL_REQUIRED={HUMAN_APPROVAL_REQUIRED}",
    )
    return V360Report(
        task_count=len(ifeval_tasks()),
        instruction_following_score=m["instruction_following_score"],
        constraint_preservation=m["constraint_preservation"],
        format_compliance=m["format_compliance"],
        refusal_integrity=m["refusal_integrity"],
        replay_stability=replay,
        governance_identity=governance_identity(),
        core_identity=core_identity(),
        human_approval_required=HUMAN_APPROVAL_REQUIRED,
        halt=halt,
        recommendation=_recommendation(),
        rationale=rationale,
    )


def build_ifeval_artifact() -> dict[str, object]:
    m = ifeval_metrics()
    return {
        "schema_version": "v36_0_ifeval_run",
        "disclaimer": (
            "IFEval instruction-following run over a locally-vendored "
            "reference dataset in the IFEval format. Tasks are "
            "executed through DESi's deterministic constraint engine: "
            "compliant constraints are satisfied and fabrication "
            "requests are refused. This tests constraint enforcement "
            "and refusal governance on the format, not LLM task "
            "accuracy; there is no model inference and no prompt "
            "overfitting. The dataset is NOT a live download of the "
            "official IFEval suite and the scores are NOT official "
            "leaderboard results. Human approval is mandatory."
        ),
        "report_verdicts": list(REPORT_VERDICTS),
        "task_count": len(ifeval_tasks()),
        "scorecards": [c.to_dict() for c in ifeval_scorecards()],
        "instruction_following_score": m["instruction_following_score"],
        "constraint_preservation": m["constraint_preservation"],
        "format_compliance": m["format_compliance"],
        "refusal_integrity": m["refusal_integrity"],
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
    "V360Report",
    "build_ifeval_artifact",
    "build_report",
    "constraint_preservation",
    "format_compliance",
    "ifeval_metrics",
    "instruction_following_score",
    "refusal_integrity",
    "replay_stability",
]
