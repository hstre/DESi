"""v28.2 - isolated branch proposals.

Each safe patch is placed on its own isolated branch
(`proposal/<patch_id>`) with a sandbox base. No branch targets
main, none auto-merges, and every one requires human approval.
These are branch *descriptions*; no git branch is actually
created here.
"""
from __future__ import annotations

from dataclasses import dataclass

from desi.self_improvement import HUMAN_APPROVAL_REQUIRED

from .patches import patches

_SANDBOX_BASE = "sandbox"
_PROTECTED_BRANCH = "main"


@dataclass(frozen=True)
class Branch:
    branch_id: str
    patch_id: str
    name: str
    base: str
    auto_merge: bool
    targets_main: bool
    human_approval_required: bool

    def is_isolated(self) -> bool:
        return (
            self.name.startswith("proposal/")
            and self.base == _SANDBOX_BASE
            and not self.auto_merge
            and not self.targets_main
            and self.name != _PROTECTED_BRANCH
            and self.human_approval_required
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "branch_id": self.branch_id,
            "patch_id": self.patch_id,
            "name": self.name,
            "base": self.base,
            "auto_merge": self.auto_merge,
            "targets_main": self.targets_main,
            "human_approval_required":
                self.human_approval_required,
            "is_isolated": self.is_isolated(),
        }


def branches() -> tuple[Branch, ...]:
    return tuple(
        Branch(
            branch_id=f"BR_{p.patch_id}",
            patch_id=p.patch_id,
            name=f"proposal/{p.patch_id}",
            base=_SANDBOX_BASE,
            auto_merge=False,
            targets_main=False,
            human_approval_required=HUMAN_APPROVAL_REQUIRED,
        )
        for p in patches()
    )


def branch_isolation() -> float:
    """Fraction of branches that are fully isolated, in [0, 1].
    The gate requires exactly 1.0."""
    bs = branches()
    if not bs:
        return 1.0
    isolated = sum(1 for b in bs if b.is_isolated())
    return round(isolated / len(bs), 6)


def merges_to_main() -> tuple[str, ...]:
    """Branches that would merge to main - must always be
    empty."""
    return tuple(
        b.branch_id for b in branches()
        if b.targets_main or b.auto_merge
    )


__all__ = [
    "Branch",
    "branch_isolation",
    "branches",
    "merges_to_main",
]
