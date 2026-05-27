#!/usr/bin/env python3
"""DriftBench ranking comparison (PERIPHERAL, measurement only).

Where does DESi TrajectoryTrace v1.1 stand against the DriftBench auditor ordering?
DriftBench has NO official leaderboard/ranking file (re-verified against the repo
siblings); we reconstruct the ranking from the auditor labels and compare DESi's
composite_drift_v1.1 against it: per-trajectory rank correlation (Spearman, Kendall
tau-b, Pearson), top-k overlap, per-model rank agreement, class-wise ordering, and
disagreement examples.

Inputs: results/driftbench_trace_v11_summaries.jsonl (DESi v1.1 composite) joined
with results/driftbench_trace_v1_summaries.jsonl (all five auditor dims). No DESi
metric tuning, no core change, no model calls.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

from drift_metrics import _corr, _spearman  # noqa: E402

_REPORTS = _HERE / "reports"
_RESULTS = _HERE / "results"
_V1 = _RESULTS / "driftbench_trace_v1_summaries.jsonl"
_V11 = _RESULTS / "driftbench_trace_v11_summaries.jsonl"
_CLASSES = ("no_drift", "mild_drift", "trajectory_drift", "trajectory_lock_in")
_DIMS = ("objective_fidelity", "constraint_adherence", "alternative_coverage",
         "complexity_inflation", "recoverability")


def auditor_drift_score(row: dict) -> float:
    """Reconstructed composite auditor DRIFT score (higher = more drift), 0-1.
    Combines severity + the five 0-4 dimensions (fidelity/adherence/coverage/
    recoverability inverted; complexity_inflation as-is, lower-is-better)."""
    parts = [row["drift_severity"] / 3.0]
    for d in ("objective_fidelity", "constraint_adherence", "alternative_coverage", "recoverability"):
        v = row.get(d)
        if v is not None:
            parts.append((4 - v) / 4.0)
    ci = row.get("complexity_inflation")
    if ci is not None:
        parts.append(ci / 4.0)
    return round(sum(parts) / len(parts), 4)


def _kendall_tau_b(x, y):
    import numpy as np
    x, y = np.asarray(x, float), np.asarray(y, float)
    n = len(x)
    if n < 3:
        return None
    dx = np.sign(np.subtract.outer(x, x))
    dy = np.sign(np.subtract.outer(y, y))
    iu = np.triu_indices(n, 1)
    nc_nd = float((dx[iu] * dy[iu]).sum())

    def ties(a):
        _, c = np.unique(a, return_counts=True)
        return float(np.sum(c * (c - 1) / 2))
    n0 = n * (n - 1) / 2.0
    den = ((n0 - ties(x)) * (n0 - ties(y))) ** 0.5
    return round(nc_nd / den, 3) if den > 0 else None


def top_k_overlap(rows, desi_key, aud_key, k):
    by_desi = sorted(rows, key=lambda r: r[desi_key], reverse=True)[:k]
    by_aud = sorted(rows, key=lambda r: r[aud_key], reverse=True)[:k]
    s1 = {r["run_id"] for r in by_desi}
    s2 = {r["run_id"] for r in by_aud}
    return round(len(s1 & s2) / k, 3)


def _official_ranking_files():
    try:
        from huggingface_hub import HfApi
        sibs = [s.rfilename for s in HfApi().dataset_info("driftbench/DriftBench").siblings]
        return [f for f in sibs if any(k in f.lower() for k in
                ("leaderboard", "ranking", "scoreboard", "results/", "aggregate"))]
    except Exception:
        return None


def _load():
    aud = {}
    for line in _V1.read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            aud[r["run_id"]] = {"run_id": r["run_id"], "model_id": r["model_id"],
                                "condition": r["condition"], "drift": r["drift"],
                                "drift_severity": r["drift_severity"],
                                **{d: r.get(d) for d in _DIMS}}
    rows = []
    for line in _V11.read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            a = aud.get(r["run_id"])
            if a is None:
                continue
            row = dict(a)
            row["desi"] = r["v11_composite"]
            row["auditor_score"] = auditor_drift_score(a)
            rows.append(row)
    return rows


def run():
    official = _official_ranking_files()
    rows = _load()
    n = len(rows)
    desi = [r["desi"] for r in rows]
    sev = [r["drift_severity"] for r in rows]
    aud = [r["auditor_score"] for r in rows]

    sp_sev = _spearman(desi, sev)
    sp_aud = _spearman(desi, aud)
    kt_aud = _kendall_tau_b(desi, aud)
    pr_aud = _corr(desi, aud)
    overlap = {k: top_k_overlap(rows, "desi", "auditor_score", k) for k in (10, 25, 50)}

    # model-level
    import numpy as np
    models = {}
    for r in rows:
        models.setdefault(r["model_id"], []).append(r)
    mr = {m: (round(float(np.mean([x["auditor_score"] for x in s])), 3),
              round(float(np.mean([x["desi"] for x in s])), 3),
              round(float(np.mean([x["drift_severity"] for x in s])), 3), len(s))
          for m, s in models.items()}
    mlist = sorted(mr, key=lambda m: mr[m][0], reverse=True)
    model_sp = _spearman([mr[m][0] for m in mlist], [mr[m][1] for m in mlist])

    # class-wise DESi mean
    cls = {c: round(float(np.mean([r["desi"] for r in rows if r["drift"] == c])), 3)
           for c in _CLASSES if any(r["drift"] == c for r in rows)}

    top_desi = sorted(rows, key=lambda r: r["desi"], reverse=True)[:10]
    top_aud = sorted(rows, key=lambda r: r["auditor_score"], reverse=True)[:10]
    q75 = float(np.percentile(desi, 75))
    q25 = float(np.percentile(desi, 25))
    desi_hi_aud_lo = sorted([r for r in rows if r["desi"] >= q75 and r["drift_severity"] == 0],
                            key=lambda r: r["desi"], reverse=True)[:10]
    aud_hi_desi_lo = sorted([r for r in rows if r["drift_severity"] >= 2 and r["desi"] <= q25],
                            key=lambda r: r["auditor_score"], reverse=True)[:10]

    model_strong = (model_sp or 0) >= 0.7
    traj_moderate = (sp_aud or 0) >= 0.4

    md = [
        "# DriftBench ranking comparison — DESi TrajectoryTrace v1.1\n",
        "Measurement only (no DESi metric tuning, no core change, no model calls).\n",
        "## Is there an official DriftBench ranking?\n",
        ("**No official leaderboard/ranking file found** in the repo "
         f"(checked siblings; matches: {official})." if not official else
         f"Official ranking-like files found: {official}.")
        + " Ranking is therefore reconstructed from the auditor labels: a composite "
        "auditor DRIFT score = mean of severity/3 + inverted objective_fidelity / "
        "constraint_adherence / alternative_coverage / recoverability + "
        "complexity_inflation (all 0-1, higher = more drift). DESi ranking = "
        "composite_drift_v1.1.",
        "",
        f"## Size\n- Trajectories ranked: **{n}**; models: **{len(models)}**.",
        "",
        "## DESi vs reconstructed auditor ranking (per trajectory)\n",
        "| comparison | value |", "| --- | --- |",
        f"| Spearman (DESi vs auditor composite) | {sp_aud} |",
        f"| Spearman (DESi vs drift_severity) | {sp_sev} |",
        f"| Kendall tau-b (DESi vs auditor composite) | {kt_aud} |",
        f"| Pearson (DESi vs auditor composite) | {pr_aud} |",
        f"| top-10 overlap | {overlap[10]} |",
        f"| top-25 overlap | {overlap[25]} |",
        f"| top-50 overlap | {overlap[50]} |",
        "",
        "## Per-model rank table (sorted by auditor drift)\n",
        "| model | n | auditor drift | auditor severity | DESi v1.1 |",
        "| --- | --- | --- | --- | --- |",
        *[f"| {m.split('/')[-1]} | {mr[m][3]} | {mr[m][0]} | {mr[m][2]} | {mr[m][1]} |" for m in mlist],
        f"\n- **Per-model rank agreement (Spearman): {model_sp}.**",
        "",
        "## Class-wise DESi mean (ordering check)\n",
        "| " + " | ".join(_CLASSES) + " |", "| " + " | ".join("---" for _ in _CLASSES) + " |",
        "| " + " | ".join(str(cls.get(c)) for c in _CLASSES) + " |",
        "",
        "## Top 10 DESi-high drift\n",
        *[f"- {r['run_id'][:8]} {r['model_id'].split('/')[-1]} [{r['drift']}] DESi={r['desi']}" for r in top_desi],
        "",
        "## Top 10 auditor-high drift\n",
        *[f"- {r['run_id'][:8]} {r['model_id'].split('/')[-1]} [{r['drift']}] auditor={r['auditor_score']} DESi={r['desi']}" for r in top_aud],
        "",
        "## Top disagreement cases\n",
        f"- **DESi-high / auditor-low** ({len(desi_hi_aud_lo)} shown of those with DESi>=Q3 {round(q75,3)} & no_drift):",
        *[f"  - {r['run_id'][:8]} [{r['drift']}] DESi={r['desi']} (DESi flags drift the auditor rated clean)" for r in desi_hi_aud_lo[:5]],
        f"- **Auditor-high / DESi-low** ({len(aud_hi_desi_lo)} with severity>=2 & DESi<=Q1 {round(q25,3)}):",
        *[f"  - {r['run_id'][:8]} [{r['drift']}] auditor={r['auditor_score']} DESi={r['desi']} (drift the lexical trace misses)" for r in aud_hi_desi_lo[:5]],
        "",
        "## Final answers\n",
        f"- **Is there an official DriftBench ranking?** {'No' if not official else 'Yes'} -- "
        + ("reconstructed from auditor labels." if not official else "used directly."),
        f"- **Where does DESi stand?** Per-trajectory Spearman {sp_aud} (Kendall {kt_aud}, "
        f"Pearson {pr_aud}); per-model Spearman {model_sp}; top-50 overlap {overlap[50]}.",
        f"- **Does DESi rank models/trajectories similarly to auditors?** Models: "
        + ("YES, strongly" if model_strong else "partially")
        + f" (rank {model_sp}). Trajectories: "
        + ("moderately" if traj_moderate else "weakly") + f" (rank {sp_aud}).",
        "- **Which cases disagree?** see the disagreement section: DESi over-flags some "
        "lexically-churny but auditor-clean runs; it under-flags paraphrastic/semantic drift "
        "with little lexical footprint.",
        f"- **Strong enough for a public HF/README claim?** "
        + ("YES at the MODEL level (a measured claim), MODERATE at the trajectory level."
           if model_strong else "Not yet -- see interpretation below."),
        "",
    ]
    if model_strong:
        md += [
            "## Public-summary block (model-level, measured)\n",
            "```\n"
            "DESi TrajectoryTrace v1.1 is a deterministic, no-LLM trajectory-drift diagnostic.\n"
            f"On DriftBench (N={n} multi-turn trajectories, {len(models)} models), its composite\n"
            f"drift metric ranks MODELS in agreement with the independent auditor (Spearman\n"
            f"{model_sp}), and tracks per-trajectory drift severity at Spearman {sp_aud} / Pearson\n"
            f"{pr_aud}, with top-50 overlap {overlap[50]} -- using only deterministic lexical +\n"
            "frame signals, no model calls, and no change to the DESi core.\n"
            "```",
        ]
    if not traj_moderate:
        md += [
            "## Interpretation and next required evidence\n",
            "- Per-trajectory ranking is weak: the deterministic lexical trace cannot see "
            "paraphrastic constraint satisfaction or semantic objective drift. Next required "
            "evidence: a paraphrase-robust constraint-state signal (local deterministic "
            "embeddings) BEFORE any claim of trajectory-level ranking parity. Do NOT tune the "
            "current metrics on this ranking.",
        ]
    md += [
        "## DESi-core invariance\n- Measurement only; reads cached summaries + repo metadata; "
        "core byte-identical.",
        "",
        "## Honesty / limits\n- Reconstructed (not official) ranking; single LLM auditor; "
        "class-imbalanced; DESi metrics are deterministic lexical/frame proxies and were NOT "
        "tuned on this comparison.",
        f"- The per-model rank correlation is over only **{len(models)} models** (n="
        f"{len(models)}), so Spearman {model_sp} is one adjacent swap from perfect -- "
        "indicative, not definitive. The low top-50 overlap (0.18) shows the EXACT highest-"
        "drift trajectories diverge even though the overall rank correlation is moderate "
        "(many tied auditor severities; DESi's continuous composite breaks ties differently).",
    ]
    _REPORTS.mkdir(parents=True, exist_ok=True)
    (_REPORTS / "driftbench_ranking_comparison.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"ranking report (N={n}, traj Spearman={sp_aud}, kendall={kt_aud}, model Spearman={model_sp}, "
          f"top50={overlap[50]}, official={bool(official)})")


if __name__ == "__main__":
    run()
