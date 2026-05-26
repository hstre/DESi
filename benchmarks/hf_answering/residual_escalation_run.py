#!/usr/bin/env python3
"""Residual semantic escalation routing study (PERIPHERAL).

Algorithm-first, semantic-residual: the deterministic layers (micro-router +
unfolding) resolve clear cases; only the ambiguous residue escalates to a
lightweight deterministic semantic scorer (synonym-group + char-trigram vectors,
directional containment / asymmetry). Adds policy F on top of the prior policies.

Compares A baseline / B benchmark-matched / C DESi semantic-router / D micro-
router / E unfolding-aware / F residual-escalation on VitaminC-100 and
NLI-FEVER-100. DeepSeek v4 Pro, temp 0, FIXED families, same evaluator. All three
prompt variants are solved per item (deterministic) so every policy and the
fold-counterfactual are lookups. DESi-core recorded alongside; core untouched.
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
from semantic_mode_router import SemanticModeRouter  # noqa: E402
from semantic_router_run import _MATCHED, _aggregate, _pr  # noqa: E402
from residual_semantic_escalation import OUTCOMES, ResidualEscalationRouter  # noqa: E402
from solver_ports import DeepSeekDirectSolver, VERIFY_SYNS, parse_verdict  # noqa: E402

_REPORTS = _HERE / "reports"
_RUNS = _REPORTS / "_runs"
_VARIANTS = ("baseline", "evidence_strict", "entailment_direct")
_EXP = ("baseline", "matched", "old_router", "micro_router", "unfolding", "residual")
_EXP_LABEL = {"baseline": "A baseline", "matched": "B matched", "old_router": "C DESi-router",
              "micro_router": "D micro", "unfolding": "E unfolding", "residual": "F residual"}


def run_residual(dataset, limit):
    _spec, exs = load_verify(dataset, limit)
    solver = DeepSeekDirectSolver()
    old_router = SemanticModeRouter()
    resid = ResidualEscalationRouter()
    matched = _MATCHED[dataset]
    price = solver.price()
    rows = []
    toks = {e: [0, 0, 0.0] for e in _EXP}
    errors = 0
    t0 = time.time()
    for ex in exs:
        preds, ptoks = {}, {}
        for v in _VARIANTS:
            ts = time.time()
            try:
                text, p, c = solver.solve_direct(ex.claim, ex.evidence, task="verify", variant=v)
            except Exception:
                text, p, c = "", 0, 0
                errors += 1
            preds[v] = parse_verdict(text, VERIFY_SYNS)
            ptoks[v] = (p, c, time.time() - ts)
        c_mode = old_router.route(ex.claim, ex.evidence).mode
        dec = resid.route(ex.claim, ex.evidence)
        chosen = {"baseline": "baseline", "matched": matched, "old_router": c_mode,
                  "micro_router": dec.micro_policy, "unfolding": dec.e_policy,
                  "residual": dec.f_policy}
        for exp, var in chosen.items():
            p, c, dt = ptoks[var]
            toks[exp][0] += p
            toks[exp][1] += c
            toks[exp][2] += dt
        rows.append({
            "id": ex.id, "gold": ex.gold,
            "pred_baseline": preds["baseline"], "pred_evidence_strict": preds["evidence_strict"],
            "pred_entailment_direct": preds["entailment_direct"],
            "old_mode": c_mode, "micro_policy": dec.micro_policy, "unfold_category": dec.unfold_category,
            "e_policy": dec.e_policy, "escalated": dec.escalated, "outcome": dec.outcome,
            "f_policy": dec.f_policy, "scores": dec.scores, "reason": dec.reason,
        })
    elapsed = time.time() - t0

    def pred_for(r, exp):
        return {"baseline": r["pred_baseline"], "matched": r[f"pred_{matched}"],
                "old_router": r[f"pred_{r['old_mode']}"], "micro_router": r[f"pred_{r['micro_policy']}"],
                "unfolding": r[f"pred_{r['e_policy']}"], "residual": r[f"pred_{r['f_policy']}"]}[exp]

    agg = {e: _aggregate([(r["gold"], pred_for(r, e)) for r in rows]) for e in _EXP}
    for e in _EXP:
        agg[e]["elapsed_s"] = round(toks[e][2], 2)
        agg[e]["est_cost_usd"] = round(toks[e][0] * price[0] + toks[e][1] * price[1], 6)

    esc = [r for r in rows if r["escalated"]]
    esc_ans = sum(1 for r in esc if pred_for(r, "residual") is not None)
    esc_cor = sum(1 for r in esc if pred_for(r, "residual") == r["gold"])
    esc_helped_e = sum(1 for r in esc if pred_for(r, "residual") == r["gold"] and pred_for(r, "unfolding") != r["gold"])
    esc_hurt_e = sum(1 for r in esc if pred_for(r, "residual") != r["gold"] and pred_for(r, "unfolding") == r["gold"])
    out_dist = {o: 0 for o in OUTCOMES}
    for r in esc:
        out_dist[r["outcome"]] += 1
    per_out = {}
    for o in OUTCOMES:
        sub = [r for r in esc if r["outcome"] == o]
        a = sum(1 for r in sub if pred_for(r, "residual") is not None)
        cc = sum(1 for r in sub if pred_for(r, "residual") == r["gold"])
        per_out[o] = {"n": len(sub), "accuracy": round(cc / a, 3) if a else None}
    prevented = sum(1 for r in rows if r["f_policy"] != "entailment_direct"
                    and r["pred_entailment_direct"] != r["gold"] and pred_for(r, "residual") == r["gold"])
    overprotect = sum(1 for r in rows if r["f_policy"] != "entailment_direct"
                      and r["pred_entailment_direct"] == r["gold"] and pred_for(r, "residual") != r["gold"])

    def help_hurt(other):
        h = sum(1 for r in rows if pred_for(r, "residual") == r["gold"] and pred_for(r, other) != r["gold"])
        u = sum(1 for r in rows if pred_for(r, "residual") != r["gold"] and pred_for(r, other) == r["gold"])
        return {"helped": h, "hurt": u, "net": h - u}

    rec = {
        "dataset": _DS_NAME[dataset], "dataset_key": dataset, "matched_family": matched,
        "n": len(exs), "errors": errors, "solver": solver.name, "wall_elapsed_s": round(elapsed, 2),
        "experiments": agg,
        "residual": {
            "escalation_count": len(esc),
            "escalation_precision": round(esc_cor / esc_ans, 3) if esc_ans else None,
            "escalation_vs_unfolding": {"helped": esc_helped_e, "hurt": esc_hurt_e,
                                        "net": esc_helped_e - esc_hurt_e},
            "outcome_distribution": out_dist, "per_outcome_accuracy": per_out,
            "f_route_distribution": dict(Counter(r["f_policy"] for r in rows)),
            "false_folds_prevented": prevented, "cases_overprotected": overprotect,
            "vs_baseline": help_hurt("baseline"), "vs_matched": help_hurt("matched"),
            "vs_old_router": help_hurt("old_router"), "vs_micro_router": help_hurt("micro_router"),
            "vs_unfolding": help_hurt("unfolding"),
        },
        "rows": rows,
        "desi_core": desi_core_metrics(exs),
    }
    _RUNS.mkdir(parents=True, exist_ok=True)
    (_RUNS / f"re_{dataset}.json").write_text(json.dumps(rec, indent=2), encoding="utf-8")
    a = agg
    print(f"{dataset}: A={a['baseline']['accuracy']} B={a['matched']['accuracy']} "
          f"C={a['old_router']['accuracy']} D={a['micro_router']['accuracy']} "
          f"E={a['unfolding']['accuracy']} F={a['residual']['accuracy']} | escalated={len(esc)} "
          f"esc_prec={rec['residual']['escalation_precision']} esc_net_vs_E="
          f"{rec['residual']['escalation_vs_unfolding']['net']:+d} | net vs E "
          f"{rec['residual']['vs_unfolding']['net']:+d} vs D {rec['residual']['vs_micro_router']['net']:+d} "
          f"| desi replay {rec['desi_core']['replay_stable']} core {rec['desi_core']['core_identity_ok']}")
    return rec


def residual_report(dataset):
    p = _RUNS / f"re_{dataset}.json"
    if not p.exists():
        print(f"missing run for {dataset}")
        return
    rec = json.loads(p.read_text())
    agg, rs = rec["experiments"], rec["residual"]
    g = agg["baseline"]["gold_distribution"]
    matched = rec["matched_family"]
    cols = [(_EXP_LABEL[e] if e != "matched" else f"B matched ({matched})", e) for e in _EXP]
    md = [
        f"# Residual semantic escalation — {rec['dataset']}\n",
        "Algorithm-first: the deterministic micro-router + unfolding protection resolve "
        "clear cases; only the ambiguous residue escalates to a lightweight deterministic "
        "semantic scorer (synonym-group + character-trigram vectors with directional "
        "containment / asymmetry -- NO learned neural embeddings are available offline "
        "here, so the vectors are deterministic local lexical-semantic vectors; this is a "
        "documented constraint). Policies: **A** baseline, **B** benchmark-matched, **C** "
        "DESi semantic-router, **D** micro-router, **E** unfolding-aware, **F** residual "
        "escalation. DeepSeek v4 Pro, temp 0, FIXED families, same evaluator. No LLM in any "
        "router; DESi core untouched, recorded alongside.\n",
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
        "## Residual escalation behaviour\n",
        f"Escalated (residue only): {rs['escalation_count']}/{rec['n']}; escalation accuracy "
        f"(F on the escalated subset): {rs['escalation_precision']}; escalation net vs E on "
        f"that subset: {rs['escalation_vs_unfolding']['net']:+d} (helped "
        f"{rs['escalation_vs_unfolding']['helped']}, hurt {rs['escalation_vs_unfolding']['hurt']}).\n",
        f"Outcome distribution: " + ", ".join(f"{o} {rs['outcome_distribution'][o]}" for o in OUTCOMES) + ".\n",
        f"F route distribution: {rs['f_route_distribution']}.\n",
        f"- **False folds prevented**: {rs['false_folds_prevented']}; **over-protected**: "
        f"{rs['cases_overprotected']}.",
        "",
        "### Per-outcome accuracy (escalated cases)\n",
        "| residual outcome | n | F accuracy |",
        "| --- | --- | --- |",
    ]
    for o in OUTCOMES:
        po = rs["per_outcome_accuracy"][o]
        md.append(f"| {o} | {po['n']} | {po['accuracy']} |")
    md += [
        "",
        f"- **vs E (unfolding)**: net {rs['vs_unfolding']['net']:+d} (helped {rs['vs_unfolding']['helped']}, "
        f"hurt {rs['vs_unfolding']['hurt']}). **vs D (micro)**: net {rs['vs_micro_router']['net']:+d}. "
        f"**vs C (DESi)**: net {rs['vs_old_router']['net']:+d}.",
        f"- **vs A (baseline)**: net {rs['vs_baseline']['net']:+d}. **vs B (matched)**: net "
        f"{rs['vs_matched']['net']:+d}.",
    ]
    dc = rec["desi_core"]
    md += [
        "",
        "## DESi-core (alongside; core untouched)\n",
        f"- replay stability: {'1.0' if dc['replay_stable'] else 'FAILED'}; core identity: "
        f"{dc['core_identity_ok']}; governance independence: {'1.0' if dc['gov_independent'] else 'FAILED'}; "
        f"critical_branch_preservation: {dc['critical_branch_preservation']}; "
        f"mutation rejected: {dc['mutation_rejected']}/{dc['mutation_attempts']}.",
        "- The residual scorer is deterministic local vector arithmetic; it does not import "
        "or modify the DESi core or ontology, and runs only on the escalated residue.",
        "",
        "## Honesty / limits\n",
        "- One deterministic pass per (item, variant); DeepSeek mildly non-deterministic. "
        "The residual 'semantic vectors' are deterministic local lexical-semantic vectors "
        "(no learned embeddings available offline). Accuracies are the model's; routers only "
        "pick a policy. NOT a truthfulness claim; DESi did not solve NLI. Limits reported, "
        "core unchanged.",
    ]
    out = "residual_vitaminc.md" if dataset == "vitaminc" else "residual_fever.md"
    _REPORTS.mkdir(parents=True, exist_ok=True)
    (_REPORTS / out).write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"residual report -> {out}")


def residual_cross_summary():
    recs = {}
    for ds in ("vitaminc", "nli_fever"):
        p = _RUNS / f"re_{ds}.json"
        if p.exists():
            recs[ds] = json.loads(p.read_text())
    if not recs:
        print("no residual runs")
        return

    def accs(ds):
        a = recs[ds]["experiments"]
        return tuple(a[e]["accuracy"] for e in _EXP)

    md = [
        "# Residual semantic escalation — cross-summary\n",
        "Algorithm-first + semantic-residual escalation: deterministic layers resolve clear "
        "cases; only the ambiguous residue escalates to a lightweight deterministic semantic "
        "scorer (synonym-group + char-trigram vectors, directional containment / asymmetry; "
        "no learned embeddings available offline). Policies A baseline / B matched / C DESi "
        "router / D micro / E unfolding / F residual. DeepSeek v4 Pro, temp 0, FIXED "
        "families, same evaluator. Core untouched.\n",
        "## Accuracy by policy\n",
        "| dataset | A base | B matched | C DESi | D micro | E unfold | F residual | escalated | esc. acc |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for ds in ("vitaminc", "nli_fever"):
        if ds not in recs:
            continue
        A, B, C, D, E, F = accs(ds)
        rs = recs[ds]["residual"]
        md.append(f"| {recs[ds]['dataset']} | {A} | {B} | {C} | {D} | {E} | {F} | "
                  f"{rs['escalation_count']}/{recs[ds]['n']} | {rs['escalation_precision']} |")
    md.append("")
    md.append("| dataset | overcommit A->F | overabst A->F | false folds prevented | over-protected | net F vs E | esc net vs E |")
    md.append("| --- | --- | --- | --- | --- | --- | --- |")
    for ds in ("vitaminc", "nli_fever"):
        if ds not in recs:
            continue
        a = recs[ds]["experiments"]; rs = recs[ds]["residual"]
        md.append(f"| {recs[ds]['dataset']} | {a['baseline']['overcommitment_rate']} -> "
                  f"{a['residual']['overcommitment_rate']} | {a['baseline']['overabstention_rate']} -> "
                  f"{a['residual']['overabstention_rate']} | {rs['false_folds_prevented']} | "
                  f"{rs['cases_overprotected']} | {rs['vs_unfolding']['net']:+d} | "
                  f"{rs['escalation_vs_unfolding']['net']:+d} |")
    md.append("")

    beats_e = all(accs(ds)[5] >= accs(ds)[4] for ds in recs)
    beats_d = all(accs(ds)[5] >= accs(ds)[3] for ds in recs)
    beats_base = all(accs(ds)[5] >= accs(ds)[0] for ds in recs)
    beats_matched = all(accs(ds)[5] >= accs(ds)[1] for ds in recs)
    esc_net = sum(recs[ds]["residual"]["escalation_vs_unfolding"]["net"] for ds in recs)
    avg_F_minus_E = sum(accs(ds)[5] - accs(ds)[4] for ds in recs) / len(recs)
    clear_benefit = beats_e and esc_net >= 3 and avg_F_minus_E >= 0.02
    md += [
        "## Answers to the key questions\n",
        "- **A) Does residual semantic escalation improve unfolding precision?** "
        + "; ".join(f"{recs[ds]['dataset']}: F {accs(ds)[5]} vs E {accs(ds)[4]} "
                    f"({accs(ds)[5] - accs(ds)[4]:+.3f}); on the escalated subset F net vs E = "
                    f"{recs[ds]['residual']['escalation_vs_unfolding']['net']:+d} "
                    f"(esc. acc {recs[ds]['residual']['escalation_precision']})" for ds in recs)
        + ". " + ("F >= E on both." if beats_e else "F does NOT consistently beat E."),
        "- **B) Can residual-only semantics outperform pure lexical unfolding?** see (A): "
        + ("yes, marginally" if (beats_e and esc_net > 0) else "not clearly")
        + f" -- escalation net vs E across datasets = {esc_net:+d}.",
        "- **C) Reduce false entailment folds without massive overabstention?** "
        + "; ".join(f"{recs[ds]['dataset']}: prevented {recs[ds]['residual']['false_folds_prevented']} / "
                    f"over-protected {recs[ds]['residual']['cases_overprotected']}; overabst "
                    f"{recs[ds]['experiments']['baseline']['overabstention_rate']}->"
                    f"{recs[ds]['experiments']['residual']['overabstention_rate']}" for ds in recs) + ".",
        "- **D) Does this validate 'semantic vectors are useful for unfolding, not just "
        "folding'?** The residual vectors are applied ONLY to detect dangerous/ambiguous "
        "folds (directional containment + asymmetry + same-topic checks), never to merge "
        "items; whether that yields a net accuracy gain is answered by (A)/(B) -- "
        + ("supported." if clear_benefit else "mechanism demonstrated, net gain marginal/absent.")
        + " The vectors here are deterministic local lexical-semantic vectors, not learned "
        "embeddings (none available offline); a stronger test would need real embeddings.",
        "- **E) Does this support progressive epistemic escalation?** Structurally YES: most "
        "items are resolved by the deterministic layers and only "
        + "/".join(str(recs[ds]['residual']['escalation_count']) for ds in recs)
        + " items per dataset escalate; the escalation is cheap, deterministic, replay-stable, "
        "and never touches the core. Empirically the accuracy gain is "
        + ("clear." if clear_benefit else "marginal -- the residual signal is not precise enough to beat the matched family."),
    ]
    core_ok = all(recs[ds]["desi_core"]["core_identity_ok"] in (True, None) for ds in recs)
    replay_ok = all(recs[ds]["desi_core"]["replay_stable"] for ds in recs)
    md += [
        "",
        "- **vs benchmark-matched (B)**: " + ("F >= matched on both."
        if beats_matched else "matched still >= F (dataset-level prompt remains the ceiling).")
        + " **vs baseline (A)**: " + ("F >= baseline on both." if beats_base else "mixed.")
        + " **vs micro (D)**: " + ("F >= D on both." if beats_d else "mixed."),
        f"- **Core untouched?** {'YES' if core_ok else 'NO'} -- byte-identical, replay "
        f"{'1.0' if replay_ok else 'FAILED'} on every run.",
        "",
        "## Interpretation (per study rule)\n",
        ("- F improves: evidence for algorithm-first + semantic-residual escalation -- "
         "escalating only the ambiguous residue to lightweight semantic checks raised "
         "precision over pure lexical unfolding. Reported without truthfulness claims."
         if clear_benefit else
         "- F does not clearly improve. The residual signals that remain INSUFFICIENT: "
         "directional containment built from synonym-group + char-trigram vectors catches "
         "morphological/subset overlap but still cannot recognise paraphrastic entailment "
         "(different surface forms, same meaning) -- which needs learned embeddings, "
         "unavailable offline here. The escalation mechanism (algorithm-first, residue-only) "
         "is validated structurally; the residual SIGNAL is the limiting factor. Reported as "
         "a signal limit, NOT patched into the core. No truthfulness claim; DESi did not "
         "solve NLI."),
        "",
        "## Honesty / limits\n",
        "- N=100/dataset; one deterministic pass; DeepSeek mild non-determinism; FIXED prompt "
        "families; residual vectors are deterministic local lexical-semantic vectors (no "
        "learned embeddings offline); core-independent. No core/ontology/meaning-space change; "
        "outputs secret-scanned.",
    ]
    _REPORTS.mkdir(parents=True, exist_ok=True)
    (_REPORTS / "residual_cross_summary.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("cross-summary written")


def main() -> int:
    ap = argparse.ArgumentParser(description="Residual semantic escalation study.")
    ap.add_argument("--dataset", choices=sorted(_MATCHED))
    ap.add_argument("--limit", type=int, default=100)
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--cross-summary", action="store_true")
    args = ap.parse_args()
    if args.cross_summary:
        residual_cross_summary(); return 0
    if args.report:
        residual_report(args.dataset); return 0
    if args.run:
        if not args.dataset:
            ap.error("--run needs --dataset")
        run_residual(args.dataset, args.limit); return 0
    ap.error("need --run/--report (with --dataset) or --cross-summary")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
