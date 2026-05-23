"""v31.1 - safe patch generation.

Each real mutation becomes a patch proposal on the isolated
branch proposal/peripheral_mutation_v1. Patches are generated
only for allowed peripheral targets; a core-targeting target
yields no patch (it was rejected at the boundary).
"""
from __future__ import annotations

from dataclasses import dataclass

from desi.peripheral_mutation import is_allowed, is_protected_core

from .mutation_engine import RealMutation, real_mutations

BRANCH = "proposal/peripheral_mutation_v1"


@dataclass(frozen=True)
class Patch:
    patch_id: str
    mutation_id: str
    target_area: str
    branch: str
    change_kind: str

    def to_dict(self) -> dict[str, object]:
        return {
            "patch_id": self.patch_id,
            "mutation_id": self.mutation_id,
            "target_area": self.target_area,
            "branch": self.branch,
            "change_kind": self.change_kind,
        }


def _patchable(m: RealMutation) -> bool:
    return (
        m.is_allowed_target
        and not is_protected_core(m.target_area)
        and is_allowed(m.target_area)
        and m.succeeded()
    )


def patches() -> tuple[Patch, ...]:
    out: list[Patch] = []
    for m in real_mutations():
        if _patchable(m):
            out.append(Patch(
                patch_id=f"PATCH_{m.mutation_id}",
                mutation_id=m.mutation_id,
                target_area=m.target_area,
                branch=BRANCH,
                change_kind=f"memoize_{m.target_area}",
            ))
    return tuple(out)


def rejected_targets() -> tuple[str, ...]:
    return tuple(sorted(
        m.target_area for m in real_mutations()
        if not _patchable(m)
    ))


def targets_main() -> bool:
    return any(p.branch == "main" for p in patches())


__all__ = [
    "BRANCH",
    "Patch",
    "patches",
    "rejected_targets",
    "targets_main",
]
