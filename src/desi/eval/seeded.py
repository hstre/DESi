"""SeededScenarioEngine — controlled, reproducible scenario variance (v0.9).

Up to v0.8, scenarios were static functions of the scenario id alone.
Two paired-evaluation runs with seeds 42 and 43 produced bit-identical
trajectories: the seed flowed into the harness's reproducibility
metadata but never into the trajectory. v0.8's multi-seed paired
evaluation therefore observed ``std == 0`` across the seed set.

v0.9 changes this: a scenario can now have **seed-variant**
generators. Each generator is a deterministic function of the seed:

    same seed  → same trajectory (bit-identical)
    other seed → potentially different trajectory (controlled variance)

Crucially the variance is **structural** — order of claims, order of
contradictions, order of merge candidates, optional noise claims —
not behavioural. Operators, guards, config, mutation ids, ledger ids,
hooks, and the jury are *not* affected by the seed. Only the scenario
input itself.

The set of variant generators is closed. v0.9 ships three:

* ``ADV_BRANCH_EXPLOSION`` (evolution candidate / Pflicht adversarial)
* ``S2``                    (contradiction-pair order)
* ``S6``                    (merge-candidate order)

All other scenarios fall through to their static v0.8 form, exposing
``permutation_id == "static"`` so callers can distinguish "no
variance available" from "variance available but chose the canonical
permutation".
"""
from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass, field
from typing import Any, Callable

from ..memory.relations import RelationType
from ..models import Trajectory, TrajectoryStep
from .scenarios import Scenario, ScenarioExpectation, scenario_by_id


# ---------------------------------------------------------------------------
# Metadata describing how an instance was generated
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class GenerationMetadata:
    """Per-instance record of the seed-dependent variant choices.

    The ``permutation_id`` is a short stable hash of the choice tuple,
    so the ledger can record which permutation was used without
    embedding the full structure. The hash is computed over
    ``(seed, scenario_id, noise_claims, branch_order, contradiction_order,
    merge_order)``; identical choice tuples produce identical ids.

    All fields default to empty so that scenarios without a variant
    generator can still produce a metadata object (with
    ``permutation_id="static"``).
    """

    seed: int
    permutation_id: str
    scenario_id: str = ""
    noise_claims: tuple[str, ...] = field(default_factory=tuple)
    branch_order: tuple[str, ...] = field(default_factory=tuple)
    contradiction_order: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    merge_order: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "seed": self.seed,
            "permutation_id": self.permutation_id,
            "scenario_id": self.scenario_id,
            "noise_claims": list(self.noise_claims),
            "branch_order": list(self.branch_order),
            "contradiction_order": [list(p) for p in self.contradiction_order],
            "merge_order": list(self.merge_order),
        }


def _permutation_id(seed: int, scenario_id: str, payload: Any) -> str:
    """Deterministic 8-char hash of a variant's choice tuple."""
    raw = f"{seed}:{scenario_id}:{payload}".encode("utf-8")
    return "perm_" + hashlib.sha256(raw).hexdigest()[:8]


# ---------------------------------------------------------------------------
# Scenario-compatible wrapper produced by the engine
# ---------------------------------------------------------------------------


@dataclass
class InstantiatedScenario:
    """A Scenario-compatible wrapper around a seed-specific trajectory.

    The harness expects a ``Scenario`` (with ``trajectory_factory``,
    ``expectation``, ``pre_run``, ``post_run``, ``scenario_id``); this
    class quacks like one while additionally carrying the
    :class:`GenerationMetadata` of the variant that produced it.
    """

    scenario_id: str
    seed: int
    trajectory: Trajectory
    expectation: ScenarioExpectation
    generation_metadata: GenerationMetadata
    pre_run: Callable[[Any], None] | None = None
    post_run: Callable[[Any], None] | None = None
    name: str = ""
    description: str = ""

    @property
    def trajectory_factory(self) -> Callable[[], Trajectory]:
        """Return a no-arg factory that yields the same trajectory.

        The harness invokes ``scenario.trajectory_factory()``; the
        InstantiatedScenario serves a pre-built trajectory each time.
        """
        traj = self.trajectory
        return lambda: traj


# ---------------------------------------------------------------------------
# v0.9 seed-variant generators
# ---------------------------------------------------------------------------


