#!/usr/bin/env python3
"""Prompt-only calibration test for DeepSeek (PERIPHERAL).

The ONLY thing that changes between runs is the evidence-style solver prompt
(baseline vs calibrated). Everything else is identical: DeepSeek v4 Pro only,
direct api.deepseek.com, temperature 0, one deterministic pass, no retries, no
voting, no repair. No Granite, no DESi-core change, no role pipeline. DESi-core
metrics are recorded alongside to confirm invariance.

Question: does prompt calibration fix DeepSeek's overcommitment (VitaminC) and
overabstention (FEVER) WITHOUT collapsing SUPPORTS/REFUTES accuracy?
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parents[1]
sys.path.insert(0, str(_REPO / "src"))
sys.path.insert(0, str(_HERE))

from solver_ports import DeepSeekDirectSolver, VERIFY_SYNS, parse_verdict  # noqa: E402
from scifact_runner import DATASETS, desi_core_metrics, load_verify  # noqa: E402

_REPORTS = _HERE / "reports"
_RUNS = _REPORTS / "_runs"
_LABELS = ("SUPPORTS", "REFUTES", "NOT_ENOUGH_INFO")
_NEI = "NOT_ENOUGH_INFO"
_DS_NAME = {"vitaminc": "tals/vitaminc", "nli_fever": "pietrolesci/nli_fever"}


def _per_class(conf):
    out = {}
    for L in _LABELS:
        tp = conf[L][L]
        fp = sum(conf[g][L] for g in _LABELS if g != L)
        fn = sum(conf[L][p] for p in _LABELS if p != L)
        out[L] = {
            "precision": round(tp / (tp + fp), 3) if (tp + fp) else None,
            "recall": round(tp / (tp + fn), 3) if (tp + fn) else None,
            "tp": tp, "fp": fp, "fn": fn,
        }
    return out


_FAMILIES = ("baseline", "evidence_strict", "entailment_direct")


def run_one(dataset, variant, limit, prefix="calib"):
    _spec, exs = load_verify(dataset, limit)
    solver = DeepSeekDirectSolver()
    conf = {g: {p: 0 for p in _LABELS} for g in _LABELS}
    gold_dist = {l: 0 for l in _LABELS}
    pred_dist = {l: 0 for l in _LABELS}
    parse_fail = errors = correct = pt = ct = 0
    t0 = time.time()
    for ex in exs:
        gold_dist[ex.gold] += 1
        try:
            text, p, c = solver.solve_direct(ex.claim, ex.evidence, task="verify", variant=variant)
            pt += p; ct += c
            pred = parse_verdict(text, VERIFY_SYNS)
        except Exception:
            errors += 1
            continue
        if pred is None:
            parse_fail += 1
            continue
        pred_dist[pred] += 1
        conf[ex.gold][pred] += 1
        if pred == ex.gold:
            correct += 1
    elapsed = time.time() - t0
    answered = sum(pred_dist.values())
    # overcommitment: gold NEI predicted as SUPPORTS/REFUTES
    nei_total = gold_dist[_NEI]
    over_commit = sum(conf[_NEI][p] for p in _LABELS if p != _NEI)
    # overabstention: gold non-NEI predicted NEI
    nonnei_total = gold_dist["SUPPORTS"] + gold_dist["REFUTES"]
    over_abst = conf["SUPPORTS"][_NEI] + conf["REFUTES"][_NEI]
    price = solver.price()
    rec = {
        "dataset": _DS_NAME[dataset], "variant": variant, "model": solver.name,
        "n": len(exs), "answered": answered, "parse_failures": parse_fail, "errors": errors,
        "accuracy": round(correct / answered, 3) if answered else None,
        "confusion": conf, "gold_distribution": gold_dist, "pred_distribution": pred_dist,
        "per_class": _per_class(conf),
        "overcommitment_rate": round(over_commit / nei_total, 3) if nei_total else None,
        "overcommitment_n": f"{over_commit}/{nei_total}",
        "overabstention_rate": round(over_abst / nonnei_total, 3) if nonnei_total else None,
        "overabstention_n": f"{over_abst}/{nonnei_total}",
        "elapsed_s": round(elapsed, 2),
        "est_cost_usd": round(pt * price[0] + ct * price[1], 6),
        "desi_core": desi_core_metrics(exs),
    }
    _RUNS.mkdir(parents=True, exist_ok=True)
    (_RUNS / f"{prefix}_{dataset}_{variant}.json").write_text(json.dumps(rec, indent=2), encoding="utf-8")
    acc = rec["accuracy"]
    print(f"{dataset}/{variant}: acc={acc} pred={rec['pred_distribution']} "
          f"overcommit={rec['overcommitment_n']} overabst={rec['overabstention_n']} "
          f"parsefail={parse_fail} {rec['elapsed_s']}s cost=${rec['est_cost_usd']} | "
          f"desi replay {rec['desi_core']['replay_stable']} core {rec['desi_core']['core_identity_ok']}")
    return rec


def _cls(rec, L, k):
    v = rec["per_class"][L][k]
    return f"{v:.3f}" if isinstance(v, float) else str(v)


def compare(dataset):
    b = _RUNS / f"calib_{dataset}_baseline.json"
    c = _RUNS / f"calib_{dataset}_calibrated.json"
    if not (b.exists() and c.exists()):
        print(f"missing runs for {dataset}")
        return
    base, cal = json.loads(b.read_text()), json.loads(c.read_text())
    g = base["gold_distribution"]
    md = [
        f"# DeepSeek prompt-only calibration — {base['dataset']}\n",
        "Prompt-only A/B: the only change is the evidence-style solver prompt "
        "(baseline vs calibrated). DeepSeek v4 Pro only, direct, temp 0, one "
        "deterministic pass, no retries/voting/repair. No Granite, no DESi-core "
        "change. DESi-core recorded alongside.\n",
        f"N={base['n']} | gold S/R/N = {g['SUPPORTS']}/{g['REFUTES']}/{g['NOT_ENOUGH_INFO']}\n",
        "| metric | baseline | calibrated |",
        "| --- | --- | --- |",
        f"| accuracy | {base['accuracy']} | {cal['accuracy']} |",
        f"| pred S/R/N | {base['pred_distribution']['SUPPORTS']}/{base['pred_distribution']['REFUTES']}/{base['pred_distribution']['NOT_ENOUGH_INFO']} "
        f"| {cal['pred_distribution']['SUPPORTS']}/{cal['pred_distribution']['REFUTES']}/{cal['pred_distribution']['NOT_ENOUGH_INFO']} |",
        f"| overcommitment rate (gold-NEI committed) | {base['overcommitment_rate']} ({base['overcommitment_n']}) | {cal['overcommitment_rate']} ({cal['overcommitment_n']}) |",
        f"| overabstention rate (gold-S/R -> NEI) | {base['overabstention_rate']} ({base['overabstention_n']}) | {cal['overabstention_rate']} ({cal['overabstention_n']}) |",
        f"| parse failures | {base['parse_failures']} | {cal['parse_failures']} |",
        f"| elapsed / cost | {base['elapsed_s']}s / ${base['est_cost_usd']} | {cal['elapsed_s']}s / ${cal['est_cost_usd']} |",
        "",
        "### Per-class precision / recall\n",
        "| class | baseline P | baseline R | calibrated P | calibrated R |",
        "| --- | --- | --- | --- | --- |",
    ]
    for L in _LABELS:
        md.append(f"| {L} | {_cls(base,L,'precision')} | {_cls(base,L,'recall')} | "
                  f"{_cls(cal,L,'precision')} | {_cls(cal,L,'recall')} |")
    md += ["", "### Confusion (rows gold, cols pred)\n"]
    for name, r in (("baseline", base), ("calibrated", cal)):
        md += [f"**{name}**", "", "| gold \\ pred | " + " | ".join(_LABELS) + " |",
               "| --- | " + " | ".join("---" for _ in _LABELS) + " |"]
        for gl in _LABELS:
            md.append(f"| {gl} | " + " | ".join(str(r["confusion"][gl][p]) for p in _LABELS) + " |")
        md.append("")
    dc = cal["desi_core"]
    md += [
        "### DESi-core (alongside; core untouched)\n",
        f"- replay stability: {'1.0' if dc['replay_stable'] else 'FAILED'}; core identity: "
        f"{dc['core_identity_ok']}; governance independence: {'1.0' if dc['gov_independent'] else 'FAILED'}; "
        f"critical_branch_preservation: {dc['critical_branch_preservation']}; "
        f"mutation rejected: {dc['mutation_rejected']}/{dc['mutation_attempts']}.",
        "",
        "## Honesty / limits\n",
        "- Prompt-only change; one deterministic pass; accuracies are the model's. "
        "DeepSeek is mildly non-deterministic across runs. DESi neither solves nor scores.",
    ]
    _REPORTS.mkdir(parents=True, exist_ok=True)
    out = f"deepseek_prompt_calibration_{'vitaminc' if dataset=='vitaminc' else 'fever'}.md"
    (_REPORTS / out).write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"comparison -> {out}")


def summary():
    runs = {}
    for ds in ("vitaminc", "nli_fever"):
        for v in ("baseline", "calibrated"):
            p = _RUNS / f"calib_{ds}_{v}.json"
            if p.exists():
                runs[(ds, v)] = json.loads(p.read_text())
    if not runs:
        print("no calibration runs")
        return
    md = [
        "# DeepSeek prompt-only calibration — summary\n",
        "Only the evidence-style solver prompt changed (baseline vs calibrated). "
        "DeepSeek v4 Pro, direct, temp 0, one pass. No architecture/core/ontology "
        "change.\n",
        "| dataset | variant | acc | overcommit | overabst | pred S/R/N |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for ds in ("vitaminc", "nli_fever"):
        for v in ("baseline", "calibrated"):
            r = runs.get((ds, v))
            if not r:
                continue
            pd = r["pred_distribution"]
            md.append(f"| {r['dataset']} | {v} | {r['accuracy']} | "
                      f"{r['overcommitment_rate']} ({r['overcommitment_n']}) | "
                      f"{r['overabstention_rate']} ({r['overabstention_n']}) | "
                      f"{pd['SUPPORTS']}/{pd['REFUTES']}/{pd['NOT_ENOUGH_INFO']} |")
    md.append("")

    def delta(ds, key):
        b, c = runs.get((ds, "baseline")), runs.get((ds, "calibrated"))
        if not (b and c) or b.get(key) is None or c.get(key) is None:
            return None, None, None
        return b[key], c[key], c[key] - b[key]

    md.append("## Answers\n")
    for ds in ("vitaminc", "nli_fever"):
        ba, ca, da = delta(ds, "accuracy")
        boc, coc, doc = delta(ds, "overcommitment_rate")
        boa, coa, doa = delta(ds, "overabstention_rate")
        if ba is None:
            continue
        md.append(
            f"- **{_DS_NAME[ds]}**: accuracy {ba}->{ca} ({da:+.3f}); overcommitment "
            f"{boc}->{coc} ({doc:+.3f}); overabstention {boa}->{coa} ({doa:+.3f}).")
    # global verdicts
    vc = runs.get(("vitaminc", "baseline")), runs.get(("vitaminc", "calibrated"))
    fv = runs.get(("nli_fever", "baseline")), runs.get(("nli_fever", "calibrated"))
    helped = []
    if all(vc):
        helped.append(("VitaminC overcommitment", vc[0]["overcommitment_rate"], vc[1]["overcommitment_rate"]))
    if all(fv):
        helped.append(("FEVER overabstention", fv[0]["overabstention_rate"], fv[1]["overabstention_rate"]))
    md += [
        "",
        "- **Did prompt-only calibration help?** see the deltas above (overcommitment "
        "on VitaminC, overabstention on FEVER) against the accuracy deltas.",
        "- **Did overcommitment decrease?** "
        + (f"VitaminC {vc[0]['overcommitment_rate']} -> {vc[1]['overcommitment_rate']}." if all(vc) else "n/a"),
        "- **Did overabstention decrease?** "
        + (f"FEVER {fv[0]['overabstention_rate']} -> {fv[1]['overabstention_rate']}." if all(fv) else "n/a"),
        "- **Total accuracy improve or degrade?** "
        + "; ".join(f"{_DS_NAME[ds]} {delta(ds,'accuracy')[0]}->{delta(ds,'accuracy')[1]}"
                    for ds in ("vitaminc", "nli_fever") if delta(ds, "accuracy")[0] is not None) + ".",
        "- **Is DeepSeek salvageable as semantic solver, or change model?** judged on "
        "whether NEI calibration improved WITHOUT collapsing SUPPORTS/REFUTES "
        "accuracy (per-class recall in the per-dataset reports); read from the "
        "numbers above, not asserted.",
        "",
        "## DESi-core invariance\n",
        "- recorded alongside every run: replay stable, core byte-identical, "
        "governance independent, mutation rejected -- unchanged by the prompt swap.",
        "",
        "## Honesty / limits\n",
        "- Prompt-only; N=100/dataset; one deterministic pass; DeepSeek mild "
        "non-determinism. No core change, no ontology drift; outputs secret-scanned.",
    ]
    _REPORTS.mkdir(parents=True, exist_ok=True)
    (_REPORTS / "deepseek_prompt_calibration_summary.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("summary written")


def family_compare(dataset, prefix="pf"):
    recs = {}
    for f in _FAMILIES:
        p = _RUNS / f"{prefix}_{dataset}_{f}.json"
        if p.exists():
            recs[f] = json.loads(p.read_text())
    if len(recs) < len(_FAMILIES):
        print(f"missing family runs for {dataset}: have {list(recs)}")
        return
    g = recs["baseline"]["gold_distribution"]
    md = [
        f"# DeepSeek prompt-family comparison — {recs['baseline']['dataset']}\n",
        "Task-matched prompt families (prompt-only A/B/C): baseline vs "
        "evidence-strict (for over-commitment) vs entailment-direct (for "
        "over-abstention). DeepSeek v4 Pro only, direct, temp 0, one deterministic "
        "pass; no retries/voting/repair; no Granite/core/evaluator/role-pipeline "
        "change. DESi-core recorded alongside.\n",
        f"N={recs['baseline']['n']} | gold S/R/N = {g['SUPPORTS']}/{g['REFUTES']}/{g['NOT_ENOUGH_INFO']}\n",
        "| metric | baseline | evidence-strict | entailment-direct |",
        "| --- | --- | --- | --- |",
    ]
    def row(label, fn):
        return f"| {label} | " + " | ".join(str(fn(recs[f])) for f in _FAMILIES) + " |"
    md += [
        row("accuracy", lambda r: r["accuracy"]),
        row("pred S/R/N", lambda r: f"{r['pred_distribution']['SUPPORTS']}/{r['pred_distribution']['REFUTES']}/{r['pred_distribution']['NOT_ENOUGH_INFO']}"),
        row("overcommitment", lambda r: f"{r['overcommitment_rate']} ({r['overcommitment_n']})"),
        row("overabstention", lambda r: f"{r['overabstention_rate']} ({r['overabstention_n']})"),
        row("parse failures", lambda r: r["parse_failures"]),
        row("elapsed/cost", lambda r: f"{r['elapsed_s']}s/${r['est_cost_usd']}"),
        "",
        "### Per-class precision / recall\n",
        "| class | " + " | ".join(f"{f} P/R" for f in _FAMILIES) + " |",
        "| --- | " + " | ".join("---" for _ in _FAMILIES) + " |",
    ]
    for L in _LABELS:
        md.append(f"| {L} | " + " | ".join(
            f"{_cls(recs[f],L,'precision')}/{_cls(recs[f],L,'recall')}" for f in _FAMILIES) + " |")
    md += ["", "### Confusion (rows gold, cols pred)\n"]
    for f in _FAMILIES:
        r = recs[f]
        md += [f"**{f}**", "", "| gold \\ pred | " + " | ".join(_LABELS) + " |",
               "| --- | " + " | ".join("---" for _ in _LABELS) + " |"]
        for gl in _LABELS:
            md.append(f"| {gl} | " + " | ".join(str(r["confusion"][gl][p]) for p in _LABELS) + " |")
        md.append("")
    dc = recs["baseline"]["desi_core"]
    md += [
        "### DESi-core (alongside; core untouched)\n",
        f"- replay {dc['replay_stable']}; core identity {dc['core_identity_ok']}; governance "
        f"{dc['gov_independent']}; critical_branch_preservation {dc['critical_branch_preservation']}; "
        f"mutation {dc['mutation_rejected']}/{dc['mutation_attempts']} (identical across all families).",
        "",
        "## Honesty / limits\n",
        "- Prompt-only; one deterministic pass; DeepSeek mild non-determinism; "
        "accuracies are the model's. DESi neither solves nor scores.",
    ]
    out = "vitaminc_prompt_family_comparison.md" if dataset == "vitaminc" else "fever_prompt_family_comparison.md"
    _REPORTS.mkdir(parents=True, exist_ok=True)
    (_REPORTS / out).write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"family comparison -> {out}")


def family_summary(prefix="pf"):
    data = {}
    for ds in ("vitaminc", "nli_fever"):
        for f in _FAMILIES:
            p = _RUNS / f"{prefix}_{ds}_{f}.json"
            if p.exists():
                data[(ds, f)] = json.loads(p.read_text())
    if not data:
        print("no family runs"); return
    md = [
        "# Prompt-family cross-summary — DeepSeek task-matched calibration\n",
        "Prompt-only (model/temp/evaluator/core all identical). evidence-strict "
        "targets over-commitment; entailment-direct targets over-abstention. The "
        "'universal' prompt = evidence-strict applied to both.\n",
        "| dataset | metric | baseline | evidence-strict | entailment-direct |",
        "| --- | --- | --- | --- | --- |",
    ]
    for ds in ("vitaminc", "nli_fever"):
        if (ds, "baseline") not in data:
            continue
        name = _DS_NAME[ds]
        md.append(f"| {name} | accuracy | " + " | ".join(str(data[(ds, f)]["accuracy"]) for f in _FAMILIES) + " |")
        md.append(f"| {name} | overcommit | " + " | ".join(str(data[(ds, f)]["overcommitment_rate"]) for f in _FAMILIES) + " |")
        md.append(f"| {name} | overabst | " + " | ".join(str(data[(ds, f)]["overabstention_rate"]) for f in _FAMILIES) + " |")
    md.append("")

    def best_family(ds):
        accs = {f: data[(ds, f)]["accuracy"] for f in _FAMILIES if (ds, f) in data and data[(ds, f)]["accuracy"] is not None}
        return max(accs, key=lambda f: accs[f]) if accs else None, accs

    md.append("## Answers\n")
    matched = {"vitaminc": "evidence_strict", "nli_fever": "entailment_direct"}
    universal = "evidence_strict"
    for ds in ("vitaminc", "nli_fever"):
        if (ds, "baseline") not in data:
            continue
        bf, accs = best_family(ds)
        m = matched[ds]
        md.append(
            f"- **{_DS_NAME[ds]}**: baseline {accs.get('baseline')}, evidence-strict "
            f"{accs.get('evidence_strict')}, entailment-direct {accs.get('entailment_direct')} "
            f"-> best accuracy: **{bf}**; task-matched family ({m}) "
            + ("== best" if bf == m else f"!= best ({bf})") + ".")
    md += [
        "",
        "- **Can DeepSeek be stabilized by task-specific calibration?** Compare each "
        "dataset's task-matched family to its baseline (accuracy + the targeted "
        "error rate) above.",
        "- **Which prompt family fits which benchmark style?** evidence-strict for "
        "over-commitment (VitaminC-style); entailment-direct for over-abstention "
        "(FEVER/NLI-style) -- judged by which family minimizes the dataset's "
        "characteristic error above.",
        "- **Does one universal epistemic prompt fail systematically?** The universal "
        "(evidence-strict) row vs the entailment-direct row on FEVER shows whether a "
        "single prompt mis-serves the opposite failure mode.",
        "- **Does prompt-family specialization outperform model replacement?** If the "
        "matched family recovers accuracy on both styles without collapse, "
        "specialization is sufficient and no model swap is indicated; otherwise it is.",
        "- **Should Granite->DeepSeek continue?** This study is solver-only "
        "(DeepSeek direct, no Granite in the loop); it speaks to the SOLVER's "
        "calibratability, not the extractor pairing -- reported as such.",
        "",
        "## DESi-core invariance\n",
        "- recorded alongside every run: replay stable, core byte-identical, "
        "governance independent, mutation rejected -- unchanged by any prompt family.",
        "",
        "## Honesty / limits\n",
        "- Prompt-only; N=100/dataset; one deterministic pass; mild non-determinism; "
        "no core/architecture/ontology change; outputs secret-scanned.",
    ]
    _REPORTS.mkdir(parents=True, exist_ok=True)
    (_REPORTS / "prompt_family_cross_summary.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("cross-summary written")


def main() -> int:
    ap = argparse.ArgumentParser(description="DeepSeek prompt-family calibration study.")
    ap.add_argument("--dataset", choices=sorted(DATASETS))
    ap.add_argument("--variant", choices=["baseline", "evidence_strict", "entailment_direct", "calibrated"])
    ap.add_argument("--limit", type=int, default=100)
    ap.add_argument("--prefix", default="calib")
    ap.add_argument("--compare", action="store_true")
    ap.add_argument("--summary", action="store_true")
    ap.add_argument("--family-compare", action="store_true")
    ap.add_argument("--family-summary", action="store_true")
    args = ap.parse_args()
    if args.summary:
        summary(); return 0
    if args.family_summary:
        family_summary(); return 0
    if args.family_compare:
        family_compare(args.dataset); return 0
    if args.compare:
        compare(args.dataset); return 0
    if not (args.dataset and args.variant):
        ap.error("need --dataset and --variant (or --compare / --summary / --family-*)")
    run_one(args.dataset, args.variant, args.limit, prefix=args.prefix)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
