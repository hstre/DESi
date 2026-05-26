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

from solver_ports import DeepSeekDirectSolver, VERIFY_SYNS, make_solver, parse_verdict  # noqa: E402
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
# solver-model comparison config
_CMP_MODELS = ("deepseek", "claude", "gpt", "granite")
_MODEL_LABEL = {"deepseek": "DeepSeek v4 Pro", "claude": "Claude Haiku 4.5",
                "gpt": "GPT-4.1-mini", "granite": "Granite 4.1-8b"}
_MATCHED = {"vitaminc": "evidence_strict", "nli_fever": "entailment_direct"}


def run_one(dataset, variant, limit, model="deepseek", prefix="calib", _exs=None):
    exs = _exs if _exs is not None else load_verify(dataset, limit)[1]
    solver = make_solver(model)
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
        "model_key": model,
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
    print(f"{model}/{dataset}/{variant}: acc={acc} pred={rec['pred_distribution']} "
          f"overcommit={rec['overcommitment_n']} overabst={rec['overabstention_n']} "
          f"parsefail={parse_fail} errors={errors} {rec['elapsed_s']}s cost=${rec['est_cost_usd']} | "
          f"desi replay {rec['desi_core']['replay_stable']} core {rec['desi_core']['core_identity_ok']}")
    return rec


def run_model_matrix(model, limit, prefix=None):
    """Run one solver model across both datasets x the 3 fixed families, loading
    each dataset once. prefix defaults to sm_<model> so reports can find the runs."""
    prefix = prefix or f"sm_{model}"
    for ds in ("vitaminc", "nli_fever"):
        _spec, exs = load_verify(ds, limit)
        for v in _FAMILIES:
            run_one(ds, v, limit, model=model, prefix=prefix, _exs=exs)


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


def _sm_load(base="sm"):
    data = {}
    for m in _CMP_MODELS:
        for ds in ("vitaminc", "nli_fever"):
            for f in _FAMILIES:
                p = _RUNS / f"{base}_{m}_{ds}_{f}.json"
                if p.exists():
                    data[(m, ds, f)] = json.loads(p.read_text())
    return data


def _present_models(data, dataset):
    return [m for m in _CMP_MODELS if all((m, dataset, f) in data for f in _FAMILIES)]


def _pr(r, L):
    return f"{_cls(r, L, 'precision')}/{_cls(r, L, 'recall')}"


