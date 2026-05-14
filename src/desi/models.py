"""Data models for DESi.

Reconciled with the canonical Dynamic Epistemic Sequencer (DES) sources.

Provenance:
    # Source: DES repo (https://github.com/hstre/DES.git)
    # Branch: claude/des-prototype-v0.1-xOEbF
    # Commit: 73ed34e09007da49fac17d2828ba8cb1c16c929c
    # File:   des.py (Claim @ L41-69; transitions T1..T9 @ L14-22)

    # Branch: paper7/noise-and-halflife
    # Commit: e5bd65ccc2c062a72c52a8fcef36f11f0aedcf21
    # File:   paper7/en.py (EN event dict @ L41-62)
    # File:   paper7/run_p7.py (per-loop record @ L258-277; failure modes @ L285-294)

    # Branch: paper8/method-operators
    # Commit: 2b39dd102363743ae5039dd9e24d7a923eb052df
    # File:   paper8/mol.py (OPERATOR_LIBRARY method operators)

See LEGACY_REUSE.md for the full provenance ledger and the rules under which
DESi may deviate from DES.

DESi accepts both the DES-canonical field names (e.g. ``loop``,
``semantic_duplication_rate``, ``id``) and the DESi project-charter aliases
(``loop_index``, ``dup_rate``, ``claim_id``, ``novel_claims_next``). Unknown
fields are preserved (``extra="allow"``) so real DES trajectory dumps round-
trip through DESi without information loss.
"""
from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


# ---------------------------------------------------------------------------
# Operators
# ---------------------------------------------------------------------------
#
# T1..T9 are the canonical DES base scheduler transitions. The names below
# match DES priority-table order.
#
# Source: DES claude/des-prototype-v0.1-xOEbF, des.py:14-22
# Commit: 73ed34e09007da49fac17d2828ba8cb1c16c929c


class Operator(str, Enum):
    """DES canonical operators.

    Members T1..T9 are the base scheduler transitions. The remaining members
    are paper8 method operators (paper8/mol.py @
    2b39dd102363743ae5039dd9e24d7a923eb052df). All other names are not part
    of DES and must not be invented here.
    """

    # T1..T9 — base scheduler. Function-name aliases match des.py exactly.
    T1 = "T1"  # resolve_conflict
    T2 = "T2"  # make_conflict_explicit
    T3 = "T3"  # request_evidence
    T4 = "T4"  # decompose_claim
    T5 = "T5"  # generate_counter_hypothesis
    T6 = "T6"  # explore_evidence_path
    T7 = "T7"  # refine_qualifier
    T8 = "T8"  # seal_claim
    T9 = "T9"  # trigger_reframing

    # Paper 8 method operators. Added — they do not replace T1..T9.
    RECURSIVE_MODULATION = "recursive_modulation"
    BOUNDARY_CONDITION_ANALYSIS = "boundary_condition_analysis"
    ADAPTIVE_VARIATION_SELECTION = "adaptive_variation_selection"
    COUNTEREXAMPLE_SEARCH = "counterexample_search"


_OPERATOR_FUNCTION_NAME_TO_T = {
    "resolve_conflict": "T1",
    "make_conflict_explicit": "T2",
    "request_evidence": "T3",
    "decompose_claim": "T4",
    "generate_counter_hypothesis": "T5",
    "explore_evidence_path": "T6",
    "refine_qualifier": "T7",
    "seal_claim": "T8",
    "trigger_reframing": "T9",
}


def normalize_operator(value: Any) -> str:
    """Accept DES canonical names, T-codes, and method-operator strings."""
    if value is None:
        return ""
    s = str(value).strip()
    if not s:
        return s
    # Function-name form -> T-code
    key = s.lower()
    if key in _OPERATOR_FUNCTION_NAME_TO_T:
        return _OPERATOR_FUNCTION_NAME_TO_T[key]
    # T-code (case-insensitive)
    if s.upper().startswith("T") and s[1:].isdigit():
        return s.upper()
    # Method operator (paper8) — keep snake_case
    return s


# ---------------------------------------------------------------------------
# Failure modes
# ---------------------------------------------------------------------------
#
# Canonical DES set: paper7/run_p7.py:285-294 + paper7/run_appendix_a.py:248.
# DESi-only additions are clearly labelled and must not be emitted as DES
# semantics.


