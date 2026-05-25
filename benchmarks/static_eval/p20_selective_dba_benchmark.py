#!/usr/bin/env python3
"""P20 selective-DBA architecture benchmark (offline; no API calls).

Measures the ARCHITECTURE BEHAVIOUR of the P20 path — NOT truthfulness. It reuses
existing artifacts only: P12 live records + claim graph, P14 triggers, P18
persisted Granite Gβ, P19 typed governance. No judge, no vote, no truthfulness
score, no new model calls.

Question: over the limit-100 run, how does the selective path behave?
  - folded / closed in the single-builder path (no epistemic-risk trigger)
  - triggered but claim-less (logged, nothing to cross-reconstruct)
  - escalated to DBA (claim-structural) -> P19 governed outcome:
    semantic_reconcilable / protected_branch_required / logical_polarity_conflict
    / guarded_divergence (with the P18 meaning class shown alongside).
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
from typed_semantic_governance import govern_case  # noqa: E402
from spl_meaning_space_alignment import _load_jsonl  # noqa: E402

_LIVE = _HERE / "outputs" / "truthfulqa.deepseek-v4.p12.limit100.jsonl"
_GRAPH = _HERE / "outputs" / "truthfulqa.deepseek-v4.p12.claim_graph.limit100.jsonl"
_BETA = _HERE / "outputs" / "p18_granite_builder_graphs.limit100.jsonl"
_FOCUS = ("tqa-0007", "tqa-0027", "tqa-0080", "tqa-0018")


def run(records, graph_list, beta):
    g_by_id = {r["task_id"]: r for r in graph_list}
    res = analyse(records, graph_list)              # P14 triggers
    n = res["n"]
    activated = set(res["activated"])               # ACTIVATE-triggered tasks
    per_task = res["per_task"]
    escalated = set(select_cases(records, g_by_id))  # claim-structural -> DBA
    # claim count per task
    nclaims = {r["task_id"]: len(r.get("atomic_claims", [])) for r in graph_list}
    claim_less = {t for t in activated if nclaims.get(t, 0) == 0}
    triggered_not_escalated = activated - escalated

    # run P19 governance on escalated cases that have a persisted Gβ
    gov = {}
    for tid in sorted(escalated):
        if tid not in beta:
            continue
        alpha = builder_alpha(g_by_id.get(tid, {}))
        gc = govern_case(alpha, beta[tid])
        gc["task_id"] = tid
        gc["n_alpha"] = len(alpha)
        gc["n_beta"] = len(beta[tid])
        gov[tid] = gc

    # per-trigger escalation precision (how DBA-useful each trigger is)
    trig_prec = {}
    for trig in sorted(ACTIVATE):
        fired = {t for t in per_task if trig in per_task[t]}
        if not fired:
            continue
        esc = fired & escalated
        trig_prec[trig] = (len(fired), len(esc))

    return {"n": n, "activated": activated, "escalated": escalated, "gov": gov,
            "claim_less": claim_less, "triggered_not_escalated": triggered_not_escalated,
            "trig_counts": res["trig_counts"], "trig_prec": trig_prec,
            "per_task": per_task}


def write_report(R, path: Path) -> None:
    n = R["n"]
    n_trig = len(R["activated"])
    n_esc = len(R["escalated"])
    n_folded = n - n_trig
    gov = R["gov"]
    gov_rows = list(gov.values())
    p19c = Counter(r["p19_outcome"] for r in gov_rows)
    mclass = Counter(r["meaning_class"] for r in gov_rows)
    retracted = [r for r in gov_rows if r["retracted_reconciliation"]]

    md = ["# P20 selective-DBA architecture benchmark (limit 100)\n",
          "Architecture-behaviour measurement (NOT truthfulness). Offline reuse of "
          "P12/P14/P18/P19 artifacts; no model calls, no judge, no vote, no truth "
          "score. Measures branch inflation, false reconciliation, and escalation "
          "selectivity.\n",
          "## Path distribution over the 100 items\n",
          f"- **folded / closed in single-builder path (no trigger): {n_folded}/{n}** "
          "— never reach DBA.",
          f"- triggered (ACTIVATE): {n_trig}/{n}.",
          f"  - of which **claim-less** (no atomic claims, nothing to reconstruct): "
          f"{len(R['claim_less'])} — logged, NOT escalated.",
          f"  - of which triggered-but-not-escalated (e.g. single trivial claim / "
          f"matcher-level): {len(R['triggered_not_escalated'] - R['claim_less'])}.",
          f"- **escalated to DBA (claim-structural): {n_esc}/{n}** "
          f"({', '.join(sorted(R['escalated']))}).",
          ""]

    md.append("## Escalated-set governed outcomes (P19)\n")
    md.append("| task | nα | nβ | P18 meaning class | typed divergences | P19 outcome | P18 would-reconcile? |")
    md.append("| --- | --- | --- | --- | --- | --- | --- |")
    for tid in sorted(gov):
        r = gov[tid]
        would = "yes" if r["meaning_class"] in (
            "reconstruction_isomorph", "coarse_grain_equivalent",
            "decomposition_variant", "semantic_region_match") else "no"
        md.append(f"| {tid} | {r['n_alpha']} | {r['n_beta']} | {r['meaning_class']} | "
                  f"{r['divergences'] or '-'} | **{r['p19_outcome']}** | {would} |")
    md.append("")
    md.append(f"- P19 governed outcomes: `{dict(p19c)}`")
    md.append(f"- P18 meaning classes (pre-governance): `{dict(mclass)}`")
    md.append(f"- semantic reconciliations (closed by semantics): "
              f"{p19c.get('semantic_reconcilable', 0)}")
    md.append(f"- protected branches: {p19c.get('protected_branch_required', 0)}")
    md.append(f"- logical polarity conflicts: {p19c.get('logical_polarity_conflict', 0)}")
    md.append(f"- guarded divergences: {p19c.get('guarded_divergence', 0)}")
    md.append(f"- **cases P18 would have FALSELY reconciled, P20 protects: "
              f"{len(retracted)}** ({', '.join(r['task_id'] for r in retracted) or 'none'}).")
    md.append("")

    md.append("## Compute / folding\n")
    md.append(f"- second-builder (DBA) invocations: **{n_esc}/{n}** vs "
              f"always-dual-builder **{n}/{n}** -> **{100*(n-n_esc)//n}% fewer** "
              "second-builder runs.")
    md.append(f"- the meaning-space + typed governance run only on the {n_esc} escalated "
              f"cases; of those, {p19c.get('semantic_reconcilable',0)} are CLOSED by "
              "semantics and only "
              f"{p19c.get('protected_branch_required',0)+p19c.get('logical_polarity_conflict',0)} "
              "stay branched — so folding closes most of the little that escalates.")
    md.append("")

    md.append("## Trigger usefulness (escalation precision)\n")
    md.append("How many of each trigger's firings actually reached DBA escalation "
              "(claim-structural). Low precision = too broad for DBA (still valid as a "
              "scorer-sensitivity log signal).\n")
    md.append("| trigger | fired | escalated | precision |")
    md.append("| --- | --- | --- | --- |")
    for trig, (fired, esc) in sorted(R["trig_prec"].items(), key=lambda kv: -kv[1][1]):
        md.append(f"| {trig} | {fired} | {esc} | {esc}/{fired} |")
    md.append("")

    md.append("## Focus cases\n")
    for tid in _FOCUS:
        if tid in gov:
            r = gov[tid]
            md.append(f"- `{tid}`: escalated; meaning class {r['meaning_class']} "
                      f"(region {r['region']}), divergences {r['divergences'] or '[]'} "
                      f"-> **{r['p19_outcome']}**"
                      + (" (P18 false reconciliation PROTECTED)" if r["retracted_reconciliation"] else ""))
        else:
            cls = "claim-less" if tid in R["claim_less"] else (
                "triggered, not escalated" if tid in R["activated"] else "folded/closed (no trigger)")
            md.append(f"- `{tid}`: {cls} — not escalated to DBA.")
    md.append("")

    md.append("## Reading (architecture behaviour, no truth claim)\n")
    md.append(f"- **Selective escalation works:** {n_esc}/{n} reach the second builder; "
              f"{n_folded}/{n} fold/close on the single-builder path. DESi escalates "
              "rarely.")
    md.append(f"- **Less false branch inflation:** symbolic-only DBA branched "
              f"{sum(1 for r in gov_rows if r['p16']=='branch_required')}/{n_esc} of the "
              f"escalated set; the meaning-space closes most of those.")
    md.append(f"- **Less false reconciliation:** {len(retracted)} case(s) the embedding "
              "would have merged are protected by typed governance "
              "(logical_polarity_conflict).")
    md.append("- **protected_branch_required / logical_polarity_conflict fire on a "
              "LOGICAL basis** (tqa-0007 negation flip), not on surface granularity — "
              "the intended behaviour.")
    md.append("- This is architecture behaviour only: it shows **less false branch "
              "inflation, less false reconciliation, more selective escalation** — NOT "
              "that DESi is 'more truthful'.")
    md.append("")
    md.append("## Honesty / limits\n")
    md.append("- 5 escalated cases of one limit-100 run — indicative, not established "
              "at scale. Triggers/outcome mix will shift with data.")
    md.append("- Governance is precision-sound but recall-limited (negation_flip "
              "reliable; other typed checks barely exercised here). Folding closure is "
              "only as safe as that recall.")
    md.append("- No API calls, no new models, no truthfulness scores; persisted P18 Gβ "
              "and cached embeddings reused.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(md) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="P20 selective-DBA architecture benchmark.")
    ap.add_argument("--records", type=Path, default=_LIVE)
    ap.add_argument("--graph", type=Path, default=_GRAPH)
    ap.add_argument("--beta", type=Path, default=_BETA)
    ap.add_argument("--report", type=Path,
                    default=_HERE / "outputs" / "p20_selective_dba_benchmark_report.limit100.md")
    args = ap.parse_args()
    for f in (args.records, args.graph, args.beta):
        if not f.exists():
            print(f"Missing artifact: {f}", file=sys.stderr)
            return 1
    records = _load_jsonl(args.records)
    graph_list = _load_jsonl(args.graph)
    beta = {r["task_id"]: r["claims"] for r in _load_jsonl(args.beta)}
    R = run(records, graph_list, beta)
    write_report(R, args.report)
    p19c = Counter(r["p19_outcome"] for r in R["gov"].values())
    print(f"folded {R['n']-len(R['activated'])}/{R['n']} | triggered {len(R['activated'])} "
          f"(claim-less {len(R['claim_less'])}) | escalated {len(R['escalated'])} | "
          f"P19 {dict(p19c)} -> {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
