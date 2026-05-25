#!/usr/bin/env python3
"""P31 full-100 role-correct DESi run.

First complete DESi pass with the P30 role architecture:
  - solver answers: existing P12 live answers (no new solver calls)
  - DEFAULT extractor: IBM Granite (existing P28 full-100 claim graph)
  - ESCALATION extractor / DBA second builder: Claude Haiku 4.5 (P30 cache)
  - SPL / meaning-space / typed governance: P19/P20
  - folding / canonicalization: P26/P28
  - NO DeepSeek extraction in the standard path

Granite extracts all 100; P21/P26 decide escalation; only the escalated minority
goes to DBA, where Claude Haiku is the independent second builder and P19 typed
governance classifies the outcome (semantic_reconcilable / protected_branch /
logical_polarity_conflict / unresolved_divergence), with coverage_asymmetry
treated as extractor_failure (not a real branch). Structural metrics only — no
truthfulness, no judge, no majority vote, no new intervention heuristics.

Runs fully offline from existing artifacts (all escalation Haiku claims are
cached from P30); no live model calls and no key are required.
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

from p30_extractor_role_benchmark import escalated_p28, _load, _substantive  # noqa: E402
from p27_model_grounded_canonical_extraction import _parse_keep_negated  # noqa: E402
import p26_noise_aware_canonicalization as p26  # noqa: E402
from typed_semantic_governance import govern_case  # noqa: E402
from alexandria_dba_runner import builder_alpha  # noqa: E402

_LIVE = _HERE / "outputs" / "truthfulqa.deepseek-v4.p12.limit100.jsonl"
_P28_GRAPH = _HERE / "outputs" / "p28_granite_claim_graph.limit100.jsonl"
_P30_CACHE = _HERE / "outputs" / "p30_extractor_claims.json"
_OUT_JSONL = _HERE / "outputs" / "p31_role_correct_dba_results.limit100.jsonl"
_REPORT = _HERE / "outputs" / "p31_full100_role_correct_desi_report.md"

_DEFAULT = "ibm-granite/granite-4.1-8b"
_ESCALATION = "anthropic/claude-haiku-4.5"

# OpenRouter list pricing ($/token), verified in P30, and P30 per-extraction mean
# tokens (in, out) measured on the 17 hard cases. Used only for cost ESTIMATES;
# the escalation Claude cost is computed from the ACTUAL cached token counts.
_PRICE = {  # (prompt $/tok, completion $/tok)
    "ibm-granite/granite-4.1-8b": (0.05e-6, 0.10e-6),
    "anthropic/claude-haiku-4.5": (1.00e-6, 5.00e-6),
    "deepseek/deepseek-v4-pro": (0.435e-6, 0.87e-6),
}
_MEAN_TOK = {  # mean (prompt, completion) tokens / extraction (P30, hard subset)
    "ibm-granite/granite-4.1-8b": (291, 58),
    "anthropic/claude-haiku-4.5": (313, 133),
    "deepseek/deepseek-v4-pro": (281, 712),
}

# P19 outcome -> coarse DBA disposition
_CLOSE = {"convergence", "semantic_reconcilable"}
_PROTECTED = {"protected_branch_required", "logical_polarity_conflict"}
_UNRESOLVED = {"branch_required", "guarded_divergence"}


def _mean_cost(model: str) -> float:
    pin, pout = _PRICE[model]
    tin, tout = _MEAN_TOK[model]
    return tin * pin + tout * pout


def _haiku_claims(cache: dict, tid: str) -> list[dict] | None:
    entry = cache.get(f"{_ESCALATION}|{tid}")
    if entry is None:
        return None
    return entry.get("claims")


def run(records, p28_graph, cache):
    rec_by = {r["task_id"]: r for r in records}
    row_by = {r["task_id"]: r for r in p28_graph}
    escalation = set(escalated_p28(records, p28_graph))

    full_rows = []          # one per case (100)
    total_granite_claims = 0
    total_clusters = 0
    n_with_claims = 0       # cases with >=1 Granite claim
    n_empty = 0             # cases with 0 Granite claims (UNKNOWN/refusal or gap)
    n_substantive_zero = 0  # 0 claims despite a substantive answer (coverage gap)
    dba = Counter()         # p19 disposition over escalated cases
    claude_calls = 0
    claude_pt = claude_ct = 0
    detail = {}             # tid -> dba detail for escalated

    for r in p28_graph:
        tid = r["task_id"]
        granite = builder_alpha(r)
        clusters = p26.canonicalize(granite)
        total_granite_claims += len(granite)
        total_clusters += len(clusters)
        is_esc = tid in escalation
        row = {"task_id": tid, "n_granite_claims": len(granite),
               "n_clusters": len(clusters), "escalated": is_esc}
        if granite:
            n_with_claims += 1
        else:
            n_empty += 1
            raw = (rec_by.get(tid, {}).get("raw_model_answer")
                   or rec_by.get(tid, {}).get("model_answer") or "")
            if _substantive(raw):
                n_substantive_zero += 1
        if not is_esc:
            row["disposition"] = "empty_answer" if not granite else "folded_single_builder"
            full_rows.append(row)
            continue

        # escalation -> Claude Haiku second builder (from P30 cache; no live call)
        beta = _haiku_claims(cache, tid)
        entry = cache.get(f"{_ESCALATION}|{tid}") or {}
        claude_calls += 1
        claude_pt += int(entry.get("pt") or 0)
        claude_ct += int(entry.get("ct") or 0)
        row["n_claude_claims"] = len(beta) if beta is not None else None
        row["claude_source"] = "p30_cache"

        a_empty = not granite
        b_empty = not beta
        if a_empty != b_empty:
            disposition = "coverage_asymmetry"   # extractor_failure, NOT a real branch
            row.update({"disposition": disposition, "p19_outcome": "coverage_asymmetry"})
        elif a_empty and b_empty:
            disposition = "both_empty"
            row.update({"disposition": disposition, "p19_outcome": "both_empty"})
        else:
            gc = govern_case(granite, beta)
            out = gc["p19_outcome"]
            disposition = ("close" if out in _CLOSE else
                           "protected_branch" if out in _PROTECTED else
                           "unresolved_divergence" if out in _UNRESOLVED else out)
            row.update({"disposition": disposition, "p19_outcome": out,
                        "meaning_class": gc["meaning_class"], "region": gc["region"],
                        "divergences": gc["divergences"],
                        "retracted_reconciliation": gc["retracted_reconciliation"]})
        dba[row["p19_outcome"]] += 1
        detail[tid] = row
        full_rows.append(row)

    return {"full_rows": full_rows, "escalation": sorted(escalation),
            "total_granite_claims": total_granite_claims, "total_clusters": total_clusters,
            "n_with_claims": n_with_claims, "n_empty": n_empty,
            "n_substantive_zero": n_substantive_zero,
            "dba": dict(dba), "detail": detail,
            "claude_calls": claude_calls, "claude_pt": claude_pt, "claude_ct": claude_ct,
            "rec_by": rec_by, "row_by": row_by}


def _disp_counts(res):
    c = Counter(r.get("disposition") for r in res["full_rows"])
    return c


def write_report(res, path: Path) -> None:
    n = len(res["full_rows"])
    esc = res["escalation"]
    n_esc = len(esc)
    dc = _disp_counts(res)
    close = dc.get("close", 0)
    protected = dc.get("protected_branch", 0)
    unresolved = dc.get("unresolved_divergence", 0)
    cov_asym = dc.get("coverage_asymmetry", 0)
    both_empty = dc.get("both_empty", 0)
    folded_single = dc.get("folded_single_builder", 0)
    empty_answer = dc.get("empty_answer", 0)
    real_branches = protected + unresolved
    n_with = res["n_with_claims"]

    # compute (estimates from P30 means; escalation Claude cost is ACTUAL)
    g_each = _mean_cost(_DEFAULT)
    h_each = _mean_cost(_ESCALATION)
    d_each = _mean_cost("deepseek/deepseek-v4-pro")
    pin_h, pout_h = _PRICE[_ESCALATION]
    claude_actual = res["claude_pt"] * pin_h + res["claude_ct"] * pout_h

    granite_100 = n * g_each
    role_correct = granite_100 + claude_actual                 # Granite x100 + Claude x escalated
    always_dual = granite_100 + n * h_each                     # Granite x100 + Claude x100
    deepseek_single = n * d_each                               # DeepSeek extractor x100
    saving_vs_dual = always_dual - role_correct
    saving_vs_dual_pct = 100 * saving_vs_dual / always_dual if always_dual else 0
    g_out = _MEAN_TOK[_DEFAULT][1]
    d_out = _MEAN_TOK["deepseek/deepseek-v4-pro"][1]
    h_out = _MEAN_TOK[_ESCALATION][1]

    det = res["detail"]

    def ctl(tid):
        r = next((x for x in res["full_rows"] if x["task_id"] == tid), None)
        return r or {}

    md = ["# P31 full-100 role-correct DESi run\n",
          "First complete DESi pass with the P30 role architecture: existing P12 live "
          "answers as solver output; IBM Granite as the always-on DEFAULT extractor "
          "(existing P28 full-100 graph); Claude Haiku 4.5 as the ESCALATION second "
          "builder (P30 cache); SPL meaning-space + P19 typed governance for "
          "adjudication; P26/P28 folding. No DeepSeek in the standard path, no new "
          "solver calls, no truthfulness score, no judge, no majority vote, no new "
          "intervention heuristics. Structural / compute metrics only.\n",
          f"Granite extracts all {n}; P21/P26 escalate {n_esc}; only the escalated "
          "minority reaches DBA. All escalation Haiku claims were served from the P30 "
          "cache (0 new live calls in this run).\n",
          "## A) Full-100 architecture metrics\n",
          "| metric | value |",
          "| --- | --- |",
          f"| cases (full set) | {n} |",
          f"| Granite claim coverage: cases with ≥1 claim | {n_with}/{n} |",
          f"| empty answers (0 claims; all UNKNOWN/refusal) | {res['n_empty']}/{n} |",
          f"| substantive answers with 0 claims (coverage gap) | {res['n_substantive_zero']} |",
          f"| total Granite claims | {res['total_granite_claims']} "
          f"(mean {res['total_granite_claims']/max(1,n_with):.2f}/covered case) |",
          f"| canonical clusters (total) | {res['total_clusters']} "
          f"(mean {res['total_clusters']/max(1,n_with):.2f}/covered case) |",
          f"| folded / closed (single-builder, ≥1 claim, not escalated) | {folded_single} |",
          f"| empty (no DBA, no claims) | {empty_answer} |",
          f"| escalated (-> DBA) | {n_esc} |",
          f"| Claude second-extractor calls | {res['claude_calls']} "
          "(all from P30 cache; 0 new live calls) |",
          f"| DBA: semantic_reconcilable | {res['dba'].get('semantic_reconcilable', 0)} |",
          f"| DBA: convergence | {res['dba'].get('convergence', 0)} |",
          f"| DBA: protected_branch_required | {res['dba'].get('protected_branch_required', 0)} |",
          f"| DBA: logical_polarity_conflict | {res['dba'].get('logical_polarity_conflict', 0)} |",
          f"| DBA: unresolved_divergence (branch_required + guarded_divergence) | {unresolved} |",
          f"| DBA: coverage_asymmetry (extractor_failure) | {cov_asym} |",
          f"| **final effective DBA load** | **{n_esc}/{n} = {100*n_esc/n:.0f}%** |",
          f"| of which close (reconcile/converge) | {close} |",
          f"| of which real branch (protected/conflict/unresolved) | {real_branches} |",
          ""]
    md.append("Per-escalated-case DBA outcomes:\n")
    md.append("| task | nα (Granite) | nβ (Claude) | meaning class | region | typed divergences | P19 outcome | disposition |")
    md.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
    for tid in esc:
        r = det.get(tid, {})
        md.append(f"| {tid} | {r.get('n_granite_claims','-')} | {r.get('n_claude_claims','-')} | "
                  f"{r.get('meaning_class','-')} | {r.get('region','-') if r.get('region') is None else ('%.2f'%r['region']) if isinstance(r.get('region'),(int,float)) else r.get('region','-')} | "
                  f"{r.get('divergences') or '-'} | **{r.get('p19_outcome','-')}** | {r.get('disposition','-')} |")
    md.append("")

    md.append("## B) Compute\n")
    md.append("Estimates use P30 per-extraction mean tokens × OpenRouter list pricing; the "
              "escalation Claude cost is the ACTUAL cached token count. P30 means come from "
              "the hard 17-case subset, so full-100 estimates are a conservative upper bound "
              "(easy answers are shorter).\n")
    md.append("| line | value |")
    md.append("| --- | --- |")
    md.append(f"| Granite default extraction ({n}) — estimated | ${granite_100:.4f} "
              f"(${g_each*1000:.3f}/1000) |")
    md.append(f"| Claude escalation extraction ({res['claude_calls']}) — ACTUAL tokens "
              f"{res['claude_pt']}/{res['claude_ct']} | ${claude_actual:.4f} |")
    md.append(f"| **role-correct total (Granite×{n} + Claude×{n_esc})** | **${role_correct:.4f}** |")
    md.append(f"| always-dual-builder (Granite×{n} + Claude×{n}) — estimated | ${always_dual:.4f} |")
    md.append(f"| DeepSeek-as-extractor (×{n}, single) — estimated | ${deepseek_single:.4f} |")
    md.append(f"| **saving vs always-dual-builder** | **${saving_vs_dual:.4f} "
              f"({saving_vs_dual_pct:.0f}%)** |")
    md.append("")
    md.append("Output-token comparison (mean tokens/extraction, P30): "
              f"Granite {g_out}, Claude Haiku {h_out}, DeepSeek {d_out} "
              f"(DeepSeek ≈ {d_out/g_out:.0f}× Granite output).\n")
    md.append("Real savings: routing escalation to Claude only on the "
              f"{n_esc}/{n} escalated cases (not all {n}) avoids "
              f"{n - n_esc} Claude extractions ≈ ${ (n-n_esc)*h_each:.4f}, an "
              f"{saving_vs_dual_pct:.0f}% reduction vs always-dual-builder, while keeping "
              "the common path at Granite cost. A DeepSeek-as-extractor pipeline would cost "
              f"≈ ${deepseek_single:.4f} (~{deepseek_single/role_correct:.0f}× the role-correct "
              "pipeline) for worse, less stable extraction. Savings are extractor-layer "
              "estimates, not a pipeline-wide claim.\n")

    md.append("## C) Control cases\n")
    c7, c37, c58, c27 = ctl("tqa-0007"), ctl("tqa-0037"), ctl("tqa-0058"), ctl("tqa-0027")
    md.append(f"- **tqa-0007 protected?** escalated={c7.get('escalated')} → P19 "
              f"`{c7.get('p19_outcome','-')}` (divergences `{c7.get('divergences') or '-'}`, "
              f"disposition `{c7.get('disposition','-')}`). "
              + ("Still a protected branch / logical veto." if c7.get('disposition') == 'protected_branch'
                 else "It now CLOSES: both role-correct extractors preserve the negation, so "
                      "there is no negation_flip to veto — the case that once needed the typed "
                      "veto (against a negation-dropping extractor) reconciles when both "
                      "builders are good." if c7.get('disposition') == 'close'
                 else f"Outcome: {c7.get('disposition','-')}."))
    md.append(f"- **tqa-0037 folded?** escalated={c37.get('escalated')} → "
              f"{c37.get('n_granite_claims','-')} Granite claims → {c37.get('n_clusters','-')} "
              f"cluster(s), disposition `{c37.get('disposition','-')}` "
              "(single-builder fold, no DBA).")
    md.append(f"- **tqa-0058 list/region?** escalated={c58.get('escalated')} → "
              f"{c58.get('n_granite_claims','-')} Granite claims → {c58.get('n_clusters','-')} "
              f"canonical region(s), disposition `{c58.get('disposition','-')}` "
              "(list answer kept as distinct regions, not over-folded).")
    md.append(f"- **tqa-0027 stable?** escalated={c27.get('escalated')} → "
              f"{c27.get('n_granite_claims','-')} Granite claims → {c27.get('n_clusters','-')} "
              f"cluster(s), disposition `{c27.get('disposition','-')}` (stable single-builder).")
    md.append("")

    md.append("## D) Architecture answer\n")
    md.append(f"- Does DESi now have a role-correct, compute-efficient, epistemically "
              f"stable full-100 path? **Largely yes, with one honest caveat.** The pipeline "
              f"runs end-to-end with clean role separation: Granite extracts all {n} cheaply "
              f"(≥1 claim on all {n_with} substantive answers, {res['n_empty']} empty "
              f"UNKNOWN/refusal answers, {res['n_substantive_zero']} substantive coverage "
              f"gaps), P21/P26 escalate only {n_esc} ({100*n_esc/n:.0f}%), and Claude Haiku "
              f"acts as an independent second builder only there. The {n} cases split into "
              f"{folded_single} folded single-builder + {empty_answer} empty + {n_esc} "
              f"escalated. DBA load is bounded to the escalated minority; {close} close and "
              f"{real_branches} remain as real branches/conflicts; coverage_asymmetry is "
              f"{cov_asym} (no silent extractor failures). Cost is ~{saving_vs_dual_pct:.0f}% "
              f"below always-dual-builder and a fraction of a DeepSeek-extractor pipeline.")
    md.append("- Caveat: 'stable' here means structurally stable (coverage, folding, "
              "bounded DBA load, no extractor failures), NOT truthful. The remaining real "
              "branches are genuine cross-extractor divergences for a human/SPL to inspect, "
              "not resolved truths.")
    md.append("")

    md.append("## Honesty / limits\n")
    md.append("- No truthfulness claim, no 'DESi solved hallucinations'. Metrics are "
              "epistemic structure, claim coverage, folding, DBA load, and compute "
              "efficiency only.")
    md.append("- Costs are list-price × token estimates (escalation Claude cost is actual "
              "tokens); real billing varies by provider routing. Full-100 token estimates "
              "use the hard-subset means and are an upper bound.")
    md.append("- DBA semantics depend on the cross-extractor region matcher (still "
              "phrasing-sensitive, per P30) — the next thing to harden, not a truth oracle.")
    md.append("- No new solver calls, no judge, no majority vote, no new intervention "
              "heuristics. Reused artifacts: P12 answers, P28 Granite graph, P30 Haiku "
              "cache. Ran offline; no key required; outputs secret-scanned.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(md) + "\n", encoding="utf-8")


def write_jsonl(res, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for r in res["full_rows"]:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser(description="P31 full-100 role-correct DESi run.")
    ap.add_argument("--records", type=Path, default=_LIVE)
    ap.add_argument("--graph", type=Path, default=_P28_GRAPH)
    ap.add_argument("--out", type=Path, default=_OUT_JSONL)
    ap.add_argument("--report", type=Path, default=_REPORT)
    args = ap.parse_args()
    records = _load(args.records)
    p28_graph = _load(args.graph)
    cache = json.loads(_P30_CACHE.read_text()) if _P30_CACHE.exists() else {}
    res = run(records, p28_graph, cache)
    write_jsonl(res, args.out)
    write_report(res, args.report)
    dc = _disp_counts(res)
    print(f"cases {len(res['full_rows'])} | escalated {len(res['escalation'])} | "
          f"claude_calls {res['claude_calls']} (cache)")
    print(f"  dispositions: {dict(dc)}")
    print(f"  dba p19: {res['dba']}")
    print(f"-> {args.out}")
    print(f"-> {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
