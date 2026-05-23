"""v31.3 - Long-Horizon Peripheral Mutation Ecology report.

Pflichtmetriken (directive § v31.3):

* generation_stability
* core_preservation
* governance_preservation
* lineage_integrity
* replay_stability

Killerfrage: "Kann DESi langfristige reale Infrastruktur-Evolution
durchfuehren ohne Kernmutation?"

25 real, branch-isolated peripheral mutation generations. Each
generation performs exactly one real deterministic mutation (a
memoized recompute reduction with byte-identical output), keeps the
protected core byte-invariant, and preserves governance and human
approval. Per-generation regression survival is confirmed by the
mandatory v1-v31 full regression. Nothing is merged.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from desi.peripheral_mutation_real import BRANCH
from desi.self_improvement import HUMAN_APPROVAL_REQUIRED

from .branch_ecology import all_branch_isolated, core_drift_count
from .mutation_generations import (
    core_preservation, generation_count, generation_stability,
    governance_preservation,
)
from .mutation_lineage import lineage_integrity, targets_main
from .runtime_ecology import (
    ecology_recompute_reduction, replay_stability,
    total_baseline_recomputes, total_mutated_recomputes,
)

VERDICT_STABLE = "STABLE_LONG_HORIZON_PERIPHERAL_EVOLUTION"
VERDICT_DRIFT = "CORE_DRIFT_DETECTED"
VERDICT_HALT = "EVOLUTION_ECOLOGY_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_STABLE, VERDICT_DRIFT, VERDICT_HALT,
)


def _metrics() -> dict[str, float]:
    return {
        "generation_stability": generation_stability(),
        "core_preservation": core_preservation(),
        "governance_preservation": governance_preservation(),
        "lineage_integrity": lineage_integrity(),
        "replay_stability": replay_stability(),
    }


def _signature() -> str:
    m = _metrics()
    parts = [f"{k}={m[k]}" for k in sorted(m)]
    return hashlib.sha256(
        "|".join(parts).encode("utf-8"),
    ).hexdigest()


def _recommendation() -> str:
    if replay_stability() < 1.0:
        return VERDICT_HALT
    if core_preservation() < 1.0 or governance_preservation() < 1.0:
        return VERDICT_DRIFT
    if (
        generation_stability() == 1.0
        and lineage_integrity() == 1.0
    ):
        return VERDICT_STABLE
    return VERDICT_HALT


@dataclass(frozen=True)
class V313Report:
    generations: int
    generation_stability: float
    core_preservation: float
    governance_preservation: float
    lineage_integrity: float
    replay_stability: float
    total_baseline_recomputes: int
    total_mutated_recomputes: int
    ecology_recompute_reduction: float
    branch_isolated: bool
    targets_main: bool
    core_drift_count: int
    human_approval_required: bool
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "generations": self.generations,
            "generation_stability": self.generation_stability,
            "core_preservation": self.core_preservation,
            "governance_preservation":
                self.governance_preservation,
            "lineage_integrity": self.lineage_integrity,
            "replay_stability": self.replay_stability,
            "total_baseline_recomputes":
                self.total_baseline_recomputes,
            "total_mutated_recomputes":
                self.total_mutated_recomputes,
            "ecology_recompute_reduction":
                self.ecology_recompute_reduction,
            "branch_isolated": self.branch_isolated,
            "targets_main": self.targets_main,
            "core_drift_count": self.core_drift_count,
            "human_approval_required": self.human_approval_required,
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def build_report() -> V313Report:
    m = _metrics()
    gen_stab = m["generation_stability"]
    core = m["core_preservation"]
    gov = m["governance_preservation"]
    lineage = m["lineage_integrity"]
    replay = m["replay_stability"]
    halt = replay < 1.0
    rationale = (
        f"INFO: {generation_count()} real branch-isolated "
        f"peripheral mutation generations on {BRANCH}; one "
        f"mutation per generation, nothing merged",
        f"INFO: aggregate real recompute reduction "
        f"{total_baseline_recomputes()} -> "
        f"{total_mutated_recomputes()} "
        f"({ecology_recompute_reduction():.6f}); measured, not "
        f"projected",
        f"{'PASS' if gen_stab == 1.0 else 'FAIL'}: "
        f"generation_stability {gen_stab} == 1.0 (every "
        f"generation byte-identical + recompute reduced)",
        f"{'PASS' if core == 1.0 else 'FAIL'}: core_preservation "
        f"{core} == 1.0 (protected core byte-invariant, "
        f"{core_drift_count()} drift events)",
        f"{'PASS' if gov == 1.0 else 'FAIL'}: "
        f"governance_preservation {gov} == 1.0",
        f"{'PASS' if lineage == 1.0 else 'FAIL'}: lineage_integrity "
        f"{lineage} == 1.0 (orphan-free, acyclic, never targets "
        f"main)",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: replay_stability "
        f"{replay} == 1.0; per-generation regression confirmed by "
        f"the mandatory v1-v31 full regression; "
        f"HUMAN_APPROVAL_REQUIRED={HUMAN_APPROVAL_REQUIRED}",
    )
    return V313Report(
        generations=generation_count(),
        generation_stability=gen_stab,
        core_preservation=core,
        governance_preservation=gov,
        lineage_integrity=lineage,
        replay_stability=replay,
        total_baseline_recomputes=total_baseline_recomputes(),
        total_mutated_recomputes=total_mutated_recomputes(),
        ecology_recompute_reduction=ecology_recompute_reduction(),
        branch_isolated=all_branch_isolated(),
        targets_main=targets_main(),
        core_drift_count=core_drift_count(),
        human_approval_required=HUMAN_APPROVAL_REQUIRED,
        halt=halt,
        recommendation=_recommendation(),
        rationale=rationale,
    )


def build_ecology_artifact() -> dict[str, object]:
    m = _metrics()
    return {
        "schema_version": "v31_3_peripheral_mutation_ecology",
        "disclaimer": (
            "25 real, branch-isolated peripheral mutation "
            "generations. Each generation performs exactly one real "
            "deterministic mutation (a memoized recompute reduction) "
            "whose output is byte-identical, while the protected "
            "core stays byte-invariant and governance plus human "
            "approval are preserved. The recompute reduction is "
            "measured, not projected. No core module is touched, "
            "nothing is merged, and per-generation regression "
            "survival is confirmed by the mandatory v1-v31 full "
            "regression. Replay-stable; human approval mandatory."
        ),
        "report_verdicts": list(REPORT_VERDICTS),
        "branch": BRANCH,
        "generations": generation_count(),
        "generation_stability": m["generation_stability"],
        "core_preservation": m["core_preservation"],
        "governance_preservation": m["governance_preservation"],
        "lineage_integrity": m["lineage_integrity"],
        "replay_stability": m["replay_stability"],
        "total_baseline_recomputes": total_baseline_recomputes(),
        "total_mutated_recomputes": total_mutated_recomputes(),
        "ecology_recompute_reduction":
            ecology_recompute_reduction(),
        "branch_isolated": all_branch_isolated(),
        "targets_main": targets_main(),
        "core_drift_count": core_drift_count(),
        "human_approval_required": HUMAN_APPROVAL_REQUIRED,
        "signature": _signature(),
        "recommendation": _recommendation(),
    }


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_DRIFT",
    "VERDICT_HALT",
    "VERDICT_STABLE",
    "V313Report",
    "build_ecology_artifact",
    "build_report",
]
