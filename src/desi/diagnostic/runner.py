"""SelfDiagnosticRunner — Aufgabe 1.

Read-only diagnostic over stable-v1.9.0 + the v2.0 sandbox. The
runner:

1. Fingerprints the stable source tree before any work begins.
2. Calls the unmodified main + tool benchmark runners.
3. Optionally accepts a pre-computed v2.0 sandbox report (so tests
   do not need to spend 30 seconds on a fresh sandbox run); falls
   back to ``artifacts/v2_0/report.json`` on disk if present.
4. Applies every discovery function and aggregates into a
   ``SelfDiagnosticReport``.
5. Verifies the stable fingerprint is byte-for-byte identical
   after the run.

Mutation, optimisation, patching — none of these happen here.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
from datetime import datetime, timezone
from typing import Any

from ..benchmark import ALL_CASES, BenchmarkRunner
from ..recursive import RecursiveResolver
from ..tools import ToolBenchmarkRunner
from .categories import DeficitCategory
from .discovery import (
    CaseResolution,
    discover_authority_coverage,
    discover_counterexample_coverage,
    discover_dead_mutation_knob,
    discover_false_block_reason,
    discover_parser_coverage,
    discover_recursion_configuration,
    discover_tool_coverage,
    discover_tool_dependency,
)
from .knobs import DEFAULT_INVENTORY, KnobInventory
from .record import DeficitRecord
from .report import SelfDiagnosticReport, compute_report_replay_hash


_STABLE_PKG_ROOT = pathlib.Path(__file__).resolve().parent.parent
_DEFAULT_SANDBOX_ARTIFACT = (
    pathlib.Path(__file__).resolve().parents[3]
    / "artifacts" / "v2_0" / "report.json"
)


def _stable_source_fingerprint(root: pathlib.Path) -> str:
    """sha256[:16] over the v1.9 source tree. v2.0/v2.1 packages are
    excluded — those may change freely without violating the
    invariant."""
    h = hashlib.sha256()
    for p in sorted(root.rglob("*.py")):
        try:
            rel = p.relative_to(root).as_posix()
        except ValueError:
            continue
        if rel.startswith("sandbox/") or rel.startswith("diagnostic/"):
            continue
        file_hash = hashlib.sha256(p.read_bytes()).hexdigest()
        h.update(f"{rel}|{file_hash}\n".encode("utf-8"))
    return h.hexdigest()[:16]


class SelfDiagnosticRunner:
    """Read-only deficit hunter."""

    def __init__(
        self,
        *,
        stable_version: str = "stable-v1.9.0",
        main_run: Any = None,
        tool_run: Any = None,
        resolutions: tuple[CaseResolution, ...] | None = None,
        sandbox_report: dict[str, Any] | None = None,
        sandbox_report_path: pathlib.Path | str | None = None,
        inventory: KnobInventory = DEFAULT_INVENTORY,
        stable_root: pathlib.Path | None = None,
    ) -> None:
        self._stable_version = stable_version
        self._injected_main = main_run
        self._injected_tool = tool_run
        self._injected_resolutions = resolutions
        self._injected_sandbox = sandbox_report
        self._sandbox_path = (
            pathlib.Path(sandbox_report_path)
            if sandbox_report_path is not None
            else _DEFAULT_SANDBOX_ARTIFACT
        )
        self._inventory = inventory
        self._stable_root = stable_root or _STABLE_PKG_ROOT

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self) -> SelfDiagnosticReport:
        started_at = datetime.now(timezone.utc)
        stable_hash_before = _stable_source_fingerprint(self._stable_root)

        main_run = (
            self._injected_main if self._injected_main is not None
            else BenchmarkRunner().run()
        )
        tool_run = (
            self._injected_tool if self._injected_tool is not None
            else ToolBenchmarkRunner().run()
        )
        resolutions = (
            self._injected_resolutions
            if self._injected_resolutions is not None
            else _collect_resolutions()
        )
        sandbox_report = self._resolve_sandbox_report()

        deficits = _discover_all(
            resolutions=resolutions,
            tool_run=tool_run,
            sandbox_report=sandbox_report,
            inventory=self._inventory,
        )

        actionable = [d for d in deficits if d.is_actionable]
        non_actionable = [d for d in deficits if not d.is_actionable]
        highest_severity = (
            max((d.severity_score for d in deficits), default=0.0)
        )
        highest_confidence = (
            max((d.confidence_score for d in deficits), default=0.0)
        )

        # Live = existing - dead, where "dead" comes from the
        # inventory plus any DEAD_MUTATION_KNOB deficit we just
        # discovered (newly-observed dead knobs).
        proven_dead = set(self._inventory.dead_knobs())
        for d in deficits:
            if d.category is DeficitCategory.DEAD_MUTATION_KNOB:
                proven_dead.update(d.candidate_knobs)
        live = sorted(self._inventory.existing - proven_dead)
        dead = sorted(proven_dead)

        recommended, blocked = _recommend(actionable, live)

        stable_hash_after = _stable_source_fingerprint(self._stable_root)
        if stable_hash_before != stable_hash_after:
            raise RuntimeError(
                "stable-v1.9.0 fingerprint changed mid-diagnostic: "
                f"{stable_hash_before} -> {stable_hash_after}",
            )

        report_payload = {
            "stable_version": self._stable_version,
            "stable_hash_before": stable_hash_before,
            "stable_hash_after": stable_hash_after,
            "total_deficits": len(deficits),
            "actionable_deficits": len(actionable),
            "non_actionable_deficits": len(non_actionable),
            "highest_severity": round(highest_severity, 6),
            "highest_confidence": round(highest_confidence, 6),
            "dead_knobs": dead,
            "live_knobs": live,
            "recommended_next_knob": recommended,
            "blocked_recommendations": blocked,
            "deficits": [d.to_dict() for d in deficits],
        }
        replay_hash = compute_report_replay_hash(report_payload)

        return SelfDiagnosticReport(
            started_at=started_at,
            finished_at=datetime.now(timezone.utc),
            stable_version=self._stable_version,
            stable_hash_before=stable_hash_before,
            stable_hash_after=stable_hash_after,
            total_deficits=len(deficits),
            actionable_deficits=len(actionable),
            non_actionable_deficits=len(non_actionable),
            highest_severity=round(highest_severity, 6),
            highest_confidence=round(highest_confidence, 6),
            dead_knobs=tuple(dead),
            live_knobs=tuple(live),
            recommended_next_knob=recommended,
            blocked_recommendations=tuple(blocked),
            deficits=tuple(deficits),
            replay_hash=replay_hash,
        )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _resolve_sandbox_report(self) -> dict[str, Any] | None:
        if self._injected_sandbox is not None:
            return self._injected_sandbox
        if self._sandbox_path.exists():
            try:
                return json.loads(self._sandbox_path.read_text())
            except (json.JSONDecodeError, OSError):
                return None
        return None


# ---------------------------------------------------------------------------
# Discovery + recommendation helpers
# ---------------------------------------------------------------------------


def _collect_resolutions() -> tuple[CaseResolution, ...]:
    """Read-only resolver pass — captures blocking_reason + depth
    that v1.5 ``BenchmarkResult`` does not surface."""
    resolver = RecursiveResolver()
    out: list[CaseResolution] = []
    for case in ALL_CASES:
        res = resolver.resolve(
            case.text,
            context=case.context,
            additional_conditions=case.additional_conditions,
        )
        out.append(CaseResolution(
            case_id=case.case_id,
            category=case.category,
            final_state=res.final_state,
            blocking_reason=res.blocking_reason,
            depth_reached=res.depth_reached,
        ))
    return tuple(out)


def _discover_all(
    *,
    resolutions: tuple[CaseResolution, ...],
    tool_run: Any,
    sandbox_report: dict[str, Any] | None,
    inventory: KnobInventory,
) -> tuple[DeficitRecord, ...]:
    findings: list[DeficitRecord] = []
    for fn in (
        discover_parser_coverage,
        discover_counterexample_coverage,
        discover_authority_coverage,
        discover_false_block_reason,
        discover_recursion_configuration,
    ):
        rec = fn(resolutions, inventory=inventory)
        if rec is not None:
            findings.append(rec)
    for fn in (discover_tool_dependency, discover_tool_coverage):
        rec = fn(tool_run, inventory=inventory)
        if rec is not None:
            findings.append(rec)
    rec = discover_dead_mutation_knob(sandbox_report, inventory=inventory)
    if rec is not None:
        findings.append(rec)
    return tuple(sorted(findings, key=lambda d: d.deficit_id))


def _recommend(
    actionable: list[DeficitRecord],
    live_knobs: list[str],
) -> tuple[str | None, list[str]]:
    """Pick the best live candidate; record any blocked ones.

    A recommendation is *blocked* when an actionable deficit
    proposed a knob that isn't in the live set (either because it's
    dead or because it doesn't exist). Blocking is explicit — the
    runner never silently swaps in a fallback.
    """
    blocked: list[str] = []
    candidates: list[tuple[float, str, str]] = []
    live_set = set(live_knobs)
    for d in actionable:
        for k in d.candidate_knobs:
            if k in live_set:
                # Score = severity * confidence — both already
                # data-derived per Aufgabe 4.
                candidates.append(
                    (round(d.severity_score * d.confidence_score, 6),
                     d.deficit_id, k),
                )
            else:
                blocked.append(k)
    if not candidates:
        return None, sorted(set(blocked))
    # Sort: higher score first, then deficit_id for stability.
    candidates.sort(key=lambda x: (-x[0], x[1], x[2]))
    return candidates[0][2], sorted(set(blocked))


__all__ = ["SelfDiagnosticRunner"]
