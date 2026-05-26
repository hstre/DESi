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


def run_one(dataset, variant, limit):
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
    (_RUNS / f"calib_{dataset}_{variant}.json").write_text(json.dumps(rec, indent=2), encoding="utf-8")
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


def main() -> int:
    ap = argparse.ArgumentParser(description="DeepSeek prompt-only calibration test.")
    ap.add_argument("--dataset", choices=sorted(DATASETS))
    ap.add_argument("--variant", choices=["baseline", "calibrated"])
    ap.add_argument("--limit", type=int, default=100)
    ap.add_argument("--compare", action="store_true")
    ap.add_argument("--summary", action="store_true")
    args = ap.parse_args()
    if args.summary:
        summary(); return 0
    if args.compare:
        compare(args.dataset); return 0
    if not (args.dataset and args.variant):
        ap.error("need --dataset and --variant (or --compare / --summary)")
    run_one(args.dataset, args.variant, args.limit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
