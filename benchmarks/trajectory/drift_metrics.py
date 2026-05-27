#!/usr/bin/env python3
"""DESi-relevant trajectory drift metrics over DriftBench (PERIPHERAL).

Computes, per DriftBench trajectory, DESi-STYLE metrics deterministically from the
transcript + brief (no model calls, no DESi-core change):
  constraint_preservation, branch_preservation, recoverability,
  trajectory_consistency, semantic_drift, final_state_deviation,
  frame_flip_rate (via the DESi frame layer), banned_incursion, composite_drift.

Then probes whether these track DriftBench's independent AUDITOR labels
(objective_fidelity / constraint_adherence / alternative_coverage / recoverability
/ drift_classification) -- i.e. whether this benchmark exercises DESi's core
strengths better than single-turn FEVER/BoolQ.
"""
from __future__ import annotations

import statistics as st
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

from trajectory_adapter import to_trajectory  # noqa: E402
from driftbench_loader import AUDITOR_DIMS, auditor_severity, load_sample  # noqa: E402

_REPORTS = _HERE / "reports"

# DESi metric  ->  natural DriftBench auditor counterpart
DESI_TO_AUDITOR = {
    "constraint_preservation": "constraint_adherence",
    "branch_preservation": "alternative_coverage",
    "recoverability": "recoverability",
    "objective_fidelity_proxy": "objective_fidelity",
    "composite_drift": "drift_severity",
}


def _clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


def trajectory_metrics(item: dict) -> dict:
    traj = to_trajectory(item)
    if not traj:
        return {}
    ret = [t["constraint_retention"] for t in traj]
    objov = [t["objective_overlap"] for t in traj]
    altc = [t["alternative_coverage"] for t in traj]
    banned = [t["banned_incursion"] for t in traj]
    frames = [t["desi_frame"] for t in traj]
    n_dir = max(1, len(item.get("brief", {}).get("plausible_directions", []) or []))

    constraint_preservation = round(sum(ret) / len(ret), 3)
    branch_preservation = round(_clamp((sum(altc) / len(altc)) / n_dir), 3)
    # recovery from the worst mid-trajectory dip back toward the opening level
    dip = min(ret)
    recoverability = round(_clamp((ret[-1] - dip) / (ret[0] - dip)) if ret[0] > dip else 1.0, 3)
    trajectory_consistency = round(_clamp(1.0 - (st.pstdev(ret) if len(ret) > 1 else 0.0)), 3)
    semantic_drift = round(_clamp(objov[0] - objov[-1]), 3)
    objective_fidelity_proxy = round(_clamp(objov[-1]), 3)
    final_state_deviation = round(_clamp(1.0 - (ret[-1] + objov[-1]) / 2.0), 3)
    frame_flip_rate = round(sum(1 for i in range(1, len(frames)) if frames[i] != frames[i - 1])
                            / max(1, len(frames) - 1), 3)
    banned_incursion = sum(banned)
    composite_drift = round(_clamp(st.mean([
        semantic_drift, final_state_deviation, 1.0 - constraint_preservation, frame_flip_rate])), 3)
    return {
        "turns": len(traj),
        "constraint_preservation": constraint_preservation,
        "branch_preservation": branch_preservation,
        "recoverability": recoverability,
        "trajectory_consistency": trajectory_consistency,
        "semantic_drift": semantic_drift,
        "objective_fidelity_proxy": objective_fidelity_proxy,
        "final_state_deviation": final_state_deviation,
        "frame_flip_rate": frame_flip_rate,
        "banned_incursion": banned_incursion,
        "composite_drift": composite_drift,
    }


def _corr(xs, ys):
    import numpy as np
    xs, ys = np.asarray(xs, float), np.asarray(ys, float)
    if len(xs) < 3 or xs.std() == 0 or ys.std() == 0:
        return None
    return round(float(np.corrcoef(xs, ys)[0, 1]), 3)


def probe(limit: int = 15):
    items = load_sample(limit)
    if not items:
        _write_blocked("load_sample returned 0 items")
        return
    rows = []
    for it in items:
        m = trajectory_metrics(it)
        a = it["auditor"]
        rows.append({
            "run_id": it["run_id"], "brief_id": it["brief_id"], "model_id": it["model_id"],
            "condition": it["condition"], "drift": a.get("drift_classification"),
            "drift_severity": auditor_severity(a.get("drift_classification")),
            "auditor": {d: a.get(d) for d in AUDITOR_DIMS}, "desi": m,
        })
    _write_report(rows)


def _write_blocked(reason):
    _REPORTS.mkdir(parents=True, exist_ok=True)
    (_REPORTS / "driftbench_probe.md").write_text(
        f"# DriftBench probe — BLOCKED\n\nExact blocker: {reason}\n", encoding="utf-8")
    print(f"BLOCKED: {reason}")


