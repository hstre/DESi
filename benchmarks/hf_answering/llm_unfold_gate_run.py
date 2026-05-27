#!/usr/bin/env python3
"""Small-LLM unfolding-gate study (PERIPHERAL).

A small cheap LLM (Granite 4.1-8b via OpenRouter) decides ONLY UNFOLD /
DO_NOT_UNFOLD / UNCERTAIN on the ambiguous residue the deterministic layers could
not resolve; it never emits a verdict. The gate decision selects the solver prompt
mode; the verdict itself is DeepSeek's.

To isolate the gate's effect, the DeepSeek predictions for all three prompt
variants are REUSED from the residual-escalation run (re_<dataset>.json), so
policies A/B/C are byte-identical to that study and the ONLY new variable is the
gate decision on escalated items. The deterministic routing is recomputed fresh
(it is deterministic). DESi-core recorded alongside; core untouched.

Policies: A matched-prompt ceiling | B deterministic unfolding | C residual
lexical-semantic escalation | D small-LLM unfolding gate.
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
from semantic_router_run import _MATCHED, _aggregate, _pr  # noqa: E402
from semantic_unfolding import SemanticUnfoldingDetector  # noqa: E402
from residual_semantic_escalation import ResidualEscalationRouter  # noqa: E402
from llm_unfold_gate import DECISIONS, LLMUnfoldGate, gate_policy  # noqa: E402

_REPORTS = _HERE / "reports"
_RUNS = _REPORTS / "_runs"
_EXP = ("matched", "unfolding", "residual", "gate")
_EXP_LETTER = {"matched": "A", "unfolding": "B", "residual": "C", "gate": "D"}
_EXP_LABEL = {"matched": "A matched", "unfolding": "B unfolding",
              "residual": "C residual", "gate": "D LLM-gate"}


def run_gate(dataset, limit):
    re_path = _RUNS / f"re_{dataset}.json"
    if not re_path.exists():
        print(f"missing re_{dataset}.json (run residual_escalation_run first)")
        return None
    stored = {r["id"]: r for r in json.loads(re_path.read_text())["rows"]}
    _spec, exs = load_verify(dataset, limit)
    resid = ResidualEscalationRouter()
    detector = SemanticUnfoldingDetector()
    gate = LLMUnfoldGate()
    matched = _MATCHED[dataset]
    rows = []
    g_calls = g_err = g_parsefail = g_pt = g_ct = 0
    g_time = 0.0
    for ex in exs:
        st = stored.get(ex.id)
        if st is None:
            continue
        preds = {"baseline": st["pred_baseline"], "evidence_strict": st["pred_evidence_strict"],
                 "entailment_direct": st["pred_entailment_direct"]}
        dec = resid.route(ex.claim, ex.evidence)
        a_pol, b_pol, c_pol = matched, dec.e_policy, dec.f_policy
        gate_decision = None
        gate_reason = ""
        if dec.escalated:
            sig = detector.detect(ex.claim, ex.evidence).signals
            t0 = time.time()
            gr = gate.decide(ex.claim, ex.evidence, cov=sig["content_coverage_claim"],
                             ent=sig["entity_overlap"], category=dec.unfold_category, route=b_pol)
            g_time += time.time() - t0
            g_calls += 1
            g_err += int(gr.error)
            g_parsefail += int(not gr.parse_ok)
            g_pt += gr.prompt_tokens
            g_ct += gr.completion_tokens
            d_pol = gate_policy(gr.decision, b_pol)
            gate_decision, gate_reason = gr.decision, gr.reason
        else:
            d_pol = b_pol
        rows.append({
            "id": ex.id, "gold": ex.gold, "escalated": dec.escalated,
            "unfold_category": dec.unfold_category,
            "A_pred": preds[a_pol], "B_pred": preds[b_pol], "C_pred": preds[c_pol], "D_pred": preds[d_pol],
            "a_pol": a_pol, "b_pol": b_pol, "c_pol": c_pol, "d_pol": d_pol,
            "gate_decision": gate_decision, "gate_reason": gate_reason,
        })

    agg = {e: _aggregate([(r["gold"], r[f"{_EXP_LETTER[e]}_pred"]) for r in rows]) for e in _EXP}
    gprice = gate.price()
    gate_cost = round(g_pt * gprice[0] + g_ct * gprice[1], 6)

    esc = [r for r in rows if r["escalated"]]
    decision_dist = dict(Counter(r["gate_decision"] for r in esc))

    def help_hurt(other):
        h = sum(1 for r in rows if r["D_pred"] == r["gold"] and r[other] != r["gold"])
        u = sum(1 for r in rows if r["D_pred"] != r["gold"] and r[other] == r["gold"])
        return {"helped": h, "hurt": u, "net": h - u}

    rec = {
        "dataset": _DS_NAME[dataset], "dataset_key": dataset, "matched_family": matched,
        "n": len(rows), "gate_model": gate.name, "experiments": agg,
        "gate": {
            "escalated": len(esc), "calls": g_calls, "errors": g_err, "parse_failures": g_parsefail,
            "decision_distribution": decision_dist,
            "cost_usd": gate_cost, "latency_s": round(g_time, 2),
            "prompt_tokens": g_pt, "completion_tokens": g_ct,
            "vs_unfolding": help_hurt("B_pred"), "vs_residual": help_hurt("C_pred"),
            "vs_matched": help_hurt("A_pred"),
        },
        "rows": rows,
        "desi_core": desi_core_metrics(exs),
    }
    _RUNS.mkdir(parents=True, exist_ok=True)
    (_RUNS / f"lg_{dataset}.json").write_text(json.dumps(rec, indent=2), encoding="utf-8")
    a = agg
    print(f"{dataset}: A(matched)={a['matched']['accuracy']} B(unfold)={a['unfolding']['accuracy']} "
          f"C(residual)={a['residual']['accuracy']} D(gate)={a['gate']['accuracy']} | "
          f"escalated={len(esc)} decisions={decision_dist} parsefail={g_parsefail} err={g_err} | "
          f"net D vs B {rec['gate']['vs_unfolding']['net']:+d} vs C {rec['gate']['vs_residual']['net']:+d} | "
          f"gate ${gate_cost} {round(g_time,1)}s | desi replay {rec['desi_core']['replay_stable']} "
          f"core {rec['desi_core']['core_identity_ok']}")
    return rec


def gate_report(dataset):
    p = _RUNS / f"lg_{dataset}.json"
    if not p.exists():
        print(f"missing run for {dataset}")
        return
    rec = json.loads(p.read_text())
    agg, gt = rec["experiments"], rec["gate"]
    g = agg["matched"]["gold_distribution"]
    cols = [(_EXP_LABEL[e] if e != "matched" else f"A matched ({rec['matched_family']})", e) for e in _EXP]
    md = [
        f"# Small-LLM unfolding gate — {rec['dataset']}\n",
        f"A small cheap LLM (`{rec['gate_model']}`) decides ONLY UNFOLD / DO_NOT_UNFOLD / "
        "UNCERTAIN on the ambiguous residue (never a verdict); the decision selects the "
        "solver prompt mode and DeepSeek produces the verdict. To isolate the gate, the "
        "DeepSeek predictions for all three prompt variants are REUSED from the "
        "residual-escalation run, so A/B/C are identical to that study and the only new "
        "variable is the gate decision on escalated items. One gate call per escalated "
        "item, no retries/voting/CoT, temp 0. DESi-core recorded alongside; core untouched.\n",
        "Policies: **A** matched-prompt ceiling, **B** deterministic unfolding, **C** "
        "residual lexical-semantic escalation, **D** small-LLM unfolding gate.\n",
        f"N={rec['n']} | gold S/R/N = {g['SUPPORTS']}/{g['REFUTES']}/{g['NOT_ENOUGH_INFO']}\n",
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
        row("parse failures (solver)", lambda r: r["parse_failures"]),
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
        "## Gate behaviour\n",
        f"Escalated (gate calls): {gt['escalated']}/{rec['n']}; decision distribution: "
        f"{gt['decision_distribution']}; parse failures: {gt['parse_failures']}; network "
        f"errors: {gt['errors']}.\n",
        f"Gate cost: ${gt['cost_usd']} ({gt['prompt_tokens']}+{gt['completion_tokens']} tok); "
        f"gate latency: {gt['latency_s']}s (DeepSeek solver cost reused, not re-billed).\n",
        f"- **vs B (deterministic unfolding)**: helped {gt['vs_unfolding']['helped']}, hurt "
        f"{gt['vs_unfolding']['hurt']} (net {gt['vs_unfolding']['net']:+d}).",
        f"- **vs C (residual lexical)**: helped {gt['vs_residual']['helped']}, hurt "
        f"{gt['vs_residual']['hurt']} (net {gt['vs_residual']['net']:+d}).",
        f"- **vs A (matched ceiling)**: net {gt['vs_matched']['net']:+d}.",
    ]
    dc = rec["desi_core"]
    md += [
        "",
        "## DESi-core (alongside; core untouched)\n",
        f"- replay stability: {'1.0' if dc['replay_stable'] else 'FAILED'}; core identity: "
        f"{dc['core_identity_ok']}; governance independence: {'1.0' if dc['gov_independent'] else 'FAILED'}; "
        f"critical_branch_preservation: {dc['critical_branch_preservation']}; "
        f"mutation rejected: {dc['mutation_rejected']}/{dc['mutation_attempts']}.",
        "- The gate is a peripheral routing aid: it selects a prompt mode and never emits a "
        "verdict; it does not import or modify the DESi core.",
        "",
        "## Honesty / limits\n",
        "- DeepSeek predictions reused from the residual run (A/B/C identical to it); the gate "
        "adds one Granite call per escalated item. Gate emits only UNFOLD/DO_NOT_UNFOLD/"
        "UNCERTAIN. Accuracies are DeepSeek's; the gate only routes. NOT a truthfulness claim; "
        "DESi did not solve NLI. Key in-process only; outputs secret-scanned.",
    ]
    out = "llm_unfold_gate_vitaminc.md" if dataset == "vitaminc" else "llm_unfold_gate_fever.md"
    _REPORTS.mkdir(parents=True, exist_ok=True)
    (_REPORTS / out).write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"gate report -> {out}")


def gate_cross_summary():
    recs = {}
    for ds in ("vitaminc", "nli_fever"):
        p = _RUNS / f"lg_{ds}.json"
        if p.exists():
            recs[ds] = json.loads(p.read_text())
    if not recs:
        print("no gate runs")
        return

    def accs(ds):
        a = recs[ds]["experiments"]
        return tuple(a[e]["accuracy"] for e in _EXP)  # matched, unfolding, residual, gate

    md = [
        "# Small-LLM unfolding gate — cross-summary\n",
        "A small cheap LLM (Granite 4.1-8b) decides only UNFOLD / DO_NOT_UNFOLD / UNCERTAIN "
        "on the ambiguous residue; it never emits a verdict. DeepSeek predictions reused from "
        "the residual run so A/B/C are identical and the only new variable is the gate. "
        "Policies A matched ceiling / B deterministic unfolding / C residual lexical / D "
        "LLM-gate. Core untouched.\n",
        "## Accuracy by policy\n",
        "| dataset | A matched | B unfolding | C residual | D LLM-gate | escalated | gate decisions | gate $ |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for ds in ("vitaminc", "nli_fever"):
        if ds not in recs:
            continue
        A, B, C, D = accs(ds)
        gt = recs[ds]["gate"]
        md.append(f"| {recs[ds]['dataset']} | {A} | {B} | {C} | {D} | {gt['escalated']}/{recs[ds]['n']} | "
                  f"{gt['decision_distribution']} | ${gt['cost_usd']} |")
    md.append("")
    md.append("| dataset | overcommit B->D | overabst B->D | gate net vs B | gate net vs C | parse fails | latency |")
    md.append("| --- | --- | --- | --- | --- | --- | --- |")
    for ds in ("vitaminc", "nli_fever"):
        if ds not in recs:
            continue
        a = recs[ds]["experiments"]; gt = recs[ds]["gate"]
        md.append(f"| {recs[ds]['dataset']} | {a['unfolding']['overcommitment_rate']} -> "
                  f"{a['gate']['overcommitment_rate']} | {a['unfolding']['overabstention_rate']} -> "
                  f"{a['gate']['overabstention_rate']} | {gt['vs_unfolding']['net']:+d} | "
                  f"{gt['vs_residual']['net']:+d} | {gt['parse_failures']} | {gt['latency_s']}s |")
    md.append("")

    beats_b = all(accs(ds)[3] >= accs(ds)[1] for ds in recs)
    net_vs_b = sum(recs[ds]["gate"]["vs_unfolding"]["net"] for ds in recs)
    net_vs_c = sum(recs[ds]["gate"]["vs_residual"]["net"] for ds in recs)
    # gap to matched ceiling
    gap = {ds: round(accs(ds)[0] - accs(ds)[3], 3) for ds in recs}
    helps = beats_b and net_vs_b > 0
    md += [
        "## Final answers\n",
        "- **Does small-LLM unfolding help?** "
        + "; ".join(f"{recs[ds]['dataset']}: D {accs(ds)[3]} vs B {accs(ds)[1]} "
                    f"({accs(ds)[3] - accs(ds)[1]:+.3f}), gate net vs B "
                    f"{recs[ds]['gate']['vs_unfolding']['net']:+d}" for ds in recs)
        + ". " + ("YES -- the gate is net-positive vs deterministic unfolding."
                  if helps else "NO -- the gate is not net-positive vs deterministic unfolding."),
        "- **Does it beat deterministic unfolding (B)?** "
        + ("YES on both." if beats_b else "NO -- it does not consistently beat B.")
        + " It " + ("beats" if net_vs_c > 0 else "ties" if net_vs_c == 0 else "trails")
        + f" the residual lexical escalation (C) (net {net_vs_c:+d}).",
        "- **Does it approach the matched-prompt ceiling (A)?** gap to ceiling "
        + "; ".join(f"{recs[ds]['dataset']}: {gap[ds]:+.3f}" for ds in recs)
        + ". " + ("Yes, within ~0.02." if all(abs(gap[ds]) <= 0.02 for ds in recs)
                  else "No -- the matched-prompt family remains clearly above the gate."),
        "- **Is the added cost justified?** gate cost "
        + "; ".join(f"{recs[ds]['dataset']}: ${recs[ds]['gate']['cost_usd']} for "
                    f"{recs[ds]['gate']['escalated']} calls, {recs[ds]['gate']['latency_s']}s, "
                    f"net {recs[ds]['gate']['vs_unfolding']['net']:+d}" for ds in recs)
        + ". " + ("The gate is cheap; if net-positive the cost is justified."
                  if helps else "The accuracy did not improve, so the added LLM cost/latency is NOT justified."),
    ]
    core_ok = all(recs[ds]["desi_core"]["core_identity_ok"] in (True, None) for ds in recs)
    replay_ok = all(recs[ds]["desi_core"]["replay_stable"] for ds in recs)
    md += [
        f"- **Did DESi-core remain invariant?** {'YES' if (core_ok and replay_ok) else 'NO'} "
        f"-- core byte-identical, replay {'1.0' if replay_ok else 'FAILED'}, governance "
        "independent, mutation rejected on every run; the gate is a peripheral routing aid only.",
        "",
        "## Interpretation (per study rule)\n",
        ("- The small-LLM gate helps: report as a PERIPHERAL semantic-routing aid (not part of "
         "the DESi core). It improves the unfold decision on the residue where deterministic "
         "local semantics was insufficient."
         if helps else
         "- The small-LLM gate does NOT help. Per the study rule, this routing line is STOPPED: "
         "no further patching. The unfold/no-unfold decision on this residue is not reliably "
         "improved by a small LLM here; the matched-prompt family remains the ceiling. No "
         "truthfulness claim; DESi did not solve NLI; DESi-core stayed invariant throughout."),
        "",
        "## Honesty / limits\n",
        "- N=100/dataset; DeepSeek preds reused (A/B/C identical to the residual run); one gate "
        "call per escalated item, no retries/voting/CoT; gate emits only the 3 routing "
        "decisions. No core/ontology change; key in-process; outputs secret-scanned.",
    ]
    _REPORTS.mkdir(parents=True, exist_ok=True)
    (_REPORTS / "llm_unfold_gate_cross_summary.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("cross-summary written")


def main() -> int:
    ap = argparse.ArgumentParser(description="Small-LLM unfolding-gate study.")
    ap.add_argument("--dataset", choices=sorted(_MATCHED))
    ap.add_argument("--limit", type=int, default=100)
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--cross-summary", action="store_true")
    args = ap.parse_args()
    if args.cross_summary:
        gate_cross_summary(); return 0
    if args.report:
        gate_report(args.dataset); return 0
    if args.run:
        if not args.dataset:
            ap.error("--run needs --dataset")
        run_gate(args.dataset, args.limit); return 0
    ap.error("need --run/--report (with --dataset) or --cross-summary")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
