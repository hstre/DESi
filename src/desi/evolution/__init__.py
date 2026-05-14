"""Constitutional Delphi Evolution Layer for DESi.

v0.5 introduces a governance-controlled self-improvement loop. DESi
may now propose changes to its own configuration after observing its
performance, but every proposed change must pass through a five-step
constitutional process:

1. :class:`ReflectionEngine` analyses a completed evaluation and
   produces a :class:`ReflectionReport`.
2. :class:`MutationProposal` translates a reflection finding into a
   concrete, falsifiable change with explicit rollback conditions.
3. :class:`CloneSandbox` builds an isolated copy of the stable
   configuration; the clone may diverge, the stable state cannot.
4. :class:`MutationEvaluation` runs the clone against the
   Pflichtsuite, the Adversarial-Suite, and the Regression suite.
5. :class:`DelphiJury` reviews the evaluation through five role
   personas; a quorum of 4/5 plus zero valid vetos is required to
   :class:`Promotion`-promote the clone to stable.

v0.5 explicit non-goals:

  * no real LLM API calls
  * no internet access
  * no silent promotions, no skipping the jury, no skipping the
    regression suite
  * no self-modification of stable memory inside a clone

Every change is observable, justified, falsifiable, and rollback-
capable. The point is not that DESi learns; the point is that DESi
justifies every change it would like to make.
"""
from __future__ import annotations

from .evaluation import (
    AdversarialPattern,
    MutationEvaluation,
    MutationEvaluationReport,
)
from .jury import (
    DelphiJury,
    JuryDecision,
    JuryMember,
    JuryReview,
    JuryRole,
    Veto,
    Vote,
)
from .promotion import (
    PromotionError,
    PromotionGate,
    PromotionResult,
    Snapshot,
    promote,
    rollback,
)
from .proposal import MutationProposal, MutationTarget
from .reflection import (
    ReflectionEngine,
    ReflectionFinding,
    ReflectionReport,
)
from .sandbox import CloneSandbox, StableConfig

__all__ = [
    "AdversarialPattern",
    "CloneSandbox",
    "DelphiJury",
    "JuryDecision",
    "JuryMember",
    "JuryReview",
    "JuryRole",
    "MutationEvaluation",
    "MutationEvaluationReport",
    "MutationProposal",
    "MutationTarget",
    "PromotionError",
    "PromotionGate",
    "PromotionResult",
    "ReflectionEngine",
    "ReflectionFinding",
    "ReflectionReport",
    "Snapshot",
    "StableConfig",
    "Veto",
    "Vote",
    "promote",
    "rollback",
]