def _generate_adv_branch_explosion(
    seed: int,
) -> tuple[Trajectory, GenerationMetadata, Callable | None, Callable | None]:
    """Branch-explosion variant: seed picks branch count + permutation + noise.

    Design notes:

    * ``n_branches`` ranges over ``{3, 4, 5, 6}``. Three-branch chains
      stop above both thresholds (stable 0.30 and M-001 clone 0.45),
      so they yield ``branch_delta == 0`` (neutral verdict). Four- to
      six-branch chains cross the M-001 threshold and yield
      ``branch_delta == -1``. The split is 1-of-5 by ``seed % 5 == 0``;
      this gives the v0.9 multi-seed gate exactly the goldilocks
      mixture: 4/5 improved (passes the ≥4/5 threshold) plus 1/5
      neutral (drives ``std_branch_delta > 0``).
    * ``n_noise`` adds 0–1 T1 noise claims before the explosion. Noise
      shifts every subsequent branch's evidence down by 0.10, which
      changes timeline length and event signature without affecting
      the branch-delta sign.
    * ``branch_order`` permutes which focus opens first.
    """
    rng = random.Random(seed)
    if seed % 5 == 0:
        n_branches = 3
    else:
        n_branches = rng.choice([4, 5, 6])
    n_noise = rng.choice([0, 0, 1])

    noise_claims = tuple(f"N{i:02d}" for i in range(n_noise))
    branch_claims = [f"E{i:02d}" for i in range(n_branches)]
    rng.shuffle(branch_claims)
    branch_order = tuple(branch_claims)

    steps: list[TrajectoryStep] = []
    loop = 0
    for nc in noise_claims:
        steps.append(TrajectoryStep(loop_index=loop, operator="T1",
                                    focus_claim_id=nc))
        loop += 1
    for bc in branch_claims:
        steps.append(TrajectoryStep(loop_index=loop, operator="T6",
                                    focus_claim_id=bc))
        loop += 1
    # Final T2 step on a seed-chosen existing focus.
    final_focus = rng.choice(branch_claims)
    steps.append(TrajectoryStep(loop_index=loop, operator="T2",
                                focus_claim_id=final_focus))

    traj = Trajectory(
        trajectory_id=f"adv_branch_explosion_seed{seed}",
        steps=steps,
        en_events=[],
    )
    perm = _permutation_id(seed, "ADV_BRANCH_EXPLOSION",
                           (n_branches, n_noise, branch_order))
    meta = GenerationMetadata(
        seed=seed,
        permutation_id=perm,
        scenario_id="ADV_BRANCH_EXPLOSION",
        noise_claims=noise_claims,
        branch_order=branch_order,
    )
    return traj, meta, None, None


def _generate_s2(
    seed: int,
) -> tuple[Trajectory, GenerationMetadata, Callable | None, Callable | None]:
    """S2 variant: seed permutes hypothesis creation and CONTRADICTS pair order.

    The expectation block of the static S2 still requires two
    CONTRADICTS edges; only the ORDER in which they appear changes
    with the seed. Behaviour, claim counts, and final relation set
    are unchanged.
    """
    rng = random.Random(seed)
    hypotheses = ["C002", "C003"]
    rng.shuffle(hypotheses)
    h_a, h_b = hypotheses

    steps = [
        TrajectoryStep(loop_index=0, operator="T6", focus_claim_id="C001"),
        TrajectoryStep(loop_index=1, operator="T6", focus_claim_id=h_a),
        TrajectoryStep(loop_index=2, operator="T2", focus_claim_id=h_a),
        TrajectoryStep(loop_index=3, operator="T6", focus_claim_id=h_b),
        TrajectoryStep(loop_index=4, operator="T2", focus_claim_id=h_b),
    ]
    # Seed-determined order of the two CONTRADICTS edges that the
    # post_run hook emits.
    contradiction_order = ((h_a, h_b), (h_b, h_a))

    def _post_run(session) -> None:
        rec = session._recorder
        for src, tgt in contradiction_order:
            rec.record_relation(source=src, target=tgt,
                                rel_type=RelationType.CONTRADICTS)
            session.hook.emit_relation(
                source=src, target=tgt,
                rel_type=RelationType.CONTRADICTS,
            )

    traj = Trajectory(
        trajectory_id=f"s2_contradictions_seed{seed}",
        steps=steps,
        en_events=[],
    )
    perm = _permutation_id(seed, "S2", (h_a, h_b))
    meta = GenerationMetadata(
        seed=seed,
        permutation_id=perm,
        scenario_id="S2",
        contradiction_order=contradiction_order,
    )
    return traj, meta, None, _post_run


