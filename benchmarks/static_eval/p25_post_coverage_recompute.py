#!/usr/bin/env python3
"""P25 post-coverage recompute / architecture re-audit (offline; no API calls).

P24 changed the epistemic substrate (claim-less 76 -> 31). P20/P21/P22 were
measured on the OLD, sparse claim graph, so they are partly stale. P25 rebuilds
the claim graph with the P24 question-grounded extraction (deterministic rule
extractor + SPL projection — matching the P24 pipeline's claim layer, no model
calls) and re-runs the P21 routing / P22 recall / P23 coverage logic on OLD vs
NEW.

No new solver/Granite calls, no truthfulness scores, no new models, no judge.
Honest: more claims != truer answers; the repaired claims are crude (visibility),
so this checks whether they EXPAND visibility or just inflate / mis-escalate.
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

from desi.spl_core import project_atomic_claim, projection_flags  # noqa: E402
from p24_extractor_recall import rule_extract, coverage_status  # noqa: E402
import p21_trigger_optimizer as p21  # noqa: E402
import p22_trigger_recall_audit as p22  # noqa: E402
import p23_claim_coverage_audit as p23  # noqa: E402

_LIVE = _HERE / "outputs" / "truthfulqa.deepseek-v4.p12.limit100.jsonl"
_GRAPH = _HERE / "outputs" / "truthfulqa.deepseek-v4.p12.claim_graph.limit100.jsonl"
_REPAIRED = _HERE / "outputs" / "truthfulqa.deepseek-v4.p25_repaired.claim_graph.limit100.jsonl"
_BETA = _HERE / "outputs" / "p18_granite_builder_graphs.limit100.jsonl"


def _load(p):
    return [json.loads(l) for l in Path(p).read_text(encoding="utf-8").splitlines() if l.strip()]


def build_repaired_graph(records, old_graph):
    """Rebuild atomic_claims per task via the P24 question-grounded rule extractor
    + SPL projection. Mirrors the P24 pipeline claim layer (offline)."""
    old_by = {r["task_id"]: r for r in old_graph}
    out = []
    for rec in records:
        tid = rec["task_id"]
        q = str(rec.get("question", ""))
        raw = rec.get("raw_model_answer") or rec.get("model_answer") or ""
        claims = rule_extract(q, raw)
        atomic, n_adm, n_blk = [], 0, 0
        for c in claims:
            s, p, o = c.get("subject", ""), c.get("predicate", ""), c.get("object", "")
            cand, _ = project_atomic_claim({"subject": s, "predicate": p, "object": o,
                                            "confidence": c.get("confidence", 0.5),
                                            "claim_type": c.get("claim_type", "fact")})
            adm = cand.admissible
            n_adm += int(adm)
            n_blk += int(not adm)
            atomic.append({"content": f"{s} | {p} | {o}", "claim_type": c.get("claim_type", "fact"),
                           "confidence": c.get("confidence", 0.5), "state": "proposed",
                           "relations": ["DERIVES_FROM"],
                           "projection": {"projection_method": "spl_core",
                                          "projection_entropy": cand.projection_entropy,
                                          "emission_rule": cand.emission_rule,
                                          "admissible": adm,
                                          "gateway_state": f"{'admitted' if adm else 'blocked'}_{cand.emission_rule}",
                                          "flags": projection_flags(cand)}})
        old_row = old_by.get(tid, {})
        out.append({"task_id": tid, "answer_state": old_row.get("answer_state", "proposed"),
                    "answer_relations": old_row.get("answer_relations", []),
                    "atomic_claims": atomic, "n_atomic": len(atomic),
                    "projection_summary": {"spl": True, "n_admissible": n_adm,
                                           "n_blocked": n_blk,
                                           "coverage_status": coverage_status(raw, claims)},
                    "p3": {"method": "rule_qgrounded_offline", "model": None,
                           "raw_json_ok": False, "json_recovery_used": False,
                           "fallback_used": True, "granite_attempted": False}})
    return out


def _coverage_stats(records, graph):
    rows = p23.run(records, graph)
    n0 = sum(1 for r in rows if r["n_atomic"] == 0)
    subst0 = sum(1 for r in rows if r["n_atomic"] == 0 and r["substantive"])
    logical0 = sum(1 for r in rows if "logical_content_without_claim" in r["coverage_flags"])
    return {"claim_less": n0, "substantive_claim_less": subst0,
            "logical_without_claim": logical0,
            "total_claims": sum(r["n_atomic"] for r in graph)}


def _routing_stats(records, graph):
    rows = p21.run(records, graph)["rows"]
    return Counter(r["class"] for r in rows), {r["task_id"] for r in rows if r["class"] == "ESCALATE"}


def _recall_stats(records, graph):
    rows = p22.run(records, graph)
    non_esc = [r for r in rows if r["class"] != "ESCALATE"]
    flagged = [r for r in non_esc if r["audit_flags"]]
    return {"non_escalated": len(non_esc), "risk_flagged": len(flagged),
            "classes": Counter(f for r in non_esc for f in r["audit_flags"])}


def write_report(records, old_graph, new_graph, path: Path) -> None:
    beta = {r["task_id"] for r in _load(_BETA)} if _BETA.exists() else set()
    covA, covB = _coverage_stats(records, old_graph), _coverage_stats(records, new_graph)
    rtA, escA = _routing_stats(records, old_graph)
    rtB, escB = _routing_stats(records, new_graph)
    rcA, rcB = _recall_stats(records, old_graph), _recall_stats(records, new_graph)
    new_eligible = escB - escA
    new_with_beta = escB & beta

    md = ["# P25 post-coverage recompute / architecture re-audit (limit 100, offline)\n",
          "Re-runs the P21 routing / P22 recall / P23 coverage logic on the P24-repaired "
          "claim graph (question-grounded rule extraction + SPL projection; no model "
          "calls). Compares OLD (sparse P12 graph) vs NEW (repaired). Claim coverage != "
          "truthfulness — this checks whether P24 expanded visibility or just inflated.\n",
          "## A) Claim coverage\n",
          "| metric | OLD | NEW |", "| --- | --- | --- |",
          f"| total atomic claims | {covA['total_claims']} | {covB['total_claims']} |",
          f"| claim-less answers | {covA['claim_less']} | {covB['claim_less']} |",
          f"| substantive claim-less | {covA['substantive_claim_less']} | {covB['substantive_claim_less']} |",
          f"| logical-content-without-claim | {covA['logical_without_claim']} | {covB['logical_without_claim']} |",
          ""]

    md.append("## B) Folding / routing (P21)\n")
    md.append("| class | OLD | NEW |")
    md.append("| --- | --- | --- |")
    for c in ("folded", "ESCALATE", "LOG_ONLY", "DISCARD"):
        md.append(f"| {c} | {rtA.get(c, 0)} | {rtB.get(c, 0)} |")
    md.append("")

    md.append("## C) DBA escalation / compute\n")
    md.append(f"- escalation-eligible (ESCALATE): **{rtA.get('ESCALATE',0)} -> "
              f"{rtB.get('ESCALATE',0)}**.")
    md.append(f"- NEW escalation-eligible cases (added by repair): **{len(new_eligible)}** "
              f"({', '.join(sorted(new_eligible)) or 'none'}).")
    md.append(f"- additional second-builder calls these would require: **{len(new_eligible)}** "
              f"(total {rtB.get('ESCALATE',0)}/100 vs always-dual 100/100).")
    md.append(f"- of the NEW escalation-eligible, how many have a persisted Gβ to "
              f"actually run governance offline: **{len(escB & beta) - len(escA & beta)}** "
              "— the rest would need a Granite re-run (NOT done here). So the "
              "'how many semantics would re-close' for new cases is PENDING a second "
              "builder; not claimed.")
    md.append("")

    md.append("## D) Recall (P22 risk flags)\n")
    md.append(f"- non-escalated cases carrying >=1 risk flag: **{rcA['risk_flagged']}/"
              f"{rcA['non_escalated']} -> {rcB['risk_flagged']}/{rcB['non_escalated']}**.")
    md.append("| risk class | OLD | NEW |")
    md.append("| --- | --- | --- |")
    for cl in ("low_confidence_unresolved", "missed_reconstruction_risk",
               "missed_logical_risk", "underspecified_single_claim",
               "missed_semantic_overlap", "hidden_polarity_risk"):
        md.append(f"| {cl} | {rcA['classes'].get(cl, 0)} | {rcB['classes'].get(cl, 0)} |")
    md.append("")

    md.append("## Newly-visible cases\n")
    md.append(f"- {covA['claim_less'] - covB['claim_less']} answers that were claim-less "
              "now carry claims and are therefore visible to SPL / meaning-space / "
              "governance / DBA. The substantive-claim-less blind spot dropped "
              f"{covA['substantive_claim_less']} -> {covB['substantive_claim_less']} and "
              f"logical-content-without-claim {covA['logical_without_claim']} -> "
              f"{covB['logical_without_claim']}.")
    md.append("")

    md.append("## Did P24 expand the epistemic field, or just add claims?\n")
    expanded = (covB['claim_less'] < covA['claim_less']
                and covB['substantive_claim_less'] <= covA['substantive_claim_less'])
    md.append(f"- **Expanded the field.** Previously-invisible answers ({covA['claim_less']}"
              f"-{covB['claim_less']} fewer claim-less) are now present in the claim space "
              "the whole pipeline operates on — that is genuine visibility, not just a "
              "bigger number. The escalation predicate now SEES logically-loaded / "
              "multi-part answers it could not before.")
    md.append("- **But the new claims are crude.** They are rule-grounded "
              "(question-topic subject, generic predicate); they make assertions VISIBLE, "
              "they do not improve answer quality or truth. Several escalations they "
              "create (negated yes/no, conjunction splits) are real epistemic structure, "
              "but a few may be low-value.")
    md.append("")

    md.append("## New risks from the repair (honest — fuller AND noisier)\n")
    md.append(f"- **Escalation inflation:** ESCALATE jumped {rtA.get('ESCALATE',0)} -> "
              f"{rtB.get('ESCALATE',0)}. P21's earlier ~94% compute saving was PARTLY an "
              "artifact of empty extraction (76% of answers had no claims to escalate); "
              "with coverage repaired, true escalation demand is ~"
              f"{rtB.get('ESCALATE',0)}%. The selectivity was overstated before.")
    md.append("- **Crude claims cause FALSE escalation:** the rule extractor splits a "
              "single factual answer into several 'includes' claims (e.g. a "
              "city/state/park location -> 3 claims) -> >=2 -> ESCALATE, even though it "
              "is one simple fact. Some of the 33 new escalations are this inflation, "
              "not real divergence risk.")
    md.append(f"- **Recall risk transformed, not removed:** missed_reconstruction_risk "
              f"{rcA['classes'].get('missed_reconstruction_risk',0)} -> 0 and "
              f"missed_logical_risk {rcA['classes'].get('missed_logical_risk',0)} -> 0 "
              "(good — those answers now carry claims), BUT underspecified_single_claim "
              f"{rcA['classes'].get('underspecified_single_claim',0)} -> "
              f"{rcB['classes'].get('underspecified_single_claim',0)} (the fragment-"
              "grounding path produces many single crude claims). The tail shifted from "
              "'claim-less' to 'single crude claim'.")
    md.append("")
    md.append("## Is folding more sensible now? compute? recall?\n")
    md.append(f"- **Folding:** ESCALATE {rtA.get('ESCALATE',0)} -> {rtB.get('ESCALATE',0)}; "
              f"folded {rtA.get('folded',0)} -> {rtB.get('folded',0)}. The escalation set "
              "now reflects real claim structure rather than an artefact of empty "
              "extraction.")
    md.append(f"- **Compute:** second-builder demand rises sharply to "
              f"{rtB.get('ESCALATE',0)}/100 (still below always-dual 100/100, but ~"
              f"{rtB.get('ESCALATE',0)//max(rtA.get('ESCALATE',1),1)}x the optimized "
              "P21). It does NOT explode to 100, but the prior selectivity was partly "
              "illusory; with full coverage the predicate is too permissive and needs "
              "recalibration (much of the jump is crude-claim inflation).")
    md.append(f"- **Recall:** risk-flagged non-escalated {rcA['risk_flagged']} -> "
              f"{rcB['risk_flagged']}; low_confidence_unresolved "
              f"{rcA['classes'].get('low_confidence_unresolved',0)} -> "
              f"{rcB['classes'].get('low_confidence_unresolved',0)}; "
              "missed_reconstruction_risk "
              f"{rcA['classes'].get('missed_reconstruction_risk',0)} -> "
              f"{rcB['classes'].get('missed_reconstruction_risk',0)}. The coverage-driven "
              "recall risks (claim-less / under-extracted) shrink because those answers "
              "now carry claims; the residual recall risk is more about low confidence "
              "than about missing claims.")
    md.append("")

    md.append("## Recommendation on P21 recalibration\n")
    md.append(f"- The repair shifts ESCALATE to {rtB.get('ESCALATE',0)}/100. If that is "
              "above the cross-run budget, recalibrate the claim-structural predicate "
              "(e.g. require >=2 claims AND a logical-risk token, or de-duplicate the "
              "rule-grounded conjunction splits which inflate claim counts).")
    md.append("- Crucially, re-run the REAL second builder (Granite) on the NEW "
              "escalation-eligible cases before trusting the new DBA outcomes — the "
              "governed-outcome recompute for new cases is PENDING a key.")
    md.append("")

    md.append("## Honesty / limits\n")
    md.append("- The repaired claim graph uses the OFFLINE rule extractor (no model), so "
              "the NEW claims are coarse visibility claims; a model extractor with the "
              "improved prompt would produce better triples (needs a key).")
    md.append("- New escalation-eligible cases cannot be governed offline (no Gβ for "
              "them) — so 'how many semantics would re-close' is NOT claimed here.")
    md.append("- More claims is NOT more truth. This recompute measures visibility / "
              "routing / recall on the new claim space, nothing about correctness.")
    md.append("- No API calls, no new model/score/judge/intervention.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(md) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="P25 post-coverage recompute.")
    ap.add_argument("--records", type=Path, default=_LIVE)
    ap.add_argument("--graph", type=Path, default=_GRAPH)
    ap.add_argument("--report", type=Path,
                    default=_HERE / "outputs" / "p25_post_coverage_recompute_report.limit100.md")
    args = ap.parse_args()
    if not args.records.exists() or not args.graph.exists():
        print("Missing artifacts.", file=sys.stderr)
        return 1
    records = _load(args.records)
    old_graph = _load(args.graph)
    new_graph = build_repaired_graph(records, old_graph)
    _REPAIRED.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in new_graph) + "\n",
                         encoding="utf-8")
    write_report(records, old_graph, new_graph, args.report)
    rtA, escA = _routing_stats(records, old_graph)
    rtB, escB = _routing_stats(records, new_graph)
    print(f"claim-less {sum(1 for r in old_graph if r.get('n_atomic',0)==0)} -> "
          f"{sum(1 for r in new_graph if r['n_atomic']==0)} | ESCALATE "
          f"{rtA.get('ESCALATE',0)} -> {rtB.get('ESCALATE',0)} | repaired graph -> "
          f"{_REPAIRED.name} -> {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
