"""v31.0 - Mutation Boundary Enforcement report.

Pflichtmetriken (directive § v31.0):

* core_protection
* boundary_enforcement
* governance_preservation
* mutation_traceability
* replay_stability

Killerfrage: "Kann DESi evolvieren ohne ihren epistemischen Kern
zu veraendern?"

Defines the immutable protected core and the allowed peripheral
evolution space, and enforces the boundary: every core-targeting
mutation is FORBIDDEN_CORE_MUTATION / REJECTED. Nothing is
mutated here; the core fingerprint is pinned.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from desi.self_improvement import HUMAN_APPROVAL_REQUIRED

from .boundaries import ALLOWED_EVOLUTION_SPACE
from .mutation_classifier import (
    accepted, core_targeting, proposed_mutations, rejected,
)
from .protected_core import (
    PROTECTED_CORE, core_fingerprint, core_identity,
)
from .risk_analysis import (
    boundary_enforcement, core_protection, mutation_traceability,
)

VERDICT_BOUNDED = "CORE_INVARIANT_BOUNDARY_ENFORCED"
VERDICT_LEAK = "CORE_BOUNDARY_LEAK"
VERDICT_HALT = "BOUNDARY_DRIFT_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_BOUNDED, VERDICT_LEAK, VERDICT_HALT,
)

_FLOOR = 0.95


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def governance_preservation() -> float:
    """1.0 iff the core fingerprint (which includes governance,
    determinism and human approval) is stable."""
    return core_identity()


def _signature() -> str:
    parts = [
        f"{m.mutation_id}|{m.target_area}|{m.status}|{m.decision}"
        for m in proposed_mutations()
    ]
    parts.append(core_fingerprint())
    return hashlib.sha256(
        "\n".join(parts).encode("utf-8"),
    ).hexdigest()


def replay_stability() -> float:
    if _signature() != _signature():
        return 0.0
    return 1.0 if core_fingerprint() == core_fingerprint() else 0.0


def _recommendation(
    *, replay: float, protection: float, enforcement: float,
    governance: float, traceability: float,
) -> str:
    if replay < 1.0:
        return VERDICT_HALT
    if protection < 1.0 or enforcement < 1.0:
        return VERDICT_LEAK
    if governance < 1.0 or traceability < _FLOOR:
        return VERDICT_HALT
    return VERDICT_BOUNDED


@dataclass(frozen=True)
class V310Report:
    proposed_count: int
    accepted_count: int
    rejected_count: int
    core_targeting_count: int
    core_protection: float
    boundary_enforcement: float
    governance_preservation: float
    mutation_traceability: float
    replay_stability: float
    human_approval_required: bool
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "proposed_count": self.proposed_count,
            "accepted_count": self.accepted_count,
            "rejected_count": self.rejected_count,
            "core_targeting_count": self.core_targeting_count,
            "core_protection": self.core_protection,
            "boundary_enforcement": self.boundary_enforcement,
            "governance_preservation":
                self.governance_preservation,
            "mutation_traceability": self.mutation_traceability,
            "replay_stability": self.replay_stability,
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


def build_report() -> V310Report:
    protection = core_protection()
    enforcement = boundary_enforcement()
    governance = governance_preservation()
    traceability = mutation_traceability()
    replay = replay_stability()
    halt = replay < 1.0
    verdict = _recommendation(
        replay=replay, protection=protection,
        enforcement=enforcement, governance=governance,
        traceability=traceability,
    )
    rationale = (
        f"INFO: {len(proposed_mutations())} proposed mutations "
        f"({len(accepted())} peripheral accepted, "
        f"{len(rejected())} rejected); {len(PROTECTED_CORE)} "
        f"protected-core areas, {len(ALLOWED_EVOLUTION_SPACE)} "
        f"allowed peripheral areas",
        "INFO: nothing is mutated here; the core fingerprint is "
        "pinned and every core-targeting proposal is rejected",
        f"{'PASS' if protection >= 1.0 else 'FAIL'}: "
        f"core_protection {protection} (core-targeting "
        f"{len(core_targeting())} all rejected)",
        f"{'PASS' if enforcement >= 1.0 else 'FAIL'}: "
        f"boundary_enforcement {enforcement}",
        f"{'PASS' if governance >= 1.0 else 'FAIL'}: "
        f"governance_preservation {governance} (core_identity "
        f"{core_identity()})",
        f"{'PASS' if traceability >= _FLOOR else 'FAIL'}: "
        f"mutation_traceability {traceability} >= 0.95",
        f"INFO: HUMAN_APPROVAL_REQUIRED="
        f"{HUMAN_APPROVAL_REQUIRED}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay} (signature "
        f"{_signature()[:12]})",
    )
    return V310Report(
        proposed_count=len(proposed_mutations()),
        accepted_count=len(accepted()),
        rejected_count=len(rejected()),
        core_targeting_count=len(core_targeting()),
        core_protection=protection,
        boundary_enforcement=enforcement,
        governance_preservation=governance,
        mutation_traceability=traceability,
        replay_stability=replay,
        human_approval_required=HUMAN_APPROVAL_REQUIRED,
        halt=halt,
        recommendation=verdict,
        rationale=rationale,
    )


def build_boundaries_artifact() -> dict[str, object]:
    return {
        "schema_version": "v31_0_mutation_boundaries",
        "disclaimer": (
            "Defines the completely-immutable protected core "
            "(replay kernel, determinism scanner, concept gates, "
            "governance core, authority filters, regression "
            "integrity, human-approval enforcement) and the "
            "allowed peripheral evolution space, and enforces the "
            "boundary: every mutation that touches the core - "
            "directly or indirectly - is FORBIDDEN_CORE_MUTATION "
            "and REJECTED. Nothing is mutated here; the core "
            "fingerprint is pinned. Human approval is mandatory. "
            "Deterministic and replay-stable."
        ),
        "report_verdicts": list(REPORT_VERDICTS),
        "protected_core": list(PROTECTED_CORE),
        "allowed_evolution_space": list(ALLOWED_EVOLUTION_SPACE),
        "proposed_mutations": [
            m.to_dict() for m in proposed_mutations()
        ],
        "core_protection": core_protection(),
        "boundary_enforcement": boundary_enforcement(),
        "governance_preservation": governance_preservation(),
        "mutation_traceability": mutation_traceability(),
        "replay_stability": replay_stability(),
        "core_identity": core_identity(),
        "core_fingerprint": core_fingerprint(),
        "human_approval_required": HUMAN_APPROVAL_REQUIRED,
        "signature": _signature(),
        "recommendation": build_report().recommendation,
    }


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_BOUNDED",
    "VERDICT_HALT",
    "VERDICT_LEAK",
    "V310Report",
    "build_boundaries_artifact",
    "build_report",
    "governance_preservation",
    "replay_stability",
]
