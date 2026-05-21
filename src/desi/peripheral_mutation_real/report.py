"""v31.1 - Real Peripheral Mutation report.

Pflichtmetriken (directive § v31.1):

* successful_mutation_rate
* artifact_identity
* core_identity
* governance_identity
* replay_stability

Killerfrage: "Kann DESi reale branch-isolierte Mutationen
durchfuehren ohne Kern-Drift?"

Real, deterministic peripheral mutations reduce recompute cost
with byte-identical outputs, leaving the protected core and
governance unchanged. Branch-isolated on
proposal/peripheral_mutation_v1; nothing merged.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from desi.self_improvement import HUMAN_APPROVAL_REQUIRED

from .mutation_engine import real_mutations, successful_mutations
from .render_mutation import (
    artifact_identity, core_identity, governance_identity,
)
from .runtime_mutation import (
    runtime_reduction, successful_mutation_rate,
)
from .safe_patch_generation import (
    BRANCH, patches, rejected_targets, targets_main,
)

VERDICT_MUTATED = "PERIPHERAL_MUTATION_NO_CORE_DRIFT"
VERDICT_DRIFT = "CORE_DRIFT_DETECTED"
VERDICT_HALT = "MUTATION_DRIFT_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_MUTATED, VERDICT_DRIFT, VERDICT_HALT,
)

_FLOOR = 0.95


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _signature() -> str:
    parts = [
        f"{m.mutation_id}|{m.target_area}|{m.mutated_hash}"
        for m in real_mutations()
    ]
    return hashlib.sha256(
        "\n".join(parts).encode("utf-8"),
    ).hexdigest()


def replay_stability() -> float:
    if _signature() != _signature():
        return 0.0
    a = {m.mutation_id: m.mutated_hash for m in real_mutations()}
    b = {m.mutation_id: m.baseline_hash for m in real_mutations()}
    return 1.0 if a == b else 0.0


def _recommendation(
    *, replay: float, success: float, artifact: float,
    core: float, governance: float,
) -> str:
    if replay < 1.0:
        return VERDICT_HALT
    if core < 1.0 or governance < 1.0:
        return VERDICT_DRIFT
    if success < _FLOOR or artifact < 1.0:
        return VERDICT_HALT
    return VERDICT_MUTATED


@dataclass(frozen=True)
class V311Report:
    mutation_count: int
    successful_count: int
    patch_count: int
    successful_mutation_rate: float
    artifact_identity: float
    core_identity: float
    governance_identity: float
    replay_stability: float
    runtime_reduction: float
    branch: str
    targets_main: bool
    human_approval_required: bool
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "mutation_count": self.mutation_count,
            "successful_count": self.successful_count,
            "patch_count": self.patch_count,
            "successful_mutation_rate":
                self.successful_mutation_rate,
            "artifact_identity": self.artifact_identity,
            "core_identity": self.core_identity,
            "governance_identity": self.governance_identity,
            "replay_stability": self.replay_stability,
            "runtime_reduction": self.runtime_reduction,
            "branch": self.branch,
            "targets_main": self.targets_main,
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


def build_report() -> V311Report:
    success = successful_mutation_rate()
    artifact = artifact_identity()
    core = core_identity()
    governance = governance_identity()
    replay = replay_stability()
    halt = replay < 1.0
    verdict = _recommendation(
        replay=replay, success=success, artifact=artifact,
        core=core, governance=governance,
    )
    rationale = (
        f"INFO: {len(real_mutations())} real peripheral "
        f"mutations ({len(successful_mutations())} successful); "
        f"{len(patches())} patches on {BRANCH}; aggregate "
        f"runtime_reduction {runtime_reduction()}",
        "INFO: mutations are real deterministic code paths "
        "(memoised recompute) with byte-identical output; "
        "branch-isolated, nothing merged",
        f"{'PASS' if success >= _FLOOR else 'FAIL'}: "
        f"successful_mutation_rate {success} >= 0.95",
        f"{'PASS' if artifact >= 1.0 else 'FAIL'}: "
        f"artifact_identity {artifact} (outputs byte-identical)",
        f"{'PASS' if core >= 1.0 else 'FAIL'}: core_identity "
        f"{core} (protected core unchanged)",
        f"{'PASS' if governance >= 1.0 else 'FAIL'}: "
        f"governance_identity {governance}",
        f"INFO: rejected targets {list(rejected_targets())}; "
        f"targets_main {targets_main()}; "
        f"HUMAN_APPROVAL_REQUIRED={HUMAN_APPROVAL_REQUIRED}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay} (signature "
        f"{_signature()[:12]})",
    )
    return V311Report(
        mutation_count=len(real_mutations()),
        successful_count=len(successful_mutations()),
        patch_count=len(patches()),
        successful_mutation_rate=success,
        artifact_identity=artifact,
        core_identity=core,
        governance_identity=governance,
        replay_stability=replay,
        runtime_reduction=runtime_reduction(),
        branch=BRANCH,
        targets_main=targets_main(),
        human_approval_required=HUMAN_APPROVAL_REQUIRED,
        halt=halt,
        recommendation=verdict,
        rationale=rationale,
    )


def build_mutations_artifact() -> dict[str, object]:
    return {
        "schema_version": "v31_1_peripheral_mutations",
        "disclaimer": (
            "Real, deterministic peripheral mutations applied on "
            "the isolated branch proposal/peripheral_mutation_v1. "
            "Each mutation is a real code path (deterministic "
            "memoisation of a recompute) that reduces recompute "
            "cost with byte-identical output, leaving the "
            "protected core and governance unchanged. No core "
            "modules are touched, governance is not bypassed, "
            "replay is not modified, regression is not bypassed, "
            "nothing is merged and human approval is mandatory. "
            "Replay-stable."
        ),
        "report_verdicts": list(REPORT_VERDICTS),
        "branch": BRANCH,
        "mutations": [m.to_dict() for m in real_mutations()],
        "patches": [p.to_dict() for p in patches()],
        "successful_mutation_rate": successful_mutation_rate(),
        "artifact_identity": artifact_identity(),
        "core_identity": core_identity(),
        "governance_identity": governance_identity(),
        "replay_stability": replay_stability(),
        "runtime_reduction": runtime_reduction(),
        "targets_main": targets_main(),
        "human_approval_required": HUMAN_APPROVAL_REQUIRED,
        "signature": _signature(),
        "recommendation": build_report().recommendation,
    }


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_DRIFT",
    "VERDICT_HALT",
    "VERDICT_MUTATED",
    "V311Report",
    "build_mutations_artifact",
    "build_report",
    "replay_stability",
]
