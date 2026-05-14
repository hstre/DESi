"""MutationProposal — concrete, falsifiable proposed change.

A MutationProposal is itself a claim: it states a problem, names a
hypothesis, specifies a target, predicts a measurable improvement,
and pre-declares the conditions under which it should be rolled back.
v0.5 requires every promotion to have walked through this object;
free-form "DESi changed" diffs are not permitted by the governance.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class MutationTarget(str, Enum):
    """Closed enumeration of v0.5 target areas.

    Adding a target requires a code change so that downstream
    governance has a stable taxonomy for routing reviews and tests.
    """

    GUARD_THRESHOLDS = "guard_thresholds"
    BRANCH_HEURISTICS = "branch_heuristics"
    MERGE_POLICY = "merge_policy"
    OPERATOR_ORDERING = "operator_ordering"
    DIAGNOSTICS = "diagnostics"


class MutationProposal(BaseModel):
    """A reviewable, falsifiable proposed change to stable DESi.

    The proposal is the unit the DelphiJury reviews. Without these
    fields the jury cannot tell *what* would change, *why*, or *when
    to undo it*.
    """

    model_config = ConfigDict(extra="forbid")

    mutation_id: str = Field(
        default_factory=lambda: "mut_" + uuid.uuid4().hex[:12],
    )
    parent_version: str = Field(
        ..., min_length=1,
        description="Stable version this proposal forks from.",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    problem: str = Field(
        ..., min_length=1,
        description="What concrete observation does this aim to fix?",
    )
    hypothesis: str = Field(
        ..., min_length=1,
        description="Why might the proposed change help? Must name a "
                    "causal claim, not a vague intent.",
    )
    target: MutationTarget = Field(
        ...,
        description="Which DESi component would change.",
    )
    config_delta: dict[str, Any] = Field(
        default_factory=dict,
        description="The actual key/value updates the clone will apply "
                    "on top of stable. Empty proposals are valid "
                    "(documentation-only) but cannot be promoted.",
    )

    expected_improvement: str = Field(
        ..., min_length=1,
        description="What measurable signal should improve, and by "
                    "how much. Stated as a delta on a named metric.",
    )
    rollback_conditions: tuple[str, ...] = Field(
        ...,
        description="Concrete conditions that, if observed, force the "
                    "mutation to be reverted. At least one is required.",
        min_length=1,
    )

    # Optional context linking back to the reflection finding that
    # motivated this proposal. Multiple findings may motivate one
    # proposal.
    motivating_findings: tuple[str, ...] = Field(default_factory=tuple)

    def serialise(self) -> dict[str, Any]:
        d = self.model_dump(mode="json")
        return d

    @classmethod
    def from_record(cls, rec: dict[str, Any]) -> "MutationProposal":
        return cls(**rec)
