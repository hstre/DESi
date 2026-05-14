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

    # Fix 3 (external-reality challenge): banner when input is not native.
    origin = getattr(t, "input_origin", None)
    _NON_AUTHORITATIVE = {"translator_heuristic", "translated_DES_conservative"}
    if origin in _NON_AUTHORITATIVE:
        lines.append("")
        lines.append(
            f"> **Input-origin disclaimer** (`input_origin = {origin}`): "
            f"diagnosis applies to translator-derived metrics, not native "
            f"DES metrics. DESi diagnoses below describe the translator's "
            f"reconstruction, not the underlying DES program's behaviour."
        )

    lines.append(_section("Input Summary"))
    lines.append(f"- trajectory_id: `{t.trajectory_id}`")
    lines.append(f"- input_origin: `{origin or 'hand_authored_fixture (default)'}`")
    lines.append(f"- domain: {t.domain or '-'}")
    lines.append(f"- seed: {t.seed or '-'}")
    lines.append(f"- persona: {t.persona or '-'}")
    lines.append(f"- steps: {m.n_steps}")
    lines.append(f"- EN events: {m.n_en_events}")
    lines.append(f"- terminal failure mode: {m.failure.terminal or 'NONE'}")
    lines.append(f"- LLM analyses enabled: {result.llm_enabled}")

    lines.append(_section("Deterministic Metrics"))
    lines.append("### EN classifications")
    if not m.en_classifications:
        lines.append("- (no EN events)")
    for c in m.en_classifications:
        lines.append(f"- loop {c.loop_index}: eni_novelty = {c.eni_novelty:.2f} -> **{c.label}**")
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

    lines.append(_section("EN Event Diagnostics"))
    _render_role(lines, result, "EN_EVENT_ANALYST")

    lines.append(_section("Penultimate EN Assessment"))
    p = m.penultimate
    lines.append(f"- candidate: **{p.has_candidate}**")
    if p.penultimate_loop is not None:
        lines.append(f"- penultimate EN: loop {p.penultimate_loop} ({p.penultimate_label})")
    if p.last_loop is not None:
        lines.append(f"- last EN: loop {p.last_loop} ({p.last_label})")
    lines.append(f"- note: {p.note}")

    # cycle-11: surface the cycle 4-7 deterministic detectors.
    lines.append(_section("New deterministic detectors (cycles 4-7)"))
    be = m.branch_explosion
    lines.append(f"- **branch_explosion**: detected = **{be.detected}** — "
                 f"{be.distinct_open_branches} distinct open branches, "
                 f"avg dup={be.avg_dup_rate}, avg novel={be.avg_novel_claims}")
    if be.detected and be.parent_claim_ids:
        lines.append(f"  - offending parent claim ids: {be.parent_claim_ids}")
    ms = m.mild_stagnation
    lines.append(f"- **mild_stagnation**: detected = **{ms.detected}** — "
                 f"tail mean novel={ms.tail_mean_novel}, "
                 f"dup_strictly_increasing={ms.dup_strictly_increasing}, "
                 f"has_phase_v_trigger={ms.has_phase_v_trigger}")
    sc = m.step_coherence
    lines.append(f"- **step_coherence**: incoherent_steps = **{len(sc.incoherent_steps)}** "
                 f"({sc.note})")
    # cycle-6 (generalization loop): surface the cycle-5 borderline-chain detector.
    bc = m.borderline_chain
    lines.append(f"- **borderline_chain** (gen-cycle 5): detected = **{bc.detected}** — "
                 f"longest run = {bc.longest_run}; {bc.note}")
    # Fix 1 (external-reality challenge): surface schema_mismatch.
    sm = m.schema_mismatch
    lines.append(f"- **schema_mismatch** (external-reality fix 1): detected = **{sm.detected}** — "
                 f"{sm.note}")
    if m.en_classifications_composite:
        lines.append("- **composite EN classifications** (cycle 7):")
        for c in m.en_classifications_composite:
            lines.append(f"  - loop {c.loop_index}: eni={c.eni_novelty:.2f}, "
                         f"recovered={c.recovered} → `{c.label}`")
    else:
        lines.append("- composite EN classifications: (no EN events)")

    # EN-reconstruction cycle 1: candidates reconstructed from upstream
    # DES operations (hypothesis_builder + target). Distinct from
    # en_classifications/composite above, which require native ENI input.
    er = m.en_reconstruction
    lines.append(_section("Reconstructed EN Candidates (cycle 1)"))
    lines.append(
        "_These are STRUCTURAL candidates derived from "
        "`operator_sub_role == 'hypothesis_builder'` with a target claim. "
        "They are NOT eni_novelty measurements; they identify loop "
        "positions where DES likely created new claims via "
        "hypothesis-building. Treat as candidates pending confirmation._"
    )
    if er.count == 0:
        lines.append("- (no candidates under rule "
                     "`cycle1_hypothesis_builder_with_target`)")
    for c in er.candidates:
        lines.append(
            f"- loop {c.loop_index}: `{c.operator}` "
            f"[{c.source_claim} → {c.target_claim}] "
            f"(rule: `{c.rule_id}`)"
        )

    # Critique-navigation cycle 2: SEPARATE section per user directive.
    # Do NOT merge with EN. Falsifier ops with target_claim are the
    # critique analog of hypothesis_builder ops.
    cn = m.critique_navigation
    lines.append(_section("Reconstructed Critique-Navigation Candidates (cycle 2)"))
    lines.append(
        "_These are STRUCTURAL candidates derived from "
        "`operator_sub_role == 'falsifier'` with a target claim. They "
        "represent DES extending the claim graph via critique rather "
        "than via construction. **They are NOT EN candidates** — the "
        "two categories share a syntactic shape but encode different "
        "epistemic moves and are surfaced separately by design._"
    )
    if cn.count == 0:
        lines.append("- (no candidates under rule "
                     "`cycle2_falsifier_with_target`)")
    for c in cn.candidates:
        lines.append(
            f"- loop {c.loop_index}: `{c.operator}` "
            f"[{c.source_claim} → {c.target_claim}] "
            f"(rule: `{c.rule_id}`)"
        )
    # Cross-reference: are any candidate loops shared between the two?
    en_loops = {c.loop_index for c in er.candidates}
    cn_loops = {c.loop_index for c in cn.candidates}
    overlap = sorted(en_loops & cn_loops)
    if er.count or cn.count:
        if overlap:
            lines.append(
                f"- **WARNING**: candidate loops appear in BOTH EN and "
                f"critique-navigation lists: {overlap}. This should not "
                f"happen — each step has exactly one sub-role."
            )
        else:
            lines.append(
                f"- cross-check: EN and critique-navigation candidate "
                f"loops are disjoint ({len(en_loops)} EN, "
                f"{len(cn_loops)} critique-nav)."
            )

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

    lines.append(_section("Skeptical Audit"))
    _render_role(lines, result, "SKEPTICAL_AUDITOR")

    lines.append(_section("Final Synthesis"))
    _render_role(lines, result, "REPORT_SYNTHESIZER")

    lines.append(_section("Claims Requiring Replication"))
    lines.append(
        "Every LLM-derived claim in this report is **EXPLORATORY** and must be "
        "replicated across additional trajectories before being treated as a "
        "DESi finding. Deterministic metrics (EN classifications, phase "
        "triggers, failure modes) are reproducible from the input JSON."
    )

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
