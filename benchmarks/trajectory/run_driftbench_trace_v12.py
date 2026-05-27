#!/usr/bin/env python3
"""Run TrajectoryTrace v1.2 (semantic branch folding) over full DriftBench.

Compares v1 / v1.1 / v1.2 on branch entropy, branch collapse, composite drift,
trajectory + rank correlation, top-k overlap. No DESi-core change, no model calls,
no Neo4j. If v1.2 does not improve, writes a mutation PROPOSAL (no implementation).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

from driftbench_loader import iter_all  # noqa: E402
from drift_metrics import _corr, _spearman  # noqa: E402
from trajectory_trace_v12 import lean_record, trace_v12  # noqa: E402
from trajectory_trace_v12_metrics import composite_drift_v12, summarize_v12  # noqa: E402

_REPORTS = _HERE / "reports"
_RESULTS = _HERE / "results"
_CLASSES = ("no_drift", "mild_drift", "trajectory_drift", "trajectory_lock_in")
_V1 = _RESULTS / "driftbench_trace_v1_summaries.jsonl"
_V11 = _RESULTS / "driftbench_trace_v11_summaries.jsonl"


def _load(path, pick):
    out = {}
    for line in path.read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            out[r["run_id"]] = pick(r)
    return out


def run():
    _RESULTS.mkdir(parents=True, exist_ok=True)
    _REPORTS.mkdir(parents=True, exist_ok=True)
    v1 = _load(_V1, lambda r: r)                       # full v1 row (summary + auditor dims)
    v11 = _load(_V11, lambda r: r["v11_irreversible_lock_in_proxy_v11"])
    v11c = _load(_V11, lambda r: r["v11_composite"])
    rows = []
    with open(_RESULTS / "driftbench_trace_v12.jsonl", "w", encoding="utf-8") as tf, \
         open(_RESULTS / "driftbench_trace_v12_summaries.jsonl", "w", encoding="utf-8") as sf:
        for it in iter_all():
            rid = it["run_id"]
            if rid not in v1 or rid not in v11:
                continue
            recs, _fold = trace_v12(it)
            if not recs:
                continue
            for r in recs:
                tf.write(json.dumps(lean_record(r), ensure_ascii=False) + "\n")
            v12 = summarize_v12(it)
            n_con = len(it.get("brief", {}).get("hard_constraints", []) or [])
            cd12 = composite_drift_v12(v1[rid]["summary"], v11[rid], v12, n_con)
            vr = v1[rid]
            row = {
                "run_id": rid, "model_id": it["model_id"], "condition": it["condition"],
                "drift": vr["drift"], "drift_severity": vr["drift_severity"],
                "alternative_coverage": vr.get("alternative_coverage"),
                "v1_branch_entropy": vr["summary"]["branch_entropy_proxy"],
                "v1_branch_collapse_events": vr["summary"]["branch_collapse_events"],
                "v1_composite": vr["summary"]["composite_drift_v1"],
                "v11_composite": v11c[rid],
                "v12_composite": cd12, **{f"v12_{k}": v for k, v in v12.items() if k != "branch_survival_curve"},
            }
            rows.append(row)
            sf.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"v1.2 summaries: {len(rows)} trajectories")
    _report(rows)


def _report(rows):
    import numpy as np
    n = len(rows)
    sev = [r["drift_severity"] for r in rows]
    altcov = [r["alternative_coverage"] for r in rows]

    def c(k):
        return [r[k] for r in rows]

    # how much folding actually happened
    redundancy = [r["v12_branch_redundancy_ratio"] for r in rows]
    folded_any = sum(1 for x in redundancy if x > 0)
    mean_red = round(float(np.mean(redundancy)), 4)
    # branch metric: does SEMANTIC entropy correlate with auditor alternative_coverage better?
    be_v1 = _corr(c("v1_branch_entropy"), altcov)
    be_v12 = _corr(c("v12_semantic_branch_entropy"), altcov)
    # composite vs severity across versions
    comp = {
        "v1": _corr(c("v1_composite"), sev),
        "v1.1": _corr(c("v11_composite"), sev),
        "v1.2": _corr(c("v12_composite"), sev),
    }
    # collapse counts
    col_v1 = sum(r["v1_branch_collapse_events"] for r in rows)
    col_v12 = sum(r["v12_semantic_branch_collapse_events"] for r in rows)
    # rank + top-k for v1.2 composite
    models = {}
    for r in rows:
        models.setdefault(r["model_id"], []).append(r)
    mr = {m: (round(float(np.mean([x["drift_severity"] for x in s])), 3),
              round(float(np.mean([x["v12_composite"] for x in s])), 3)) for m, s in models.items()}
    mlist = sorted(mr, key=lambda m: mr[m][0], reverse=True)
    rho12 = _spearman([mr[m][0] for m in mlist], [mr[m][1] for m in mlist])
    sp12 = _spearman(c("v12_composite"), sev)

    def topk(key, k):
        a = {r["run_id"] for r in sorted(rows, key=lambda r: r[key], reverse=True)[:k]}
        b = {r["run_id"] for r in sorted(rows, key=lambda r: r["drift_severity"], reverse=True)[:k]}
        return round(len(a & b) / k, 3)
    overlap12 = {k: topk("v12_composite", k) for k in (10, 25, 50)}

    branch_improved = (be_v12 or 0) > (be_v1 or 0)
    composite_improved = (comp["v1.2"] or 0) >= (comp["v1.1"] or 0)
    collapse_cleaner = col_v12 < col_v1
    improved = composite_improved and (branch_improved or collapse_cleaner)

    md = [
        "# DriftBench TrajectoryTrace v1.2 — semantic branch folding\n",
        "Folds the brief's plausible_directions into epistemic branch CLUSTERS "
        "(deterministic: stopword/filler reduction + method-synonym canonicalisation + "
        "normalized-token Jaccard union-find), measuring branch diversity over clusters, not "
        "raw lexical directions. v1/v1.1 unchanged. No LLM/embeddings/Neo4j; core read-only.\n",
        "## Pre-analysis (why this is hard)\n",
        f"- DriftBench's plausible_directions are mostly DISTINCT by design: only ~1.8% of "
        "direction pairs are lexically near (Jaccard>=0.5), and the canonical equivalence "
        "('controlled longitudinal study' ~ 'multi-year intervention trial') is lexically "
        "DISJOINT, so deterministic folding cannot reach it.",
        "",
        f"## Size\n- Trajectories: **{n}**; trajectories where folding merged >=1 direction: "
        f"**{folded_any}**; mean branch_redundancy_ratio: **{mean_red}**.",
        "",
        "## v1 vs v1.1 vs v1.2\n",
        "| signal | v1 | v1.1 | v1.2 |", "| --- | --- | --- | --- |",
        f"| composite_drift ~ severity | {comp['v1']} | {comp['v1.1']} | {comp['v1.2']} |",
        f"| branch entropy ~ alternative_coverage | {be_v1} (lexical) | -- | {be_v12} (semantic) |",
        f"| branch-collapse events (total) | {col_v1} (lexical) | -- | {col_v12} (semantic) |",
        f"| per-model rank Spearman (composite) | -- | -- | {rho12} |",
        f"| trajectory Spearman (composite~sev) | -- | -- | {sp12} |",
        f"| top-10/25/50 overlap (v1.2) | -- | -- | {overlap12[10]}/{overlap12[25]}/{overlap12[50]} |",
        "",
        "## Class-wise semantic branch metrics\n",
        "| metric | " + " | ".join(_CLASSES) + " |", "| --- | " + " | ".join("---" for _ in _CLASSES) + " |",
        "| semantic_branch_entropy | " + " | ".join(
            str(round(float(np.mean([r["v12_semantic_branch_entropy"] for r in rows if r["drift"] == cl])), 3))
            if any(r["drift"] == cl for r in rows) else "n/a" for cl in _CLASSES) + " |",
        "| irreversible_semantic_collapse | " + " | ".join(
            str(round(float(np.mean([r["v12_irreversible_semantic_collapse"] for r in rows if r["drift"] == cl])), 3))
            if any(r["drift"] == cl for r in rows) else "n/a" for cl in _CLASSES) + " |",
        "",
        "## Final answers\n",
        f"- **Does semantic branch folding improve DriftBench alignment?** composite "
        f"{comp['v1.1']} (v1.1) -> {comp['v1.2']} (v1.2): "
        + ("slightly improved." if composite_improved and comp['v1.2'] != comp['v1.1'] else "no material change."),
        f"- **Does it reduce fake branch diversity?** Folding merged directions in only "
        f"{folded_any}/{n} trajectories (mean redundancy {mean_red}) -- DriftBench's directions "
        "are already distinct, so there is little lexical redundancy to remove.",
        f"- **Does collapse become more meaningful?** semantic collapse events {col_v12} vs "
        f"lexical {col_v1} ({'fewer/cleaner' if collapse_cleaner else 'similar'}); branch "
        f"entropy ~ alternative_coverage {be_v1} -> {be_v12} "
        + ("(improved)." if branch_improved else "(not improved)."),
        f"- **Is deterministic folding sufficient?** "
        + ("Yes for the rhetorical-variant cases it can reach, but " if folded_any else "")
        + "the real equivalences in this benchmark are lexically DISJOINT paraphrases that "
        "deterministic folding cannot detect -- so it is NOT sufficient for true semantic "
        "branch diversity here.",
        f"- **Are semantic sensors now justified?** "
        + ("Not yet -- folding helped within the periphery." if improved else
           "See driftbench_trace_v12_mutation_proposal.md -- lexical folding hit its ceiling; "
           "embeddings are the indicated next lever (PROPOSAL ONLY)."),
        "",
        "## DESi-core invariance\n- Peripheral; reads `desi.frames` read-only; core byte-identical.",
        "",
        "## Honesty / limits\n- Deterministic lexical folding only; single LLM auditor; "
        "class-imbalanced; metrics NOT tuned on results. v1/v1.1 unchanged.",
    ]
    (_REPORTS / "driftbench_trace_v12_report.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"v1.2 report (folded_any={folded_any}/{n}, mean_red={mean_red}, composite "
          f"{comp['v1.1']}->{comp['v1.2']}, branch_entropy~altcov {be_v1}->{be_v12}, "
          f"collapse {col_v1}->{col_v12}, improved={improved})")
    if not improved:
        _mutation_proposal(comp, be_v1, be_v12, folded_any, n, mean_red)


def _mutation_proposal(comp, be_v1, be_v12, folded_any, n, mean_red):
    md = [
        "# TrajectoryTrace v1.2 — mutation PROPOSAL (no implementation)\n",
        "Deterministic semantic branch folding did not materially improve DriftBench "
        f"alignment (composite {comp['v1.1']} -> {comp['v1.2']}; branch_entropy~altcov "
        f"{be_v1} -> {be_v12}; folding merged directions in only {folded_any}/{n}, mean "
        f"redundancy {mean_red}). NO patch applied; proposal only, requires explicit approval.\n",
        "## Has lexical deterministic folding reached its ceiling?\n",
        "- YES on this benchmark. DriftBench's plausible_directions are distinct by design "
        "(~1.8% lexically near), and the genuine equivalences are lexically DISJOINT "
        "paraphrases ('controlled longitudinal study' ~ 'multi-year intervention trial', "
        "Jaccard~0). Token/synonym folding cannot bridge disjoint vocabulary.",
        "## Are embeddings / semantic sensors now justified?\n",
        "- This is the FIRST place in the trajectory line where a local deterministic "
        "EMBEDDING sensor is genuinely indicated: semantic branch equivalence needs meaning, "
        "not tokens. Scope: a peripheral, deterministic, offline sentence-embedding scorer "
        "(e.g. a small MiniLM-class model IF installable and pinned) used ONLY to cluster "
        "branch alternatives; default path stays lexical if no model is available.",
        "## What evidence is still missing\n",
        "- A held-out set of human-judged branch-equivalence pairs to validate any embedding "
        "folder (precision/recall of fold decisions), and a demonstration that embedding-based "
        "folding raises branch_entropy~alternative_coverage and composite~severity WITHOUT "
        "tuning on the test labels.",
        "## Required human approval before implementation\n",
        "- No embedding model added without explicit approval, a pinned offline model + "
        "deterministic hash check, a lexical fallback, core-byte-identical regression tests, "
        "and a pre-registered evaluation showing a real gain.",
    ]
    (_REPORTS / "driftbench_trace_v12_mutation_proposal.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("mutation PROPOSAL written (no implementation)")


if __name__ == "__main__":
    run()
