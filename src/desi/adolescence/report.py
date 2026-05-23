"""v5.0 — sandbox-runtime Pflichtmetriken.

Five metrics (directive § v5.0):

* ``session_replay_rate`` - fraction of sessions
  whose run-then-replay produces a bit-identical
  trajectory (matched final_hash + matched
  every step's state_hash).
* ``rollback_success`` - fraction of (session,
  checkpoint) pairs where the rollback target's
  reconstructed state hash matches the snapshot's
  recorded state hash.
* ``snapshot_integrity`` - fraction of snapshots
  whose recomputed state hash matches the value
  pinned on the snapshot record.
* ``seed_invariance`` - same-seed determinism
  rate: every config replayed twice must produce
  identical sessions.
* ``replay_stability`` - 1.0 iff
  ``build_report()`` is deterministic across
  two back-to-back invocations.

Killerfrage: "Kann DESi erwachsen werden, ohne
ihr Gedaechtnis zu verlieren?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache

from .runtime import (
    default_session_configs, replay_session,
    rollback_to, run_session,
)
from .sandbox import state_hash
from .session import (
    Session, SessionConfig,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@lru_cache(maxsize=1)
def _sessions_pass_a() -> tuple[Session, ...]:
    return tuple(
        run_session(c)
        for c in default_session_configs()
    )


@lru_cache(maxsize=1)
def _sessions_pass_b() -> tuple[Session, ...]:
    return tuple(
        replay_session(c)
        for c in default_session_configs()
    )


def session_replay_rate() -> float:
    a = _sessions_pass_a()
    b = _sessions_pass_b()
    if not a:
        return 0.0
    ok = sum(
        1 for x, y in zip(a, b)
        if x.to_dict() == y.to_dict()
    )
    return _round(ok / len(a))


def seed_invariance() -> float:
    """Two independent passes over the same
    configs must produce identical sessions."""
    return session_replay_rate()


def snapshot_integrity() -> float:
    sessions = _sessions_pass_a()
    total = 0
    ok = 0
    for s in sessions:
        for snap in s.snapshots:
            total += 1
            state = rollback_to(
                s.config, snap.step,
            )
            if state_hash(state) == (
                snap.state_hash
            ):
                ok += 1
    if total == 0:
        return 0.0
    return _round(ok / total)


def rollback_success() -> float:
    sessions = _sessions_pass_a()
    total = 0
    ok = 0
    for s in sessions:
        for snap in s.snapshots:
            total += 1
            state = rollback_to(
                s.config, snap.step,
            )
            if (
                state_hash(state)
                == snap.state_hash
                and state.step == snap.step
            ):
                ok += 1
    if total == 0:
        return 0.0
    return _round(ok / total)


@dataclass(frozen=True)
class V50Report:
    session_count: int
    snapshot_count: int
    session_replay_rate: float
    rollback_success: float
    snapshot_integrity: float
    seed_invariance: float
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "session_count":
                self.session_count,
            "snapshot_count":
                self.snapshot_count,
            "session_replay_rate":
                self.session_replay_rate,
            "rollback_success":
                self.rollback_success,
            "snapshot_integrity":
                self.snapshot_integrity,
            "seed_invariance":
                self.seed_invariance,
            "replay_stability":
                self.replay_stability,
            "halt": self.halt,
            "recommendation":
                self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def _replay_stability() -> float:
    a = (
        session_replay_rate(),
        rollback_success(),
        snapshot_integrity(),
        seed_invariance(),
    )
    b = (
        session_replay_rate(),
        rollback_success(),
        snapshot_integrity(),
        seed_invariance(),
    )
    return 1.0 if a == b else 0.0


def _recommendation(
    srr: float, rb: float, si: float,
    seed: float, replay: float,
) -> str:
    if replay < 1.0:
        return "HALT_REPLAY_DRIFT"
    if (
        srr == 1.0 and rb == 1.0
        and si == 1.0 and seed == 1.0
    ):
        return "SANDBOX_READY"
    if srr >= 0.95 and rb >= 0.95:
        return "SANDBOX_NEARLY_READY"
    return "SANDBOX_UNSTABLE"


def build_report() -> V50Report:
    srr = session_replay_rate()
    rb = rollback_success()
    si = snapshot_integrity()
    seed = seed_invariance()
    replay = _replay_stability()
    halt = replay < 1.0
    verdict = _recommendation(
        srr, rb, si, seed, replay,
    )
    sessions = _sessions_pass_a()
    snap_total = sum(
        len(s.snapshots) for s in sessions
    )
    rationale = (
        f"INFO: session_count {len(sessions)}",
        f"INFO: snapshot_count {snap_total}",
        f"{'PASS' if srr == 1.0 else 'FAIL'}: "
        f"session_replay_rate {srr}",
        f"{'PASS' if rb == 1.0 else 'FAIL'}: "
        f"rollback_success {rb}",
        f"{'PASS' if si == 1.0 else 'FAIL'}: "
        f"snapshot_integrity {si}",
        f"{'PASS' if seed == 1.0 else 'FAIL'}: "
        f"seed_invariance {seed}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )
    return V50Report(
        session_count=len(sessions),
        snapshot_count=snap_total,
        session_replay_rate=srr,
        rollback_success=rb,
        snapshot_integrity=si,
        seed_invariance=seed,
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_sandbox_runtime_artifact(
) -> dict[str, object]:
    sessions = _sessions_pass_a()
    return {
        "schema_version":
            "v5_0_sandbox_runtime",
        "session_count": len(sessions),
        "snapshot_count": sum(
            len(s.snapshots) for s in sessions
        ),
        "sessions": [
            s.to_dict() for s in sessions
        ],
        "session_replay_rate":
            session_replay_rate(),
        "rollback_success":
            rollback_success(),
        "snapshot_integrity":
            snapshot_integrity(),
        "seed_invariance": seed_invariance(),
    }


__all__ = [
    "V50Report",
    "build_report",
    "build_sandbox_runtime_artifact",
    "rollback_success",
    "seed_invariance",
    "session_replay_rate",
    "snapshot_integrity",
]
