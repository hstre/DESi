"""Constitutional Delphi Evolution Layer for DESi.

v0.5 established the constitutional process (Reflection → Proposal →
Clone → Evaluation → Jury → Promotion + Snapshot + Rollback).

v0.6 hardens the audit and turns vetos into action:

* :class:`EvolutionLedger` — append-only forensic trail covering every
  step of the process.
* :class:`VetoToTestSynthesiser` — converts a valid veto into a
  :class:`VetoTestObligation` plus a pytest skeleton string. An
  obligation must reach a terminal state (PASSED or WAIVED) before
  promotion is allowed.
* :class:`PathQualityMetrics` — deterministic raw counters per run,
  surface for future statistical work without v0.6 doing any stats.
* :class:`ProposalDraftBuilder` — emits ``MutationProposal`` drafts
  with ``requires_ratification=True`` from a ``ReflectionFinding``.
* :func:`promote_with_ledger` — promotion that refuses to proceed
  without a complete audit trail.

v0.6 explicit non-goals:

  * no behaviour-changing config_delta application
  * no real LLM API calls (jury members carry ``model_label`` only)
  * no statistical significance tests
  * no parallel-clone scheduling
  * no in-place mutation of ledger entries
"""
from __future__ import annotations

from .draft import ProposalDraftBuilder
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
from .ledger import EvolutionLedger, LedgerEntry, LedgerEventType
from .metrics import PathQualityMetrics, compute_path_quality
from .promotion import (
    PromotionError,
    PromotionGate,
    PromotionResult,
    Snapshot,
    promote,
    promote_with_ledger,
    rollback,
)
from .proposal import MutationProposal, MutationTarget
from .reflection import (
    ReflectionEngine,
    ReflectionFinding,
    ReflectionReport,
)
from .sandbox import CloneSandbox, StableConfig
from .veto_followup import (
    ObligationStatus,
    VetoTestObligation,
    VetoToTestSynthesiser,
    is_resolved,
)

__all__ = [
    "AdversarialPattern",
    "CloneSandbox",
    "DelphiJury",
    "EvolutionLedger",
    "JuryDecision",
    "JuryMember",
    "JuryReview",
    "JuryRole",
    "LedgerEntry",
    "LedgerEventType",
    "MutationEvaluation",
    "MutationEvaluationReport",
    "MutationProposal",
    "MutationTarget",
    "ObligationStatus",
    "PathQualityMetrics",
    "PromotionError",
    "PromotionGate",
    "PromotionResult",
    "ProposalDraftBuilder",
    "ReflectionEngine",
    "ReflectionFinding",
    "ReflectionReport",
    "Snapshot",
    "StableConfig",
    "Veto",
    "VetoTestObligation",
    "VetoToTestSynthesiser",
    "Vote",
    "compute_path_quality",
    "is_resolved",
    "promote",
    "promote_with_ledger",
    "rollback",
]
