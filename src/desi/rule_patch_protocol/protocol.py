"""RulePatchProtocol orchestrator — Aufgaben 3 + 4 + 5.

Walks every :class:`PatchPhase` in declaration order. The first
phase that fails halts the walk and the resulting
:class:`RulePatchRecord` carries the partial outcome plus a
deterministic ``fail_reason``.

Read-only by construction. Calls only the existing v1.5 / v1.9 /
v2.3 / v2.4 / v2.5 / v2.6 entry points; never mutates state.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
from datetime import datetime, timezone

from .candidate import PatchCandidate
from .phases import PHASE_ORDER, PatchPhase
from .record import (
    PhaseOutcome,
    RulePatchRecord,
    compute_record_replay_hash,
)
from .runners import (
    compute_benchmark_hashes,
    run_discovery,
    run_guard_synthesis,
    run_implementation,
    run_regression,
    run_replay_verification,
    run_risk_probe,
)


_DEFAULT_REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
_DEFAULT_ARTIFACT_ROOT = _DEFAULT_REPO_ROOT / "artifacts"


class RulePatchProtocol:
    """Stateless orchestrator over the seven phases."""

    def __init__(
        self,
        *,
        repo_root: pathlib.Path | None = None,
        artifact_root: pathlib.Path | None = None,
    ) -> None:
        self._repo_root = repo_root or _DEFAULT_REPO_ROOT
        self._artifact_root = artifact_root or _DEFAULT_ARTIFACT_ROOT

    def run(self, candidate: PatchCandidate) -> RulePatchRecord:
        outcomes: list[PhaseOutcome] = []
        before_hashes: dict[str, str] = {}
        after_hashes: dict[str, str] = {}
        fail_reason: str = ""
        final_phase: PatchPhase = PatchPhase.DISCOVERY

        for phase in PHASE_ORDER:
            if phase is PatchPhase.COMPLETE:
                # Terminal "all-passed" sentinel; reached only when
                # every prior phase passed.
                final_phase = PatchPhase.COMPLETE
                break

            if phase is PatchPhase.DISCOVERY:
                outcome = run_discovery(
                    candidate, artifact_root=self._artifact_root,
                )
            elif phase is PatchPhase.RISK_PROBE:
                outcome = run_risk_probe(
                    candidate, artifact_root=self._artifact_root,
                )
            elif phase is PatchPhase.GUARD_SYNTHESIS:
                outcome = run_guard_synthesis(candidate)
            elif phase is PatchPhase.IMPLEMENTATION:
                outcome = run_implementation(
                    candidate, repo_root=self._repo_root,
                )
            elif phase is PatchPhase.REGRESSION:
                # Two regression calls: first captures the
                # "before" hashes, second compares against them.
                # In this read-only protocol there is no
                # observable "before vs after" — the same source
                # tree is in effect — so both calls return the
                # same hashes. The mismatch path is reserved for
                # an in-process patch + revert workflow.
                before = run_regression(candidate, expected_hashes=None)
                if not before.passed:
                    outcome = before
                else:
                    before_hashes = before.data.get("hashes", {})
                    after = run_regression(
                        candidate, expected_hashes=before_hashes,
                    )
                    after_hashes = after.data.get("hashes", {})
                    outcome = after
            elif phase is PatchPhase.REPLAY_VERIFICATION:
                outcome = run_replay_verification(candidate)
            else:
                outcome = PhaseOutcome(
                    phase=phase, passed=False,
                    reason=f"unknown phase {phase!r}",
                )

            outcomes.append(outcome)
            final_phase = phase
            if not outcome.passed:
                fail_reason = outcome.reason
                break

        passed = all(o.passed for o in outcomes) and (
            final_phase is PatchPhase.COMPLETE
        )

        patch_id = _make_patch_id(candidate)
        record_payload = {
            "patch_id": patch_id,
            "target_rule": candidate.target_rule,
            "source_branch": candidate.source_branch,
            "phase": final_phase.value,
            "passed": passed,
            "created_guards": [g.name for g in candidate.guards],
            "touched_files": list(candidate.touched_files),
            "benchmark_hash_before": _hash_dict(before_hashes),
            "benchmark_hash_after": _hash_dict(after_hashes),
            "phase_outcomes": [o.to_dict() for o in outcomes],
            "fail_reason": fail_reason,
        }
        replay_hash = compute_record_replay_hash(record_payload)
        return RulePatchRecord(
            patch_id=patch_id,
            target_rule=candidate.target_rule,
            source_branch=candidate.source_branch,
            phase=final_phase,
            passed=passed,
            created_guards=tuple(g.name for g in candidate.guards),
            touched_files=tuple(candidate.touched_files),
            benchmark_hash_before=_hash_dict(before_hashes),
            benchmark_hash_after=_hash_dict(after_hashes),
            replay_hash=replay_hash,
            timestamp=datetime.now(timezone.utc),
            phase_outcomes=tuple(outcomes),
            fail_reason=fail_reason,
        )


def _hash_dict(d: dict[str, str]) -> str:
    if not d:
        return ""
    raw = json.dumps(
        d, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def _make_patch_id(candidate: PatchCandidate) -> str:
    return "pp_" + candidate.fingerprint()


__all__ = ["RulePatchProtocol"]