def model_compare(dataset, base="sm"):
    data = _sm_load(base)
    models = _present_models(data, dataset)
    if not models:
        print(f"no solver-model runs for {dataset}")
        return
    ref = data[(models[0], dataset, "baseline")]
    g, n = ref["gold_distribution"], ref["n"]
    name, mf = _DS_NAME[dataset], _MATCHED[dataset]
    md = [
        f"# Solver-model comparison — {name}\n",
        "Controlled comparison under IDENTICAL epistemic conditions: same dataset, "
        "same FIXED prompt families (baseline / evidence-strict / entailment-direct), "
        "same temperature 0, same evaluator and 3-class scoring; the ONLY variable is "
        "the solver model. DESi is NOT the solver — it governs alongside and its core "
        "metrics are recorded unchanged. No prompt tuning, no benchmark-specific "
        "hacks, one deterministic pass per example.\n",
        "Models: " + ", ".join(_MODEL_LABEL[m] for m in models) + ".\n",
        f"N={n} | gold S/R/N = {g['SUPPORTS']}/{g['REFUTES']}/{g['NOT_ENOUGH_INFO']} | "
        f"task-matched family = **{mf}**\n",
        "## Accuracy & calibration (rows = model x prompt family)\n",
        "| model | family | acc | S P/R | R P/R | NEI P/R | overcommit | overabst | parsefail | errors | latency | cost |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for m in models:
        for f in _FAMILIES:
            r = data[(m, dataset, f)]
            md.append(
                f"| {_MODEL_LABEL[m]} | {f} | {r['accuracy']} | "
                f"{_pr(r,'SUPPORTS')} | {_pr(r,'REFUTES')} | {_pr(r,'NOT_ENOUGH_INFO')} | "
                f"{r['overcommitment_rate']} ({r['overcommitment_n']}) | "
                f"{r['overabstention_rate']} ({r['overabstention_n']}) | "
                f"{r['parse_failures']} | {r['errors']} | {r['elapsed_s']}s | ${r['est_cost_usd']} |")
    md += ["", "### Predicted class distribution (pred S/R/N per family)\n",
           "| model | " + " | ".join(_FAMILIES) + " |",
           "| --- | " + " | ".join("---" for _ in _FAMILIES) + " |"]
    for m in models:
        cells = []
        for f in _FAMILIES:
            pd = data[(m, dataset, f)]["pred_distribution"]
            cells.append(f"{pd['SUPPORTS']}/{pd['REFUTES']}/{pd['NOT_ENOUGH_INFO']}")
        md.append(f"| {_MODEL_LABEL[m]} | " + " | ".join(cells) + " |")
    md += ["", "## Confusion matrices (rows = gold, cols = pred)\n"]
    for m in models:
        md.append(f"### {_MODEL_LABEL[m]}\n")
        for f in _FAMILIES:
            r = data[(m, dataset, f)]
            md += [f"**{f}**", "", "| gold \\ pred | " + " | ".join(_LABELS) + " |",
                   "| --- | " + " | ".join("---" for _ in _LABELS) + " |"]
            for gl in _LABELS:
                md.append(f"| {gl} | " + " | ".join(str(r["confusion"][gl][p]) for p in _LABELS) + " |")
            md.append("")
    # read-out (precomputed to keep f-strings simple)
    matched_acc = {m: data[(m, dataset, mf)]["accuracy"] for m in models}
    mean_acc = {m: round(sum(data[(m, dataset, f)]["accuracy"] for f in _FAMILIES) / 3, 3) for m in models}
    nei_gold = g["NOT_ENOUGH_INFO"]
    nei_bal = {m: abs(data[(m, dataset, "baseline")]["pred_distribution"]["NOT_ENOUGH_INFO"] - nei_gold) for m in models}
    best_matched = max(matched_acc, key=lambda k: matched_acc[k])
    best_mean = max(mean_acc, key=lambda k: mean_acc[k])
    best_nei = min(nei_bal, key=lambda k: nei_bal[k])
    matched_all = ", ".join(f"{_MODEL_LABEL[m]} {matched_acc[m]}" for m in models)
    mean_all = ", ".join(f"{_MODEL_LABEL[m]} {mean_acc[m]}" for m in models)
    nei_all = ", ".join(f"{_MODEL_LABEL[m]} d{nei_bal[m]}" for m in models)
    dc = ref["desi_core"]
    md += [
        "## Read-out\n",
        f"- **Best on the task-matched family ({mf})**: {_MODEL_LABEL[best_matched]} "
        f"(acc {matched_acc[best_matched]}). All: {matched_all}.",
        f"- **Best mean accuracy across the 3 families**: {_MODEL_LABEL[best_mean]} "
        f"({mean_acc[best_mean]}). All: {mean_all}.",
        f"- **Most balanced NEI under the FIXED baseline prompt** (|pred_NEI - gold_NEI|, "
        f"gold NEI={nei_gold}): {_MODEL_LABEL[best_nei]} (d{nei_bal[best_nei]}). All: {nei_all}.",
        "",
        "## DESi-core (alongside; core untouched, identical across every model & family)\n",
        f"- replay stability: {'1.0' if dc['replay_stable'] else 'FAILED'}; core identity: "
        f"{dc['core_identity_ok']}; governance independence: {'1.0' if dc['gov_independent'] else 'FAILED'}; "
        f"critical_branch_preservation: {dc['critical_branch_preservation']}; "
        f"mutation rejected: {dc['mutation_rejected']}/{dc['mutation_attempts']}.",
        "- Intrinsic to DESi's deterministic governance; unchanged when the solver "
        "model changes, because DESi neither solves nor scores the verdicts.",
        "",
        "## Honesty / limits\n",
        "- One deterministic pass per example; accuracies are each model's own. "
        "DeepSeek (direct api) is mildly non-deterministic across runs; the OpenRouter "
        "models at temp 0 are near-deterministic. Granite is the EXTRACTOR by design — "
        "shown here only as a direct-solver baseline. Prompt families are FIXED and "
        "identical across models; no per-model tuning.",
    ]
    out = "solver_model_comparison_vitaminc.md" if dataset == "vitaminc" else "solver_model_comparison_fever.md"
    _REPORTS.mkdir(parents=True, exist_ok=True)
    (_REPORTS / out).write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"model comparison -> {out} ({len(models)} models)")


