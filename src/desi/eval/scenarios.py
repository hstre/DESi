"""Seven controlled problem-class scenarios for v0.4.

Each scenario is a reproducible (Trajectory, expectation) pair plus a
small set of follow-up actions the harness performs to surface a
specific structural pattern. v0.4 cannot change DESi behaviour, so a
scenario's *expectation* is the observation pattern that should appear
in the recorded memory + emitted timeline when DESi runs against the
trajectory.

The seven scenarios are:

* S1 — exclusive claim: one method-strong claim survives.
* S2 — contradictory claims: a CONTRADICTS edge must be observable.
* S3 — plausible nonsense: content alone must not promote a claim.
* S4 — uncomfortable truth: method-strong, intuition-weak claim.
* S5 — branching problem: two claims stay open simultaneously.
* S6 — premature merge trap: scenario provides a tempting merge that
  the harness records as *refused* (the memory must NOT contain a
  MERGED_INTO edge for the trap pair).
* S7 — memory trap: an old claim is preloaded; recording the new
  trajectory must not silently inherit its method.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from ..memory.relations import RelationType
from ..models import Trajectory, TrajectoryStep


@dataclass(frozen=True)
class ScenarioExpectation:
    """What the harness should be able to verify after running.

    Each field is optional; absent fields are not asserted.
    """

    # Required minimum count of timeline events of a given type.
    min_event_counts: dict[str, int] = field(default_factory=dict)
    # Required relation types that must appear in the recorded store.
    required_relation_types: tuple[str, ...] = ()
    # Relation types that MUST NOT appear in the recorded store.
    forbidden_relation_types: tuple[str, ...] = ()
    # Required claim_ids in the store.
    required_claim_ids: tuple[str, ...] = ()
    # Free-form notes for human readers.
    notes: str = ""


@dataclass(frozen=True)
class Scenario:
    """A reproducible problem-class probe."""

    scenario_id: str
    name: str
    description: str
    trajectory_factory: Callable[[], Trajectory]
    expectation: ScenarioExpectation
    # Post-run hook callbacks the harness invokes after compute_all.
    # The hook may emit guard events, merge-refusal events, etc., via
    # the session's emitter methods. None when no post-run actions
    # are required.
    post_run: Callable[[Any], None] | None = None
    # Optional pre-run callback, used by S7 to seed the recorder with
    # a "stale" claim that pre-dates the trajectory.
    pre_run: Callable[[Any], None] | None = None


# ---------------------------------------------------------------------------
# Trajectory builders
# ---------------------------------------------------------------------------


def _step(loop: int, op: str, focus: str | None = None,
          **extra: Any) -> TrajectoryStep:
    return TrajectoryStep(loop_index=loop, operator=op,
                          focus_claim_id=focus, **extra)


def _trajectory_s1() -> Trajectory:
    # Three competing claims; only C001 receives a method-strong path.
    return Trajectory(
        trajectory_id="s1_exclusive",
        steps=[
            _step(0, "T6", "C001"),    # hypothesis_builder
            _step(1, "T2", "C001"),    # make_conflict_explicit (kept on C001)
            _step(2, "T6", "C002"),    # competing hypothesis
            _step(3, "T1", "C002"),    # weak resolve
            _step(4, "T6", "C003"),    # third candidate
            _step(5, "T8", "C001"),    # seal_claim back on C001
        ],
        en_events=[],
    )


def _trajectory_s2() -> Trajectory:
    # Two contradictory hypotheses sharing a parent claim.
    return Trajectory(
        trajectory_id="s2_contradictions",
        steps=[
            _step(0, "T6", "C001"),
            _step(1, "T6", "C002"),    # hypothesis A
            _step(2, "T2", "C002"),    # explicit conflict
            _step(3, "T6", "C003"),    # hypothesis B
            _step(4, "T2", "C003"),    # explicit conflict
        ],
        en_events=[],
    )


def _trajectory_s3() -> Trajectory:
    # A claim with strong-sounding content but weak operator path.
    return Trajectory(
        trajectory_id="s3_plausible_nonsense",
        steps=[
            _step(0, "T1", "C001"),    # weak resolve, no hypothesis_builder
            _step(1, "T1", "C002"),
        ],
        en_events=[],
    )


def _trajectory_s4() -> Trajectory:
    # Method is strong (T6 + T3 evidence + T8 seal); intuition would say
    # the conclusion is uncomfortable but the path is sound.
    return Trajectory(
        trajectory_id="s4_uncomfortable_truth",
        steps=[
            _step(0, "T6", "C001"),
            _step(1, "T3", "C001"),
            _step(2, "T2", "C001"),
            _step(3, "T8", "C001"),
        ],
        en_events=[],
    )


def _trajectory_s5() -> Trajectory:
    # Two branches stay open in parallel — focus alternates.
    return Trajectory(
        trajectory_id="s5_branching",
        steps=[
            _step(0, "T6", "B_left"),
            _step(1, "T6", "B_right"),
            _step(2, "T3", "B_left"),
            _step(3, "T3", "B_right"),
            _step(4, "T2", "B_left"),
            _step(5, "T2", "B_right"),
        ],
        en_events=[],
    )


def _trajectory_s6() -> Trajectory:
    # Two distinct hypotheses with surface-similar focus ids;
    # the harness's post_run hook *refuses* a tempting merge.
    return Trajectory(
        trajectory_id="s6_refused_merge",
        steps=[
            _step(0, "T6", "C_alpha"),
            _step(1, "T3", "C_alpha"),
            _step(2, "T6", "C_alpha_prime"),    # tempting near-duplicate
            _step(3, "T3", "C_alpha_prime"),
        ],
        en_events=[],
    )


def _trajectory_s7() -> Trajectory:
    # New trajectory that touches a claim id that the pre_run hook
    # seeded into the recorder with weak method.
    return Trajectory(
        trajectory_id="s7_memory_trap",
        steps=[
            _step(0, "T6", "C_legacy"),    # would otherwise inherit "human" method
            _step(1, "T3", "C_legacy"),
        ],
        en_events=[],
    )


# ---------------------------------------------------------------------------
# Post-run / pre-run callbacks
# ---------------------------------------------------------------------------


def _post_s2_contradictions(session) -> None:
    """Emit two CONTRADICTS edges between the two hypotheses and the parent.

    The session's underlying recorder holds the active run; emit
    relations into it via the recorder, then surface a timeline event.
    """
    rec = session._recorder
    rec.record_relation(source="C002", target="C003",
                        rel_type=RelationType.CONTRADICTS)
    session.hook.emit_relation(source="C002", target="C003",
                                rel_type=RelationType.CONTRADICTS)
    rec.record_relation(source="C003", target="C002",
                        rel_type=RelationType.CONTRADICTS)
    session.hook.emit_relation(source="C003", target="C002",
                                rel_type=RelationType.CONTRADICTS)


def _post_s5_branching(session) -> None:
    """Mark both branches as still open at run end (no auto-merge)."""
    session.hook.emit_guard_passed(operator="branch_keeper", loop_index=5)


def _post_s6_refused_merge(session) -> None:
    """Record the *refused* merge: a guard blocks it."""
    session.hook.emit_guard_blocked(
        operator="merge_claims",
        loop_index=4,
        guard_result="blocked",
        reason="surface_similarity_only; methodological_distinctness_unverified",
    )


def _pre_s7_seed_legacy_claim(session) -> None:
    """Seed a method-weak legacy claim into the recorder before the run.

    The session is post-construction but pre-on_run_start at this
    point. The recorder is not yet inside an active run, so we open
    a short bookkeeping run, write the legacy claim, and close it.
    The actual scenario run starts immediately after.
    """
    rec = session._recorder
    rec.start_run(
        run_id="run_s7_legacy_seed",
        model="legacy_seed",
        config={"seed_for": "s7"},
        label="s7_legacy_seed",
    )
    rec.record_claim(
        content="C_legacy",
        method="hearsay",     # deliberately weak
        operator_path=("hearsay",),
        claim_id="C_legacy_old",   # distinct id; the trap is content-similarity
    )
    rec.end_run()


# ---------------------------------------------------------------------------
# Scenario registry
# ---------------------------------------------------------------------------


SCENARIOS: tuple[Scenario, ...] = (
    Scenario(
        scenario_id="S1",
        name="exclusive_claim",
        description="Three competing claims; one has a method-strong path.",
        trajectory_factory=_trajectory_s1,
        expectation=ScenarioExpectation(
            required_claim_ids=("C001", "C002", "C003"),
            min_event_counts={"operator_started": 6, "claim_created": 3},
            notes="Memory must record all three; only C001 receives T8 seal.",
        ),
    ),
    Scenario(
        scenario_id="S2",
        name="contradictory_claims",
        description="Two hypotheses contradict each other.",
        trajectory_factory=_trajectory_s2,
        expectation=ScenarioExpectation(
            required_claim_ids=("C001", "C002", "C003"),
            required_relation_types=("CONTRADICTS",),
            min_event_counts={"relation_created": 2},
            notes="Two CONTRADICTS edges expected (one per direction).",
        ),
        post_run=_post_s2_contradictions,
    ),
    Scenario(
        scenario_id="S3",
        name="plausible_nonsense",
        description="Surface plausibility, weak method.",
        trajectory_factory=_trajectory_s3,
        expectation=ScenarioExpectation(
            required_claim_ids=("C001", "C002"),
            min_event_counts={"claim_created": 2},
            forbidden_relation_types=(),
            notes="Method is recorded as T1 (weak resolve); harness verifies "
                  "memory does not silently upgrade method to T6.",
        ),
    ),
    Scenario(
        scenario_id="S4",
        name="uncomfortable_truth",
        description="Method strong, conclusion unintuitive.",
        trajectory_factory=_trajectory_s4,
        expectation=ScenarioExpectation(
            required_claim_ids=("C001",),
            min_event_counts={"operator_started": 4},
            notes="Operator path T6 -> T3 -> T2 -> T8 must be visible.",
        ),
    ),
    Scenario(
        scenario_id="S5",
        name="branching_problem",
        description="Two parallel branches stay open.",
        trajectory_factory=_trajectory_s5,
        expectation=ScenarioExpectation(
            required_claim_ids=("B_left", "B_right"),
            min_event_counts={
                "branch_opened": 2,
                "branch_closed": 2,    # both closed at run end
            },
            notes="Branches are alternated; both must appear as opened.",
        ),
        post_run=_post_s5_branching,
    ),
    Scenario(
        scenario_id="S6",
        name="refused_merge",
        description="A tempting near-duplicate; merge must be refused.",
        trajectory_factory=_trajectory_s6,
        expectation=ScenarioExpectation(
            required_claim_ids=("C_alpha", "C_alpha_prime"),
            forbidden_relation_types=("MERGED_INTO",),
            min_event_counts={"guard_blocked": 1},
            notes="No MERGED_INTO edge between the two hypotheses; one "
                  "guard_blocked event is expected.",
        ),
        post_run=_post_s6_refused_merge,
    ),
    Scenario(
        scenario_id="S7",
        name="memory_trap",
        description="Stale claim in memory; new run must not inherit method.",
        trajectory_factory=_trajectory_s7,
        expectation=ScenarioExpectation(
            required_claim_ids=("C_legacy",),
            notes="Two distinct claims share content C_legacy: one with "
                  "method 'hearsay' (legacy), one with method 'T6'. The "
                  "harness verifies both exist; memory does not collapse "
                  "them.",
        ),
        pre_run=_pre_s7_seed_legacy_claim,
    ),
)


def list_scenarios() -> list[Scenario]:
    return list(SCENARIOS)


def scenario_by_id(scenario_id: str) -> Scenario:
    for s in SCENARIOS:
        if s.scenario_id == scenario_id:
            return s
    raise KeyError(f"unknown scenario_id: {scenario_id!r}")
