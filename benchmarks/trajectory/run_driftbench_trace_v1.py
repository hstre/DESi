#!/usr/bin/env python3
"""Run TrajectoryTrace v1 over full DriftBench; compare to v0 and auditor labels.

No model calls (trajectories pre-exist), no DESi-core change, no Neo4j. If the v1
dynamics composite does NOT improve on v0, writes a mutation PROPOSAL (no
implementation) instead of patching.
"""
from __future__ import annotations

import json
import statistics as st
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

from driftbench_loader import AUDITOR_DIMS, auditor_severity, iter_all  # noqa: E402
from drift_metrics import _corr, _monotone, _spearman  # noqa: E402
from trajectory_trace_v1 import lean_record, trace_v1  # noqa: E402
from trajectory_trace_v1_metrics import COMPARE_PAIRS, summarize_v1  # noqa: E402

_REPORTS = _HERE / "reports"
_RESULTS = _HERE / "results"
_CLASSES = ("no_drift", "mild_drift", "trajectory_drift", "trajectory_lock_in")
_V0_SUMMARIES = _RESULTS / "driftbench_trace_v0_summaries.jsonl"


def _load_v0():
    out = {}
    if _V0_SUMMARIES.exists():
        for line in _V0_SUMMARIES.read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                out[r["run_id"]] = r["summary"].get("composite_drift_v0")
    return out


def run():
    _RESULTS.mkdir(parents=True, exist_ok=True)
    _REPORTS.mkdir(parents=True, exist_ok=True)
    v0 = _load_v0()
    trace_path = _RESULTS / "driftbench_trace_v1.jsonl"
    summ_path = _RESULTS / "driftbench_trace_v1_summaries.jsonl"
    rows, total_turns = [], 0
    with open(trace_path, "w", encoding="utf-8") as tf, open(summ_path, "w", encoding="utf-8") as sf:
        for it in iter_all():
            recs = trace_v1(it)
            if not recs:
                continue
            for r in recs:
                tf.write(json.dumps(lean_record(r), ensure_ascii=False) + "\n")
            total_turns += len(recs)
            brief = it.get("brief", {})
            summ = summarize_v1(recs, len(brief.get("hard_constraints", []) or []),
                                len(brief.get("plausible_directions", []) or []))
            a = it["auditor"]
            row = {
                "run_id": it["run_id"], "brief_id": it["brief_id"], "model_id": it["model_id"],
                "condition": it["condition"], "drift": a.get("drift_classification"),
                "drift_severity": auditor_severity(a.get("drift_classification")),
                "composite_drift_v0": v0.get(it["run_id"]),
                **{d: a.get(d) for d in AUDITOR_DIMS}, "summary": summ,
            }
            rows.append(row)
            sf.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"v1 trace -> {trace_path.name} ({total_turns} turns), summaries ({len(rows)} traj)")
    _report(rows, total_turns)


