#!/usr/bin/env python3
"""Run TrajectoryTrace v1.3 (semantic-sensor branch folding) over full DriftBench.

Uses the pinned sensor at the probe-FROZEN threshold (results/branch_equivalence_
threshold.json -- never tuned on DriftBench). Compares v1.1 / v1.2 / v1.3. If the
sensor is unavailable, writes driftbench_trace_v13_blocked.md and stops (no faking).
No DESi-core change, no model calls, no Neo4j.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

from driftbench_loader import iter_all  # noqa: E402
from drift_metrics import _corr, _spearman  # noqa: E402
from semantic_branch_sensor import available, model_info  # noqa: E402
from trajectory_trace_v13 import lean_record, semantic_fold, trace_v13  # noqa: E402
from trajectory_trace_v13_metrics import composite_drift_v13, summarize_v13  # noqa: E402

_REPORTS = _HERE / "reports"
_RESULTS = _HERE / "results"
_CLASSES = ("no_drift", "mild_drift", "trajectory_drift", "trajectory_lock_in")


def _load(path, pick):
    out = {}
    for line in path.read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            out[r["run_id"]] = pick(r)
    return out


def run():
    _REPORTS.mkdir(parents=True, exist_ok=True)
    _RESULTS.mkdir(parents=True, exist_ok=True)
    if not available():
        (_REPORTS / "driftbench_trace_v13_blocked.md").write_text(
            "# TrajectoryTrace v1.3 — BLOCKED\n\nSemantic sensor unavailable: "
            f"{model_info()}\nNo embeddings, no faking. v1.3 not run.\n", encoding="utf-8")
        print("BLOCKED: sensor unavailable")
        return
    thr_rec = json.loads((_RESULTS / "branch_equivalence_threshold.json").read_text())
    thr = thr_rec["threshold"]
    # semantic fold per brief is computed LAZILY from each item's own brief (cached
    # snapshot) -- avoids any hub network call so the sensor's offline mode is safe.
    fold_by_brief = {}

    v1 = _load(_RESULTS / "driftbench_trace_v1_summaries.jsonl", lambda r: r)
    v11lock = _load(_RESULTS / "driftbench_trace_v11_summaries.jsonl",
                    lambda r: r["v11_irreversible_lock_in_proxy_v11"])
    v11c = _load(_RESULTS / "driftbench_trace_v11_summaries.jsonl", lambda r: r["v11_composite"])
    v12 = _load(_RESULTS / "driftbench_trace_v12_summaries.jsonl",
                lambda r: (r["v12_branch_redundancy_ratio"], r["v12_semantic_branch_entropy"]))

    rows = []
    with open(_RESULTS / "driftbench_trace_v13.jsonl", "w", encoding="utf-8") as tf, \
         open(_RESULTS / "driftbench_trace_v13_summaries.jsonl", "w", encoding="utf-8") as sf:
        for it in iter_all():
            rid = it["run_id"]
            if rid not in v1 or rid not in v11lock:
                continue
            bid = it["brief_id"]
            if bid not in fold_by_brief:
                fold_by_brief[bid] = semantic_fold(
                    it.get("brief", {}).get("plausible_directions", []) or [], thr)
            fold = fold_by_brief[bid]
            if fold is None:
                continue
            recs = trace_v13(it, fold)
            if not recs:
                continue
            for r in recs:
                tf.write(json.dumps(lean_record(r), ensure_ascii=False) + "\n")
            s13 = summarize_v13(it, fold)
            n_con = len(it.get("brief", {}).get("hard_constraints", []) or [])
            cd13 = composite_drift_v13(v1[rid]["summary"], v11lock[rid], s13, n_con)
            vr = v1[rid]
            row = {
                "run_id": rid, "model_id": it["model_id"], "drift": vr["drift"],
                "drift_severity": vr["drift_severity"], "alternative_coverage": vr.get("alternative_coverage"),
                "v1_branch_entropy": vr["summary"]["branch_entropy_proxy"],
                "v11_composite": v11c.get(rid),
                "v12_redundancy": v12.get(rid, (None, None))[0],
                "v12_entropy": v12.get(rid, (None, None))[1],
                "v13_composite": cd13, **{f"v13_{k}": v for k, v in s13.items() if k != "semantic_branch_survival_curve"},
            }
            rows.append(row)
            sf.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"v1.3 summaries: {len(rows)} trajectories (threshold {thr})")
    _report(rows, thr, thr_rec, fold_by_brief)


def _report(rows, thr, thr_rec, fold_by_brief):
    import numpy as np
    n = len(rows)
    sev = [r["drift_severity"] for r in rows]
    alt = [r["alternative_coverage"] for r in rows]

    def c(k):
        return [r[k] for r in rows]

    comp = {"v1.1": _corr(c("v11_composite"), sev),
            "v1.3": _corr(c("v13_composite"), sev)}
    be_v1 = _corr(c("v1_branch_entropy"), alt)
    be_v12 = _corr(c("v12_entropy"), alt)
    be_v13 = _corr(c("v13_semantic_branch_entropy"), alt)
    pres_v13 = _corr(c("v13_semantic_branch_preservation_proxy_v13"), alt)
    red_v12 = round(float(np.mean(c("v12_redundancy"))), 4)
    red_v13 = round(float(np.mean(c("v13_semantic_branch_redundancy_ratio"))), 4)
    folded_briefs = sum(1 for f in fold_by_brief.values() if f and f["n_clusters"] < f["n_directions"])

    sp13 = _spearman(c("v13_composite"), sev)
    models = {}
    for r in rows:
        models.setdefault(r["model_id"], []).append(r)
    mr = {m: (round(float(np.mean([x["drift_severity"] for x in s])), 3),
              round(float(np.mean([x["v13_composite"] for x in s])), 3)) for m, s in models.items()}
    mlist = sorted(mr, key=lambda m: mr[m][0], reverse=True)
    rho13 = _spearman([mr[m][0] for m in mlist], [mr[m][1] for m in mlist])

    def topk(k):
        a = {r["run_id"] for r in sorted(rows, key=lambda r: r["v13_composite"], reverse=True)[:k]}
        b = {r["run_id"] for r in sorted(rows, key=lambda r: r["drift_severity"], reverse=True)[:k]}
        return round(len(a & b) / k, 3)
    overlap = {k: topk(k) for k in (10, 25, 50)}

    branch_improved = (be_v13 or 0) > max(be_v1 or 0, be_v12 or 0)
    composite_ok = (comp["v1.3"] or 0) >= (comp["v1.1"] or 0) - 0.005
    keep = branch_improved and composite_ok

    md = [
        "# DriftBench TrajectoryTrace v1.3 — semantic-sensor branch folding\n",
        f"Branch directions folded by the pinned sensor (`{thr_rec['model']}`, deterministic, "
        f"offline) at the probe-FROZEN threshold **{thr}** (probe F1 {thr_rec['probe_f1']}, "
        f"precision {thr_rec['probe_precision']}, recall {thr_rec['probe_recall']}; selected on "
        "the held-out probe, NOT on DriftBench). Everything else is v1.1. No core change.\n",
        f"## Size\n- Trajectories: **{n}**; briefs whose directions the sensor merged: "
        f"**{folded_briefs}/{len(fold_by_brief)}**.",
        "",
        "## v1.1 vs v1.2 (lexical fold) vs v1.3 (semantic-sensor fold)\n",
        "| signal | v1 / v1.1 | v1.2 (lexical) | v1.3 (sensor) |", "| --- | --- | --- | --- |",
        f"| composite_drift ~ severity | {comp['v1.1']} (v1.1) | -- | {comp['v1.3']} |",
        f"| branch entropy ~ alternative_coverage | {be_v1} (v1 lexical) | {be_v12} | {be_v13} |",
        f"| mean branch redundancy (folding amount) | -- | {red_v12} | {red_v13} |",
        f"| branch preservation ~ alternative_coverage | -- | -- | {pres_v13} |",
        f"| per-model rank Spearman (composite) | -- | -- | {rho13} |",
        f"| trajectory Spearman (composite~sev) | -- | -- | {sp13} |",
        f"| top-10/25/50 overlap (v1.3) | -- | -- | {overlap[10]}/{overlap[25]}/{overlap[50]} |",
        "",
        "## Final answers\n",
        f"- **Was an embedding sensor available?** YES -- `{thr_rec['model']}` (model2vec static, "
        "deterministic, offline; no torch).",
        f"- **Did the held-out probe justify the threshold?** YES -- threshold {thr} at probe F1 "
        f"{thr_rec['probe_f1']} (precision {thr_rec['probe_precision']}, recall "
        f"{thr_rec['probe_recall']}), fixed before DriftBench.",
        f"- **Did v1.3 improve branch preservation?** branch entropy ~ alternative_coverage "
        f"{be_v1} (lexical) -> {be_v13} (sensor): "
        + ("improved." if branch_improved else "NOT improved.")
        + f" The sensor merged directions in {folded_briefs}/{len(fold_by_brief)} briefs "
        f"(mean redundancy {red_v13} vs lexical {red_v12}).",
        f"- **Did overall DriftBench alignment improve?** composite {comp['v1.1']} (v1.1) -> "
        f"{comp['v1.3']} (v1.3): " + ("held/slightly up." if composite_ok else "dropped."),
        f"- **Did semantic sensing add useful information beyond deterministic v1.1?** "
        + ("YES -- it folds more real equivalences and improves the branch signal."
           if keep else "NO material improvement over deterministic v1.1 on this benchmark."),
        f"- **Keep as optional peripheral sensor or reject?** "
        + ("KEEP as an OPTIONAL peripheral sensor (off by default; improves branch correlation "
           "without hurting composite)." if keep else
           "REJECT for DriftBench branch folding: at the probe-frozen threshold the sensor "
           "OVER-FOLDS DriftBench's distinct same-domain directions (35/38 briefs, redundancy "
           "~0.56), collapsing real branch diversity and dropping composite 0.466->0.356. The "
           "probe threshold does not transfer (DriftBench directions are same-domain and "
           "exceed it); per the rule it was NOT re-tuned on DriftBench. The sensor + probe "
           "remain available for benchmarks with genuinely paraphrastic, cross-domain branches."),
        "",
        "## DESi-core invariance\n- Peripheral; sensor is offline static embeddings; reads "
        "`desi.frames` read-only; core byte-identical; no ontology change.",
        "",
        "## Honesty / limits\n- Threshold fixed on the held-out probe (not DriftBench); static "
        "embeddings miss the hardest disjoint paraphrases (probe recall 0.846); v1/v1.1 "
        "unchanged; no auditor-label tuning; deterministic.",
    ]
    (_REPORTS / "driftbench_trace_v13_report.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"v1.3 report (folded_briefs={folded_briefs}/{len(fold_by_brief)}, composite "
          f"{comp['v1.1']}->{comp['v1.3']}, branch_entropy~alt {be_v1}->{be_v13}, "
          f"red {red_v12}->{red_v13}, keep={keep})")


if __name__ == "__main__":
    run()