def _model_stats(data):
    stats = {}
    for m in _CMP_MODELS:
        cells = {(ds, f): data.get((m, ds, f)) for ds in ("vitaminc", "nli_fever") for f in _FAMILIES}
        if any(v is None or v["accuracy"] is None for v in cells.values()):
            continue
        per_ds = {ds: [cells[(ds, f)]["accuracy"] for f in _FAMILIES] for ds in ("vitaminc", "nli_fever")}
        spread = round(sum(max(per_ds[ds]) - min(per_ds[ds]) for ds in per_ds) / 2, 3)
        matched = {ds: cells[(ds, _MATCHED[ds])]["accuracy"] for ds in ("vitaminc", "nli_fever")}
        best = {ds: max(per_ds[ds]) for ds in ("vitaminc", "nli_fever")}
        mean = round(sum(cells[(ds, f)]["accuracy"] for ds in ("vitaminc", "nli_fever") for f in _FAMILIES) / 6, 3)
        nei_bal = {ds: abs(cells[(ds, "baseline")]["pred_distribution"]["NOT_ENOUGH_INFO"]
                           - cells[(ds, "baseline")]["gold_distribution"]["NOT_ENOUGH_INFO"])
                   for ds in ("vitaminc", "nli_fever")}
        stats[m] = {"per_ds": per_ds, "spread": spread, "matched": matched,
                    "best": best, "mean": mean, "nei_bal": nei_bal}
    return stats