class FailureMode(str, Enum):
    """Trajectory failure-mode labels.

    Canonical DES failure modes (paper7/run_p7.py:285-294 @
    e5bd65ccc2c062a72c52a8fcef36f11f0aedcf21):

        ENTROPY_COLLAPSE       — last-5 entropy > 0.80
        SEMANTIC_DUPLICATION   — dup_rate > 0.60
        NOVELTY_COLLAPSE       — last-10 loops with novel_claims == 0
        GRAPH_TOO_LARGE        — total_claims > 500
        METHOD_COLLAPSE        — method-diversity score < 0.30 over last 5

    DESi-only (have no DES canonical source; do not emit when writing DES
    trajectories):

        NONE                   — sentinel for "no failure"
        ATTRACTOR_LOCK         — DESi heuristic for terminal attractor
        PREMATURE_TERMINATION  — DESi heuristic for early termination
        DRIFT                  — DESi heuristic for question drift
        DEAD_BRANCH            — DESi heuristic for unrecoverable branch
    """

    # DES canonical
    ENTROPY_COLLAPSE = "ENTROPY_COLLAPSE"
    SEMANTIC_DUPLICATION = "SEMANTIC_DUPLICATION"
    NOVELTY_COLLAPSE = "NOVELTY_COLLAPSE"
    GRAPH_TOO_LARGE = "GRAPH_TOO_LARGE"
    METHOD_COLLAPSE = "METHOD_COLLAPSE"
    # DESi-only
    NONE = "NONE"
    ATTRACTOR_LOCK = "ATTRACTOR_LOCK"
    PREMATURE_TERMINATION = "PREMATURE_TERMINATION"
    DRIFT = "DRIFT"
    DEAD_BRANCH = "DEAD_BRANCH"


# ---------------------------------------------------------------------------
# Claim — SPO triple, matches DES dataclass exactly.
# ---------------------------------------------------------------------------
#
# Source: DES claude/des-prototype-v0.1-xOEbF, des.py:41-69
# Commit: 73ed34e09007da49fac17d2828ba8cb1c16c929c


class ClaimState(BaseModel):
    """Mirror of DES `Claim`.

    Field semantics, defaults, and the status / modality literal sets match
    DES exactly. ``claim_id`` is exposed as an alias of the DES field ``id``
    for DESi-charter compatibility — both forms load.
    """

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    # DES canonical fields
    id: str = Field(..., validation_alias="id", serialization_alias="id")
    subject: str = ""
    predicate: str = ""
    object: str = ""
    # status ∈ {unknown, supported, disputed, contradicted, underspecified}
    status: str = "unknown"
    confidence: float = 0.5
    # modality ∈ {hypothesis, suggestion, evidence, established}
    modality: str = "hypothesis"
    evidence_refs: list[str] = Field(default_factory=list)
    scope: dict[str, Any] = Field(default_factory=dict)
    qualifier: dict[str, Any] = Field(default_factory=dict)
    conflict: bool = False
    branch_open: bool = False
    sealed: bool = False
    is_synthesis: bool = False
    is_role_generated: bool = False
    generated_by: str = ""
    history: list[str] = Field(default_factory=list)  # operator codes, e.g. ["T3","T4"]
    parent_id: str | None = None

    @model_validator(mode="before")
    @classmethod
    def _accept_claim_id_alias(cls, data: Any) -> Any:
        """Accept the DESi-charter alias ``claim_id`` as input for ``id``."""
        if isinstance(data, dict) and "id" not in data and "claim_id" in data:
            data = {**data, "id": data["claim_id"]}
        return data

    @property
    def claim_id(self) -> str:
        """DESi-charter alias for DES ``id``."""
        return self.id


# ---------------------------------------------------------------------------
# EN event — Epistemic Navigator probe outcome.
# ---------------------------------------------------------------------------
#
# Source: DES paper7/noise-and-halflife, paper7/en.py @ L41-62
# Commit: e5bd65ccc2c062a72c52a8fcef36f11f0aedcf21
# Composite: 0.5*novelty + 0.3*non_drift + 0.2*float(admitted)
# Post-hoc: paper7/run_p7.py:548 writes back `novelty_produced_next_loop`.


