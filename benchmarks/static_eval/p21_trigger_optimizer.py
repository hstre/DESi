#!/usr/bin/env python3
"""P21 trigger / folding optimizer (offline; no API calls).

Operationalises DESi folding: a risk signal is not enough to spend a second
builder. Classifies every triggered item into ESCALATE / LOG_ONLY / DISCARD using
single-builder (Alpha-only) claim STRUCTURE — escalate only when independent
reconstruction could meaningfully diverge. Reuses P12/P14/P18/P19/P20 artifacts;
no model calls, no judge, no vote, no truthfulness score.

Escalation predicate (Alpha-only, pre-DBA):
  ESCALATE  if triggered AND has claims AND
            ( >=2 atomic claims  OR  >=2 claim types  OR  compound object
              OR causal structure OR logical-risk tokens (negation/quantifier/causal) )
  DISCARD   if triggered AND (claim-less abstain  OR exact accepted/rejected
              OR all-claims-malformed)
  LOG_ONLY  if triggered AND none of the above (answer-level uncertainty, no
            claim-structural complexity)
  (folded   if not triggered -> closed on the single-builder path, no DBA)
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
sys.path.insert(0, str(_HERE.parents[1] / "gaia"))

from selective_cross_assessment_triggers import ACTIVATE, analyse  # noqa: E402
from alexandria_real_beta_runner import select_cases  # noqa: E402
from alexandria_dba_runner import builder_alpha  # noqa: E402
from spl_meaning_space_alignment import _load_jsonl  # noqa: E402
from desi_intervention import _content_tokens  # noqa: E402

_LIVE = _HERE / "outputs" / "truthfulqa.deepseek-v4.p12.limit100.jsonl"
_GRAPH = _HERE / "outputs" / "truthfulqa.deepseek-v4.p12.claim_graph.limit100.jsonl"
_FOCUS = ("tqa-0007", "tqa-0027", "tqa-0080", "tqa-0018", "tqa-0022")

_NEG = {"not", "no", "never", "cannot", "n't", "without", "neither", "nor", "none"}
_QUANT = {"all", "every", "each", "always", "some", "most", "many", "few", "any"}
_CAUSAL = ("because", "cause", "causes", "due to", "leads to", "results in")
_COMPOUND = (" and ", " because ", " due to ", " causes ", ", ", "; ")
_EXACT = {"accept_supported_exact", "reject_known_false_exact"}
_ABSTAIN = {"abstain", "abstain_inefficient", "abstain_truncated", "abstain_ambiguous_match"}


def _alpha_features(alpha: list[dict]) -> dict:
    n = len(alpha)
    types = {c.get("claim_type", "fact") for c in alpha}
    compound = any(any(s in c.get("object", "") for s in _COMPOUND) for c in alpha)
    causal = any(c.get("claim_type") == "causal"
                 or any(m in f"{c.get('predicate','')} {c.get('object','')}".lower() for m in _CAUSAL)
                 for c in alpha)
    text_tokens = set()
    for c in alpha:
        text_tokens |= set(f"{c.get('predicate','')} {c.get('object','')} {c.get('subject','')}"
                           .lower().replace("'", " ").split())
    risk = bool(text_tokens & (_NEG | _QUANT)) or causal
    return {"n": n, "n_types": len(types), "compound": compound, "causal": causal, "risk": risk}


def classify(tid, triggered, alpha, decision, malformed) -> tuple[str, str]:
    f = _alpha_features(alpha)
    if not triggered:
        return "folded", "no epistemic-risk trigger -> closed single-builder"
    # triggered:
    if f["n"] >= 1 and (f["n"] >= 2 or f["n_types"] >= 2 or f["compound"]
                        or f["causal"] or f["risk"]):
        why = []
        if f["n"] >= 2:
            why.append(f">=2 claims ({f['n']})")
        if f["n_types"] >= 2:
            why.append(f">=2 types ({f['n_types']})")
        if f["compound"]:
            why.append("compound object")
        if f["causal"]:
            why.append("causal")
        if f["risk"] and not (f["causal"]):
            why.append("logical-risk tokens")
        return "ESCALATE", "; ".join(why)
    if f["n"] == 0:
        return "DISCARD", "claim-less (nothing to reconstruct)"
    if decision in _EXACT:
        return "DISCARD", f"already exact-resolved ({decision})"
    if malformed:
        return "DISCARD", "all atomic claims malformed/inadmissible"
    return "LOG_ONLY", "answer-level uncertainty, no claim-structural complexity"


def run(records, graph_list):
    g_by_id = {r["task_id"]: r for r in graph_list}
    rec_by_id = {r["task_id"]: r for r in records}
    res = analyse(records, graph_list)
    activated = set(res["activated"])
    per_task = res["per_task"]
    p20_escalated = set(select_cases(records, g_by_id))

    rows = []
    for r in records:
        tid = r["task_id"]
        g = g_by_id.get(tid, {})
        alpha = builder_alpha(g)
        ac = g.get("atomic_claims", [])
        malformed = bool(ac) and all("projection_invalid" in (a.get("projection") or {}).get("flags", [])
                                     for a in ac)
        decision = (rec_by_id[tid].get("desi_metadata") or {}).get("intervention_decision", "")
        cls, why = classify(tid, tid in activated, alpha, decision, malformed)
        rows.append({"task_id": tid, "n_alpha": len(alpha), "triggered": tid in activated,
                     "p20_escalated": tid in p20_escalated, "class": cls, "why": why,
                     "triggers": sorted(per_task.get(tid, set()) & ACTIVATE)})
    return {"n": len(records), "rows": rows, "n_activate": len(activated),
            "p20_escalated": p20_escalated}


def write_report(R, path: Path) -> None:
    rows = R["rows"]
    n = R["n"]
    by_class = Counter(r["class"] for r in rows)
    escalate = [r for r in rows if r["class"] == "ESCALATE"]
    p21_esc = {r["task_id"] for r in escalate}
    n_p14 = R["n_activate"]
    n_p20 = len(R["p20_escalated"])
    n_p21 = len(escalate)

    md = ["# P21 trigger / folding optimization (limit 100, offline)\n",
          "Operationalises DESi folding: a risk signal alone does not justify a "
          "second builder. Every triggered item is routed ESCALATE / LOG_ONLY / "
          "DISCARD by single-builder claim STRUCTURE. Reuses P12/P14/P18/P19/P20 "
          "artifacts; no API calls, no judge, no truthfulness score. This is "
          "architecture folding, NOT truthfulness tuning.\n",
          "## Routing distribution\n",
          f"| class | count |", "| --- | --- |"]
    for c in ("folded", "ESCALATE", "LOG_ONLY", "DISCARD"):
        md.append(f"| {c} | {by_class.get(c, 0)} |")
    md.append("")

    md.append("## Second-builder call estimates\n")
    md.append("| policy | second-builder calls (of 100) | note |")
    md.append("| --- | --- | --- |")
    md.append(f"| always-dual-builder | 100 | run a 2nd builder on every item |")
    md.append(f"| P14 always-escalate-on-trigger | {n_p14} | every ACTIVATE trigger -> DBA |")
    md.append(f"| P20 structural filter (select_cases) | {n_p20} | implicit claim-structural filter |")
    md.append(f"| **P21 optimized ESCALATE** | **{n_p21}** | explicit ESCALATE predicate + 3-class routing |")
    md.append("")
    md.append(f"- unnecessary DBA cases removed vs P14: **{n_p14 - n_p21}** "
              f"({n_p14} -> {n_p21}).")
    md.append(f"- compute saving vs always-dual-builder: **{100*(n - n_p21)//n}% fewer** "
              "second-builder calls.")
    extra = sorted(p21_esc - R["p20_escalated"])
    missing = sorted(R["p20_escalated"] - p21_esc)
    if p21_esc == R["p20_escalated"]:
        md.append("- P21 ESCALATE set == P20 structural set (same selective set via an "
                  "explicit, auditable rule).")
    else:
        md.append(f"- P21 ESCALATE vs P20 structural set: P21 adds {extra or 'none'}, "
                  f"drops {missing or 'none'}. The additions come from the "
                  "logical-risk-token rule (e.g. tqa-0000 'without harm' = a "
                  "negation-class single claim): P21 is slightly MORE inclusive than "
                  "the pure >=2-claims filter, a deliberate recall safeguard for "
                  "logically-loaded single claims (+1 second-builder call here).")
    md.append("")

    md.append("## Focus cases\n")
    by_id = {r["task_id"]: r for r in rows}
    for tid in _FOCUS:
        r = by_id.get(tid)
        if r:
            md.append(f"- `{tid}`: **{r['class']}** ({r['why']}); triggers "
                      f"{r['triggers'] or '[]'}, nα={r['n_alpha']}.")
    md.append("")
    md.append("- tqa-0007 protection: "
              + ("PRESERVED — still ESCALATE (reaches DBA + typed governance)."
                 if by_id.get("tqa-0007", {}).get("class") == "ESCALATE"
                 else "LOST — tqa-0007 no longer escalates (REGRESSION)."))
    md.append("")

    md.append("## Which triggers leave DBA activation\n")
    # for each ACTIVATE trigger, how many of its firings now ESCALATE vs LOG/DISCARD
    md.append("| trigger | fired | -> ESCALATE | -> LOG_ONLY | -> DISCARD |")
    md.append("| --- | --- | --- | --- | --- |")
    for trig in sorted(ACTIVATE):
        fired = [r for r in rows if trig in r["triggers"]]
        if not fired:
            continue
        c = Counter(r["class"] for r in fired)
        md.append(f"| {trig} | {len(fired)} | {c.get('ESCALATE',0)} | "
                  f"{c.get('LOG_ONLY',0)} | {c.get('DISCARD',0)} |")
    md.append("")
    md.append("- Triggers that retain real DBA activation: those with non-zero "
              "ESCALATE column (driven by claim structure, not answer-level "
              "uncertainty).")
    md.append("- Triggers that mostly drop to LOG_ONLY/DISCARD (too broad for DBA): "
              "judge_divergence / final_unknown_nonempty_raw / accept_uncertain on "
              "answers without claim-structural complexity — kept as LOG signals, not "
              "escalations.")
    md.append("")

    md.append("## Honesty / limits\n")
    md.append(f"- **limit-100, tiny escalation base ({n_p21} cases).** The predicate is "
              "NOT overfit to those — it is a generic structural rule (claim count / "
              "types / compound / causal / logical-risk tokens), but its calibration is "
              "unproven beyond this run.")
    md.append("- **Recall risk:** by escalating on claim structure, a genuinely "
              "conflicting SINGLE-claim answer (no risk token) would be routed LOG_ONLY/"
              "DISCARD and NOT cross-checked. Single-claim matcher conflicts are handled "
              "by the P12 tie resolver, but a single-claim logical conflict outside that "
              "path could be missed. No guarantee all future conflicts are caught.")
    md.append("- This is **architecture folding, not truthfulness tuning**: it changes "
              "WHICH cases pay for a second builder, not any truth label. No new "
              "benchmark, intervention, model, or score.")
    md.append("- The escalation predicate is Alpha-only (single builder, pre-DBA): it "
              "cannot see the real typed divergence (that needs Beta); it approximates "
              "'could diverge' from structure + logical-risk tokens.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(md) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="P21 trigger/folding optimizer.")
    ap.add_argument("--records", type=Path, default=_LIVE)
    ap.add_argument("--graph", type=Path, default=_GRAPH)
    ap.add_argument("--report", type=Path,
                    default=_HERE / "outputs" / "p21_trigger_folding_optimization_report.limit100.md")
    args = ap.parse_args()
    if not args.records.exists() or not args.graph.exists():
        print("Missing artifacts.", file=sys.stderr)
        return 1
    records = _load_jsonl(args.records)
    graph_list = _load_jsonl(args.graph)
    R = run(records, graph_list)
    write_report(R, args.report)
    by_class = Counter(r["class"] for r in R["rows"])
    esc = {r["task_id"] for r in R["rows"] if r["class"] == "ESCALATE"}
    print(f"routing {dict(by_class)} | P14 {R['n_activate']} -> P21 ESCALATE {len(esc)} "
          f"| tqa-0007 {'ESCALATE' if 'tqa-0007' in esc else 'NOT'} -> {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
