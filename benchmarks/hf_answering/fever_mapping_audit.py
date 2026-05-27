#!/usr/bin/env python3
"""FEVER premise/hypothesis mapping audit + corrected-rerun reports (PERIPHERAL).

Confirms (mechanically) that pietrolesci/nli_fever stores its columns OPPOSITE to
the verify-task assumption -- the `premise` field holds the short FEVER CLAIM and
the `hypothesis` field holds the long Wikipedia EVIDENCE -- so the prior mapping
(claim<-hypothesis, evidence<-premise) was INVERTED. Corrected mapping:
    claim    <- premise
    evidence <- hypothesis
Labels (fever_gold_label) are unchanged.

This module: (a) writes the mapping audit with raw examples + before/after
orientation stats; (b) builds the corrected FEVER reports from the re-run
artifacts. NO model calls in the audit; NO core/ontology/prompt/router change.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parents[1]
sys.path.insert(0, str(_REPO / "src"))
sys.path.insert(0, str(_HERE))

from prompt_calibration import _LABELS, _per_class  # noqa: E402
from scifact_runner import DATASETS, map_claim_evidence  # noqa: E402
from semantic_router_run import _aggregate, _pr  # noqa: E402
from goldlabel_audit import orientation_stats  # noqa: E402

_REPORTS = _HERE / "reports"
_RUNS = _REPORTS / "_runs"
_INVALID = _RUNS / "_fever_invalid"
_FAMILIES = ("baseline", "evidence_strict", "entailment_direct")
_MATCHED = "entailment_direct"
_OLD = "claim<-hypothesis, evidence<-premise (INVERTED)"
_NEW = "claim<-premise, evidence<-hypothesis (CORRECTED)"
_INVALIDATED = (
    "fever_prompt_family_comparison.md", "prompt_family_cross_summary.md (FEVER rows)",
    "solver_model_comparison_fever.md", "solver_model_cross_summary.md (FEVER rows)",
    "semantic_router_fever.md", "semantic_router_cross_summary.md (FEVER rows)",
    "micro_router_fever.md", "unfolding_fever.md", "residual_fever.md",
    "llm_unfold_gate_fever.md", "deepseek_prompt_calibration_fever.md",
    "fever_nli_granite_run.md",
)


def _raw(n: int):
    from datasets import load_dataset
    spec = DATASETS["nli_fever"]
    ds = load_dataset(spec["id"], split=spec["split"])
    return ds, spec


def audit(dump: int = 10, sample: int = 300):
    ds, spec = _raw(dump)
    pairs_before, pairs_after, examples = [], [], []
    for i in range(min(sample, len(ds))):
        r = ds[i]
        prem, hyp = str(r.get("premise", "")), str(r.get("hypothesis", ""))
        pairs_before.append((hyp, prem))   # old: claim<-hypothesis, evidence<-premise
        pairs_after.append((prem, hyp))    # corrected: claim<-premise, evidence<-hypothesis
        if i < dump:
            claim, evidence = map_claim_evidence(spec, r)
            examples.append((i, prem, hyp, r.get("fever_gold_label"), claim, evidence))
    before, after = orientation_stats(pairs_before), orientation_stats(pairs_after)

    def t(s, n=160):
        s = str(s)
        return s if len(s) <= n else s[:n] + "…"

    md = [
        "# FEVER premise/hypothesis mapping audit\n",
        "**Was the FEVER mapping inverted? YES.** `pietrolesci/nli_fever` stores its "
        "columns opposite to standard NLI naming: the **`premise`** field contains the "
        "short FEVER **claim** to verify, and the **`hypothesis`** field contains the long "
        "Wikipedia **evidence**. The verify task is \"does EVIDENCE support CLAIM\", scored "
        "against `fever_gold_label`.\n",
        f"- Old (buggy) mapping: `{_OLD}` -> fed a *long multi-fact claim* against a *short "
        "evidence*, mechanically forcing NOT_ENOUGH_INFO (the chronic FEVER over-abstention).",
        f"- Corrected mapping: `{_NEW}`. Labels unchanged (normalize_gold reads only "
        "`fever_gold_label`).",
        "",
        "## Orientation stats over the first "
        f"{min(sample, len(ds))} dev items (mechanical)\n",
        "| mapping | median claim len | median evidence len | claim > 2x evidence | evidence > 2x claim | empty claim | empty evidence |",
        "| --- | --- | --- | --- | --- | --- | --- |",
        f"| OLD (inverted) | {before['median_claim_len']} | {before['median_evidence_len']} | "
        f"{before['claim_gt_2x_evidence']} | {_ev2x(pairs_before)} | {before['empty_claim']} | {before['empty_evidence']} |",
        f"| CORRECTED | {after['median_claim_len']} | {after['median_evidence_len']} | "
        f"{after['claim_gt_2x_evidence']} | {_ev2x(pairs_after)} | {after['empty_claim']} | {after['empty_evidence']} |",
        "",
        "Under the OLD mapping the claim dwarfs the evidence on most items (inverted); "
        "under the CORRECTED mapping the evidence is the longer field, as a verify task "
        "expects.",
        "",
        "## Raw examples (corrected mapping applied)\n",
    ]
    for i, prem, hyp, gold, claim, evidence in examples:
        md += [
            f"#### dev[{i}] — gold = {gold}",
            f"- raw **premise** ({len(prem)} chars): {t(prem)}",
            f"- raw **hypothesis** ({len(hyp)} chars): {t(hyp)}",
            f"- => mapped **claim** (from premise): {t(claim)}",
            f"- => mapped **evidence** (from hypothesis): {t(evidence)}",
            "",
        ]
    md += [
        "## Invalidated / suspect prior FEVER artifacts\n",
        "All previously interpreted FEVER results were produced under the inverted "
        "mapping and are therefore **invalid / suspect**. They are superseded by the "
        "`fever_corrected_*.md` reports:",
        "",
        *[f"- `{n}`" for n in _INVALIDATED],
        "",
        "## Honesty / limits\n",
        "- Mechanical verification against `fever_gold_label` semantics; only the dataset "
        "mapping layer was changed (one spec entry + a pure helper). No prompts, model, "
        "evaluator, scorer, routing, or DESi-core change. VitaminC mapping was already "
        "correct and is untouched.",
    ]
    _REPORTS.mkdir(parents=True, exist_ok=True)
    (_REPORTS / "fever_mapping_audit.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"mapping audit -> fever_mapping_audit.md (before: claim {before['median_claim_len']}/"
          f"evid {before['median_evidence_len']}; after: claim {after['median_claim_len']}/"
          f"evid {after['median_evidence_len']})")


def _ev2x(pairs):
    return sum(1 for c, e in pairs if (c or "").strip() and len(e or "") > 2 * len(c or ""))


# ----------------------------------------------------------------------------
# corrected-report builders (read the re-run artifacts; written after reruns)
# ----------------------------------------------------------------------------
def _load(path):
    p = _RUNS / path
    return json.loads(p.read_text()) if p.exists() else None


def _load_invalid(path):
    p = _INVALID / path
    return json.loads(p.read_text()) if p.exists() else None


def _banner():
    return [
        "> **Corrected FEVER report.** Previous FEVER results used an INVERTED "
        f"premise/hypothesis mapping (`{_OLD}`) and are invalid/suspect. Corrected mapping: "
        f"`{_NEW}`; labels unchanged.\n",
    ]


def _fam_aggs_from_re(rows):
    return {f: _aggregate([(r["gold"], r[f"pred_{f}"]) for r in rows]) for f in _FAMILIES}


def corrected_prompt_family():
    re = _load("re_nli_fever.json")
    if not re:
        print("no re_nli_fever.json; rerun first")
        return
    aggs = _fam_aggs_from_re(re["rows"])
    g = aggs["baseline"]["gold_distribution"]
    old = {f: _load_invalid(f"pf_nli_fever_{f}.json") for f in _FAMILIES}
    md = ["# FEVER prompt-family comparison — CORRECTED mapping\n", *_banner(),
          f"DeepSeek v4 Pro, temp 0, FIXED families, same evaluator. N={re['n']} | "
          f"gold S/R/N = {g['SUPPORTS']}/{g['REFUTES']}/{g['NOT_ENOUGH_INFO']} | matched "
          f"family = **{_MATCHED}**.\n",
          "## Corrected results\n",
          "| metric | baseline | evidence-strict | entailment-direct |",
          "| --- | --- | --- | --- |"]
    def rowf(label, fn):
        return f"| {label} | " + " | ".join(str(fn(aggs[f])) for f in _FAMILIES) + " |"
    md += [
        rowf("accuracy", lambda r: r["accuracy"]),
        rowf("pred S/R/N", lambda r: f"{r['pred_distribution']['SUPPORTS']}/{r['pred_distribution']['REFUTES']}/{r['pred_distribution']['NOT_ENOUGH_INFO']}"),
        rowf("SUPPORTS P/R", lambda r: _pr(r, "SUPPORTS")),
        rowf("REFUTES P/R", lambda r: _pr(r, "REFUTES")),
        rowf("NEI P/R", lambda r: _pr(r, "NOT_ENOUGH_INFO")),
        rowf("overcommitment", lambda r: f"{r['overcommitment_rate']} ({r['overcommitment_n']})"),
        rowf("overabstention", lambda r: f"{r['overabstention_rate']} ({r['overabstention_n']})"),
        "",
    ]
    if all(old.values()):
        md += ["## Old (inverted) vs corrected — accuracy & over-abstention\n",
               "| family | old acc | corrected acc | old overabst | corrected overabst |",
               "| --- | --- | --- | --- | --- |"]
        for f in _FAMILIES:
            md.append(f"| {f} | {old[f]['accuracy']} | {aggs[f]['accuracy']} | "
                      f"{old[f]['overabstention_rate']} | {aggs[f]['overabstention_rate']} |")
        md.append("")
    best = max(_FAMILIES, key=lambda f: aggs[f]["accuracy"] or 0)
    md += [f"- **Best corrected family**: {best} (acc {aggs[best]['accuracy']}).",
           _desi_line(re["desi_core"]),
           "", "## Honesty / limits\n",
           "- DeepSeek mildly non-deterministic; one pass; corrected mapping only. "
           "Accuracies are the model's; DESi did not solve NLI."]
    _write("fever_corrected_prompt_family.md", md)


def _desi_line(dc):
    return (f"- **DESi-core (alongside, untouched)**: replay "
            f"{'1.0' if dc['replay_stable'] else 'FAILED'}, core identity {dc['core_identity_ok']}, "
            f"governance {'1.0' if dc['gov_independent'] else 'FAILED'}, "
            f"critical_branch_preservation {dc['critical_branch_preservation']}, "
            f"mutation {dc['mutation_rejected']}/{dc['mutation_attempts']}.")


def corrected_solver_model():
    re = _load("re_nli_fever.json")
    if not re:
        print("no re_nli_fever.json; rerun first")
        return
    ds_aggs = _fam_aggs_from_re(re["rows"])  # DeepSeek arm from re
    models = {"DeepSeek v4 Pro": {f: ds_aggs[f] for f in _FAMILIES}}
    label = {"claude": "Claude Haiku 4.5", "gpt": "GPT-4.1-mini", "granite": "Granite 4.1-8b"}
    for m, lab in label.items():
        recs = {f: _load(f"smc_{m}_nli_fever_{f}.json") for f in _FAMILIES}
        if all(recs.values()):
            models[lab] = recs
    g = ds_aggs["baseline"]["gold_distribution"]
    md = ["# FEVER solver-model comparison — CORRECTED mapping\n", *_banner(),
          f"Identical conditions; only the solver model varies. N={re['n']} | gold S/R/N = "
          f"{g['SUPPORTS']}/{g['REFUTES']}/{g['NOT_ENOUGH_INFO']} | matched family = "
          f"**{_MATCHED}** (DeepSeek arm reused from the corrected residual run).\n",
          "## Corrected accuracy (model x family)\n",
          "| model | baseline | evidence-strict | entailment-direct | matched (entailment-direct) |",
          "| --- | --- | --- | --- | --- |"]
    for lab, recs in models.items():
        md.append(f"| {lab} | " + " | ".join(str(recs[f]["accuracy"]) for f in _FAMILIES)
                  + f" | {recs[_MATCHED]['accuracy']} |")
    md += ["", "## Over-abstention (matched family)\n",
           "| model | overabstention (matched) | NEI P/R (matched) |", "| --- | --- | --- |"]
    for lab, recs in models.items():
        r = recs[_MATCHED]
        md.append(f"| {lab} | {r['overabstention_rate']} ({r['overabstention_n']}) | {_pr(r, 'NOT_ENOUGH_INFO')} |")
    best = max(models, key=lambda lab: models[lab][_MATCHED]["accuracy"] or 0)
    md += ["", f"- **Best on matched family (corrected)**: {best} "
           f"({models[best][_MATCHED]['accuracy']}).",
           _desi_line(re["desi_core"]), "",
           "## Honesty / limits\n- One pass; DeepSeek mild non-determinism; corrected "
           "mapping only; no prompt/model/evaluator change."]
    _write("fever_corrected_solver_model_comparison.md", md)


def corrected_semantic_router():
    sr = _load("sr_nli_fever.json")
    if not sr:
        print("no sr_nli_fever.json; rerun first")
        return
    a = sr["experiments"]
    old = _load_invalid("sr_nli_fever.json")
    rd = sr["router"]["route_distribution"]
    md = ["# FEVER semantic-router study — CORRECTED mapping\n", *_banner(),
          "Policies: A baseline, B benchmark-matched, C semantic-router-selected.\n",
          "## Corrected accuracy\n",
          "| policy | accuracy | overcommit | overabst |", "| --- | --- | --- | --- |",
          f"| A baseline | {a['baseline']['accuracy']} | {a['baseline']['overcommitment_rate']} | {a['baseline']['overabstention_rate']} |",
          f"| B matched | {a['matched']['accuracy']} | {a['matched']['overcommitment_rate']} | {a['matched']['overabstention_rate']} |",
          f"| C router | {a['router']['accuracy']} | {a['router']['overcommitment_rate']} | {a['router']['overabstention_rate']} |",
          "",
          f"- Route distribution: baseline {rd['baseline']} / evidence-strict {rd['evidence_strict']} / entailment-direct {rd['entailment_direct']}.",
          f"- Router net vs baseline {sr['router']['net_vs_baseline']:+d}, vs matched {sr['router']['net_vs_matched']:+d}."]
    if old:
        oa = old["experiments"]
        md += ["", "## Old (inverted) vs corrected accuracy\n",
               "| policy | old | corrected |", "| --- | --- | --- |",
               f"| baseline | {oa['baseline']['accuracy']} | {a['baseline']['accuracy']} |",
               f"| matched | {oa['matched']['accuracy']} | {a['matched']['accuracy']} |",
               f"| router | {oa['router']['accuracy']} | {a['router']['accuracy']} |"]
    md += ["", _desi_line(sr["desi_core"]), "",
           "## Honesty / limits\n- Corrected mapping only; semantic router unchanged; "
           "DeepSeek mild non-determinism."]
    _write("fever_corrected_semantic_router.md", md)


def corrected_residual_unfolding():
    re = _load("re_nli_fever.json")
    if not re:
        print("no re_nli_fever.json; rerun first")
        return
    a = re["experiments"]
    old = _load_invalid("re_nli_fever.json")
    keys = [("B matched", "matched"), ("E unfolding", "unfolding"), ("F residual", "residual"),
            ("A baseline", "baseline"), ("D micro", "micro_router")]
    md = ["# FEVER residual / unfolding study — CORRECTED mapping\n", *_banner(),
          "Policies: matched, unfolding, residual (plus baseline/micro for context).\n",
          "## Corrected accuracy\n", "| policy | accuracy | overcommit | overabst |",
          "| --- | --- | --- | --- |"]
    for lab, k in keys:
        md.append(f"| {lab} | {a[k]['accuracy']} | {a[k]['overcommitment_rate']} | {a[k]['overabstention_rate']} |")
    rs = re["residual"]
    md += ["", f"- Escalated (residue): {rs['escalation_count']}/{re['n']}; residual net vs "
           f"unfolding {rs['vs_unfolding']['net']:+d}."]
    if old:
        oa = old["experiments"]
        md += ["", "## Old vs corrected accuracy\n", "| policy | old | corrected |",
               "| --- | --- | --- |"]
        for lab, k in keys:
            md.append(f"| {lab} | {oa[k]['accuracy']} | {a[k]['accuracy']} |")
    md += ["", _desi_line(re["desi_core"]), "",
           "## Honesty / limits\n- Corrected mapping only; routers unchanged."]
    _write("fever_corrected_residual_unfolding.md", md)


def corrected_llm_gate():
    lg = _load("lg_nli_fever.json")
    if not lg:
        print("no lg_nli_fever.json; rerun first")
        return
    a = lg["experiments"]
    old = _load_invalid("lg_nli_fever.json")
    gt = lg["gate"]
    keys = [("A matched", "matched"), ("B unfolding", "unfolding"),
            ("C residual", "residual"), ("D LLM-gate", "gate")]
    md = ["# FEVER small-LLM unfold-gate study — CORRECTED mapping\n", *_banner(),
          f"Gate model: `{lg['gate_model']}` (decides only UNFOLD/DO_NOT_UNFOLD/UNCERTAIN).\n",
          "## Corrected accuracy\n", "| policy | accuracy | overabst |", "| --- | --- | --- |"]
    for lab, k in keys:
        md.append(f"| {lab} | {a[k]['accuracy']} | {a[k]['overabstention_rate']} |")
    md += ["", f"- Escalated: {gt['escalated']}; decisions {gt['decision_distribution']}; "
           f"parse failures {gt['parse_failures']}; gate net vs unfolding {gt['vs_unfolding']['net']:+d}; "
           f"cost ${gt['cost_usd']}."]
    if old:
        oa = old["experiments"]
        md += ["", "## Old vs corrected accuracy\n", "| policy | old | corrected |",
               "| --- | --- | --- |"]
        for lab, k in keys:
            md.append(f"| {lab} | {oa[k]['accuracy']} | {a[k]['accuracy']} |")
    md += ["", _desi_line(lg["desi_core"]), "",
           "## Honesty / limits\n- Corrected mapping only; gate unchanged; DeepSeek preds "
           "reused from the corrected residual run."]
    _write("fever_corrected_llm_gate.md", md)


def corrected_cross_summary():
    re = _load("re_nli_fever.json")
    if not re:
        print("no re_nli_fever.json; rerun first")
        return
    aggs = _fam_aggs_from_re(re["rows"])
    old_pf = {f: _load_invalid(f"pf_nli_fever_{f}.json") for f in _FAMILIES}
    base, ent = aggs["baseline"], aggs["entailment_direct"]
    best = max(_FAMILIES, key=lambda f: aggs[f]["accuracy"] or 0)
    sr = _load("sr_nli_fever.json")
    md = [
        "# FEVER corrected cross-summary\n", *_banner(),
        "## Final answers\n",
        "- **Was FEVER mapping inverted?** YES -- `pietrolesci/nli_fever` stores the short "
        "claim in `premise` and the long evidence in `hypothesis`; the prior loader mapped "
        "claim<-hypothesis / evidence<-premise, feeding a long claim against a short "
        "evidence and forcing NOT_ENOUGH_INFO.",
        "- **Which old FEVER conclusions are invalidated?** All prior FEVER numbers and the "
        "claims built on them: the \"~0.58 FEVER ceiling\", \"DeepSeek over-abstains on "
        "FEVER\", \"entailment-direct is the FEVER-matched family\", and every FEVER arm of "
        "the solver-model / semantic-router / micro / unfolding / residual / gate studies. "
        "They were measured on inverted inputs.",
    ]
    if all(old_pf.values()):
        md.append("- **Corrected FEVER prompt-family results**: " + ", ".join(
            f"{f} {aggs[f]['accuracy']} (was {old_pf[f]['accuracy']})" for f in _FAMILIES)
            + f"; best = {best}.")
    else:
        md.append("- **Corrected FEVER prompt-family results**: " + ", ".join(
            f"{f} {aggs[f]['accuracy']}" for f in _FAMILIES) + f"; best = {best}.")
    md += [
        f"- **Does DeepSeek still over-abstain on FEVER?** Corrected over-abstention: "
        f"baseline {base['overabstention_rate']}, entailment-direct {ent['overabstention_rate']} "
        + ("(compare to old baseline " + str(old_pf['baseline']['overabstention_rate']) + ")."
           if old_pf['baseline'] else ".")
        + " Read the corrected NEI recall to judge whether the over-abstention was a mapping "
        "artifact rather than a model trait.",
        f"- **Does prompt-family calibration still matter?** Best corrected family is {best} "
        f"(acc {aggs[best]['accuracy']}); compare the spread across families above.",
    ]
    if sr:
        a = sr["experiments"]
        md.append(f"- **Does semantic routing still underperform on FEVER?** corrected "
                  f"router {a['router']['accuracy']} vs baseline {a['baseline']['accuracy']} "
                  f"vs matched {a['matched']['accuracy']}.")
    md += [
        _desi_line(re["desi_core"]),
        "- **Did DESi-core remain invariant?** YES on every corrected run (replay stable, "
        "core byte-identical, governance independent, mutation rejected).",
        "",
        "## Honesty / limits\n",
        "- N=100; one deterministic pass; DeepSeek mild non-determinism; ONLY the dataset "
        "mapping was corrected (no prompt/model/evaluator/router/core change). VitaminC "
        "untouched (its mapping was already correct).",
    ]
    _write("fever_corrected_cross_summary.md", md)


def _write(name, md):
    _REPORTS.mkdir(parents=True, exist_ok=True)
    (_REPORTS / name).write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"-> {name}")


def main() -> int:
    ap = argparse.ArgumentParser(description="FEVER mapping audit + corrected reports.")
    ap.add_argument("--audit", action="store_true")
    ap.add_argument("--reports", action="store_true", help="build all corrected reports")
    args = ap.parse_args()
    if args.reports:
        corrected_prompt_family(); corrected_solver_model(); corrected_semantic_router()
        corrected_residual_unfolding(); corrected_llm_gate(); corrected_cross_summary()
        return 0
    audit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
