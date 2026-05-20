"""Markdown report writer for DESi meta-analyses."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from .meta_analyzer import MetaAnalysisResult


_TEMPLATE_SECTIONS = (
    "Input Summary",
    "Deterministic Metrics",
    "Phase Detection",
    "EN Event Diagnostics",
    "Penultimate EN Assessment",
    "Attractor Diagnosis",
    "Skeptical Audit",
    "Final Synthesis",
    "Claims Requiring Replication",
)


def _section(title: str) -> str:
    return f"\n## {title}\n"


def render_report(result: MetaAnalysisResult) -> str:
    t = result.trajectory
    m = result.metrics
    phases = result.phases
    lines: list[str] = []

    lines.append("# DESi Trajectory Report")
    lines.append("")
    lines.append(
        f"_Generated {datetime.now(timezone.utc).isoformat(timespec='seconds')} "
        f"— EXPLORATORY, small n. Do not generalise without replication._"
    )

    # 1. Input summary
    lines.append(_section("Input Summary"))
    lines.append(f"- trajectory_id: `{t.trajectory_id}`")
    lines.append(f"- domain: {t.domain or '-'}")
    lines.append(f"- seed: {t.seed or '-'}")
    lines.append(f"- persona: {t.persona or '-'}")
    lines.append(f"- steps: {m.n_steps}")
    lines.append(f"- EN events: {m.n_en_events}")
    lines.append(f"- terminal failure mode: {m.failure.terminal or 'NONE'}")
    lines.append(f"- LLM analyses enabled: {result.llm_enabled}")

    # 2. Deterministic metrics
    lines.append(_section("Deterministic Metrics"))
    lines.append("### EN classifications")
    if not m.en_classifications:
        lines.append("- (no EN events)")
    for c in m.en_classifications:
        lines.append(
            f"- loop {c.loop_index}: eni_novelty = {c.eni_novelty:.2f} -> **{c.label}**"
        )
    lines.append("")
    lines.append("### Novelty recovery per EN event")
    if not m.novelty_recoveries:
        lines.append("- (no EN events)")
    for r in m.novelty_recoveries:
        dd = "n/a" if r.dup_delta is None else f"{r.dup_delta:+.2f}"
        nc = "n/a" if r.novel_claims_next is None else r.novel_claims_next
        lines.append(
            f"- loop {r.loop_index}: dup_delta = {dd}, novel_claims_next = {nc}, "
            f"recovered = **{r.recovered}**"
        )

    # 3. Phase detection
    lines.append(_section("Phase Detection"))
    if not phases.phases:
        lines.append("- (no phase rules triggered)")
    for ps in phases.phases:
        lines.append(
            f"### {ps.name}  (loops {ps.start_loop}..{ps.end_loop}, "
            f"confidence: {ps.confidence})"
        )
        for ev in ps.trigger_evidence:
            lines.append(f"- {ev}")
        lines.append("")

    # 4. EN diagnostics (LLM)
    lines.append(_section("EN Event Diagnostics"))
    _render_role(lines, result, "EN_EVENT_ANALYST")

    # 5. Penultimate EN assessment
    lines.append(_section("Penultimate EN Assessment"))
    p = m.penultimate
    lines.append(f"- candidate: **{p.has_candidate}**")
    if p.penultimate_loop is not None:
        lines.append(
            f"- penultimate EN: loop {p.penultimate_loop} ({p.penultimate_label})"
        )
    if p.last_loop is not None:
        lines.append(f"- last EN: loop {p.last_loop} ({p.last_label})")
    lines.append(f"- note: {p.note}")

    # 6. Attractor diagnosis (deterministic + LLM)
    lines.append(_section("Attractor Diagnosis"))
    a = m.attractor
    lines.append("### Deterministic candidates")
    if not a.candidate_claim_ids:
        lines.append("- (no terminal attractor candidates by heuristic)")
    for cid in a.candidate_claim_ids:
        lines.append(f"- `{cid}`")
    lines.append(f"- method: {a.method}")
    lines.append(f"- note: {a.note}")
    lines.append("")
    lines.append("### LLM attractor diagnostician")
    _render_role(lines, result, "ATTRACTOR_DIAGNOSTICIAN")

    # 7. Skeptical audit
    lines.append(_section("Skeptical Audit"))
    _render_role(lines, result, "SKEPTICAL_AUDITOR")

    # 8. Final synthesis
    lines.append(_section("Final Synthesis"))
    _render_role(lines, result, "REPORT_SYNTHESIZER")

    # 9. Claims requiring replication
    lines.append(_section("Claims Requiring Replication"))
    lines.append(
        "Every LLM-derived claim in this report is **EXPLORATORY** and must be "
        "replicated across additional trajectories before being treated as a "
        "DESi finding. Deterministic metrics (EN classifications, phase "
        "triggers, failure modes) are reproducible from the input JSON."
    )

    # Trajectory analyst output is informative but not in the template
    # sections; append it as an appendix for completeness when available.
    if result.role_by_name("TRAJECTORY_ANALYST"):
        lines.append(_section("Appendix: Trajectory Analyst notes"))
        _render_role(lines, result, "TRAJECTORY_ANALYST")

    return "\n".join(lines).rstrip() + "\n"


def _render_role(lines: list[str], result: MetaAnalysisResult, role: str) -> None:
    out = result.role_by_name(role)
    if out is None:
        if result.llm_enabled:
            lines.append(f"_(role {role} produced no output)_")
        else:
            lines.append("_(LLM disabled; this section is intentionally empty)_")
        return
    if out.error:
        lines.append(f"_(role {role} failed: {out.error})_")
        return
    lines.append(out.content.strip())


def write_report(result: MetaAnalysisResult, out_path: str | Path) -> Path:
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(render_report(result), encoding="utf-8")
    return p


def default_report_path(trajectory_id: str, out_dir: str | Path = "outputs") -> Path:
    return Path(out_dir) / f"{trajectory_id}_desi_report.md"
