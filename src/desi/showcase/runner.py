"""ShowcaseRunner — generate externally-readable demonstration artefacts.

The runner takes a scenario id (S2 / S6 / S7), invokes the v0.4
EvaluationHarness, and writes the artefact bundle to a directory. The
bundle is self-contained: a reviewer who reads ``analysis.md`` plus
``timeline.md`` plus ``snapshot_end.json`` can verify every claim in
the description without rerunning the code.

The runner does not change DESi behaviour. It is observation-only and
re-uses the v0.4 surface unchanged.
"""
from __future__ import annotations

import json
import pathlib
from collections import Counter
from dataclasses import dataclass, field
from typing import Iterable

from ..eval import EvaluationHarness, EvaluationResult, scenario_by_id
from ..observe import (
    GraphSnapshot,
    TimelineEvent,
    timeline_to_json,
    timeline_to_markdown,
)
from .descriptions import SHOWCASE_DESCRIPTIONS, SHOWCASE_IDS


@dataclass
class ShowcaseArtifacts:
    """File-path manifest for one showcase run.

    Every attribute is the absolute path of the produced artefact. A
    test asserts that all of them exist after :meth:`ShowcaseRunner.run`
    completes.
    """

    scenario_id: str
    directory: pathlib.Path
    summary_json: pathlib.Path
    timeline_md: pathlib.Path
    timeline_json: pathlib.Path
    snapshot_start_json: pathlib.Path
    snapshot_end_json: pathlib.Path
    snapshot_end_cypher: pathlib.Path
    analysis_md: pathlib.Path

    def paths(self) -> tuple[pathlib.Path, ...]:
        return (
            self.summary_json,
            self.timeline_md,
            self.timeline_json,
            self.snapshot_start_json,
            self.snapshot_end_json,
            self.snapshot_end_cypher,
            self.analysis_md,
        )


class ShowcaseRunner:
    """Generate showcase artefact bundles for the v0.4.1 demonstration set.

    >>> runner = ShowcaseRunner(out_dir=tmp_path)
    >>> arts = runner.run("S2", seed=42)
    >>> arts.summary_json.exists()
    True

    The default scenario set is ``S2, S6, S7``. Call :meth:`run_all` to
    produce every showcase plus the cross-cutting ``baseline_notes.md``.
    """

    DEFAULT_IDS: tuple[str, ...] = SHOWCASE_IDS

    def __init__(
        self,
        *,
        out_dir: pathlib.Path | str,
        model: str = "claude-opus-4-7",
        config: dict | None = None,
    ) -> None:
        self.out_dir = pathlib.Path(out_dir)
        self._harness = EvaluationHarness(
            model=model,
            config=config or {"version": "v0.4.1"},
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, scenario_id: str, *, seed: int = 42) -> ShowcaseArtifacts:
        if scenario_id not in self.DEFAULT_IDS:
            raise ValueError(
                f"scenario_id {scenario_id!r} is not in the v0.4.1 "
                f"showcase set {self.DEFAULT_IDS}"
            )
        scenario = scenario_by_id(scenario_id)
        result = self._harness.run_scenario(scenario, seed=seed)
        directory = self.out_dir / scenario_id
        directory.mkdir(parents=True, exist_ok=True)
        return self._emit_artifacts(scenario_id, result, directory)

    def run_all(self, *, seed: int = 42) -> dict[str, ShowcaseArtifacts]:
        """Run S2, S6, S7 and emit baseline_notes.md alongside the bundles."""
        out: dict[str, ShowcaseArtifacts] = {}
        for sid in self.DEFAULT_IDS:
            out[sid] = self.run(sid, seed=seed)
        # Cross-cutting note across all three.
        baseline = self.out_dir / "baseline_notes.md"
        baseline.parent.mkdir(parents=True, exist_ok=True)
        baseline.write_text(_render_baseline_notes(out))
        return out

    # ------------------------------------------------------------------
    # Artefact emission
    # ------------------------------------------------------------------

    def _emit_artifacts(
        self,
        scenario_id: str,
        result: EvaluationResult,
        directory: pathlib.Path,
    ) -> ShowcaseArtifacts:
        summary_path = directory / "summary.json"
        timeline_md_path = directory / "timeline.md"
        timeline_json_path = directory / "timeline.json"
        snapshot_start_path = directory / "snapshot_start.json"
        snapshot_end_path = directory / "snapshot_end.json"
        snapshot_end_cypher_path = directory / "snapshot_end.cypher"
        analysis_path = directory / "analysis.md"

        summary_path.write_text(_render_summary(scenario_id, result))
        timeline_md_path.write_text(timeline_to_markdown(result.timeline))
        timeline_json_path.write_text(timeline_to_json(result.timeline))

        start_snap = _find_snapshot(result.snapshots, "start")
        end_snap = _find_snapshot(result.snapshots, "end")
        snapshot_start_path.write_text(start_snap.to_json())
        snapshot_end_path.write_text(end_snap.to_json())
        snapshot_end_cypher_path.write_text(end_snap.to_cypher())

        analysis_path.write_text(
            _render_analysis(scenario_id, result, end_snap),
        )

        return ShowcaseArtifacts(
            scenario_id=scenario_id,
            directory=directory,
            summary_json=summary_path,
            timeline_md=timeline_md_path,
            timeline_json=timeline_json_path,
            snapshot_start_json=snapshot_start_path,
            snapshot_end_json=snapshot_end_path,
            snapshot_end_cypher=snapshot_end_cypher_path,
            analysis_md=analysis_path,
        )


# ---------------------------------------------------------------------------
# Render helpers
# ---------------------------------------------------------------------------