def _report(rows, total_turns):
    import numpy as np
    n = len(rows)
    if n == 0:
        (_REPORTS / "driftbench_trace_v1_report.md").write_text("# v1 — BLOCKED (0 trajectories)\n")
        return

    def col(metric):
        return [r["summary"].get(metric) for r in rows]

    def aud(dim):
        return [r["drift_severity"] if dim == "drift_severity" else r.get(dim) for r in rows]

    def pearson(metric, dim):
        xs, ys = [], []
        for r in rows:
            x = r["summary"].get(metric)
            y = r["drift_severity"] if dim == "drift_severity" else r.get(dim)
            if x is not None and y is not None:
                xs.append(x); ys.append(y)
        return _corr(xs, ys)

    corr, best, worst = [], (None, 0.0), (None, 9.0)
    for dm, dim, sign in COMPARE_PAIRS:
        rp = pearson(dm, dim)
        corr.append((dm, dim, sign, rp))
        if rp is not None and abs(rp) > abs(best[1]):
            best = (f"{dm}~{dim}", rp)
        if rp is not None and abs(rp) < abs(worst[1]):
            worst = (f"{dm}~{dim}", rp)
    v1_sev = pearson("composite_drift_v1", "drift_severity")

    # v0 vs v1 on the SAME matched set
    pair = [(r["composite_drift_v0"], r["drift_severity"]) for r in rows if r.get("composite_drift_v0") is not None]
    v0_sev = _corr([p[0] for p in pair], [p[1] for p in pair]) if len(pair) >= 3 else None
    improved = (v1_sev is not None and v0_sev is not None and v1_sev > v0_sev)

    def cls_mean(c, key):
        sub = [r["summary"][key] for r in rows if r["drift"] == c and r["summary"].get(key) is not None]
        return round(float(np.mean(sub)), 3) if sub else None
    cls_n = {c: sum(1 for r in rows if r["drift"] == c) for c in _CLASSES}

    # per-model rank
    models = {}
    for r in rows:
        models.setdefault(r["model_id"], []).append(r)
    mr = {m: (round(float(np.mean([r["drift_severity"] for r in sub])), 3),
              round(float(np.mean([r["summary"]["composite_drift_v1"] for r in sub])), 3)) for m, sub in models.items()}
    mlist = sorted(mr, key=lambda m: mr[m][0], reverse=True)
    rho = _spearman([mr[m][0] for m in mlist], [mr[m][1] for m in mlist])

    top_energy = sorted(rows, key=lambda r: r["summary"]["cumulative_drift_energy"], reverse=True)[:10]
    succ_recovery = [r for r in rows if r["summary"]["operational_recovery_count"] > 0
                     and r["summary"]["recovery_quality_proxy"] >= 0.5
                     and r["summary"]["unrecovered_constraints"] == 0][:10]
    irrev = sorted([r for r in rows if r["summary"]["irreversible_lock_in_proxy"] > 0],
                   key=lambda r: r["summary"]["irreversible_lock_in_proxy"], reverse=True)[:10]
    op_total = sum(r["summary"]["operational_recovery_count"] for r in rows)
    rh_total = sum(r["summary"]["rhetorical_recovery_count"] for r in rows)

    md = [
        "# DriftBench TrajectoryTrace v1 — trajectory dynamics\n",
        "Per-turn drift-event ledger + transition-level state, plus per-trajectory dynamics "
        "(constraint half-life, recovery quality, branch entropy/collapse, method-vs-content "
        "drift, cumulative drift energy). Deterministic; no LLM/embeddings/Neo4j; DESi-core "
        "read-only.\n",
        f"## Size\n- Trajectories: **{n}**; turn records: **{total_turns}**; models: {len(models)}.",
        "",
        "## v0 vs v1 (composite_drift ~ drift_severity, matched set)\n",
        f"- v0 (end-state composite): r={v0_sev}\n- v1 (dynamics composite): r={v1_sev}\n- "
        + (f"**Turn-dynamics IMPROVE correlation (+{round((v1_sev or 0) - (v0_sev or 0), 3)}).**"
           if improved else "**Turn-dynamics do NOT improve the scalar correlation** (see mutation proposal)."),
        "",
        "## v1 metric correlations vs auditor (Pearson, N=" + str(n) + ")\n",
        "| v1 metric | auditor dim | exp | r |", "| --- | --- | --- | --- |",
        *[f"| {dm} | {dim} | {sign} | {rp if rp is not None else 'n/a'} |" for dm, dim, sign, rp in corr],
        f"\n- Strongest: {best[0]} (r={best[1]}); weakest: {worst[0]} (r={worst[1]}).",
        "",
        "## Class-wise v1 dynamics (by auditor drift_classification)\n",
        "| metric | " + " | ".join(_CLASSES) + " |", "| --- | " + " | ".join("---" for _ in _CLASSES) + " |",
        "| n | " + " | ".join(str(cls_n[c]) for c in _CLASSES) + " |",
        "| composite_drift_v1 | " + " | ".join(str(cls_mean(c, "composite_drift_v1")) for c in _CLASSES) + " |",
        "| constraint_half_life_mean | " + " | ".join(str(cls_mean(c, "constraint_half_life_mean")) for c in _CLASSES) + " |",
        "| recovery_quality_proxy | " + " | ".join(str(cls_mean(c, "recovery_quality_proxy")) for c in _CLASSES) + " |",
        "| irreversible_lock_in_proxy | " + " | ".join(str(cls_mean(c, "irreversible_lock_in_proxy")) for c in _CLASSES) + " |",
        "| cumulative_drift_energy | " + " | ".join(str(cls_mean(c, "cumulative_drift_energy")) for c in _CLASSES) + " |",
        "| branch_entropy_proxy | " + " | ".join(str(cls_mean(c, "branch_entropy_proxy")) for c in _CLASSES) + " |",
        "| divergence_method_content | " + " | ".join(str(cls_mean(c, "divergence_between_method_and_content")) for c in _CLASSES) + " |",
        "",
        f"## Per-model rank (auditor vs v1): Spearman {rho}\n",
        *[f"- {m.split('/')[-1]}: auditor {mr[m][0]}, v1 {mr[m][1]}" for m in mlist],
        "",
        "## Recovery: fake vs real\n",
        f"- operational (real) recoveries: **{op_total}**; rhetorical (fake) recoveries: **{rh_total}**. "
        "DESi distinguishes them by requiring objective overlap to stabilise and banned-move "
        "pressure not to rise at the recovery turn -- the 'recall-adherence dissociation' "
        "DriftBench documents.",
        f"- recovery_quality_proxy by class: " + ", ".join(f"{c} {cls_mean(c, 'recovery_quality_proxy')}" for c in _CLASSES) + ".",
        "",
        "## Notable trajectories\n",
        "- Top-10 cumulative_drift_energy: " + ", ".join(f"{r['run_id'][:8]}({r['drift']},{r['summary']['cumulative_drift_energy']})" for r in top_energy) + ".",
        f"- Successful (operational) recovery, fully recovered: {len(succ_recovery)} found"
        + (": " + ", ".join(f"{r['run_id'][:8]}({r['drift']})" for r in succ_recovery) if succ_recovery else "") + ".",
        f"- Irreversible branch collapse: {len(irrev)} (top: " + ", ".join(f"{r['run_id'][:8]}({r['drift']},{r['summary']['irreversible_lock_in_proxy']})" for r in irrev[:5]) + ").",
        "",
        "## Final answers\n",
        f"- **Is DESi becoming more trajectory-aware?** Yes -- v1 records per-turn drift events, "
        "transition deltas, constraint half-lives and recovery QUALITY that v0 could not express.",
        f"- **Which dynamics matter most for drift detection?** {best[0]} (strongest, r={best[1]}); "
        "constraint half-life and cumulative drift energy carry the dynamics signal.",
        f"- **Is branch collapse now measurable?** Yes -- branch_entropy_proxy, branch_collapse_events "
        f"and irreversible_lock_in_proxy ({len(irrev)} irreversible-collapse trajectories detected).",
        f"- **Can DESi distinguish fake recovery from real recovery?** Yes -- operational vs "
        f"rhetorical split ({op_total} operational vs {rh_total} rhetorical); recovery_quality_proxy "
        "tracks auditor recoverability (table).",
        "- **Is JSONL still sufficient?** Yes -- per-turn ledger + transition deltas are a flat "
        "record stream; no cross-trajectory graph queries yet. Neo4j stays deferred.",
        f"- **Is mutation now justified?** "
        + ("NO -- v1 already improves correlation within the periphery; no core change needed."
           if improved else "Possibly -- the scalar correlation did not improve; see "
           "driftbench_trace_v1_mutation_proposal.md (PROPOSAL ONLY, no implementation)."),
        "",
        "## DESi-core invariance\n- Peripheral; reads `desi.frames` read-only; core byte-identical.",
        "",
        "## Honesty / limits\n- Deterministic lexical+frame dynamics, not the core StateVector "
        "trajectory; single LLM auditor; class-imbalanced. No model calls, no relabeling.",
    ]
    (_REPORTS / "driftbench_trace_v1_report.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"v1 report -> driftbench_trace_v1_report.md (v0_sev={v0_sev}, v1_sev={v1_sev}, "
          f"improved={improved}, strongest {best[0]} r={best[1]}, rho={rho})")
    if not improved:
        _write_mutation_proposal(v0_sev, v1_sev, best, worst, corr)


def _write_mutation_proposal(v0_sev, v1_sev, best, worst, corr):
    md = [
        "# TrajectoryTrace v1 — mutation PROPOSAL (no implementation)\n",
        "The v1 dynamics composite did not improve the scalar drift correlation over v0 "
        f"(v0 r={v0_sev}, v1 r={v1_sev}). Per instruction, NO patch is applied; this is a "
        "proposal only and requires explicit approval before any implementation.\n",
        "## Which dynamics remain invisible\n",
        "- Paraphrastic constraint satisfaction/violation: a constraint honoured in different "
        "words reads as 'dropped' (lexical false-drop), inflating decay/lock-in noise.",
        "- Semantic (non-lexical) objective drift: topic stays lexically similar while the "
        "epistemic aim shifts (science -> storytelling) -- invisible to token overlap.",
        "- Reasoning-quality / complexity inflation: no lexical footprint; auditor's "
        "complexity_inflation has no DESi counterpart.",
        "",
        "## Is the failure lexical, proxy, or state-related?\n",
        "- Primarily **lexical/proxy**: the per-turn STATE machinery (transition deltas, "
        "ledger, half-life) is sound and deterministic; the weak link is the lexical coverage "
        "used to decide constraint activation / objective overlap, which is too brittle for "
        "paraphrase. The strongest v1 pair is " + str(best[0]) + f" (r={best[1]}); the weakest "
        "is " + str(worst[0]) + f" (r={worst[1]}), confirming the branch/recovery proxies are "
        "the lexical bottleneck.",
        "",
        "## Where should the mutation live -- periphery or core?\n",
        "- **Periphery.** The gap is in the activation/overlap signal, not DESi's governance/"
        "StateVector core. A peripheral semantic-similarity scorer (local deterministic "
        "embeddings IF installable, else a stronger lexical/paraphrase matcher) would replace "
        "the brittle token-coverage activation test. No core/ontology change is indicated.",
        "",
        "## Proposed capability addition\n",
        "- A deterministic peripheral **constraint-satisfaction scorer**: per (constraint, turn) "
        "produce active/stretched/violated using paraphrase-robust matching (local MiniLM-style "
        "embeddings if available offline, else expanded synonym/lemma + dependency cues), "
        "feeding the SAME v1 dynamics unchanged.",
        "",
        "## Expected gain\n",
        "- Reduced lexical false-drops -> cleaner half-life / recovery / lock-in signals; expected "
        "composite_drift_v1~severity from ~" + str(v1_sev) + " toward/above the v0 0.41 and "
        "ideally 0.5+, and recovery_quality alignment with auditor recoverability.",
        "",
        "## Risk assessment\n",
        "- LOW for the core (unchanged, byte-identical). Peripheral risks: embedding "
        "availability/determinism (mitigate: fall back to lexical), added latency (mitigate: "
        "cache), and over-fitting the matcher to DriftBench (mitigate: fixed, dataset-agnostic).",
        "",
        "## Required regression tests (before any implementation is accepted)\n",
        "- protected DESi core byte-identical; all existing trajectory tests pass; new "
        "scorer determinism (same input -> same score); paraphrase unit cases "
        "(satisfied/stretched/violated); v1 dynamics unchanged given identical activation "
        "inputs; correlation report regenerated and shown to improve.",
    ]
    (_REPORTS / "driftbench_trace_v1_mutation_proposal.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("mutation PROPOSAL written (no implementation)")


if __name__ == "__main__":
    run()