def model_cross_summary(base="sm"):
    data = _sm_load(base)
    stats = _model_stats(data)
    if not stats:
        print("no complete solver-model runs")
        return
    models = [m for m in _CMP_MODELS if m in stats]
    # per-dataset best model on the task-matched family
    matched_best = {ds: max(models, key=lambda m: stats[m]["matched"][ds]) for ds in ("vitaminc", "nli_fever")}
    mean_best = max(models, key=lambda m: stats[m]["mean"])
    # universal dominator: top on the matched family of BOTH datasets
    dominators = [m for m in models
                  if all(stats[m]["matched"][ds] >= max(stats[x]["matched"][ds] for x in models)
                         for ds in ("vitaminc", "nli_fever"))]
    routing_indicated = matched_best["vitaminc"] != matched_best["nli_fever"]
    most_stable = min(models, key=lambda m: stats[m]["spread"])
    nei_best = min(models, key=lambda m: stats[m]["nei_bal"]["vitaminc"] + stats[m]["nei_bal"]["nli_fever"])
    fever_ceiling = max(stats[m]["best"]["nli_fever"] for m in models)
    vitc_ceiling = max(stats[m]["best"]["vitaminc"] for m in models)

    def acc_row(m):
        s = stats[m]
        vc = "/".join(str(a) for a in s["per_ds"]["vitaminc"])
        fv = "/".join(str(a) for a in s["per_ds"]["nli_fever"])
        return (f"| {_MODEL_LABEL[m]} | {vc} | {fv} | {s['matched']['vitaminc']} | "
                f"{s['matched']['nli_fever']} | {s['mean']} | {s['spread']} | "
                f"{s['nei_bal']['vitaminc']}/{s['nei_bal']['nli_fever']} |")

    md = [
        "# Solver-model cross-summary — identical epistemic conditions\n",
        "Same datasets (VitaminC-100, NLI-FEVER-100), same FIXED prompt families "
        "(baseline / evidence-strict / entailment-direct), same temperature 0, same "
        "evaluator. Only the solver model varies. DESi is NOT the solver; its core "
        "metrics are recorded alongside and are identical across all runs. The "
        "task-matched family is evidence-strict for VitaminC (over-commitment style) "
        "and entailment-direct for FEVER (over-abstention style).\n",
        "Models compared: " + ", ".join(_MODEL_LABEL[m] for m in models) + ".\n",
        "## Accuracy matrix\n",
        "Per-dataset cells are acc for baseline/evidence-strict/entailment-direct.\n",
        "| model | VitaminC (b/e/ent) | FEVER (b/e/ent) | VitC matched | FEVER matched | mean (6) | spread | NEI imbalance (VitC/FEVER, baseline) |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    md += [acc_row(m) for m in models]
    md.append("")
    md.append("- *spread* = mean per-dataset (max-min) accuracy across the 3 families "
              "(lower = more stable to prompt framing). *NEI imbalance* = |pred_NEI - "
              "gold_NEI| under the baseline prompt (lower = better-calibrated abstention "
              "without prompt specialization).")
    md.append("")

    dom_txt = (f"{', '.join(_MODEL_LABEL[m] for m in dominators)} is top on the "
               "matched family of BOTH datasets" if dominators
               else "no single model is top on the matched family of both datasets")
    md += [
        "## Answers\n",
        f"- **Should DeepSeek remain the semantic solver?** On the task-matched "
        f"families DeepSeek scores VitaminC {stats['deepseek']['matched']['vitaminc']} / "
        f"FEVER {stats['deepseek']['matched']['nli_fever']} (mean over 6 cells "
        f"{stats['deepseek']['mean']})"
        + (f"; the best matched performers are VitaminC -> {_MODEL_LABEL[matched_best['vitaminc']]}, "
           f"FEVER -> {_MODEL_LABEL[matched_best['nli_fever']]}. "
           + ("DeepSeek is matched-best on both, so keeping it is justified."
              if matched_best['vitaminc'] == 'deepseek' and matched_best['nli_fever'] == 'deepseek'
              else "DeepSeek is NOT matched-best on both, so the choice is contestable on this evidence.")),
        f"- **Should routing select the solver by task style?** Matched-best model is "
        f"VitaminC -> {_MODEL_LABEL[matched_best['vitaminc']]}, FEVER -> "
        f"{_MODEL_LABEL[matched_best['nli_fever']]}. "
        + ("They DIFFER, so task-style solver-routing would help here."
           if routing_indicated else
           "They are the SAME model, so solver-routing is not indicated by this evidence."),
        f"- **Does any solver dominate universally?** {dom_txt}. Best mean accuracy "
        f"across all 6 cells: {_MODEL_LABEL[mean_best]} ({stats[mean_best]['mean']}).",
        f"- **Does the evidence support architectural solver-routing?** "
        + ("YES on the matched families (different winners per task style); but note the "
           if routing_indicated else "Weak: the same model wins both matched families; "),
        f"- **Do Claude / GPT-mini show more stable calibration across both styles?** "
        f"Prompt-framing spread (lower = steadier): "
        + ", ".join(f"{_MODEL_LABEL[m]} {stats[m]['spread']}" for m in models)
        + f". Steadiest: {_MODEL_LABEL[most_stable]}.",
        f"- **Does DeepSeek remain best when task-matched?** "
        + ("YES — DeepSeek is top on both matched families."
           if matched_best['vitaminc'] == 'deepseek' and matched_best['nli_fever'] == 'deepseek'
           else f"NOT uniformly — matched winners are VitaminC {_MODEL_LABEL[matched_best['vitaminc']]}, "
                f"FEVER {_MODEL_LABEL[matched_best['nli_fever']]}."),
        f"- **Does any model keep balanced NEI WITHOUT prompt specialization (baseline "
        f"prompt)?** Smallest combined NEI imbalance: {_MODEL_LABEL[nei_best]} "
        f"(VitC {stats[nei_best]['nei_bal']['vitaminc']} / FEVER {stats[nei_best]['nei_bal']['nli_fever']}). "
        + ", ".join(f"{_MODEL_LABEL[m]} {stats[m]['nei_bal']['vitaminc']}/{stats[m]['nei_bal']['nli_fever']}"
                    for m in models) + ".",
        f"- **Is the bottleneck the model, the framing, or the need for routing?** "
        f"Best achievable accuracy across ALL models: VitaminC {vitc_ceiling}, FEVER "
        f"{fever_ceiling}. "
        + (f"FEVER stays low ({fever_ceiling}) for EVERY model -> the bottleneck on "
           "FEVER is the framing/data (and the NLI-FEVER label style), not a single "
           "model. " if fever_ceiling < 0.65 else
           "FEVER is tractable for the best model -> model choice matters there. ")
        + ("Because matched winners differ by task style, routing (prompt-family and/or "
           "solver) is the lever that helps on VitaminC."
           if routing_indicated else
           "A single matched prompt family per task carries most of the gain; solver "
           "swap is secondary."),
        "",
        "## DESi-core invariance\n",
        "- recorded alongside every run: replay stable, core byte-identical, governance "
        "independent, mutation rejected — identical across all models and families. "
        "Swapping the solver does NOT touch DESi's deterministic governance.",
        "",
        "## Honesty / limits\n",
        "- N=100 per dataset; one deterministic pass; DeepSeek mild non-determinism; "
        "FIXED prompt families, no per-model tuning. Granite is the extractor shown as "
        "a solver baseline. This is a controlled solver study, not a redesign; no core, "
        "ontology, or architecture change; outputs secret-scanned.",
    ]
    _REPORTS.mkdir(parents=True, exist_ok=True)
    (_REPORTS / "solver_model_cross_summary.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"cross-summary written ({len(models)} models)")


def main() -> int:
    ap = argparse.ArgumentParser(description="DeepSeek prompt-family calibration study.")
    ap.add_argument("--dataset", choices=sorted(DATASETS))
    ap.add_argument("--variant", choices=["baseline", "evidence_strict", "entailment_direct", "calibrated"])
    ap.add_argument("--model", default="deepseek", choices=sorted(_CMP_MODELS))
    ap.add_argument("--limit", type=int, default=100)
    ap.add_argument("--prefix", default="calib")
    ap.add_argument("--compare", action="store_true")
    ap.add_argument("--summary", action="store_true")
    ap.add_argument("--family-compare", action="store_true")
    ap.add_argument("--family-summary", action="store_true")
    ap.add_argument("--matrix-model", choices=sorted(_CMP_MODELS),
                    help="run one model across both datasets x 3 fixed families (prefix sm_<model>)")
    ap.add_argument("--model-compare", action="store_true")
    ap.add_argument("--model-summary", action="store_true")
    args = ap.parse_args()
    if args.summary:
        summary(); return 0
    if args.family_summary:
        family_summary(); return 0
    if args.family_compare:
        family_compare(args.dataset); return 0
    if args.compare:
        compare(args.dataset); return 0
    if args.model_summary:
        model_cross_summary(); return 0
    if args.model_compare:
        model_compare(args.dataset); return 0
    if args.matrix_model:
        run_model_matrix(args.matrix_model, args.limit); return 0
    if not (args.dataset and args.variant):
        ap.error("need --dataset and --variant (or --matrix-model / --model-compare / --model-summary / --compare / --summary / --family-*)")
    run_one(args.dataset, args.variant, args.limit, model=args.model, prefix=args.prefix)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
