"""v28.2 - patch proposals (descriptions only, never applied).

A patch is a *description* of a proposed change (target area,
target module, change kind) - it is never an applied diff and
never modifies any real source. Patches are generated only for
governance-safe accepted proposals; an attempt to patch an
unsafe/forbidden target is rejected outright.
"""
from __future__ import annotations

from dataclasses import dataclass

from desi.self_improvement import is_forbidden_target, is_safe_target
from desi.self_improvement_wild import is_governance_safe, proposals

# accepted wild proposal -> a named (but untouched) target module
# and a descriptive change kind.
_TARGET_MODULE: dict[str, str] = {
    "WS1": "desi.epistemic_graph.lineage",
    "WS2": "desi.epistemic_graph_queries.queries",
    "WS3": "desi.output_ports_multi.renderer",
    "WS4": "desi.research_ecology.ecology",
    "WS5": "desi.research_harvester.claims",
    "WS6": "desi.self_improvement_branches.sandbox_validation",
}


@dataclass(frozen=True)
class Patch:
    patch_id: str
    source_proposal_id: str
    target_area: str
    target_module: str
    change_kind: str
    is_safe: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "patch_id": self.patch_id,
            "source_proposal_id": self.source_proposal_id,
            "target_area": self.target_area,
            "target_module": self.target_module,
            "change_kind": self.change_kind,
            "is_safe": self.is_safe,
        }


def _patch_safe(p) -> bool:
    return (
        is_governance_safe(p)
        and is_safe_target(p.target_area)
        and not is_forbidden_target(p.target_area)
    )


def patches() -> tuple[Patch, ...]:
    """Patches generated for governance-safe proposals only."""
    out: list[Patch] = []
    for p in proposals():
        if _patch_safe(p):
            out.append(Patch(
                patch_id=f"PATCH_{p.proposal_id}",
                source_proposal_id=p.proposal_id,
                target_area=p.target_area,
                target_module=_TARGET_MODULE.get(
                    p.proposal_id, f"(area:{p.target_area})"),
                change_kind=f"propose_{p.label}",
                is_safe=True,
            ))
    return tuple(out)


def rejected_patch_attempts() -> tuple[str, ...]:
    """Proposal ids for which patch generation was refused
    (unsafe / forbidden target)."""
    return tuple(
        p.proposal_id for p in proposals()
        if not _patch_safe(p)
    )


def unsafe_patch_attempt_count() -> int:
    return sum(1 for p in proposals() if not _patch_safe(p))


def unsafe_patch_rejection() -> float:
    """Fraction of unsafe patch attempts rejected, in [0, 1]."""
    attempts = unsafe_patch_attempt_count()
    if attempts == 0:
        return 1.0
    rejected = len(rejected_patch_attempts())
    return round(rejected / attempts, 6)


__all__ = [
    "Patch",
    "patches",
    "rejected_patch_attempts",
    "unsafe_patch_attempt_count",
    "unsafe_patch_rejection",
]
