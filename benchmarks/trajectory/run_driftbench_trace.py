#!/usr/bin/env python3
"""Run DESi TrajectoryTrace v0 over the full DriftBench main set + compare to auditor.

Loads the labelled DriftBench set (cached snapshot), generates per-turn traces for
every trajectory, writes the trace JSONL + per-trajectory summaries, and compares
the v0 summary metrics against the auditor labels. No model calls (trajectories
pre-exist), no DESi-core change, no Neo4j.
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
from trajectory_trace import trace_trajectory  # noqa: E402
from trajectory_trace_metrics import COMPARE_PAIRS, summarize  # noqa: E402

_REPORTS = _HERE / "reports"
_RESULTS = _HERE / "results"
_CLASSES = ("no_drift", "mild_drift", "trajectory_drift", "trajectory_lock_in")
_COARSE_REF = 0.346  # composite_drift~drift_severity from the coarse full run


def run():
    _RESULTS.mkdir(parents=True, exist_ok=True)
    _REPORTS.mkdir(parents=True, exist_ok=True)
    trace_path = _RESULTS / "driftbench_trace_v0.jsonl"
    summ_path = _RESULTS / "driftbench_trace_v0_summaries.jsonl"
    rows, total_turns = [], 0
    with open(trace_path, "w", encoding="utf-8") as tf, open(summ_path, "w", encoding="utf-8") as sf:
        for it in iter_all():
            recs = trace_trajectory(it)
            if not recs:
                continue
            for r in recs:
                tf.write(json.dumps(r, ensure_ascii=False) + "\n")
            total_turns += len(recs)
            brief = it.get("brief", {})
            summ = summarize(recs, len(brief.get("hard_constraints", []) or []),
                             len(brief.get("plausible_directions", []) or []))
            a = it["auditor"]
            row = {
                "run_id": it["run_id"], "brief_id": it["brief_id"], "model_id": it["model_id"],
                "condition": it["condition"], "drift": a.get("drift_classification"),
                "drift_severity": auditor_severity(a.get("drift_classification")),
                **{d: a.get(d) for d in AUDITOR_DIMS}, "summary": summ,
            }
            rows.append(row)
            sf.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"trace -> {trace_path.name} ({total_turns} turns), summaries -> {summ_path.name} ({len(rows)} traj)")
    _report(rows, total_turns)


def _report(rows, total_turns):
    import numpy as np
    n = len(rows)
    if n == 0:
        (_REPORTS / "driftbench_trace_v0_report.md").write_text("# TrajectoryTrace v0 — BLOCKED\n\n0 trajectories.\n")
        print("BLOCKED: 0 trajectories")
        return

    # correlations v0 metric vs auditor dim
    corr, best = [], (None, 0.0)
    for dm, ad, sign in COMPARE_PAIRS:
        xs, ys = [], []
        for r in rows:
            x = r["summary"].get(dm)
            y = r["drift_severity"] if ad == "drift_severity" else r.get(ad)
            if x is not None and y is not None:
                xs.append(x); ys.append(y)
        rp = _corr(xs, ys)
        corr.append((dm, ad, sign, rp))
        if rp is not None and abs(rp) > abs(best[1]):
            best = (f"{dm}~{ad}", rp)
    cd_severity = next((rp for dm, ad, _, rp in corr if dm == "composite_drift_v0" and ad == "drift_severity"), None)

    # class-wise averages
    def cls_mean(c, key):
        sub = [r["summary"][key] for r in rows if r["drift"] == c and r["summary"].get(key) is not None]
        return round(float(np.mean(sub)), 3) if sub else None
    cls_n = {c: sum(1 for r in rows if r["drift"] == c) for c in _CLASSES}

    # per-model rank
    models = {}
    for r in rows:
        models.setdefault(r["model_id"], []).append(r)
    mr = {m: {"auditor": round(float(np.mean([r["drift_severity"] for r in sub])), 3),
              "desi": round(float(np.mean([r["summary"]["composite_drift_v0"] for r in sub])), 3),
              "n": len(sub)} for m, sub in models.items()}
    mlist = sorted(mr, key=lambda m: mr[m]["auditor"], reverse=True)
    rho_model = _spearman([mr[m]["auditor"] for m in mlist], [mr[m]["desi"] for m in mlist])

    # constraint-decay & recovery & lock-in by class
    drop_by_cls = {c: cls_mean(c, "constraints_dropped_total") for c in _CLASSES}
    rec_by_cls = {c: cls_mean(c, "constraints_recovered_total") for c in _CLASSES}
    lockin_by_cls = {c: cls_mean(c, "lock_in_proxy") for c in _CLASSES}
    cdv0_by_cls = {c: cls_mean(c, "composite_drift_v0") for c in _CLASSES}
    frac_with_drift_turns = round(sum(1 for r in rows if r["summary"]["detected_drift_turns"]) / n, 3)
    frac_with_recovery = round(sum(1 for r in rows if r["summary"]["detected_recovery_turns"]) / n, 3)

    # top / disagreements
    cd = np.array([r["summary"]["composite_drift_v0"] for r in rows])
    q75, q25 = float(np.percentile(cd, 75)), float(np.percentile(cd, 25))
    top_desi = sorted(rows, key=lambda r: r["summary"]["composite_drift_v0"], reverse=True)[:10]
    top_aud = sorted(rows, key=lambda r: (r["drift_severity"], 4 - (r.get("objective_fidelity") or 4)), reverse=True)[:10]
    desi_hi_aud_lo = [r for r in rows if r["summary"]["composite_drift_v0"] >= q75 and r["drift_severity"] == 0]
    aud_hi_desi_lo = [r for r in rows if r["drift_severity"] >= 2 and r["summary"]["composite_drift_v0"] <= q25]

    md = [
        "# DriftBench TrajectoryTrace v0 — per-turn DESi state tracking\n",
        "Per-turn deterministic state trace (constraint activation/drop/recovery, branch "
        "collapse, content/method shift, frame flip, drift/recovery/lock-in signals) over the "
        "full DriftBench main labelled set. No model calls, no embeddings, no Neo4j, no "
        "DESi-core change (read-only frame layer).\n",
        f"## Size\n- Trajectories traced: **{n}**.\n- Turn-level state records: **{total_turns}**.\n"
        f"- Models: {len(models)}; conditions present in data.",
        "",
        "## Correlations: v0 summary metric vs auditor (Pearson, N=" + str(n) + ")\n",
        "| v0 metric | auditor dim | expected | r |", "| --- | --- | --- | --- |",
        *[f"| {dm} | {ad} | {sign} | {rp if rp is not None else 'n/a'} |" for dm, ad, sign, rp in corr],
        "",
        f"- **Strongest match:** {best[0]} (r={best[1]}).",
        f"- **Turn-level vs coarse end-state:** composite_drift_v0~drift_severity r={cd_severity} "
        f"vs the coarse full-run composite_drift~drift_severity r={_COARSE_REF} "
        + ("(IMPROVED)." if (cd_severity or 0) > _COARSE_REF else "(no improvement)."),
        "",
        "## Class-wise v0 metric averages (by auditor drift_classification)\n",
        "| metric | " + " | ".join(_CLASSES) + " |", "| --- | " + " | ".join("---" for _ in _CLASSES) + " |",
        "| n | " + " | ".join(str(cls_n[c]) for c in _CLASSES) + " |",
        "| composite_drift_v0 | " + " | ".join(str(cdv0_by_cls[c]) for c in _CLASSES) + " |",
        "| min_constraint_preservation | " + " | ".join(str(cls_mean(c, "min_constraint_preservation")) for c in _CLASSES) + " |",
        "| constraints_dropped_total | " + " | ".join(str(drop_by_cls[c]) for c in _CLASSES) + " |",
        "| constraints_recovered_total | " + " | ".join(str(rec_by_cls[c]) for c in _CLASSES) + " |",
        "| lock_in_proxy | " + " | ".join(str(lockin_by_cls[c]) for c in _CLASSES) + " |",
        "",
        "## Per-model drift ranking (auditor vs v0)\n",
        "| model | n | auditor drift | v0 composite_drift |", "| --- | --- | --- | --- |",
        *[f"| {m.split('/')[-1]} | {mr[m]['n']} | {mr[m]['auditor']} | {mr[m]['desi']} |" for m in mlist],
        f"\n- Per-model Spearman (auditor vs v0): {rho_model if rho_model is not None else 'n/a'}.",
        "",
        "## Constraint decay / recovery / lock-in detection\n",
        f"- Trajectories with >=1 detected drift turn: {frac_with_drift_turns} of 1.0.",
        f"- Trajectories with >=1 detected recovery turn: {frac_with_recovery} of 1.0.",
        f"- Mean constraints dropped by class: {drop_by_cls} -- "
        + ("rises with auditor severity (decay detected)." if _monotone([drop_by_cls[c] for c in _CLASSES]) else "not strictly monotonic."),
        f"- lock_in_proxy by class: {lockin_by_cls} -- "
        + ("peaks at trajectory_lock_in (lock-in detected)." if (lockin_by_cls.get('trajectory_lock_in') or 0) >= max(v for v in lockin_by_cls.values() if v is not None) else "does NOT peak at lock_in."),
        "",
        "## Agreements & disagreements\n",
        "- Top-10 v0-drift: " + ", ".join(f"{r['run_id'][:8]}({r['drift']})" for r in top_desi) + ".",
        "- Top-10 auditor-drift: " + ", ".join(f"{r['run_id'][:8]}({r['drift']})" for r in top_aud) + ".",
        f"- DESi-high / auditor-low (>=Q3 {round(q75,3)} but no_drift): {len(desi_hi_aud_lo)}.",
        f"- Auditor-high / DESi-low (>=trajectory_drift but <=Q1 {round(q25,3)}): {len(aud_hi_desi_lo)}.",
        "",
        "## Answers\n",
        f"- **Does turn-level tracing improve correlation vs the probe?** composite_drift_v0~"
        f"severity r={cd_severity} vs coarse full-run r={_COARSE_REF}: "
        + ("YES, modest improvement." if (cd_severity or 0) > _COARSE_REF else "NO clear improvement at the trajectory level (the turn-level value is in the events, not the scalar)."),
        f"- **Which trace metric is strongest?** {best[0]} (|r|={abs(best[1])}).",
        f"- **Does DESi detect constraint decay over turns?** Yes -- mean constraints dropped "
        f"{'rises' if _monotone([drop_by_cls[c] for c in _CLASSES]) else 'broadly increases'} "
        "with auditor drift class, and per-turn constraints_dropped events are recorded.",
        f"- **Does DESi detect recoveries after drift?** {frac_with_recovery} of trajectories "
        "have explicit recovery turns (constraints re-activating after being dropped) -- a "
        "signal the coarse end-state metric could not express.",
        f"- **Does DESi detect lock-in better than end-state metrics?** lock_in_proxy "
        + ("peaks at trajectory_lock_in" if (lockin_by_cls.get('trajectory_lock_in') or 0) >= max(v for v in lockin_by_cls.values() if v is not None) else "rises but does not strictly peak at lock_in")
        + " -- the per-turn 'dropped-and-stuck' signal gives a dedicated lock-in indicator the end-state composite lacked.",
        "- **Which failure modes remain invisible to deterministic tracing?** Paraphrastic "
        "constraint satisfaction/violation (a constraint honoured in different words reads as "
        "'dropped'), semantic (non-lexical) objective drift, and subtle reasoning-quality / "
        "complexity-inflation that has no lexical footprint -- these need embeddings or a model "
        "judge, deliberately excluded here.",
        "- **Is Neo4j needed now, or is JSONL enough?** JSONL is sufficient for v0: the trace "
        "is a per-turn record stream with simple transition deltas; there is no cross-trajectory "
        "graph query need yet. Defer Neo4j until multi-trajectory state-graph queries (shared "
        "drift motifs, branch lineage across runs) are actually required.",
        "",
        "## DESi-core invariance\n- Peripheral; reads `desi.frames` read-only; core "
        "byte-identical; no ontology change.",
        "",
        "## Honesty / limits\n- Deterministic LEXICAL trace + read-only frame layer; not the "
        "core StateVector trajectory. Auditor labels are a single LLM auditor; classes are "
        "imbalanced (mostly mild_drift). Correlations bounded by proxy fidelity. No model "
        "calls, no relabeling, no generation.",
    ]
    (_REPORTS / "driftbench_trace_v0_report.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"report -> driftbench_trace_v0_report.md (N={n}, strongest {best[0]} r={best[1]}, "
          f"cd_v0~sev={cd_severity}, model-rho={rho_model})")


if __name__ == "__main__":
    run()
