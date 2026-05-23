"""EvaluationHarness — runs scenarios and packages their observations.

A single harness instance is single-use per scenario: it builds a
fresh recorder + ObservationSession, runs the scenario through
:func:`desi.runner.run_desi`, takes the post-run snapshot, and
returns an :class:`EvaluationResult` that bundles everything the
researcher needs to audit the run.

Reproducibility: identical scenario + seed + model + config produces
identical (timeline, snapshot list) — wall-clock timestamps are
metadata only and excluded from equality.
"""
from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from ..diagnostics import DeterministicMetrics
from ..memory.recorder import MemoryRecorder
from ..memory.store import InMemoryStore, MemoryStore
from ..observe.session import ObservationSession
from ..observe.snapshot import GraphSnapshot
from ..observe.timeline import EventType, TimelineEvent
from ..runner import run_desi
from .scenarios import Scenario


def config_hash(config: dict[str, Any] | None) -> str:
    """Deterministic 16-char hash of a config dict."""
    if not config:
        return ""
    items = sorted((str(k), str(v)) for k, v in config.items())
    raw = "\x00".join(f"{k}={v}" for k, v in items).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


@dataclass
class EvaluationResult:
    """Complete record of one scenario evaluation."""

    evaluation_id: str
    scenario_id: str
    seed: int
    timestamp: datetime
    model: str
    config_hash: str
    report: DeterministicMetrics
    timeline: list[TimelineEvent]
    snapshots: list[GraphSnapshot]
    expectations_met: dict[str, bool]
    expectations_detail: dict[str, str] = field(default_factory=dict)
    hook_errors: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(self.expectations_met.values())


class EvaluationHarness:
    """Runs scenarios with full observation capture."""

    def __init__(
        self,
        *,
        store_factory=InMemoryStore,
        model: str = "claude-opus-4-7",
        config: dict[str, Any] | None = None,
    ) -> None:
        self._store_factory = store_factory
        self._model = model
        self._config = dict(config or {})

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run_scenario(
        self,
        scenario: Scenario,
        *,
        seed: int = 0,
        evaluation_id: str | None = None,
    ) -> EvaluationResult:
        """Run a single scenario; return its full evaluation record."""
        eval_id = evaluation_id or _new_evaluation_id(scenario.scenario_id, seed)
        timestamp = datetime.now(timezone.utc)

        store = self._store_factory()
        recorder = MemoryRecorder(store)
        session = ObservationSession(
            recorder=recorder,
            model=self._model,
            seed=seed,
            config={**self._config, "scenario_id": scenario.scenario_id,
                    "seed": seed},
        )

        if scenario.pre_run is not None:
            scenario.pre_run(session)

        trajectory = scenario.trajectory_factory()
        # Inline the run_desi lifecycle so that scenario.post_run can
        # write into the still-active run before on_run_end seals it.
        # The result remains identical to run_desi(trajectory,
        # memory_hook=session.hook); the inlining only reorders the
        # post_run callback inside the open-run window.
        from ..diagnostics import compute_all as _compute_all
        session.hook.on_run_start(trajectory)
        for step in trajectory.steps:
            session.hook.on_step(step)
        report = _compute_all(trajectory)
        if scenario.post_run is not None:
            scenario.post_run(session)
        session.hook.on_run_end(report)

        expectations_met, expectations_detail = self._check_expectations(
            scenario, session, store,
        )
        hook_errors = [
            f"{e.stage}: {type(e.exception).__name__}: {e.exception}"
            for e in session.hook.errors
        ]

        return EvaluationResult(
            evaluation_id=eval_id,
            scenario_id=scenario.scenario_id,
            seed=seed,
            timestamp=timestamp,
            model=self._model,
            config_hash=config_hash({**self._config,
                                      "scenario_id": scenario.scenario_id,
                                      "seed": seed}),
            report=report,
            timeline=session.timeline(),
            snapshots=list(session.snapshots),
            expectations_met=expectations_met,
            expectations_detail=expectations_detail,
            hook_errors=hook_errors,
        )

    def run_all(
        self,
        scenarios: list[Scenario] | None = None,
        *,
        seed: int = 0,
    ) -> list[EvaluationResult]:
        from .scenarios import list_scenarios as _ls
        scs = scenarios if scenarios is not None else _ls()
        return [self.run_scenario(s, seed=seed) for s in scs]

    # ------------------------------------------------------------------
    # Expectation checking
    # ------------------------------------------------------------------

    def _check_expectations(
        self,
        scenario: Scenario,
        session: ObservationSession,
        store: MemoryStore,
    ) -> tuple[dict[str, bool], dict[str, str]]:
        exp = scenario.expectation
        met: dict[str, bool] = {}
        detail: dict[str, str] = {}

        # Required claim ids.
        if exp.required_claim_ids:
            store_ids = {c.claim_id for c in store.all_claims()}
            missing = [cid for cid in exp.required_claim_ids
                       if cid not in store_ids]
            met["required_claim_ids"] = not missing
            detail["required_claim_ids"] = (
                "all present" if not missing
                else f"missing: {missing}"
            )

        # Required relation types.
        if exp.required_relation_types:
            relations_internal = getattr(store, "_relations", [])
            present_types = {r.rel_type.value for r in relations_internal}
            missing_types = [t for t in exp.required_relation_types
                             if t not in present_types]
            met["required_relation_types"] = not missing_types
            detail["required_relation_types"] = (
                "all present" if not missing_types
                else f"missing: {missing_types}"
            )

        # Forbidden relation types.
        if exp.forbidden_relation_types:
            relations_internal = getattr(store, "_relations", [])
            present_types = {r.rel_type.value for r in relations_internal}
            forbidden_present = [t for t in exp.forbidden_relation_types
                                 if t in present_types]
            met["forbidden_relation_types_absent"] = not forbidden_present
            detail["forbidden_relation_types_absent"] = (
                "all absent" if not forbidden_present
                else f"unexpectedly present: {forbidden_present}"
            )

        # Minimum event counts by event_type.
        if exp.min_event_counts:
            actual: dict[str, int] = {}
            for ev in session.events:
                key = ev.event_type.value
                actual[key] = actual.get(key, 0) + 1
            shortfalls: list[str] = []
            for et, n_required in exp.min_event_counts.items():
                if actual.get(et, 0) < n_required:
                    shortfalls.append(
                        f"{et}: {actual.get(et, 0)} < {n_required}"
                    )
            met["min_event_counts"] = not shortfalls
            detail["min_event_counts"] = (
                "all met" if not shortfalls
                else "; ".join(shortfalls)
            )

        return met, detail


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _new_evaluation_id(scenario_id: str, seed: int) -> str:
    raw = f"{scenario_id}\x00{seed}\x00{uuid.uuid4().hex[:8]}".encode("utf-8")
    return "eval_" + hashlib.sha256(raw).hexdigest()[:12]
