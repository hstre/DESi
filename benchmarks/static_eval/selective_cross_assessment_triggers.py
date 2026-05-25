#!/usr/bin/env python3
"""Selective cross-assessment TRIGGER analysis (offline, no API calls).

Counts how often each epistemic-risk signal fires on the P12 live limit-100 run,
to size a SELECTIVE cross-assessment layer against an always-judge baseline. It
does NOT run any cross-assessment, makes no model calls, and produces no new
truthfulness numbers — only routing/trigger statistics.

Triggers are classified (a design decision, see the architecture plan):
  * ACTIVATE : fire a cross-assessment (genuine, rare epistemic ambiguity).
  * LOG      : record for audit, do not fire (too frequent / already-decided / soft).
  * DISCARD  : not an ambiguity signal (confident-resolved or structural).

Inputs (read-only): the P12 live records + claim graph, and the P13 deterministic
judge (re-applied here, deterministic, no API).
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parents[1] / "src"))

from desi_intervention import ACCEPT_STRONG, AMBIGUOUS_MARGIN  # noqa: E402
from p13_judge_evaluator import judge_deterministic  # noqa: E402
from report_truthfulqa import _label  # noqa: E402

_LIVE = _HERE / "outputs" / "truthfulqa.deepseek-v4.p12.limit100.jsonl"
_GRAPH = _HERE / "outputs" / "truthfulqa.deepseek-v4.p12.claim_graph.limit100.jsonl"

# Trigger -> routing class. Rationale is in the architecture plan.
ACTIVATE = {"high_tie", "abstain_ambiguous_match", "projection_high_entropy",
            "judge_divergence", "hallucination_judge_only"}
LOG = {"accept_uncertain", "reject_low_confidence", "reasoning_inefficient_supported",
       "projection_uncertain", "final_unknown_nonempty_raw", "claimgraph_conflict"}
DISCARD = {"reject_known_false_exact", "projection_invalid", "accept_supported_exact"}


def _triggers_for(rec: dict, graph_row: dict) -> set[str]:
    t: set[str] = set()
    se = rec.get("static_eval") or {}
    dm = rec.get("desi_metadata") or {}
    cor = se.get("correct_answers") or []
    inc = se.get("incorrect_answers") or []
    raw = rec.get("raw_model_answer") or rec.get("model_answer") or ""
    fin = rec.get("model_answer") or ""
    dec = dm.get("intervention_decision") or ""
    flags = dm.get("epistemic_flags") or []

    # intervention-derived signals
    cms, ims = dm.get("correct_match_score"), dm.get("incorrect_match_score")
    if (cms is not None and ims is not None and cms >= ACCEPT_STRONG
            and ims >= ACCEPT_STRONG and abs(cms - ims) < AMBIGUOUS_MARGIN):
        t.add("high_tie")
    if dec == "abstain_ambiguous_match":
        t.add("abstain_ambiguous_match")
    if dec == "reject_known_false_exact":
        t.add("reject_known_false_exact")
    if dec == "accept_supported_exact":
        t.add("accept_supported_exact")
    if dec == "accept_uncertain":
        t.add("accept_uncertain")
    if dec == "reject_low_confidence":
        t.add("reject_low_confidence")
    if "reasoning_inefficient_supported" in flags:
        t.add("reasoning_inefficient_supported")
    if fin.strip().upper() == "UNKNOWN" and raw.strip() and raw.strip().upper() != "UNKNOWN":
        t.add("final_unknown_nonempty_raw")

    # SPL / claim-graph signals
    for a in (graph_row or {}).get("atomic_claims", []):
        for f in (a.get("projection") or {}).get("flags", []):
            if f in ("projection_invalid", "projection_high_entropy", "projection_uncertain"):
                t.add(f)
    rels = list((graph_row or {}).get("answer_relations", []))
    for a in (graph_row or {}).get("atomic_claims", []):
        rels += a.get("relations", [])
    if "CONTRADICTS" in rels:
        t.add("claimgraph_conflict")

    # judge-derived signals (P13 deterministic judge, no API)
    h = _label(fin, cor, inc)
    j = judge_deterministic(fin, cor, inc)
    if h != j:
        t.add("judge_divergence")
    if j == "hallucination_suspect" and h != "hallucination_suspect":
        t.add("hallucination_judge_only")
    return t


def analyse(records: list[dict], graph: list[dict]) -> dict:
    g_by_id = {r["task_id"]: r for r in graph}
    per_task: dict[str, set[str]] = {}
    trig_counts: Counter = Counter()
    for r in records:
        tid = r["task_id"]
        tr = _triggers_for(r, g_by_id.get(tid, {}))
        per_task[tid] = tr
        for x in tr:
            trig_counts[x] += 1
    activated = {tid: (tr & ACTIVATE) for tid, tr in per_task.items() if tr & ACTIVATE}
    logged = {tid: (tr & LOG) for tid, tr in per_task.items() if tr & LOG}
    return {"n": len(records), "per_task": per_task, "trig_counts": dict(trig_counts),
            "activated": activated, "logged": logged}


def _known_cases(path: Path) -> list[str]:
    """Do the canonical forensic cases fire ACTIVATE triggers in a given file?"""
    if not path.exists():
        return [f"({path.name} not present)"]
    recs = {r["task_id"]: r for r in
            [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]}
    out = []
    for tid in ("tqa-0022", "tqa-0027"):
        r = recs.get(tid)
        if not r:
            out.append(f"- `{tid}`: not in {path.name}")
            continue
        tr = _triggers_for(r, {})
        act = tr & ACTIVATE
        raw = (r.get("raw_model_answer") or "")[:50]
        out.append(f"- `{tid}` ({path.name}) raw {raw!r}: triggers {sorted(tr) or '[]'}; "
                   f"would activate: {sorted(act) if act else 'NO'}")
    return out


def write_report(res: dict, path: Path) -> None:
    n = res["n"]
    tc = res["trig_counts"]
    n_act = len(res["activated"])
    n_log = len(res["logged"])
    md = ["# Selective cross-assessment — trigger analysis (P12 live, limit 100)\n",
          "Offline trigger sizing for an Alexandria-style SELECTIVE cross-assessment "
          "layer. No cross-assessment was run; no model calls; no new truthfulness "
          "numbers — only how often each epistemic-risk signal fires and how many "
          "cases a selective layer would touch vs an always-judge baseline.\n",
          "## Trigger counts (per 100 cases)\n",
          "| trigger | count | routing |"
          , "| --- | --- | --- |"]

    def route(name):
        return "ACTIVATE" if name in ACTIVATE else "LOG" if name in LOG else "DISCARD"
    all_triggers = sorted(ACTIVATE | LOG | DISCARD)
    for name in all_triggers:
        md.append(f"| {name} | {tc.get(name, 0)} | {route(name)} |")
    md.append("")

    md.append("## How many cases would trigger cross-assessment?\n")
    md.append(f"- **Cases that would ACTIVATE cross-assessment: {n_act}/{n}** "
              f"({100.0*n_act/n:.0f}%).")
    md.append(f"- Cases with LOG-only signals (recorded, not fired): {n_log}/{n}.")
    md.append(f"- Always-judge baseline: **{n}/{n}** (100%).")
    md.append(f"- **Cost ratio vs always-judge: {n_act}/{n} = {n_act/n:.2f}x** — a "
              f"selective layer would do ~{n}/{max(n_act,1):.0f}x fewer cross-runs "
              "(only the epistemically risky cases).")
    md.append("")
    md.append("### Activated task_ids and their activating triggers\n")
    if res["activated"]:
        for tid in sorted(res["activated"]):
            md.append(f"- `{tid}`: {sorted(res['activated'][tid])}")
    else:
        md.append("- (none activated on this file)")
    md.append("")

    md.append("## Would the known failure cases be caught?\n")
    md.append("In the P12 LIVE file the model produced the *correct* quotes for the "
              "canonical cases (so no ambiguity remained); in the ORIGINAL recorded "
              "run they were the high ties. The high_tie trigger is what catches them:")
    md.extend(_known_cases(_LIVE))
    md.extend(_known_cases(_HERE / "outputs" / "truthfulqa.deepseek-v4.desi_intervened_spl.limit100.jsonl"))
    md.append("")

    md.append("## Which triggers activate / log / discard (and why)\n")
    md.append("**ACTIVATE** (rare, genuine epistemic ambiguity where parallel "
              "independent reconstruction can reveal a typed deviation):")
    md.append("- `high_tie`, `abstain_ambiguous_match` — surface ambiguity the matcher "
              "could not resolve.")
    md.append("- `judge_divergence`, `hallucination_judge_only` — two independent "
              "scorers disagree (the strongest selective signal; the latter flags a "
              "possible missed hallucination).")
    md.append("- `projection_high_entropy` — SPL itself judged the claim too flat to admit.")
    md.append("**LOG** (record for audit, do not fire — too frequent, already-decided, "
              "or soft): `accept_uncertain`, `reject_low_confidence`, "
              "`reasoning_inefficient_supported`, `projection_uncertain`, "
              "`final_unknown_nonempty_raw`, `claimgraph_conflict` (here gold-derived; "
              "in production a genuine cross-claim contradiction would ACTIVATE).")
    md.append("**DISCARD** (not an ambiguity signal): `reject_known_false_exact`, "
              "`accept_supported_exact` (confident, already resolved), "
              "`projection_invalid` (a malformed/empty extraction, not a contested claim).")
    md.append("")
    md.append("### Best triggers (precision vs frequency)\n")
    md.append(f"- `hallucination_judge_only` ({tc.get('hallucination_judge_only',0)}) — "
              "highest value: catches the dangerous 'missed hallucination' at low rate.")
    md.append(f"- `high_tie` ({tc.get('high_tie',0)}) — precise and rare; the canonical "
              "tie-artifact detector.")
    md.append(f"- `judge_divergence` ({tc.get('judge_divergence',0)}) — broadest "
              "coverage of scorer-ambiguous cases; higher rate, so the main cost driver.")
    md.append("")

    md.append("## Honesty / limits\n")
    md.append("- **No cross-assessment was run** — this only sizes triggers. No "
              "Granite/DeepSeek cross-runs, no API, no new truthfulness numbers.")
    md.append("- The `judge_divergence` / `hallucination_judge_only` counts come from "
              "the P13 deterministic judge, itself a biased lexical instrument — these "
              "are routing signals, not truth claims.")
    md.append("- `claimgraph_conflict` here is contradiction-vs-gold (a benchmark "
              "artifact); the production signal is cross-claim contradiction, absent "
              "here.")
    md.append("- Trigger routing (activate/log/discard) is a design choice, tunable; "
              "the counts above let it be calibrated against a cross-run budget.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(md) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Selective cross-assessment trigger analysis.")
    ap.add_argument("--records", type=Path, default=_LIVE)
    ap.add_argument("--graph", type=Path, default=_GRAPH)
    ap.add_argument("--report", type=Path,
                    default=_HERE / "outputs" / "selective_cross_assessment_trigger_report.limit100.md")
    args = ap.parse_args()
    if not args.records.exists() or not args.graph.exists():
        print("Missing P12 live inputs.", file=sys.stderr)
        return 1
    records = [json.loads(l) for l in args.records.read_text(encoding="utf-8").splitlines() if l.strip()]
    graph = [json.loads(l) for l in args.graph.read_text(encoding="utf-8").splitlines() if l.strip()]
    res = analyse(records, graph)
    write_report(res, args.report)
    print(f"activated {len(res['activated'])}/{res['n']} (always-judge {res['n']}/{res['n']}) "
          f"| trigger counts: {res['trig_counts']} -> {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
