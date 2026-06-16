"""EpistemicGapSnapshot - the stable, typed, READ-ONLY interface between Layer 9 and DESi.

The whole point of this boundary: Kevin (and DESi) must NOT reach into Layer-9 core structures.
Layer 9 *projects* only what the solution-space analysis needs into these plain, frozen DTOs; DESi
analyses the snapshot; Kevin consumes DESi's proposals. Nothing here imports a Layer-9 class, so the
contract stays extractable and the coupling stays one-way and explicit.

Affinities are plain strings (the content-free thinking-move vocabulary, e.g. "causal", "boundary")
so neither DESi nor this contract depends on Kevin's or Layer 9's enums.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class MethodRecord:
    """One method's trial history - the real evidence of what HAS been tried and how it went."""

    method_id: str
    affinities: tuple[str, ...]            # thinking-moves this method carries
    contexts_tested: tuple[str, ...] = ()  # ids of conflicts/questions it was tried on
    positive_trials: int = 0
    negative_trials: int = 0
    inconclusive_trials: int = 0


@dataclass(frozen=True)
class ConflictGap:
    """An OPEN conflict Layer 9 still holds - the prime place creativity is owed."""

    id: str
    kind: str                              # taxonomy of the incompatibility
    severity: str                          # "soft" | "hard"
    scope: tuple[str, ...] = ()            # the claim ids / topics it spans
    attempted_affinities: tuple[str, ...] = ()  # moves already tried ON THIS conflict
    unresolved_since: int = 0              # ledger sequence / tick it has been open


@dataclass(frozen=True)
class EvidenceGap:
    claim_id: str
    missing_evidence_type: str
    source_independence: float = 0.0       # 0 = single source, 1 = many independent
    downstream_importance: float = 0.0     # how much rests on this claim


@dataclass(frozen=True)
class OpenQuestion:
    question_id: str
    topic: str
    constraints: tuple[str, ...] = ()
    attempted_methods: tuple[str, ...] = ()


@dataclass(frozen=True)
class SnapshotProvenance:
    snapshot_hash: str = ""
    layer9_sequence: int = 0


@dataclass(frozen=True)
class EpistemicGapSnapshot:
    """A read-only projection of the epistemic state relevant to finding solution spaces. Only OPEN
    conflicts / live gaps appear - a resolved conflict is simply absent (so it can never be proposed
    as a blind spot again, which is the intervention-sensitivity the contract requires)."""

    conflicts: tuple[ConflictGap, ...] = ()
    evidence_gaps: tuple[EvidenceGap, ...] = ()
    method_history: tuple[MethodRecord, ...] = ()
    open_questions: tuple[OpenQuestion, ...] = ()
    provenance: SnapshotProvenance = field(default_factory=SnapshotProvenance)
