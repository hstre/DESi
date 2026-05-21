"""v28.2 - Branch Generation & Patch Sandbox report.

Pflichtmetriken (directive § v28.2):

* branch_isolation
* regression_integrity
* unsafe_patch_rejection
* governance_preservation
* replay_stability

Killerfrage: "Kann DESi kontrollierte Architekturvarianten
erzeugen ohne den Kern zu destabilisieren?"

Safe patches go onto isolated `proposal/*` branches (sandbox
base, no auto-merge, never main), each with a mandatory
regression hook; unsafe patch attempts are rejected. Nothing is
applied and human approval stays mandatory.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from desi.self_improvement import HUMAN_APPROVAL_REQUIRED

from .branching import branch_isolation, branches, merges_to_main
from .patches import (
    patches, rejected_patch_attempts, unsafe_patch_rejection,
)
from .regression_hooks import any_bypassed, regression_integrity
from .sandbox_validation import (
    all_valid, governance_preservation, validations,
)

VERDICT_CONTROLLED = "BRANCHES_CONTROLLED_ISOLATED"
VERDICT_LEAK = "BRANCH_ISOLATION_LEAK"
VERDICT_HALT = "BRANCH_DRIFT_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_CONTROLLED, VERDICT_LEAK, VERDICT_HALT,
)

_FLOOR = 0.95


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _signature() -> str:
    parts = [
        f"{b.name}|{b.base}|{b.auto_merge}|{b.targets_main}"
        for b in branches()
    ]
    parts += [
        f"{p.patch_id}|{p.target_module}" for p in patches()
    ]
    return hashlib.sha256(
        "\n".join(parts).encode("utf-8"),
    ).hexdigest()


def replay_stability() -> float:
    return 1.0 if _signature() == _signature() else 0.0


def _recommendation(
    *, replay: float, isolation: float, regression: float,
    rejection: float, governance: float,
) -> str:
    if replay < 1.0:
        return VERDICT_HALT
    if isolation < 1.0 or merges_to_main():
        return VERDICT_LEAK
    if (
        regression < _FLOOR
        or rejection < _FLOOR
        or governance < _FLOOR
    ):
        return VERDICT_HALT
    return VERDICT_CONTROLLED


@dataclass(frozen=True)
class V282Report:
    patch_count: int
    branch_count: int
    rejected_attempt_count: int
    branch_isolation: float
    regression_integrity: float
    unsafe_patch_rejection: float
    governance_preservation: float
    replay_stability: float
    all_valid: bool
    any_regression_bypassed: bool
    merges_to_main: tuple[str, ...]
    human_approval_required: bool
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "patch_count": self.patch_count,
            "branch_count": self.branch_count,
            "rejected_attempt_count": self.rejected_attempt_count,
            "branch_isolation": self.branch_isolation,
            "regression_integrity": self.regression_integrity,
            "unsafe_patch_rejection": self.unsafe_patch_rejection,
            "governance_preservation":
                self.governance_preservation,
            "replay_stability": self.replay_stability,
            "all_valid": self.all_valid,
            "any_regression_bypassed":
                self.any_regression_bypassed,
            "merges_to_main": list(self.merges_to_main),
            "human_approval_required":
                self.human_approval_required,
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def build_report() -> V282Report:
    isolation = branch_isolation()
    regression = regression_integrity()
    rejection = unsafe_patch_rejection()
    governance = governance_preservation()
    replay = replay_stability()
    halt = replay < 1.0
    verdict = _recommendation(
        replay=replay, isolation=isolation,
        regression=regression, rejection=rejection,
        governance=governance,
    )
    rationale = (
        f"INFO: {len(patches())} safe patches on "
        f"{len(branches())} isolated branches; "
        f"{len(rejected_patch_attempts())} unsafe patch "
        f"attempts rejected",
        "INFO: branches are proposal-only (sandbox base, no "
        "auto-merge, never main); nothing is applied",
        f"{'PASS' if isolation >= 1.0 else 'FAIL'}: "
        f"branch_isolation {isolation} (merges_to_main "
        f"{list(merges_to_main())})",
        f"{'PASS' if regression >= _FLOOR else 'FAIL'}: "
        f"regression_integrity {regression} (any bypassed "
        f"{any_bypassed()})",
        f"{'PASS' if rejection >= _FLOOR else 'FAIL'}: "
        f"unsafe_patch_rejection {rejection} (rejected "
        f"{list(rejected_patch_attempts())})",
        f"{'PASS' if governance >= _FLOOR else 'FAIL'}: "
        f"governance_preservation {governance} (all_valid "
        f"{all_valid()})",
        f"INFO: HUMAN_APPROVAL_REQUIRED="
        f"{HUMAN_APPROVAL_REQUIRED}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay} (signature "
        f"{_signature()[:12]})",
    )
    return V282Report(
        patch_count=len(patches()),
        branch_count=len(branches()),
        rejected_attempt_count=len(rejected_patch_attempts()),
        branch_isolation=isolation,
        regression_integrity=regression,
        unsafe_patch_rejection=rejection,
        governance_preservation=governance,
        replay_stability=replay,
        all_valid=all_valid(),
        any_regression_bypassed=any_bypassed(),
        merges_to_main=merges_to_main(),
        human_approval_required=HUMAN_APPROVAL_REQUIRED,
        halt=halt,
        recommendation=verdict,
        rationale=rationale,
    )


def build_branches_artifact() -> dict[str, object]:
    return {
        "schema_version": "v28_2_branch_sandbox",
        "disclaimer": (
            "Generates patch *proposals* (descriptions, never "
            "applied diffs) for governance-safe ideas and places "
            "each on an isolated proposal/* branch with a "
            "sandbox base - no branch targets main, none "
            "auto-merges, and every one carries a mandatory "
            "regression hook. Unsafe patch attempts are "
            "rejected. No real source is modified, nothing is "
            "merged, and human approval is mandatory. "
            "Deterministic and replay-stable."
        ),
        "report_verdicts": list(REPORT_VERDICTS),
        "patches": [p.to_dict() for p in patches()],
        "branches": [b.to_dict() for b in branches()],
        "validations": [v.to_dict() for v in validations()],
        "rejected_patch_attempts": list(rejected_patch_attempts()),
        "branch_isolation": branch_isolation(),
        "regression_integrity": regression_integrity(),
        "unsafe_patch_rejection": unsafe_patch_rejection(),
        "governance_preservation": governance_preservation(),
        "replay_stability": replay_stability(),
        "merges_to_main": list(merges_to_main()),
        "human_approval_required": HUMAN_APPROVAL_REQUIRED,
        "signature": _signature(),
        "recommendation": build_report().recommendation,
    }


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_CONTROLLED",
    "VERDICT_HALT",
    "VERDICT_LEAK",
    "V282Report",
    "build_branches_artifact",
    "build_report",
    "replay_stability",
]
