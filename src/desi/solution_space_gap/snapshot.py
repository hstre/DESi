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

# The version of THIS snapshot contract. A projector stamps it into the provenance so a consumer can
# tell which schema produced a snapshot (and refuse / adapt on a mismatch). Bump on a breaking change.
SCHEMA_VERSION = "epistemic_gap_snapshot_v1"


@dataclass(frozen=True)
class MethodRecord:
    """A method's GENERAL repertoire - which thinking-moves it carries (not a per-conflict outcome).
    Per-conflict, scope-bound outcomes live in ``MethodTrial`` so a local failure can NEVER become a
    global demotion."""

    method_id: str
    affinities: tuple[str, ...]            # thinking-moves this method carries
    contexts_tested: tuple[str, ...] = ()  # ids of conflicts/questions it was tried on


# A trial result is methodological information ONLY for the last three; a technical failure says
# nothing about whether the move fits, so it must NOT demote the move.
TRIAL_RESULTS = ("untried", "technical_failure", "no_benefit", "harmful", "success", "inconclusive",
                 "unknown")


@dataclass(frozen=True)
class MethodTrial:
    """ONE scope-bound attempt of a thinking-move on a conflict. The demotion of a move is bound to
    (conflict, scope, method_variant, result) - never global. ``result`` distinguishes a technical
    failure (no signal) from no_benefit / harmful / success (real signal)."""

    affinity: str
    target_conflict: str                   # the conflict id it was tried on
    result: str                            # one of TRIAL_RESULTS
    scope: str = "unknown"                 # task scope; "unknown" for missing, never silently empty
    method_variant: str = "unknown"
    count: int = 1


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
    # Optional, appended (positional construction of the first two stays valid): which core commit and
    # schema produced the snapshot, and per-field source/confidence marks (direct / derived / unknown)
    # so a consumer can see what is real vs. absent. All default to empty -> older callers unaffected.
    core_commit: str = ""
    schema_version: str = ""
    field_sources: dict = field(default_factory=dict)


@dataclass(frozen=True)
class EpistemicGapSnapshot:
    """A read-only projection of the epistemic state relevant to finding solution spaces. Only OPEN
    conflicts / live gaps appear - a resolved conflict is simply absent (so it can never be proposed
    as a blind spot again, which is the intervention-sensitivity the contract requires)."""

    conflicts: tuple[ConflictGap, ...] = ()
    evidence_gaps: tuple[EvidenceGap, ...] = ()
    method_history: tuple[MethodRecord, ...] = ()       # the general repertoire (affinities carried)
    method_trials: tuple[MethodTrial, ...] = ()         # scope-bound per-conflict trial OUTCOMES
    open_questions: tuple[OpenQuestion, ...] = ()
    provenance: SnapshotProvenance = field(default_factory=SnapshotProvenance)
