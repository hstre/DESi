"""Read-only phase runners — Aufgabe 3.

Each runner takes a :class:`PatchCandidate` and returns a
:class:`PhaseOutcome`. No runner mutates state, no runner writes
files, no runner alters production behaviour.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
from datetime import datetime, timezone
from typing import Any

from .candidate import PatchCandidate
from .phases import PatchPhase
from .record import PhaseOutcome


# ---------------------------------------------------------------------------
# DISCOVERY — verify the v2.4/v2.5/v2.6 read-only artefacts exist
# ---------------------------------------------------------------------------


def run_discovery(
    candidate: PatchCandidate,
    *,
    artifact_root: pathlib.Path,
) -> PhaseOutcome:
    """Aufgabe 3 — DISCOVERY: read v2.4 + v2.5 + v2.6 artefacts."""
    missing: list[str] = []
    found: dict[str, str] = {}
    for rel in candidate.required_artifacts:
        p = artifact_root / rel
        if not p.exists():
            missing.append(rel)
            continue
        # Capture the artefact's sha256[:16] so the protocol can
        # later prove every required input existed at decision
        # time.
        found[rel] = hashlib.sha256(p.read_bytes()).hexdigest()[:16]
    if missing:
        return PhaseOutcome(
            phase=PatchPhase.DISCOVERY,
            passed=False,
            reason=f"missing artefacts: {missing!r}",
            data={"missing": missing, "found": found},
        )
    return PhaseOutcome(
        phase=PatchPhase.DISCOVERY,
        passed=True,
        reason="all required artefacts present",
        data={"artefact_hashes": found},
    )


# ---------------------------------------------------------------------------
# RISK_PROBE — confirm the candidate's v2.6 probe report shows no
# known-FP reopen and no authority/philosophy/metaphor touch
# ---------------------------------------------------------------------------


def run_risk_probe(
    candidate: PatchCandidate,
    *,
    artifact_root: pathlib.Path,
) -> PhaseOutcome:
    probe = artifact_root / "v2_6" / "report.json"
    if not probe.exists():
        return PhaseOutcome(
            phase=PatchPhase.RISK_PROBE,
            passed=False,
            reason="v2.6 probe artefact missing",
        )
    payload = json.loads(probe.read_text())
    metrics = payload.get("metrics", {})
    issues: list[str] = []
    if metrics.get("known_false_positive_reopen_rate", 1.0) != 0.0:
        issues.append("known_false_positive_reopen_rate != 0.0")
    if metrics.get("authority_touch_rate", 1.0) != 0.0:
        issues.append("authority_touch_rate != 0.0")
    if metrics.get("philosophy_touch_rate", 1.0) != 0.0:
        issues.append("philosophy_touch_rate != 0.0")
    safe = payload.get("safe_to_implement", False)
    if not safe:
        issues.append("safe_to_implement == False")
    if issues:
        return PhaseOutcome(
            phase=PatchPhase.RISK_PROBE,
            passed=False,
            reason="; ".join(issues),
            data={"safe_to_implement": safe, "metrics": metrics},
        )
    return PhaseOutcome(
        phase=PatchPhase.RISK_PROBE,
        passed=True,
        reason="probe clean",
        data={"safe_to_implement": safe},
    )


# ---------------------------------------------------------------------------
# GUARD_SYNTHESIS — every guard must be observable, no case_id checks,
# no allowlists
# ---------------------------------------------------------------------------


_FORBIDDEN_OBSERVABLE_TOKENS: frozenset[str] = frozenset({
    "case_id", "allowlist", "allow_list", "whitelist",
})

_ALLOWED_OBSERVABLES: frozenset[str] = frozenset({
    "rule_iteration_order",
    "premise_kind",
    "premise_text_substring",
    "conclusion_text_substring",
    "premise_token_graph",
    "conclusion_token_overlap",
    "premise_count",
    "conclusion_kind",
})


def run_guard_synthesis(candidate: PatchCandidate) -> PhaseOutcome:
    if len(candidate.guards) < 2:
        return PhaseOutcome(
            phase=PatchPhase.GUARD_SYNTHESIS,
            passed=False,
            reason="missing_guards: at least two guards required",
            data={"guard_count": len(candidate.guards)},
        )
    issues: list[str] = []
    for g in candidate.guards:
        obs = g.observable.lower()
        for bad in _FORBIDDEN_OBSERVABLE_TOKENS:
            if bad in obs:
                issues.append(
                    f"guard {g.name!r} uses forbidden observable "
                    f"token {bad!r}"
                )
        if obs not in _ALLOWED_OBSERVABLES:
            issues.append(
                f"guard {g.name!r} observable {g.observable!r} "
                "is not in ALLOWED_OBSERVABLES"
            )
    if issues:
        return PhaseOutcome(
            phase=PatchPhase.GUARD_SYNTHESIS,
            passed=False,
            reason="; ".join(issues),
            data={"issues": issues},
        )
    return PhaseOutcome(
        phase=PatchPhase.GUARD_SYNTHESIS,
        passed=True,
        reason=f"{len(candidate.guards)} guards approved",
        data={"guard_names": [g.name for g in candidate.guards]},
    )


# ---------------------------------------------------------------------------
# IMPLEMENTATION — verify the declared touched_files exist on disk
# and that only allowed roots were touched
# ---------------------------------------------------------------------------


_ALLOWED_IMPLEMENTATION_ROOTS: tuple[str, ...] = (
    "src/desi/logic/",
)


_ALLOWED_TEST_ROOTS: tuple[str, ...] = (
    "tests/",
)


_ALLOWED_DOC_ROOTS: tuple[str, ...] = (
    "docs/", "artifacts/",
)


def run_implementation(
    candidate: PatchCandidate,
    *,
    repo_root: pathlib.Path,
) -> PhaseOutcome:
    issues: list[str] = []
    missing: list[str] = []
    for rel in candidate.touched_files:
        p = repo_root / rel
        if not p.exists():
            missing.append(rel)
            continue
        if not (
            any(rel.startswith(r) for r in _ALLOWED_IMPLEMENTATION_ROOTS)
            or any(rel.startswith(r) for r in _ALLOWED_TEST_ROOTS)
            or any(rel.startswith(r) for r in _ALLOWED_DOC_ROOTS)
            or rel == "src/desi/rule_audit/categories.py"
        ):
            issues.append(
                f"file {rel!r} outside allowed implementation roots"
            )
    if missing:
        issues.append(f"declared but missing files: {missing!r}")
    if issues:
        return PhaseOutcome(
            phase=PatchPhase.IMPLEMENTATION,
            passed=False,
            reason="; ".join(issues),
            data={"missing": missing, "issues": issues},
        )
    return PhaseOutcome(
        phase=PatchPhase.IMPLEMENTATION,
        passed=True,
        reason=f"{len(candidate.touched_files)} declared files present",
        data={"touched_count": len(candidate.touched_files)},
    )


# ---------------------------------------------------------------------------
# REGRESSION — compute the six benchmark hashes; expose them so the
# orchestrator can compare to the candidate's expected baseline
# ---------------------------------------------------------------------------


def _canonical_hash(payload: Any) -> str:
    raw = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), default=str,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def compute_benchmark_hashes() -> dict[str, str]:
    """sha256[:16] over the canonical-JSON of each benchmark output.

    Reads are pure — no patching, no overrides, no rebinding.
    """
    from ..benchmark import BenchmarkRunner
    from ..benchmark_multistep import MultiStepBenchmarkRunner
    from ..bridge_audit import BridgeEntryAuditRunner, build_funnel_report
    from ..causal_probe import CausalChainProbeRunner, build_probe_report
    from ..rule_audit import RuleCoverageRunner, build_rule_coverage_report
    from ..tools import ToolBenchmarkRunner

    # Build each report payload deterministically, hash it.
    main = BenchmarkRunner().run()
    main_payload = [
        {
            "case_id": r.case.case_id,
            "final_state": r.final_state.value,
            "false_positive": r.false_positive,
            "false_negative": r.false_negative,
            "replay_hash": r.replay_hash,
        }
        for r in main.results
    ]
    tool = ToolBenchmarkRunner().run()
    tool_payload = [
        {
            "case_id": r.case.case_id,
            "dispatched": r.dispatched,
            "succeeded": r.succeeded,
            "correct": r.correct,
        }
        for r in tool.results
    ]
    ms = MultiStepBenchmarkRunner().run()
    ms_payload = [
        {
            "case_id": r.case.case_id,
            "final_state": r.final_state.value,
            "depth_reached": r.depth_reached,
            "replay_hash": r.replay_hash,
        }
        for r in ms.results
    ]
    now = datetime.now(timezone.utc)
    bridge_rep = build_funnel_report(
        BridgeEntryAuditRunner().run(),
        started_at=now, finished_at=now,
    )
    rule_rep = build_rule_coverage_report(
        RuleCoverageRunner().run(),
        started_at=now, finished_at=now,
    )
    probe_rep = build_probe_report(
        CausalChainProbeRunner().run(),
        started_at=now, finished_at=now,
    )
    return {
        "v1_5_main": _canonical_hash(main_payload),
        "v1_9_tool": _canonical_hash(tool_payload),
        "v2_3_multistep": _canonical_hash(ms_payload),
        "v2_4_bridge_audit": bridge_rep.replay_hash,
        "v2_5_rule_audit": rule_rep.replay_hash,
        "v2_6_causal_probe": probe_rep.replay_hash,
    }


def run_regression(
    candidate: PatchCandidate,
    *,
    expected_hashes: dict[str, str] | None = None,
) -> PhaseOutcome:
    """Compute current hashes; if ``expected_hashes`` is supplied,
    compare. The orchestrator collects ``before`` (no expected) and
    ``after`` (expected = before) calls."""
    current = compute_benchmark_hashes()
    if expected_hashes is None:
        return PhaseOutcome(
            phase=PatchPhase.REGRESSION,
            passed=True,
            reason="baseline hashes captured",
            data={"hashes": current},
        )
    drifts: list[str] = []
    for k, v in expected_hashes.items():
        if current.get(k) != v:
            drifts.append(
                f"{k}: expected {v}, got {current.get(k)}",
            )
    if drifts:
        return PhaseOutcome(
            phase=PatchPhase.REGRESSION,
            passed=False,
            reason="; ".join(drifts),
            data={"drifts": drifts, "hashes": current},
        )
    return PhaseOutcome(
        phase=PatchPhase.REGRESSION,
        passed=True,
        reason="all six benchmark hashes identical to baseline",
        data={"hashes": current},
    )


# ---------------------------------------------------------------------------
# REPLAY_VERIFICATION — two full benchmark runs must produce
# identical hashes
# ---------------------------------------------------------------------------


def run_replay_verification(candidate: PatchCandidate) -> PhaseOutcome:
    a = compute_benchmark_hashes()
    b = compute_benchmark_hashes()
    drifts = [
        f"{k}: a={va} b={b.get(k)}"
        for k, va in a.items() if b.get(k) != va
    ]
    if drifts:
        return PhaseOutcome(
            phase=PatchPhase.REPLAY_VERIFICATION,
            passed=False,
            reason="non-deterministic benchmark: " + "; ".join(drifts),
            data={"drifts": drifts},
        )
    return PhaseOutcome(
        phase=PatchPhase.REPLAY_VERIFICATION,
        passed=True,
        reason="two consecutive runs match bit-for-bit",
        data={"hashes": a},
    )


__all__ = [
    "compute_benchmark_hashes",
    "run_discovery",
    "run_guard_synthesis",
    "run_implementation",
    "run_regression",
    "run_replay_verification",
    "run_risk_probe",
]