def _write_report(rows):
    n = len(rows)
    # correlations DESi metric vs natural auditor counterpart
    corrs = {}
    for dm, ad in DESI_TO_AUDITOR.items():
        xs = [r["desi"].get(dm) for r in rows]
        ys = [r["drift_severity"] if ad == "drift_severity" else r["auditor"].get(ad) for r in rows]
        pair = [(x, y) for x, y in zip(xs, ys) if x is not None and y is not None]
        corrs[(dm, ad)] = _corr([p[0] for p in pair], [p[1] for p in pair]) if len(pair) >= 3 else None
    cond_mix = {}
    for r in rows:
        cond_mix[r["condition"]] = cond_mix.get(r["condition"], 0) + 1
    drift_mix = {}
    for r in rows:
        drift_mix[r["drift"]] = drift_mix.get(r["drift"], 0) + 1

    md = [
        "# DriftBench probe — DESi trajectory diagnosis\n",
        "**Dataset actually loaded:** `driftbench/DriftBench` (HF hub, CC-BY-4.0), split "
        "`validation`. Real multi-turn LLM-ideation trajectories with an independent auditor; "
        "no faking, no model calls (trajectories already exist; DESi analyses them).\n",
        f"**Probe size:** {n} trajectories. Conditions: {cond_mix}. Drift labels: {drift_mix}.\n",
        "## Schema\n",
        "- **brief** (initial intent + constraints): objective, hard_constraints[3-8], "
        "banned_moves[2-5], success_criteria[2+], plausible_directions[2-5].",
        "- **transcript**: system + alternating user(pressure)/assistant turns (~11 turns).",
        "- **auditor labels** (0-4): objective_fidelity, constraint_adherence, "
        "alternative_coverage, complexity_inflation, recoverability; plus "
        "drift_classification {no_drift, mild_drift, trajectory_drift, trajectory_lock_in} "
        "and per-turn drift_events.",
        "",
        "## DESi metric mapping (which map naturally, which do not)\n",
        "| DESi-style metric | DriftBench counterpart | maps naturally? |",
        "| --- | --- | --- |",
        "| constraint_preservation | constraint_adherence | YES (direct) |",
        "| branch_preservation | alternative_coverage | YES (direct) |",
        "| recoverability | recoverability | YES (direct) |",
        "| semantic_drift / objective_fidelity_proxy | objective_fidelity | YES (direct) |",
        "| final_state_deviation | blind-judge brief-vs-final | YES (proxy) |",
        "| trajectory_consistency | (per-turn drift_events) | PARTIAL (no single scalar) |",
        "| frame_flip_rate (DESi frame layer) | — | DESi-intrinsic, no direct label |",
        "| composite_drift | drift_classification severity | YES (ordinal) |",
        "| (none) | complexity_inflation | NOT mapped (needs reasoning-depth analysis) |",
        "",
        "Every core DESi strength the task named — constraint preservation, semantic drift, "
        "recoverability, trajectory consistency, branch preservation, final-state deviation — "
        "has a NATURAL counterpart here, unlike single-turn FEVER/BoolQ which have none.",
        "",
        "## First probe results — per trajectory\n",
        "| run | model | cond | drift label | DESi composite_drift | DESi constr_presv (auditor adher) | DESi branch (auditor altcov) | DESi recov (auditor recov) |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for r in rows:
        d, a = r["desi"], r["auditor"]
        md.append(f"| {r['run_id'][:8]} | {str(r['model_id']).split('/')[-1][:16]} | {r['condition'][:16]} "
                  f"| {r['drift']} | {d.get('composite_drift')} | {d.get('constraint_preservation')} "
                  f"({a.get('constraint_adherence')}) | {d.get('branch_preservation')} "
                  f"({a.get('alternative_coverage')}) | {d.get('recoverability')} ({a.get('recoverability')}) |")
    md += [
        "",
        "## Correlation: DESi-style metric vs DriftBench auditor (Pearson, probe N)\n",
        "| DESi metric | auditor counterpart | r |", "| --- | --- | --- |",
    ]
    for (dm, ad), r in corrs.items():
        md.append(f"| {dm} | {ad} | {r if r is not None else 'n/a (constant/too few)'} |")
    pos = [r for r in corrs.values() if isinstance(r, float)]
    md += [
        "",
        "- Positive r for the constraint/branch/recoverability/fidelity pairs and for "
        "composite_drift-vs-severity indicates the deterministic DESi-style trajectory "
        "diagnosis tracks the benchmark's independent drift labels. "
        + (f"{sum(1 for r in pos if r > 0)}/{len(pos)} computed correlations are positive."
           if pos else "Correlations were not computable on this small probe (constant columns)."),
        "",
        "## Does this benchmark measure DESi's core strengths better than FEVER/BoolQ?\n",
        "**YES.** FEVER/BoolQ are single-turn classification: they have no trajectory, no "
        "evolving constraints, no recoverability, no branch structure — none of DESi's named "
        "strengths apply, and (as the FEVER mapping saga showed) accuracy there was dominated "
        "by label/mapping issues. DriftBench is intrinsically multi-turn with explicit hard "
        "constraints, banned moves, plausible directions, iterative pressure, and an auditor "
        "that scores exactly the dimensions DESi is built around (constraint adherence, "
        "objective fidelity, alternative coverage, recoverability, drift). It is a far better "
        "fit for evaluating DESi's trajectory/drift/constraint-retention machinery.",
        "",
        "## DESi-core invariance\n",
        "- This is a peripheral adapter: it READS the DESi frame layer (`desi.frames`) only; "
        "no core/ontology change. The deterministic StateVector/governance core is untouched.",
        "",
        "## Honesty / limits\n",
        "- Probe only (small N); DESi-style metrics use deterministic LEXICAL proxies for "
        "constraint/objective/branch coverage plus the DESi frame layer for frame-flip — they "
        "are NOT the DESi core's internal StateVector trajectory (there is no public arbitrary-"
        "text trajectory factory). Auditor labels are a single LLM auditor. No model calls, no "
        "relabeling, no generation (trajectories pre-exist). Correlations are indicative, not "
        "conclusive, at this N.",
    ]
    _REPORTS.mkdir(parents=True, exist_ok=True)
    (_REPORTS / "driftbench_probe.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"probe report -> driftbench_probe.md ({n} trajectories; "
          f"corr computed: {sum(1 for v in corrs.values() if isinstance(v, float))}/{len(corrs)})")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=15)
    probe(ap.parse_args().limit)
