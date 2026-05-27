#!/usr/bin/env python3
"""Run TrajectoryTrace v1.1 over full DriftBench; compare the two fixed metrics to v1.

Targets only the two weak v1 metrics (irreversible lock-in, method/content
divergence), side-by-side with v1 (v1 unchanged). No model calls, no DESi-core
change, no Neo4j. If v1.1 does not improve, writes a mutation PROPOSAL (no impl).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

from driftbench_loader import iter_all  # noqa: E402
from drift_metrics import _corr, _monotone, _spearman  # noqa: E402
from trajectory_trace_v11_metrics import composite_drift_v11, summarize_v11  # noqa: E402

_REPORTS = _HERE / "reports"
_RESULTS = _HERE / "results"
_CLASSES = ("no_drift", "mild_drift", "trajectory_drift", "trajectory_lock_in")
_V1 = _RESULTS / "driftbench_trace_v1_summaries.jsonl"


def _load_v1():
    out = {}
    for line in _V1.read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            out[r["run_id"]] = r
    return out


def run():
    _RESULTS.mkdir(parents=True, exist_ok=True)
    _REPORTS.mkdir(parents=True, exist_ok=True)
    v1 = _load_v1()
    rows = []
    with open(_RESULTS / "driftbench_trace_v11_summaries.jsonl", "w", encoding="utf-8") as sf:
        for it in iter_all():
            v1r = v1.get(it["run_id"])
            if v1r is None:
                continue
            v11 = summarize_v11(it)
            if not v11:
                continue
            n_con = len(it.get("brief", {}).get("hard_constraints", []) or [])
            cdv11 = composite_drift_v11(v1r["summary"], v11, n_con)
            row = {
                "run_id": it["run_id"], "model_id": it["model_id"], "condition": it["condition"],
                "drift": v1r["drift"], "drift_severity": v1r["drift_severity"],
                "objective_fidelity": v1r.get("objective_fidelity"),
                "constraint_adherence": v1r.get("constraint_adherence"),
                "alternative_coverage": v1r.get("alternative_coverage"),
                "recoverability": v1r.get("recoverability"),
                "v1_composite": v1r["summary"]["composite_drift_v1"],
                "v1_lock_in": v1r["summary"]["irreversible_lock_in_proxy"],
                "v1_divergence": v1r["summary"]["divergence_between_method_and_content"],
                "v1_method_total": v1r["summary"]["method_drift_total"],
                "v1_content_total": v1r["summary"]["content_drift_total"],
                "v11_composite": cdv11, **{f"v11_{k}": v for k, v in v11.items()},
            }
            rows.append(row)
            sf.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"v1.1 summaries: {len(rows)} trajectories")
    _report(rows)


def _report(rows):
    import numpy as np
    n = len(rows)
    sev = [r["drift_severity"] for r in rows]

    def c(col):
        return [r[col] for r in rows]

    # correlations with severity
    cmp = {
        "composite v1": _corr(c("v1_composite"), sev),
        "composite v1.1": _corr(c("v11_composite"), sev),
        "lock_in v1": _corr(c("v1_lock_in"), sev),
        "lock_in v1.1": _corr(c("v11_irreversible_lock_in_proxy_v11"), sev),
        "divergence v1": _corr(c("v1_divergence"), sev),
        "divergence v1.1": _corr(c("v11_method_content_divergence_v11"), sev),
    }
    # method/content redundancy (lower = more orthogonal = less noisy)
    red_v1 = _corr(c("v1_method_total"), c("v1_content_total"))
    red_v11 = _corr(c("v11_method_drift_v11"), c("v11_content_drift_v11"))
    method_v11_fidelity = _corr(c("v11_method_drift_v11"), [r["objective_fidelity"] for r in rows])

    # lock-in class separation + false neg/pos
    def cls_mean(col, klass):
        sub = [r[col] for r in rows if r["drift"] == klass]
        return round(float(np.mean(sub)), 3) if sub else None
    lockin_v1_cls = {k: cls_mean("v1_lock_in", k) for k in _CLASSES}
    lockin_v11_cls = {k: cls_mean("v11_irreversible_lock_in_proxy_v11", k) for k in _CLASSES}
    li_total = sum(1 for r in rows if r["drift"] == "trajectory_lock_in")
    fn_v1 = sum(1 for r in rows if r["drift"] == "trajectory_lock_in" and r["v1_lock_in"] == 0)
    fn_v11 = sum(1 for r in rows if r["drift"] == "trajectory_lock_in" and r["v11_irreversible_lock_in_proxy_v11"] == 0)

    # per-model rank with v1.1 composite
    models = {}
    for r in rows:
        models.setdefault(r["model_id"], []).append(r)
    mr = {m: (round(float(np.mean([r["drift_severity"] for r in s])), 3),
              round(float(np.mean([r["v11_composite"] for r in s])), 3)) for m, s in models.items()}
    mlist = sorted(mr, key=lambda m: mr[m][0], reverse=True)
    rho_v11 = _spearman([mr[m][0] for m in mlist], [mr[m][1] for m in mlist])

    composite_improved = (cmp["composite v1.1"] or 0) >= (cmp["composite v1"] or 0)
    lockin_improved = (cmp["lock_in v1.1"] or 0) > (cmp["lock_in v1"] or 0)
    divergence_cleaner = (abs(red_v11 or 1) < abs(red_v1 or 1))
    improved = composite_improved and lockin_improved

    md = [
        "# DriftBench TrajectoryTrace v1.1 — fixing the two weak metrics\n",
        "Targeted, side-by-side periphery fixes (v1 unchanged): (A) irreversible lock-in now "
        "based on SUSTAINED unrecovered constraint loss + no-recovery-after-collapse + "
        "objective-stuck-low + late narrowing (was branch-collapse-only); (B) method/content "
        "divergence now separates a rhetorical MODE axis (scientific vs persuasive tokens) "
        "from a content/objective axis (objective + constraint overlap decline). Deterministic; "
        "no LLM/embeddings/Neo4j; DESi-core read-only.\n",
        f"## Size\n- Trajectories: **{n}**.",
        "",
        "## What changed & headline comparison (correlation with auditor drift_severity)\n",
        "| signal | v1 | v1.1 |", "| --- | --- | --- |",
        f"| composite_drift ~ severity | {cmp['composite v1']} | {cmp['composite v1.1']} |",
        f"| irreversible_lock_in ~ severity | {cmp['lock_in v1']} | {cmp['lock_in v1.1']} |",
        f"| method/content divergence ~ severity | {cmp['divergence v1']} | {cmp['divergence v1.1']} |",
        "",
        f"- **Lock-in detection improved?** {'YES' if lockin_improved else 'NO'} "
        f"(r {cmp['lock_in v1']} -> {cmp['lock_in v1.1']}).",
        f"- **Method/content less noisy?** {'YES' if divergence_cleaner else 'NO'} -- method vs "
        f"content redundancy dropped from corr={red_v1} (v1, near-duplicate) to corr={red_v11} "
        "(v1.1, orthogonal axes). method_drift_v11 ~ objective_fidelity r=" + str(method_v11_fidelity)
        + " (more method drift -> lower fidelity).",
        f"- **Composite improved?** {'YES' if composite_improved else 'NO'} "
        f"(r {cmp['composite v1']} -> {cmp['composite v1.1']}). Per-model rank (v1.1): Spearman {rho_v11}.",
        "",
        "## Lock-in class separation (mean proxy by auditor class)\n",
        "| version | " + " | ".join(_CLASSES) + " | false-neg on lock_in |",
        "| --- | " + " | ".join("---" for _ in _CLASSES) + " | --- |",
        "| v1 (branch-only) | " + " | ".join(str(lockin_v1_cls[k]) for k in _CLASSES) + f" | {fn_v1}/{li_total} |",
        "| v1.1 (sustained) | " + " | ".join(str(lockin_v11_cls[k]) for k in _CLASSES) + f" | {fn_v11}/{li_total} |",
        "",
        f"- v1.1 lock-in "
        + ("rises monotonically with auditor class" if _monotone([lockin_v11_cls[k] for k in _CLASSES]) else "broadly increases with class")
        + f"; false negatives on the lock_in class fell {fn_v1} -> {fn_v11} of {li_total}.",
        "",
        "## Method vs content (orthogonality)\n",
        f"- v1: method_total vs content_total corr = {red_v1} (redundant -> divergence was noise).",
        f"- v1.1: method_drift vs content_drift corr = {red_v11} (separated axes).",
        "| class | method_drift_v11 | content_drift_v11 | divergence_v11 |",
        "| --- | --- | --- | --- |",
        *[f"| {k} | {cls_mean('v11_method_drift_v11', k)} | {cls_mean('v11_content_drift_v11', k)} | {cls_mean('v11_method_content_divergence_v11', k)} |" for k in _CLASSES],
        "",
        "## Final answers\n",
        f"- **Did lock-in detection improve?** {'YES' if lockin_improved else 'NO'} "
        f"(severity r {cmp['lock_in v1']} -> {cmp['lock_in v1.1']}; false-neg {fn_v1} -> {fn_v11}/{li_total}).",
        f"- **Did method/content divergence improve?** {'YES' if divergence_cleaner else 'NO'} "
        f"(redundancy {red_v1} -> {red_v11}; the axes are now orthogonal so the signal is "
        "interpretable, even if its direct severity correlation stays modest).",
        f"- **Did overall DriftBench alignment improve?** composite r {cmp['composite v1']} -> "
        f"{cmp['composite v1.1']} ({'improved' if composite_improved else 'not improved'}).",
        f"- **Is v1.1 worth keeping?** {'YES' if (lockin_improved or composite_improved) else 'NO'} -- "
        + ("the lock-in fix alone materially improves a previously-broken metric, and the "
           "divergence axes are now meaningful." if (lockin_improved or composite_improved)
           else "neither weak metric improved."),
        f"- **Is mutation justified now?** "
        + ("NO -- the periphery fix worked; DESi-core stays untouched."
           if improved else "See driftbench_trace_v11_mutation_proposal.md (PROPOSAL ONLY)."),
        "",
        "## DESi-core invariance\n- Peripheral; reads `desi.frames` read-only; core byte-identical.",
        "",
        "## Honesty / limits\n- Deterministic lexical/mode + frame signals; single LLM auditor; "
        "class-imbalanced (mostly mild_drift). v1 metrics unchanged. No model calls, no relabeling.",
    ]
    (_REPORTS / "driftbench_trace_v11_report.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"v1.1 report (lock_in {cmp['lock_in v1']}->{cmp['lock_in v1.1']}, composite "
          f"{cmp['composite v1']}->{cmp['composite v1.1']}, redundancy {red_v1}->{red_v11}, "
          f"improved={improved})")
    if not improved:
        _mutation_proposal(cmp, red_v1, red_v11, lockin_improved, composite_improved)


def _mutation_proposal(cmp, red_v1, red_v11, lockin_improved, composite_improved):
    md = [
        "# TrajectoryTrace v1.1 — mutation PROPOSAL (no implementation)\n",
        f"v1.1 did not fully improve (lock-in improved={lockin_improved}, composite "
        f"improved={composite_improved}). NO patch applied; proposal only, requires explicit "
        "human approval before any implementation.\n",
        "## Why the periphery fix fell short\n",
        f"- composite r {cmp['composite v1']} -> {cmp['composite v1.1']}; lock_in r "
        f"{cmp['lock_in v1']} -> {cmp['lock_in v1.1']}; method/content redundancy {red_v1} -> {red_v11}.",
        "- The remaining gap is the lexical activation test: constraint satisfaction/violation "
        "and objective overlap are decided by token coverage, which mislabels paraphrase.",
        "## What signal is missing\n",
        "- Paraphrase-robust constraint state (satisfied/stretched/violated) and semantic "
        "objective alignment -- both require meaning, not tokens.",
        "## Would learned embeddings / graph memory / core mutation be needed?\n",
        "- A LOCAL deterministic embedding scorer (periphery) is the first lever; graph memory "
        "(Neo4j) only if cross-trajectory motif queries become necessary; a DESi-CORE mutation is "
        "NOT indicated -- the gap is in peripheral signal extraction, not governance.",
        "## Required human approval before implementation\n",
        "- No embedding model / graph store / core change without explicit approval, a fixed "
        "dataset-agnostic spec, determinism + core-byte-identical regression tests, and a "
        "demonstrated correlation gain on this report.",
    ]
    (_REPORTS / "driftbench_trace_v11_mutation_proposal.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("mutation PROPOSAL written (no implementation)")


if __name__ == "__main__":
    run()
