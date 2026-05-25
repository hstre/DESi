#!/usr/bin/env python3
"""P17 driver: apply SPL semantic alignment to the P16 DeepSeek-vs-Granite cases.

Uses the alignment layer (spl_semantic_alignment) to re-characterise the P16 DBA
outcomes: a branch_required driven only by granularity/grouping over the same
semantic region becomes granularity_overlap / semantic_isomorph instead.

Gβ (Granite) source, in order: a persisted artifact
(outputs/granite_beta_graphs.p16.json), else a fresh Granite re-run on the 5
selected cases if OPENROUTER_API_KEY is present (and it is persisted), else none
— in which case only the offline alignment MECHANISM is validated (no real
reduction is claimed). No judge, no vote, no aggregation, no truth decision.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parents[1] / "src"))
sys.path.insert(0, str(_HERE.parents[1] / "gaia"))

from alexandria_adjudication import adjudicate  # noqa: E402
from alexandria_diff_engine import diff_graphs  # noqa: E402
from alexandria_dba_runner import _edges, builder_alpha  # noqa: E402
from alexandria_real_beta_runner import builder_beta_real, select_cases  # noqa: E402
from spl_semantic_alignment import align_graphs, semantic_reoutcome  # noqa: E402

_LIVE = _HERE / "outputs" / "truthfulqa.deepseek-v4.p12.limit100.jsonl"
_GRAPH = _HERE / "outputs" / "truthfulqa.deepseek-v4.p12.claim_graph.limit100.jsonl"
_BETA_STORE = _HERE / "outputs" / "granite_beta_graphs.p16.json"
_GRANITE = "ibm-granite/granite-4.1-8b"


def _load_jsonl(p: Path) -> list[dict]:
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def _get_beta(selected, rec_by_id) -> tuple[dict | None, str]:
    """Return ({task_id: beta_claims}, source-note) or (None, reason)."""
    if _BETA_STORE.exists():
        return json.loads(_BETA_STORE.read_text(encoding="utf-8")), "persisted artifact"
    if os.environ.get("OPENROUTER_API_KEY"):
        store = {}
        for tid in selected:
            ans = rec_by_id[tid].get("raw_model_answer") or rec_by_id[tid].get("model_answer") or ""
            claims, meta = builder_beta_real(ans, "openrouter-alt", _GRANITE)
            if claims is None:
                return None, f"granite re-run failed: {meta.get('status')}"
            store[tid] = claims
        _BETA_STORE.write_text(json.dumps(store, ensure_ascii=False, indent=0), encoding="utf-8")
        return store, f"fresh Granite re-run via OpenRouter ({_GRANITE}), persisted"
    return None, "no persisted Gβ and no OPENROUTER_API_KEY (Granite re-run not possible)"


def _granularity_variant(claims: list[dict]) -> list[dict]:
    """Mechanism unit-test helper: produce a COARSER reconstruction of the SAME
    region by merging all claims that share a subject into one (concatenated
    object). For >=2 claims this guarantees a real granularity (count) difference
    over an identical content region. NOT a model output."""
    if len(claims) < 2:
        return [dict(c) for c in claims]
    by_subj: dict[str, list[dict]] = {}
    for c in claims:
        by_subj.setdefault(c.get("subject", ""), []).append(c)
    out = []
    for subj, group in by_subj.items():
        merged_obj = "; ".join(c.get("object", "") for c in group if c.get("object"))
        out.append({"subject": subj, "predicate": group[0].get("predicate", ""),
                    "object": merged_obj, "confidence": group[0].get("confidence", 0.7),
                    "claim_type": group[0].get("claim_type", "fact")})
    return out


def run(records, graph, selected, beta_store):
    rec_by_id = {r["task_id"]: r for r in records}
    g_by_id = {r["task_id"]: r for r in graph}
    rows = []
    for tid in selected:
        alpha = builder_alpha(g_by_id.get(tid, {}))
        if beta_store is not None:
            beta = beta_store.get(tid, [])
            report = diff_graphs(alpha, beta, source_ref=tid,
                                 alpha_edges=_edges(alpha, grouped=False),
                                 beta_edges=_edges(beta, grouped=True))
            p16 = adjudicate(report).outcome.value
            align = align_graphs(alpha, beta)
            p17 = semantic_reoutcome(p16, align)
            rows.append({"task_id": tid, "n_alpha": len(alpha), "n_beta": len(beta),
                         "p16_outcome": p16, "alignment": align["alignment"],
                         "region_jaccard": align["region_jaccard"],
                         "p17_outcome": p17, "diffs": report.counts_by_type()})
        else:
            # mechanism validation only
            self_align = align_graphs(alpha, [dict(a) for a in alpha])
            var = _granularity_variant(alpha)
            gran_align = align_graphs(alpha, var)
            rows.append({"task_id": tid, "n_alpha": len(alpha),
                         "self_alignment": self_align["alignment"],
                         "granularity_variant_alignment": gran_align["alignment"],
                         "granularity_reconcilable": gran_align["reconcilable"],
                         "n_variant": len(var)})
    return rows


def write_report(rows, beta_note, real, path: Path) -> None:
    md = ["# SPL semantic alignment report (P17)\n",
          "Cross-model claim alignment via spl_core, applied to the P16 "
          "DeepSeek(Alpha)-vs-Granite(Beta) cases, to re-characterise granularity/"
          "grouping-only `branch_required` as same-region alignment. No judge, no "
          "vote, no truth decision. Alignment is canonical-lexical + spl_core "
          "projection signals — NOT a learned meaning embedding (see scope note).\n",
          f"Gβ source: {beta_note}.\n"]

    if real:
        p16c = Counter(r["p16_outcome"] for r in rows)
        p17c = Counter(r["p17_outcome"] for r in rows)
        br_before = p16c.get("branch_required", 0)
        br_after = p17c.get("branch_required", 0)
        md.append("## Outcome re-characterisation (P16 -> P17)\n")
        md.append(f"- branch_required: **{br_before} -> {br_after}** "
                  f"(reduced by {br_before - br_after} via semantic alignment).")
        md.append(f"- P16 outcomes: `{dict(p16c)}`")
        md.append(f"- P17 outcomes: `{dict(p17c)}`")
        md.append("")
        md.append("| task | n_alpha | n_beta | P16 outcome | alignment | region | P17 outcome |")
        md.append("| --- | --- | --- | --- | --- | --- | --- |")
        for r in rows:
            md.append(f"| {r['task_id']} | {r['n_alpha']} | {r['n_beta']} | "
                      f"{r['p16_outcome']} | {r['alignment']} | {r['region_jaccard']} | "
                      f"**{r['p17_outcome']}** |")
        md.append("")
        md.append("## Analysis cases\n")
        for tid in ("tqa-0027", "tqa-0080", "tqa-0007"):
            r = next((x for x in rows if x["task_id"] == tid), None)
            if r:
                md.append(f"- `{tid}`: P16 {r['p16_outcome']} -> P17 **{r['p17_outcome']}** "
                          f"(alignment {r['alignment']}, region_jaccard "
                          f"{r['region_jaccard']}, diffs {r['diffs']}).")
        md.append("")
        # relation_mismatch artefact check
        rel_only = [r for r in rows if set(r["diffs"]) == {"relation_mismatch"}]
        md.append("## Was relation_mismatch only a grouping artefact?\n")
        if rel_only:
            md.append(f"- {len(rel_only)} case(s) had ONLY relation_mismatch; their "
                      "alignment: "
                      + ", ".join(f"{r['task_id']}={r['alignment']}" for r in rel_only)
                      + ". Where the region overlaps, this is a grouping artefact, not a "
                      "real divergence — exactly the spurious branch_required P17 targets.")
        else:
            md.append("- No case had relation_mismatch as the sole diff in this run.")
        md.append("")
        md.append("## Reading\n")
        md.append(f"- **Does SPL alignment reduce spurious branch_required?** "
                  f"{br_before} -> {br_after} on these cases. "
                  + ("Yes, measurable reduction." if br_after < br_before else
                     "No reduction on this run (the divergences were not same-region)."))
        md.append("- **Which became semantic_isomorph / granularity_overlap?** "
                  + (", ".join(f"{r['task_id']}={r['p17_outcome']}" for r in rows
                               if r["p17_outcome"] in ("semantic_isomorph", "granularity_overlap"))
                     or "none") + ".")
        md.append("- **Which stayed real divergence (branch_required)?** "
                  + (", ".join(r["task_id"] for r in rows if r["p17_outcome"] == "branch_required")
                     or "none") + " — these reconstruct genuinely different regions.")
    else:
        md.append("## Builder Beta unavailable — mechanism validation only\n")
        md.append("No persisted Gβ and no key, so the real DeepSeek-vs-Granite reduction "
                  "is NOT computed here (the P16 Granite claims were not persisted; one "
                  "Granite re-run is needed). **No reduction is claimed.** Instead the "
                  "alignment MECHANISM is unit-tested offline on the Alpha graphs:\n")
        md.append("| task | n_alpha | Alpha-self alignment | granularity-variant alignment | reconcilable |")
        md.append("| --- | --- | --- | --- | --- |")
        for r in rows:
            md.append(f"| {r['task_id']} | {r['n_alpha']} | {r['self_alignment']} | "
                      f"{r['granularity_variant_alignment']} | {r['granularity_reconcilable']} |")
        md.append("")
        self_ok = all(r["self_alignment"] == "semantic_isomorph" for r in rows)
        gran_ok = all(r["granularity_reconcilable"] for r in rows if r["n_variant"] != r["n_alpha"])
        md.append(f"- Alpha-vs-Alpha => semantic_isomorph for all: "
                  f"{'PASS' if self_ok else 'mixed'} (identity must be isomorphic).")
        md.append("- Known granularity difference (claims merged into a coarser "
                  "same-region reconstruction) classified as a reconcilable "
                  "`granularity_overlap`, NOT `structurally_divergent`, for every "
                  "multi-subject-collapsing case: "
                  f"{'PASS' if gran_ok else 'see table'} (cases whose claims have "
                  "distinct subjects stay semantic_isomorph, which is also correct). "
                  "This is a UNIT TEST of the mechanism, NOT a claim about real model "
                  "divergence.")
        md.append("- To get the real reduction: provide OPENROUTER_API_KEY and re-run "
                  "(Granite re-runs the 5 cases, Gβ is persisted, real alignment applied).")
    md.append("")

    md.append("## Architecture question: was SPL admissibility or semantic alignment?\n")
    md.append("- **SPL has been an ADMISSIBILITY / entropy layer, not a semantic "
              "alignment layer.** `spl_core` projects a claim into a confidence-shaped "
              "entropy over a SYNTHETIC relation distribution (keyed on the predicate "
              "string) and gates it (E0–E3). That is excellent for 'should this claim "
              "be admitted?', but it carries **no meaning-space / embedding**, so it "
              "cannot natively tell that two differently-worded claims denote the same "
              "fact.")
    md.append("- P17's alignment therefore leans on the CANONICAL form (normalised "
              "s/p/o token overlap) plus spl_core's projection/entropy *neighbourhood* "
              "as a secondary signal. It recognises lexical/structural isomorphism and "
              "region overlap — a real, useful step — but it is NOT semantic "
              "understanding and isomorphy is NOT 'solved'.")
    md.append("- **Architecture limit now visible:** to be a true semantic alignment "
              "layer, SPL needs a genuine meaning space (embeddings or a real relation "
              "matrix), not a confidence-derived entropy. Until then, cross-model "
              "alignment is bounded by lexical/canonical overlap of the extracted claims.")
    md.append("")
    md.append("## Honesty / limits\n")
    md.append("- Alignment is canonical-lexical + spl_core projection signals, NOT a "
              "learned embedding; semantic_isomorph here = lexical/structural isomorphism, "
              "not proven meaning-equivalence.")
    md.append("- Reused spl_core (no new parallel SPL). No new API calls beyond an "
              "optional Granite re-run of the 5 P16 cases. No judge/vote/aggregation, no "
              "new truthfulness scores, no intervention/SPL-core changes.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(md) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="P17 SPL semantic alignment runner.")
    ap.add_argument("--records", type=Path, default=_LIVE)
    ap.add_argument("--graph", type=Path, default=_GRAPH)
    ap.add_argument("--report", type=Path,
                    default=_HERE / "outputs" / "spl_semantic_alignment_report.limit100.md")
    args = ap.parse_args()
    if not args.records.exists() or not args.graph.exists():
        print("Missing P12 live inputs.", file=sys.stderr)
        return 1
    records = _load_jsonl(args.records)
    graph = _load_jsonl(args.graph)
    g_by_id = {r["task_id"]: r for r in graph}
    selected = select_cases(records, g_by_id)
    rec_by_id = {r["task_id"]: r for r in records}
    beta_store, note = _get_beta(selected, rec_by_id)
    rows = run(records, graph, selected, beta_store)
    write_report(rows, note, beta_store is not None, args.report)
    print(f"selected {len(selected)} | Gβ: {note} | real={beta_store is not None} "
          f"-> {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