class ENEvent(BaseModel):
    """Mirror of the DES EN event dict (paper7/en.py)."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    loop_index: int = Field(..., validation_alias="loop_index")
    persona: str | None = None

    # DES-canonical scores
    eni_novelty: float
    eni_non_drift: float | None = None
    eni_admissibility: float | None = None
    eni_composite: float | None = None  # DES computes this; DESi never recomputes
    admitted: bool = False
    rejection_reason: str | None = None
    question: str | None = None

    # Post-hoc augmentation (paper7/run_p7.py:548)
    # DESi-charter alias: ``novel_claims_next`` accepted on input.
    novelty_produced_next_loop: int | None = None
    novel_claims_next: int | None = None  # deprecated alias kept for the project charter

    # Context (DESi addition; helpful for downstream metrics)
    dup_rate_before: float | None = None
    dup_rate_after: float | None = None

    @model_validator(mode="before")
    @classmethod
    def _normalise(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        normalised = dict(data)
        # accept DES-canonical ``loop`` as ``loop_index``
        if "loop_index" not in normalised and "loop" in normalised:
            normalised["loop_index"] = normalised["loop"]
        # mirror novel_claims_next <-> novelty_produced_next_loop
        if (
            "novelty_produced_next_loop" not in normalised
            and "novel_claims_next" in normalised
        ):
            normalised["novelty_produced_next_loop"] = normalised["novel_claims_next"]
        elif (
            "novel_claims_next" not in normalised
            and "novelty_produced_next_loop" in normalised
        ):
            normalised["novel_claims_next"] = normalised["novelty_produced_next_loop"]
        return normalised


# ---------------------------------------------------------------------------
# Per-loop trajectory step.
# ---------------------------------------------------------------------------
#
# Source: DES paper7/noise-and-halflife, paper7/run_p7.py:258-277
# Commit: e5bd65ccc2c062a72c52a8fcef36f11f0aedcf21
#
# DESi accepts both the DESi-charter aliases (``loop_index``, ``dup_rate``)
# and the DES-canonical names (``loop``, ``semantic_duplication_rate``).


class TrajectoryStep(BaseModel):
    """Mirror of the DES per-loop metrics record."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    loop_index: int
    # DESi-charter convenience fields
    focus_claim_id: str | None = None
    operator: str  # canonical T-code (e.g. "T3") or method-operator slug
    novel_claims: int = 0
    dup_rate: float = 0.0
    failure_mode: FailureMode | str | None = None
    claims: list[ClaimState] = Field(default_factory=list)
    # Fix 1 (external-reality challenge): per-step list of metric names
    # that were ABSENT from the input dict (vs explicitly set to 0).
    # Populated by `_normalise` before model construction; consumed by
    # `validate_step_metric_coherence` to avoid mislabelling missing
    # data as contradictory.
    missing_metrics: list[str] = Field(default_factory=list, alias="_missing_metrics")

    # DES-canonical extras (preserved when present; not required)
    question: str | None = None
    method_type: str | None = None
    frame_type: str | None = None
    claim_curvature: float | None = None
    claim_count: int | None = None
    total_claims: int | None = None
    open_claims: int | None = None
    sealed_claims: int | None = None
    disputed_claims: int | None = None
    redundant_claims: int | None = None
    entropy: float | None = None
    branch_growth: int | None = None
    contradictions_resolved: int | None = None
    total_contradictions: int | None = None
    question_utility: float | None = None

    @model_validator(mode="before")
    @classmethod
    def _normalise(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        normalised = dict(data)
        # DES `loop` -> DESi `loop_index`
        if "loop_index" not in normalised and "loop" in normalised:
            normalised["loop_index"] = normalised["loop"]
        # DES `semantic_duplication_rate` -> DESi `dup_rate`
        if (
            "dup_rate" not in normalised
            and "semantic_duplication_rate" in normalised
        ):
            normalised["dup_rate"] = normalised["semantic_duplication_rate"]
        # canonicalise operator code
        if "operator" in normalised:
            normalised["operator"] = normalize_operator(normalised["operator"])
        # Fix 1 (external-reality challenge): record which metric fields
        # were originally absent from the input dict. Cycle-6's
        # `validate_step_metric_coherence` consults this to distinguish
        # "missing data" from "self-contradictory data". Without this,
        # all-zero defaults on schema-impoverished input look identical
        # to a deliberate dup=0/novel=0 step authored by hand.
        missing: list[str] = []
        for key in ("novel_claims", "dup_rate"):
            # Treat as missing iff the canonical key AND any known DES
            # alias are all absent from the raw input.
            present = key in data
            if key == "dup_rate":
                present = present or "semantic_duplication_rate" in data
            if not present:
                missing.append(key)
        normalised["_missing_metrics"] = missing
        return normalised


# ---------------------------------------------------------------------------
# Top-level trajectory document.
# ---------------------------------------------------------------------------
#
# This wrapper is a DESi construct: DES itself persists EpistemicState (a
# claim graph) plus log files. A "trajectory" in DESi terms is a sequence of
# DES per-loop records plus paper7 EN events, packaged for meta-analysis.


class Trajectory(BaseModel):
    """A DES trajectory packaged for DESi meta-analysis.

    DESi accepts a `claims` dict in DES `EpistemicState` form via the
    optional `epistemic_state` extra field; current DESi diagnostics only
    consume `steps` and `en_events`.
    """

    model_config = ConfigDict(extra="allow")

    trajectory_id: str
    domain: str | None = None
    seed: str | None = None
    persona: str | None = None
    steps: list[TrajectoryStep] = Field(default_factory=list)
    en_events: list[ENEvent] = Field(default_factory=list)
    terminal_failure_mode: FailureMode | str | None = None
    # Fix 3 (external-reality challenge): origin of this trajectory's data.
    # Canonical values:
    #   "hand_authored_fixture"     — DESi-side hand-built test fixture
    #   "translator_heuristic"      — synth fields fabricated by a translator
    #   "live_DES"                  — native DES output (no DESi-side fields)
    #   "translated_DES_conservative" — DES output translated with no synth
    # Default None preserves backward compatibility with pre-fix trajectories;
    # downstream consumers treat None as "hand_authored_fixture" for the
    # report-disclaimer test (the existing n=10 and n=20 suites are all
    # hand-authored).
    input_origin: str | None = None