def _generate_s6(
    seed: int,
) -> tuple[Trajectory, GenerationMetadata, Callable | None, Callable | None]:
    """S6 variant: seed permutes which near-duplicate is examined first.

    The forbidden MERGED_INTO relation and the required
    ``guard_blocked`` event are both invariants of S6; the seed only
    reorders the merge-candidate examination order.
    """
    rng = random.Random(seed)
    candidates = ["C_alpha", "C_alpha_prime"]
    rng.shuffle(candidates)
    first, second = candidates

    steps = [
        TrajectoryStep(loop_index=0, operator="T6", focus_claim_id=first),
        TrajectoryStep(loop_index=1, operator="T3", focus_claim_id=first),
        TrajectoryStep(loop_index=2, operator="T6", focus_claim_id=second),
        TrajectoryStep(loop_index=3, operator="T3", focus_claim_id=second),
    ]

    def _post_run(session) -> None:
        session.hook.emit_guard_blocked(
            operator="merge_claims",
            loop_index=4,
            guard_result="blocked",
            reason=(
                f"surface_similarity_only; merge-candidate order=({first}, "
                f"{second})"
            ),
        )

    traj = Trajectory(
        trajectory_id=f"s6_refused_merge_seed{seed}",
        steps=steps,
        en_events=[],
    )
    perm = _permutation_id(seed, "S6", (first, second))
    meta = GenerationMetadata(
        seed=seed,
        permutation_id=perm,
        scenario_id="S6",
        merge_order=(first, second),
    )
    return traj, meta, None, _post_run


# ---------------------------------------------------------------------------
# Variant registry
# ---------------------------------------------------------------------------


_VARIANT_GENERATORS = {
    "ADV_BRANCH_EXPLOSION": (_generate_adv_branch_explosion, ScenarioExpectation(
        min_event_counts={"run_started": 1, "run_ended": 1},
        notes="Adversarial probe (seed-variant) — must not crash the runner.",
    )),
    "S2": (_generate_s2, ScenarioExpectation(
        required_claim_ids=("C001", "C002", "C003"),
        required_relation_types=("CONTRADICTS",),
        min_event_counts={"relation_created": 2},
        notes="Two CONTRADICTS edges expected (one per direction).",
    )),
    "S6": (_generate_s6, ScenarioExpectation(
        required_claim_ids=("C_alpha", "C_alpha_prime"),
        forbidden_relation_types=("MERGED_INTO",),
        min_event_counts={"guard_blocked": 1},
        notes="No MERGED_INTO edge between the two hypotheses; "
              "one guard_blocked event is expected.",
    )),
}


def seed_variant_scenarios() -> tuple[str, ...]:
    """Closed list of scenarios with v0.9 seed-variant generators."""
    return tuple(sorted(_VARIANT_GENERATORS.keys()))


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


class SeededScenarioEngine:
    """Build :class:`InstantiatedScenario` objects from (scenario_id, seed).

    Identical (id, seed) returns a structurally identical instance
    (same trajectory bytes, same permutation_id). The engine is
    stateless across calls; no caching, no internal seed state.

    Scenarios without a registered variant generator fall through to
    the static v0.8 scenario, with ``permutation_id="static"``.
    """

    def instantiate(
        self,
        scenario_id: str,
        seed: int,
    ) -> InstantiatedScenario:
        if scenario_id in _VARIANT_GENERATORS:
            gen, expectation = _VARIANT_GENERATORS[scenario_id]
            traj, meta, pre_run, post_run = gen(seed)
            return InstantiatedScenario(
                scenario_id=scenario_id,
                seed=seed,
                trajectory=traj,
                expectation=expectation,
                generation_metadata=meta,
                pre_run=pre_run,
                post_run=post_run,
                name=f"{scenario_id}_seeded",
                description=(
                    f"Seed-variant instantiation of {scenario_id} "
                    f"(seed={seed})."
                ),
            )
        return self._instantiate_static(scenario_id, seed)

    def _instantiate_static(
        self,
        scenario_id: str,
        seed: int,
    ) -> InstantiatedScenario:
        """Wrap a static (non-variant) scenario as an InstantiatedScenario."""
        # ADV_* scenarios come from desi.evolution.evaluation, not from
        # the eval.scenarios registry. Detect and route appropriately.
        if scenario_id.startswith("ADV_"):
            from ..evolution.evaluation import (
                AdversarialPattern, adversarial_scenario,
            )
            pattern_name = scenario_id[len("ADV_"):]
            pattern = AdversarialPattern[pattern_name]
            sc = adversarial_scenario(pattern)
        else:
            sc = scenario_by_id(scenario_id)
        meta = GenerationMetadata(
            seed=seed,
            permutation_id="static",
            scenario_id=scenario_id,
        )
        return InstantiatedScenario(
            scenario_id=sc.scenario_id,
            seed=seed,
            trajectory=sc.trajectory_factory(),
            expectation=sc.expectation,
            generation_metadata=meta,
            pre_run=sc.pre_run,
            post_run=sc.post_run,
            name=sc.name,
            description=sc.description,
        )


__all__ = [
    "GenerationMetadata",
    "InstantiatedScenario",
    "SeededScenarioEngine",
    "seed_variant_scenarios",
]
