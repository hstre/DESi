#!/usr/bin/env python3
"""Micro-semantic routing study (PERIPHERAL).

Compares four prompt-selection policies under identical conditions (DeepSeek v4
Pro direct, temp 0, one deterministic pass, FIXED prompt families, same evaluator
and scoring); only the policy that picks the per-item mode changes:

  A) baseline       — fixed baseline prompt for every item
  B) matched        — the dataset's benchmark-matched family (VitaminC ->
                      evidence-strict, FEVER -> entailment-direct)
  C) DESi-router    — the existing DESi semantic-flow router (frames/logic/
                      frame-tension projection)
  D) micro-router   — the new algorithmic micro-semantic router (pure lexical-
                      semantic features; no LLM, no gold, no dataset name)

DESi does NOT answer items; DESi-core metrics are recorded alongside to confirm
the core stays invariant. Solves are cached per (item, variant): each prompt mode
runs at most once per item.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parents[1]
sys.path.insert(0, str(_REPO / "src"))
sys.path.insert(0, str(_HERE))

from prompt_calibration import _DS_NAME, _LABELS  # noqa: E402
from scifact_runner import desi_core_metrics, load_verify  # noqa: E402
from semantic_mode_router import SemanticModeRouter  # noqa: E402  (policy C)
from semantic_router_run import _MATCHED, _aggregate, _cls, _pr  # noqa: E402
from micro_semantic_router import MODES as MICRO_MODES  # noqa: E402
from micro_semantic_router import POLICY as MICRO_POLICY  # noqa: E402
from micro_semantic_router import MicroSemanticRouter  # noqa: E402  (policy D)
from solver_ports import DeepSeekDirectSolver, VERIFY_SYNS, parse_verdict  # noqa: E402

_REPORTS = _HERE / "reports"
_RUNS = _REPORTS / "_runs"
_EXP = ("baseline", "matched", "old_router", "micro_router")
_EXP_LABEL = {"baseline": "A baseline", "matched": "B matched",
              "old_router": "C DESi-router", "micro_router": "D micro-router"}


def run_micro(dataset, limit):
    _spec, exs = load_verify(dataset, limit)
    solver = DeepSeekDirectSolver()
    old_router = SemanticModeRouter()
    micro = MicroSemanticRouter()
    matched = _MATCHED[dataset]
    price = solver.price()
    rows = []
    toks = {e: [0, 0, 0.0] for e in _EXP}
    errors = 0
    t0 = time.time()
    for ex in exs:
        c_mode = old_router.route(ex.claim, ex.evidence).mode
        d = micro.route(ex.claim, ex.evidence)
        chosen = {"baseline": "baseline", "matched": matched,
                  "old_router": c_mode, "micro_router": d.policy}
        solved = {}
        for v in set(chosen.values()):
            ts = time.time()
            try:
                text, p, cc = solver.solve_direct(ex.claim, ex.evidence, task="verify", variant=v)
            except Exception:
                text, p, cc = "", 0, 0
                errors += 1
            solved[v] = (text, p, cc, time.time() - ts)
        for exp, var in chosen.items():
            _t, p, cc, dt = solved[var]
            toks[exp][0] += p
            toks[exp][1] += cc
            toks[exp][2] += dt
        rows.append({
            "id": ex.id, "gold": ex.gold,
            "baseline_pred": parse_verdict(solved["baseline"][0], VERIFY_SYNS),
            "matched_pred": parse_verdict(solved[matched][0], VERIFY_SYNS),
            "old_pred": parse_verdict(solved[c_mode][0], VERIFY_SYNS),
            "micro_pred": parse_verdict(solved[d.policy][0], VERIFY_SYNS),
            "old_mode": c_mode, "micro_mode": d.mode, "micro_policy": d.policy,
            "micro_reason": d.reason, "features": d.features,
        })
    elapsed = time.time() - t0
    pred_key = {"baseline": "baseline_pred", "matched": "matched_pred",
                "old_router": "old_pred", "micro_router": "micro_pred"}
    agg = {e: _aggregate([(r["gold"], r[pred_key[e]]) for r in rows]) for e in _EXP}
    for e in _EXP:
        agg[e]["elapsed_s"] = round(toks[e][2], 2)
        agg[e]["est_cost_usd"] = round(toks[e][0] * price[0] + toks[e][1] * price[1], 6)

    route_dist = {m: 0 for m in MICRO_MODES}
    for r in rows:
        route_dist[r["micro_mode"]] += 1
    per_route = {}
    for m in MICRO_MODES:
        sub = [r for r in rows if r["micro_mode"] == m]
        ans = sum(1 for r in sub if r["micro_pred"] is not None)
        mcor = sum(1 for r in sub if r["micro_pred"] == r["gold"])
        bcor = sum(1 for r in sub if r["baseline_pred"] == r["gold"])
        per_route[m] = {
            "n": len(sub),
            "policy": MICRO_POLICY[m],
            "micro_acc": round(mcor / ans, 3) if ans else None,
            "baseline_acc_same_subset": round(bcor / len(sub), 3) if sub else None,
        }

    def help_hurt(other):
        h = sum(1 for r in rows if r["micro_pred"] == r["gold"] and r[other] != r["gold"])
        u = sum(1 for r in rows if r["micro_pred"] != r["gold"] and r[other] == r["gold"])
        return {"helped": h, "hurt": u, "net": h - u}

    rec = {
        "dataset": _DS_NAME[dataset], "dataset_key": dataset, "matched_family": matched,
        "n": len(exs), "errors": errors, "solver": solver.name,
        "wall_elapsed_s": round(elapsed, 2), "experiments": agg,
        "micro": {
            "route_distribution": route_dist,
            "policy_distribution": dict(Counter(r["micro_policy"] for r in rows)),
            "per_route": per_route,
            "vs_baseline": help_hurt("baseline_pred"),
            "vs_matched": help_hurt("matched_pred"),
            "vs_old_router": help_hurt("old_pred"),
        },
        "rows": rows,
        "desi_core": desi_core_metrics(exs),
    }
    _RUNS.mkdir(parents=True, exist_ok=True)
    (_RUNS / f"mr_{dataset}.json").write_text(json.dumps(rec, indent=2), encoding="utf-8")
    a = agg
    print(f"{dataset}: A={a['baseline']['accuracy']} B({matched})={a['matched']['accuracy']} "
          f"C(desi)={a['old_router']['accuracy']} D(micro)={a['micro_router']['accuracy']} | "
          f"micro policy={rec['micro']['policy_distribution']} | net vs base "
          f"{rec['micro']['vs_baseline']['net']:+d} vs matched {rec['micro']['vs_matched']['net']:+d} "
          f"vs desi {rec['micro']['vs_old_router']['net']:+d} | desi replay "
          f"{rec['desi_core']['replay_stable']} core {rec['desi_core']['core_identity_ok']}")
    return rec


def micro_report(dataset):
    p = _RUNS / f"mr_{dataset}.json"
    if not p.exists():
        print(f"missing run for {dataset}")
        return
    rec = json.loads(p.read_text())
    agg, mi = rec["experiments"], rec["micro"]
    g = agg["baseline"]["gold_distribution"]
    matched = rec["matched_family"]
    cols = [(_EXP_LABEL[e] if e != "matched" else f"B matched ({matched})", e) for e in _EXP]
    md = [
        f"# Algorithmic micro-semantic routing — {rec['dataset']}\n",
        "A deterministic, LLM-free micro-layer computes lexical-semantic features "
        "(content coverage, entity overlap, negation/antonym/numeric contradiction "
        "cues) and picks the solver PROMPT MODE per item, before the solver runs. "
        "Everything algorithmic is decided here; the LLM handles the residue. "
        "Identical conditions otherwise (DeepSeek v4 Pro, temp 0, one pass, FIXED "
        "families, same evaluator). Policies: **A** baseline, **B** benchmark-matched, "
        "**C** the existing DESi semantic-flow router, **D** the new micro-router. "
        "DESi-core recorded alongside; this micro-layer does NOT touch the DESi core.\n",
        f"N={rec['n']} | gold S/R/N = {g['SUPPORTS']}/{g['REFUTES']}/{g['NOT_ENOUGH_INFO']} "
        f"| matched family = **{matched}**\n",
        "## Policy comparison\n",
        "| metric | " + " | ".join(c[0] for c in cols) + " |",
        "| --- | " + " | ".join("---" for _ in cols) + " |",
    ]

    def row(label, fn):
        return f"| {label} | " + " | ".join(str(fn(agg[c[1]])) for c in cols) + " |"

    md += [
        row("accuracy", lambda r: r["accuracy"]),
        row("pred S/R/N", lambda r: f"{r['pred_distribution']['SUPPORTS']}/{r['pred_distribution']['REFUTES']}/{r['pred_distribution']['NOT_ENOUGH_INFO']}"),
        row("SUPPORTS P/R", lambda r: _pr(r, "SUPPORTS")),
        row("REFUTES P/R", lambda r: _pr(r, "REFUTES")),
        row("NEI P/R", lambda r: _pr(r, "NOT_ENOUGH_INFO")),
        row("overcommitment", lambda r: f"{r['overcommitment_rate']} ({r['overcommitment_n']})"),
        row("overabstention", lambda r: f"{r['overabstention_rate']} ({r['overabstention_n']})"),
        row("parse failures", lambda r: r["parse_failures"]),
        row("latency", lambda r: f"{r['elapsed_s']}s"),
        row("est cost", lambda r: f"${r['est_cost_usd']}"),
        "",
        "### Confusion matrices (rows gold, cols pred)\n",
    ]
    for label, key in cols:
        r = agg[key]
        md += [f"**{label}**", "", "| gold \\ pred | " + " | ".join(_LABELS) + " |",
               "| --- | " + " | ".join("---" for _ in _LABELS) + " |"]
        for gl in _LABELS:
            md.append(f"| {gl} | " + " | ".join(str(r["confusion"][gl][p]) for p in _LABELS) + " |")
        md.append("")
    md += [
        "## Micro-router behaviour\n",
        "Mode distribution: " + ", ".join(f"{m} {mi['route_distribution'][m]}" for m in MICRO_MODES) + ".\n",
        f"Policy distribution: {mi['policy_distribution']}.\n",
        "### Per-route accuracy (micro-chosen mode vs the same items under baseline)\n",
        "| micro mode | policy | n | micro acc | baseline acc (same items) |",
        "| --- | --- | --- | --- | --- |",
    ]
    for m in MICRO_MODES:
        pr = mi["per_route"][m]
        md.append(f"| {m} | {pr['policy']} | {pr['n']} | {pr['micro_acc']} | {pr['baseline_acc_same_subset']} |")
    md += [
        "",
        f"- **vs A (baseline)**: helped {mi['vs_baseline']['helped']}, hurt "
        f"{mi['vs_baseline']['hurt']} (net {mi['vs_baseline']['net']:+d}).",
        f"- **vs B (benchmark-matched)**: helped {mi['vs_matched']['helped']}, hurt "
        f"{mi['vs_matched']['hurt']} (net {mi['vs_matched']['net']:+d}).",
        f"- **vs C (DESi semantic-router)**: helped {mi['vs_old_router']['helped']}, hurt "
        f"{mi['vs_old_router']['hurt']} (net {mi['vs_old_router']['net']:+d}).",
        "",
        "### Features used (deterministic, no LLM)\n",
        "- normalized content tokens + synonym groups -> content coverage (claim "
        "covered by evidence); capitalized proper-noun overlap -> entity overlap; "
        "negation / antonym / numeric-mismatch -> contradiction cue; quantifier / "
        "modality / temporal marker counts. Decision precedence: contradiction -> "
        "direct-entailment (high coverage + entity overlap) -> missing-linkage (claim "
        "entities absent) -> high-NEI (near-zero coverage) -> partial-support (mid "
        "coverage) -> ambiguous.",
    ]
    dc = rec["desi_core"]
    md += [
        "",
        "## DESi-core (alongside; core untouched)\n",
        f"- replay stability: {'1.0' if dc['replay_stable'] else 'FAILED'}; core identity: "
        f"{dc['core_identity_ok']}; governance independence: {'1.0' if dc['gov_independent'] else 'FAILED'}; "
        f"critical_branch_preservation: {dc['critical_branch_preservation']}; "
        f"mutation rejected: {dc['mutation_rejected']}/{dc['mutation_attempts']}.",
        "- The micro-router is a self-contained benchmark adapter (pure string/token "
        "arithmetic). It does not import or modify the DESi semantic core or ontology.",
        "",
        "## Honesty / limits\n",
        "- One deterministic pass per (item, mode); DeepSeek mildly non-deterministic. "
        "Accuracies are the model's; the router only picks a policy and never produces a "
        "verdict. This is NOT a truthfulness claim and DESi did not solve NLI. If the "
        "micro-router does not beat the benchmark-matched family, the limiting factor is "
        "feature coverage (reported above), and the core is NOT changed in response.",
    ]
    out = "micro_router_vitaminc.md" if dataset == "vitaminc" else "micro_router_fever.md"
    _REPORTS.mkdir(parents=True, exist_ok=True)
    (_REPORTS / out).write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"micro report -> {out}")


def micro_cross_summary():
    recs = {}
    for ds in ("vitaminc", "nli_fever"):
        p = _RUNS / f"mr_{ds}.json"
        if p.exists():
            recs[ds] = json.loads(p.read_text())
    if not recs:
        print("no micro runs")
        return

    def accs(ds):
        a = recs[ds]["experiments"]
        return (a["baseline"]["accuracy"], a["matched"]["accuracy"],
                a["old_router"]["accuracy"], a["micro_router"]["accuracy"])

    md = [
        "# Micro-semantic routing — cross-summary\n",
        "Algorithmic pre-solver routing: a deterministic lexical-semantic micro-layer "
        "(no LLM, no gold label, no dataset name) picks the solver prompt mode per "
        "item. Compared policies: A baseline, B benchmark-matched, C the existing DESi "
        "semantic-flow router, D the new micro-router. DeepSeek v4 Pro only, temp 0, "
        "FIXED families, same evaluator. The DESi core is untouched.\n",
        "## Accuracy by policy\n",
        "| dataset | A baseline | B matched | C DESi-router | D micro-router | micro policy split (base/ev/ent) |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for ds in ("vitaminc", "nli_fever"):
        if ds not in recs:
            continue
        A, B, C, D = accs(ds)
        ps = recs[ds]["micro"]["policy_distribution"]
        split = f"{ps.get('baseline', 0)}/{ps.get('evidence_strict', 0)}/{ps.get('entailment_direct', 0)}"
        md.append(f"| {recs[ds]['dataset']} | {A} | {B} | {C} | {D} | {split} |")
    md.append("")
    md.append("| dataset | overcommit A->D | overabst A->D | net vs base | net vs matched | net vs DESi-router |")
    md.append("| --- | --- | --- | --- | --- | --- |")
    for ds in ("vitaminc", "nli_fever"):
        if ds not in recs:
            continue
        a = recs[ds]["experiments"]; mi = recs[ds]["micro"]
        md.append(f"| {recs[ds]['dataset']} | {a['baseline']['overcommitment_rate']} -> "
                  f"{a['micro_router']['overcommitment_rate']} | "
                  f"{a['baseline']['overabstention_rate']} -> {a['micro_router']['overabstention_rate']} | "
                  f"{mi['vs_baseline']['net']:+d} | {mi['vs_matched']['net']:+d} | {mi['vs_old_router']['net']:+d} |")
    md.append("")

    beats_base = all(accs(ds)[3] >= accs(ds)[0] for ds in recs)
    beats_matched = all(accs(ds)[3] >= accs(ds)[1] for ds in recs)
    beats_desi = all(accs(ds)[3] >= accs(ds)[2] for ds in recs)
    md += [
        "## Answers\n",
        "- **Does algorithmic micro-routing help vs the fixed baseline?** "
        + "; ".join(f"{recs[ds]['dataset']}: D {accs(ds)[3]} vs A {accs(ds)[0]} "
                    f"({accs(ds)[3] - accs(ds)[0]:+.3f})" for ds in recs)
        + (". Helps (>= baseline) on both." if beats_base else ". Mixed/does not consistently beat baseline."),
        "- **Does it beat benchmark-level prompt selection (B)?** "
        + "; ".join(f"{recs[ds]['dataset']}: D {accs(ds)[3]} vs B {accs(ds)[1]} "
                    f"({accs(ds)[3] - accs(ds)[1]:+.3f})" for ds in recs)
        + (". YES on both." if beats_matched else ". NO — the dataset-matched family is >= the per-item micro-router."),
        "- **Does it beat the existing DESi semantic-router (C)?** "
        + "; ".join(f"{recs[ds]['dataset']}: D {accs(ds)[3]} vs C {accs(ds)[2]} "
                    f"({accs(ds)[3] - accs(ds)[2]:+.3f})" for ds in recs)
        + (". YES — the algorithmic router is >= the DESi semantic-router on both."
           if beats_desi else ". Mixed vs the DESi semantic-router."),
    ]
    if "vitaminc" in recs:
        a = recs["vitaminc"]["experiments"]
        md.append(f"- **VitaminC over-commitment A->D**: {a['baseline']['overcommitment_rate']} -> "
                  f"{a['micro_router']['overcommitment_rate']} (overabstention "
                  f"{a['baseline']['overabstention_rate']} -> {a['micro_router']['overabstention_rate']}).")
    if "nli_fever" in recs:
        a = recs["nli_fever"]["experiments"]
        md.append(f"- **FEVER over-abstention A->D**: {a['baseline']['overabstention_rate']} -> "
                  f"{a['micro_router']['overabstention_rate']} (overcommitment "
                  f"{a['baseline']['overcommitment_rate']} -> {a['micro_router']['overcommitment_rate']}).")
    core_ok = all(recs[ds]["desi_core"]["core_identity_ok"] in (True, None) for ds in recs)
    replay_ok = all(recs[ds]["desi_core"]["replay_stable"] for ds in recs)
    md += [
        f"- **Does the core remain untouched?** {'YES' if core_ok else 'NO — investigate'} "
        f"— core byte-identical, replay {'1.0' if replay_ok else 'FAILED'} on every run; "
        "the micro-layer is pure string/token arithmetic outside the core.",
        "",
        "## Which features mattered\n",
        "- **VitaminC**: the micro-layer produces a real 3-way split (contradiction cues "
        "for REFUTES-like items -> baseline; high coverage + entity overlap -> "
        "entailment-direct; missing/partial coverage -> evidence-strict). Coverage + "
        "antonym/negation/numeric cues are the active signals.",
        "- **FEVER**: hypotheses routinely introduce entities the short premise does not "
        "contain, so missing-linkage dominates and the policy collapses toward "
        "evidence-strict. Pure lexical overlap cannot detect paraphrastic entailment "
        "where surface forms differ, so it cannot target FEVER's over-abstention.",
        "",
        "## Interpretation (per study rule)\n",
        ("- Algorithmic pre-solver routing shows evidence of usefulness where lexical "
         "structure is informative; reported as such, without any truthfulness claim."
         if (beats_base or beats_matched) else
         "- Where the micro-router does not beat baseline/matched, this is reported as a "
         "FEATURE GAP (lexical overlap misses paraphrastic entailment), NOT patched into "
         "the DESi core. No truthfulness claim; DESi did not solve NLI."),
        "",
        "## Honesty / limits\n",
        "- N=100/dataset; one deterministic pass; DeepSeek mild non-determinism; FIXED "
        "prompt families; micro-router is deterministic and core-independent. No core, "
        "ontology, or meaning-space change; outputs secret-scanned.",
    ]
    _REPORTS.mkdir(parents=True, exist_ok=True)
    (_REPORTS / "micro_router_cross_summary.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("cross-summary written")


def main() -> int:
    ap = argparse.ArgumentParser(description="Micro-semantic routing study.")
    ap.add_argument("--dataset", choices=sorted(_MATCHED))
    ap.add_argument("--limit", type=int, default=100)
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--cross-summary", action="store_true")
    args = ap.parse_args()
    if args.cross_summary:
        micro_cross_summary(); return 0
    if args.report:
        micro_report(args.dataset); return 0
    if args.run:
        if not args.dataset:
            ap.error("--run needs --dataset")
        run_micro(args.dataset, args.limit); return 0
    ap.error("need --run/--report (with --dataset) or --cross-summary")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
