"""v28.2 - sandbox validation of patch proposals.

Each patch branch is validated in the sandbox: it must preserve
replay, preserve governance and require regression. Validation
is a deterministic check over the patch/branch descriptions - no
code is executed or modified.
"""
from __future__ import annotations

from dataclasses import dataclass

from desi.self_improvement import is_forbidden_target

from .branching import Branch, branches
from .patches import Patch, patches
from .regression_hooks import RegressionHook, hooks


@dataclass(frozen=True)
class ValidationResult:
    branch_id: str
    patch_id: str
    replay_preserved: bool
    governance_preserved: bool
    regression_enforced: bool

    def is_valid(self) -> bool:
        return (
            self.replay_preserved
            and self.governance_preserved
            and self.regression_enforced
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "branch_id": self.branch_id,
            "patch_id": self.patch_id,
            "replay_preserved": self.replay_preserved,
            "governance_preserved": self.governance_preserved,
            "regression_enforced": self.regression_enforced,
            "is_valid": self.is_valid(),
        }


def validations() -> tuple[ValidationResult, ...]:
    patch_by_id = {p.patch_id: p for p in patches()}
    hook_by_branch = {h.branch_id: h for h in hooks()}
    out: list[ValidationResult] = []
    for b in branches():
        patch = patch_by_id.get(b.patch_id)
        hook = hook_by_branch.get(b.branch_id)
        governance_ok = (
            patch is not None
            and patch.is_safe
            and not is_forbidden_target(patch.target_area)
        )
        out.append(ValidationResult(
            branch_id=b.branch_id,
            patch_id=b.patch_id,
            replay_preserved=b.is_isolated(),
            governance_preserved=governance_ok,
            regression_enforced=(
                hook is not None and hook.is_enforced()
            ),
        ))
    return tuple(out)


def all_valid() -> bool:
    vs = validations()
    return bool(vs) and all(v.is_valid() for v in vs)


def governance_preservation() -> float:
    """Fraction of validated branches that preserve governance,
    in [0, 1]."""
    vs = validations()
    if not vs:
        return 1.0
    ok = sum(1 for v in vs if v.governance_preserved)
    return round(ok / len(vs), 6)


__all__ = [
    "ValidationResult",
    "all_valid",
    "governance_preservation",
    "validations",
]