def _render_summary(scenario_id: str, result: EvaluationResult) -> str:
    """Compact, deterministic-modulo-timestamp JSON summary."""
    doc = {
        "scenario_id": scenario_id,
        "evaluation_id": result.evaluation_id,
        "seed": result.seed,
        "model": result.model,
        "config_hash": result.config_hash,
        "timestamp": result.timestamp.isoformat(),
        "passed": result.passed,
        "expectations_met": dict(result.expectations_met),
        "expectations_detail": dict(result.expectations_detail),
        "hook_errors": list(result.hook_errors),
        "counts": {
            "timeline_events": len(result.timeline),
            "snapshots": len(result.snapshots),
        },
    }
    return json.dumps(doc, indent=2) + "\n"


def _render_analysis(
    scenario_id: str,
    result: EvaluationResult,
    end_snap: GraphSnapshot,
) -> str:
    desc = SHOWCASE_DESCRIPTIONS[scenario_id]
    operator_counts = _count_operators(result.timeline)
    claim_count = len(end_snap.claims)
    relation_summary = _summarise_relations(end_snap.relations)
    guard_blocked = _filter_events(result.timeline, "guard_blocked")
    claim_ids = sorted({c["claim_id"] for c in end_snap.claims})

    lines: list[str] = []
    lines.append(f"# {scenario_id} — {desc['title']}")
    lines.append("")
    lines.append(f"*Generated from evaluation_id `{result.evaluation_id}` "
                 f"(seed={result.seed}, model={result.model}).*")
    lines.append("")
    lines.append("## Problem")
    lines.append("")
    lines.append(desc["problem"])
    lines.append("")
    lines.append("## DESi Verhalten")
    lines.append("")
    lines.append(f"- **Operators fired** (count): "
                 f"{_format_counter(operator_counts)}")
    lines.append(f"- **Distinct claims created**: {claim_count} — "
                 f"`{', '.join(claim_ids)}`")
    if guard_blocked:
        for ge in guard_blocked:
            payload = ge.payload
            lines.append(
                f"- **Guard blocked** ({payload.get('operator', '?')}, "
                f"loop {payload.get('loop_index', '?')}): "
                f"{payload.get('reason', '')!s}"
            )
    else:
        lines.append("- **Guards triggered**: none in this run.")
    lines.append("")
    lines.append("## Endzustand")
    lines.append("")
    lines.append(f"- **Final claims in graph**: {claim_count}")
    for cid in claim_ids:
        method = _claim_method(end_snap.claims, cid)
        lines.append(f"  - `{cid}` (method: `{method}`)")
    lines.append(f"- **Final relations**:")
    if not relation_summary:
        lines.append("  - none")
    else:
        for rel_type, count in sorted(relation_summary.items()):
            lines.append(f"  - `{rel_type}`: {count}")
    lines.append("")
    lines.append("## Warum relevant?")
    lines.append("")
    lines.append(desc["why_relevant"])
    lines.append("")
    return "\n".join(lines)


def _render_baseline_notes(
    artifacts_by_id: dict[str, ShowcaseArtifacts],
) -> str:
    lines: list[str] = []
    lines.append("# DESi v0.4.1 — Baseline contrast notes")
    lines.append("")
    lines.append(
        "Qualitative comparison between a classical LLM path and the "
        "DESi path on each of the three v0.4.1 showcase scenarios. "
        "These notes are deliberately not benchmarks; they describe "
        "what is *structurally visible* in the DESi artefacts that "
        "would not be visible in a typical LLM run."
    )
    lines.append("")
    for sid in artifacts_by_id:
        desc = SHOWCASE_DESCRIPTIONS[sid]
        lines.append(f"## {sid} — {desc['title']}")
        lines.append("")
        lines.append(f"**Goal:** {desc['goal']}")
        lines.append("")
        lines.append("### Klassischer LLM-Pfad")
        lines.append("")
        lines.append(desc["classical_path"])
        lines.append("")
        lines.append("### DESi-Pfad")
        lines.append("")
        lines.append(desc["desi_path"])
        lines.append("")
        rel_path = pathlib.Path(sid) / "analysis.md"
        lines.append(f"*Full per-scenario analysis: `{rel_path.as_posix()}`*")
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Small extraction helpers
# ---------------------------------------------------------------------------


def _find_snapshot(snaps: Iterable[GraphSnapshot], label: str) -> GraphSnapshot:
    for snap in snaps:
        if snap.label == label:
            return snap
    # Fallback: pick the first / last as appropriate.
    snaps_list = list(snaps)
    if label == "start" and snaps_list:
        return snaps_list[0]
    if label == "end" and snaps_list:
        return snaps_list[-1]
    raise ValueError(f"no snapshot with label {label!r} and no fallback")


def _count_operators(timeline: Iterable[TimelineEvent]) -> Counter[str]:
    c: Counter[str] = Counter()
    for ev in timeline:
        if ev.event_type.value == "operator_started":
            op = ev.payload.get("operator")
            if op:
                c[str(op)] += 1
    return c


def _format_counter(c: Counter[str]) -> str:
    parts = [f"{op} ({n})" for op, n in sorted(c.items())]
    return ", ".join(parts) if parts else "none"


def _summarise_relations(relations: Iterable[dict]) -> dict[str, int]:
    out: dict[str, int] = {}
    for rel in relations:
        rt = rel.get("rel_type", "?")
        out[rt] = out.get(rt, 0) + 1
    return out


def _filter_events(
    timeline: Iterable[TimelineEvent],
    event_type_value: str,
) -> list[TimelineEvent]:
    return [e for e in timeline if e.event_type.value == event_type_value]


def _claim_method(claims: Iterable[dict], claim_id: str) -> str:
    for c in claims:
        if c.get("claim_id") == claim_id:
            return str(c.get("method", "?"))
    return "?"
