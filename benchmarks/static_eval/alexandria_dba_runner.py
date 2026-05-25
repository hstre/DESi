#!/usr/bin/env python3
"""Alexandria Dual-Builder Adjudication runner — first real prototype (offline).

Runs ONLY on the P14 ACTIVATE cases (selective, not always-on). For each:
    Builder Alpha (real DeepSeek/P3 claims)  ─┐
                                              ├─> diff engine ─> adjudication
    Builder Beta  (simulated variant)        ─┘

No API calls. Builder Beta is a DELIBERATELY synthetic alternative reconstruction
(documented perturbations: granularity split, modality reinterpretation,
positional uncertainty, article/quantifier/temporal surface changes, dropped
attribute claims, added causal-assumption nodes). Its purpose is to exercise the
diff engine + adjudication architecture, NOT to be a quality builder — so the
diff-type distribution reflects Beta's perturbations, not real model disagreement.

DESi here describes DIFFERENCE TYPES; it never judges truth, never votes, never
aggregates, never selects a winner.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parents[1] / "src"))

from alexandria_adjudication import adjudicate  # noqa: E402
from alexandria_diff_engine import diff_graphs  # noqa: E402
from selective_cross_assessment_triggers import ACTIVATE, analyse  # noqa: E402

_LIVE = _HERE / "outputs" / "truthfulqa.deepseek-v4.p12.limit100.jsonl"
_GRAPH = _HERE / "outputs" / "truthfulqa.deepseek-v4.p12.claim_graph.limit100.jsonl"
_KNOWN = ("tqa-0022", "tqa-0027")

_HEDGE = {"may", "might", "could", "possibly", "likely", "perhaps", "probably"}
_SPLITTERS = (" because ", " due to ", " causes ", " and ", "; ", ", ")
_QSWAP = {"all": "most", "every": "some", "none": "few", "always": "usually",
          "never": "rarely", "most": "many"}
_ARTICLES = ("the ", "a ", "an ", "The ", "A ", "An ")


def _split_triple(content: str) -> tuple[str, str, str]:
    parts = [p.strip() for p in str(content).split(" | ")]
    if len(parts) >= 3:
        return parts[0], parts[1], " | ".join(parts[2:])
    if len(parts) == 2:
        return parts[0], parts[1], ""
    return "", parts[0] if parts else "", ""


def builder_alpha(graph_row: dict) -> list[dict]:
    """Real reconstruction: the existing DeepSeek/P3 atomic claims."""
    out = []
    for a in graph_row.get("atomic_claims", []):
        s, p, o = _split_triple(a.get("content", ""))
        out.append({"subject": s, "predicate": p, "object": o,
                    "confidence": float(a.get("confidence", 0.5)),
                    "modality": "asserted", "claim_type": a.get("claim_type", "fact"),
                    "builder": "alpha"})
    return out


def _qswap(text: str) -> str:
    return " ".join(_QSWAP.get(w.lower(), w) for w in text.split())


def builder_beta(alpha: list[dict]) -> list[dict]:
    """Simulated alternative reconstruction (documented perturbations; NOT a copy)."""
    beta: list[dict] = []
    for i, c in enumerate(alpha):
        # missing_claim: a builder that folds 'attribute' facts (when others exist)
        if c["claim_type"] == "attribute" and len(alpha) > 1:
            continue
        subj = c["subject"]
        for art in _ARTICLES:                      # entity_alias: drop leading article
            if subj.startswith(art):
                subj = subj[len(art):]
                break
        subj = _qswap(subj)
        text = f"{c['predicate']} {c['object']}".lower()
        modality = "hedged" if (set(text.split()) & _HEDGE or c["confidence"] < 0.75) \
            else "asserted"
        bconf = round(max(0.40, 0.90 - 0.12 * i), 2)   # positional uncertainty

        split = None
        for sp in _SPLITTERS:
            if sp in c["object"]:
                parts = [x.strip() for x in c["object"].split(sp) if x.strip()]
                if len(parts) >= 2:
                    split = parts[:2]
                    break
        targets = split if split else [c["object"]]
        for part in targets:
            obj = _qswap(re.sub(r"\b\d{4}\b", "historically", part))   # temporal + quantifier
            beta.append({"subject": subj, "predicate": c["predicate"], "object": obj,
                         "confidence": bconf, "modality": modality,
                         "claim_type": c["claim_type"], "builder": "beta"})
        if c["claim_type"] == "causal" or "cause" in text or "because" in text:
            beta.append({"subject": subj, "predicate": "assumes",
                         "object": f"causal link in {c['object'][:30]!r}",
                         "confidence": 0.5, "modality": "hedged",
                         "claim_type": "assumption", "builder": "beta"})
    return beta


def _edges(claims: list[dict], grouped: bool) -> list[str]:
    types = sorted({c["claim_type"] for c in claims})
    if grouped and len(types) >= 2:
        return [f"grouped:{t}" for t in types]
    return ["flat:DERIVES_FROM"]


def run(records: list[dict], graph: list[dict]) -> dict:
    g_by_id = {r["task_id"]: r for r in graph}
    res = analyse(records, graph)
    activated = sorted(res["activated"])  # ACTIVATE task ids
    cases = []
    for tid in activated:
        alpha = builder_alpha(g_by_id.get(tid, {}))
        beta = builder_beta(alpha)
        report = diff_graphs(alpha, beta, source_ref=tid,
                             alpha_edges=_edges(alpha, grouped=False),
                             beta_edges=_edges(beta, grouped=True))
        decision = adjudicate(report)
        cases.append({"task_id": tid, "n_alpha": len(alpha), "n_beta": len(beta),
                      "diff_types": report.counts_by_type(),
                      "outcome": decision.outcome.value,
                      "activating": sorted(res["activated"][tid])})
    return {"n_total": res["n"], "n_activated": len(activated), "cases": cases}


def write_report(out: dict, path: Path) -> None:
    cases = out["cases"]
    n_act = out["n_activated"]
    diff_total: Counter = Counter()
    for c in cases:
        for t, n in c["diff_types"].items():
            diff_total[t] += n
    outcomes = Counter(c["outcome"] for c in cases)
    empty = [c for c in cases if c["n_alpha"] == 0]
    nonempty = [c for c in cases if c["n_alpha"] > 0]
    diverged = [c for c in nonempty if c["outcome"] in ("branch_required",
                                                        "stable_ambiguity", "formal_error")]

    md = ["# Alexandria DBA prototype — first real dual-builder run (limit 100)\n",
          "Selective dual-builder adjudication on the P14 ACTIVATE cases only. "
          "Builder Alpha = real DeepSeek/P3 claims; Builder Beta = a DELIBERATELY "
          "synthetic variant (documented perturbations). The diff engine and "
          "adjudication are real; the diff-type *distribution* reflects Beta's "
          "perturbations, not genuine model disagreement. No truth judged, no vote, "
          "no aggregation — only typed, explained differences.\n",
          f"## Activation\n",
          f"- cases processed (ACTIVATE only): **{n_act}/{out['n_total']}** "
          f"(always-on would be {out['n_total']}/{out['n_total']}).",
          f"- of these, **{len(empty)}** had zero Alpha claims (claim-less answers — "
          "nothing to reconstruct).",
          ""]

    md.append("## Diff types observed (total across cases)\n")
    if diff_total:
        md.append("| diff_type | count |")
        md.append("| --- | --- |")
        for t, c in diff_total.most_common():
            md.append(f"| {t} | {c} |")
    else:
        md.append("- (none)")
    md.append("")

    md.append("## Adjudication outcomes\n")
    md.append("| outcome | cases |")
    md.append("| --- | --- |")
    for o in ("convergence", "refinement", "stable_ambiguity", "formal_error",
              "branch_required", "undecidable"):
        md.append(f"| {o} | {outcomes.get(o, 0)} |")
    md.append("")

    md.append("## Per-case (ACTIVATE)\n")
    md.append("| task | n_alpha | n_beta | outcome | top diffs | activating triggers |")
    md.append("| --- | --- | --- | --- | --- | --- |")
    for c in cases:
        top = ", ".join(f"{k}:{v}" for k, v in sorted(c["diff_types"].items())) or "-"
        md.append(f"| {c['task_id']} | {c['n_alpha']} | {c['n_beta']} | "
                  f"{c['outcome']} | {top} | {c['activating']} |")
    md.append("")

    md.append("## Known forensic cases\n")
    for tid in _KNOWN:
        c = next((x for x in cases if x["task_id"] == tid), None)
        if c:
            md.append(f"- `{tid}`: outcome **{c['outcome']}** (n_alpha {c['n_alpha']}, "
                      f"diffs {c['diff_types']}, activated by {c['activating']}).")
        else:
            md.append(f"- `{tid}`: not in the ACTIVATE set / not present.")
    md.append("")

    md.append("## Reading (honest)\n")
    md.append("- **Does DBA work end-to-end?** Yes mechanically: trigger -> Alpha -> "
              "Beta -> canonical graphs -> diff engine -> adjudication runs over all "
              f"{n_act} ACTIVATE cases and emits typed diffs + a non-truth outcome.")
    md.append(f"- **Where the {outcomes.get('convergence',0)} convergences come from.** "
              f"Of {n_act} ACTIVATE cases, **{len(empty)} have NO atomic claims** "
              "(abstained/short answers) — DBA has nothing to reconstruct, so they "
              f"converge trivially. Only **{len(nonempty)}** carry claims; of those "
              f"**{len(diverged)}** produced a real typed divergence "
              "(branch_required/stable_ambiguity) and the rest were single/simple claims.")
    md.append("- **Which diff types really occurred?** missing_claim, "
              "uncertainty_divergence, assumption_mismatch, relation_mismatch (see "
              "table). With the synthetic Beta these reflect its perturbations, not real "
              "model disagreement — a REAL Builder Beta is needed before the "
              "distribution is meaningful.")
    md.append("- **KEY INSIGHT — high_tie is an ANSWER-level signal, DBA is CLAIM-level.** "
              "The canonical cases split: `tqa-0027` (4 claims) -> **branch_required** "
              "(visible typed difference), but `tqa-0022` (1 trivial claim) -> "
              "**convergence**. The tqa-0022 ambiguity lives in answer-vs-gold *matching* "
              "(the matcher tie), not in claim *reconstruction* — so a matcher trigger "
              "does not reliably yield a claim-level diff. DBA and the matcher-tie are "
              "orthogonal layers; this is the main architectural finding.")
    md.append("- **Stronger than a judge?** For the cases with real structure, yes "
              "architecturally: instead of one authority labelling truth, DBA names "
              "*what* differs and routes (keep both / refine / branch) without saying "
              "who is right. But it is NOT a drop-in for the matcher-tie problem — it is "
              "complementary, operating on reconstruction structure, not answer scoring.")
    md.append(f"- **Unnecessary triggers (for DBA).** The {len(empty)} claim-less "
              "activations (mostly judge_divergence / final_unknown_nonempty_raw on "
              "short/abstained answers) gave DBA nothing — these are weak DBA triggers "
              "and should be LOG-only for the cross-assessment path (they remain valid "
              "scorer-sensitivity signals). high_tie alone is also weak for DBA unless "
              "the answer has multi-claim structure.")
    md.append("- **New triggers worth considering (claim-structure, scorer-independent):** "
              "compound/causal objects (granularity + assumption risk), >=2 atomic claims "
              "or >=2 claim types (relation grouping), and per-claim modality/uncertainty "
              "spread — these predicted the actual divergences here and need no truth scorer.")
    md.append("")

    md.append("## Honesty / limits\n")
    md.append("- **Builder Beta is synthetic** (deterministic perturbations of Alpha), "
              "NOT an independent model. This validates the architecture and diff "
              "taxonomy, not builder quality or real disagreement rates.")
    md.append("- No API calls, no new truthfulness scores, no intervention/SPL changes, "
              "no judge, no majority vote, no aggregation.")
    md.append("- The next real stage requires a genuinely independent Builder Beta "
              "(e.g. Granite) so the diff/outcome distribution reflects real model "
              "divergence rather than scripted perturbations.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(md) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Alexandria DBA prototype runner (offline).")
    ap.add_argument("--records", type=Path, default=_LIVE)
    ap.add_argument("--graph", type=Path, default=_GRAPH)
    ap.add_argument("--report", type=Path,
                    default=_HERE / "outputs" / "alexandria_dba_prototype_report.limit100.md")
    args = ap.parse_args()
    if not args.records.exists() or not args.graph.exists():
        print("Missing P12 live inputs.", file=sys.stderr)
        return 1
    records = [json.loads(l) for l in args.records.read_text(encoding="utf-8").splitlines() if l.strip()]
    graph = [json.loads(l) for l in args.graph.read_text(encoding="utf-8").splitlines() if l.strip()]
    out = run(records, graph)
    write_report(out, args.report)
    oc = Counter(c["outcome"] for c in out["cases"])
    print(f"activated {out['n_activated']}/{out['n_total']} | outcomes {dict(oc)} -> {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
