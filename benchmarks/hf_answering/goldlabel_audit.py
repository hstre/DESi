#!/usr/bin/env python3
"""Gold-label & task-underdetermination audit PREP (PERIPHERAL).

Before any further solver/prompt/router "fix", check whether the benchmark labels
themselves are epistemically clean. This script does PURELY MECHANICAL extraction
from captured run artifacts -- NO model calls, NO judgment, NO relabeling, NO
change to prompts/routing/evaluator. It surfaces candidate cases where the model
disagrees with the gold label and dumps them for HUMAN annotation.

Prediction source: re_<dataset>.json (the residual-escalation run), which stores,
per item, the DeepSeek prediction under all three FIXED prompt families
(baseline / evidence_strict / entailment_direct) plus the gold label. Claim and
evidence text are joined from the dataset by id (load_verify; deterministic).

Focus (as requested):
  * gold = NOT_ENOUGH_INFO but model predicted SUPPORTS/REFUTES  (over-commitment)
  * gold = SUPPORTS/REFUTES but model predicted NEI              (over-abstention)
  * cases where the prediction changed across prompt families    (calibration-sensitive)

A case is flagged "consistent disagreement" when EVERY answered prompt family
disagrees with gold, and "calibrated-prompt still disagrees" when the family
specifically calibrated to fix that error mode still disagrees -- both are
mechanical signals, not judgments about who is right.
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

_REPORTS = _HERE / "reports"
_RUNS = _REPORTS / "_runs"
_ANNOT = _HERE / "goldlabel_audit_annotations.jsonl"
_NEI = "NOT_ENOUGH_INFO"
_FAMILIES = ("baseline", "evidence_strict", "entailment_direct")
_MATCHED = {"vitaminc": "evidence_strict", "nli_fever": "entailment_direct"}
_OPP = {"SUPPORTS": "REFUTES", "REFUTES": "SUPPORTS"}

# human-only taxonomy (filled during manual annotation; never auto-assigned)
TAXONOMY = (
    "MODEL_CLEARLY_WRONG",
    "GOLD_LABEL_PLAUSIBLE",
    "GOLD_LABEL_QUESTIONABLE",
    "UNDERDETERMINED",
    "PARTIAL_SUPPORT_ONLY",
    "REQUIRES_OUTSIDE_KNOWLEDGE",
    "BENCHMARK_CONVENTION",
    "AMBIGUOUS_PARAPHRASE",
    "LABEL_MAPPING_ARTIFACT",
)
_TAX_DEF = {
    "MODEL_CLEARLY_WRONG": "the gold label is right; the model is simply wrong",
    "GOLD_LABEL_PLAUSIBLE": "gold defensible, model defensible too, but gold is fine",
    "GOLD_LABEL_QUESTIONABLE": "the gold label looks wrong / hard to justify",
    "UNDERDETERMINED": "the evidence does not determine S/R; NEI is defensible",
    "PARTIAL_SUPPORT_ONLY": "evidence partially supports; gold treats partial as full",
    "REQUIRES_OUTSIDE_KNOWLEDGE": "gold needs world knowledge beyond the evidence",
    "BENCHMARK_CONVENTION": "gold follows a dataset convention, not pure entailment",
    "AMBIGUOUS_PARAPHRASE": "wording mismatch makes the relation ambiguous",
    "LABEL_MAPPING_ARTIFACT": "label normalization/mapping artifact, not content",
}


def classify_case(gold: str, preds: dict) -> dict | None:
    """Pure: given gold and {family: label_or_None}, return mechanical audit fields
    or None if no family disagrees (not an error case)."""
    answered = {f: p for f, p in preds.items() if p is not None}
    if not answered:
        return None
    disagree = {f: p for f, p in answered.items() if p != gold}
    if not disagree:
        return None
    pred_set = set(answered.values())
    if gold == _NEI:
        etype = "gold_NEI_model_commits"
        calibrated = "evidence_strict"  # the abstain-calibrated family
    elif _NEI in pred_set:
        etype = "gold_committed_model_NEI"
        calibrated = "entailment_direct"  # the commit-calibrated family
    else:
        etype = "direction_flip"          # gold S/R, model predicted the opposite, no NEI
        calibrated = None
    cal_disagree = bool(calibrated and answered.get(calibrated) is not None
                        and answered[calibrated] != gold)
    return {
        "error_type": etype,
        "n_disagree": len(disagree),
        "n_answered": len(answered),
        "changed_across_prompts": len(pred_set) > 1,
        "consistent_disagreement": len(disagree) == len(answered),
        "calibrated_family": calibrated,
        "calibrated_still_disagrees": cal_disagree,
    }


def extract_candidates(rows: list) -> list:
    """Pure: from artifact rows (id, gold, pred_<family>...) build candidate records
    (without text). Sorted by mechanical suspicion (most suspicious first)."""
    out = []
    for r in rows:
        preds = {f: r.get(f"pred_{f}") for f in _FAMILIES}
        c = classify_case(r["gold"], preds)
        if c is None:
            continue
        out.append({
            "item_id": r["id"], "gold": r["gold"],
            "preds": {f: preds[f] for f in _FAMILIES}, **c,
        })
    # suspicion rank: consistent disagreement, then calibrated-still-disagrees,
    # then more families disagreeing. (mechanical ordering, not a verdict)
    out.sort(key=lambda c: (c["consistent_disagreement"], c["calibrated_still_disagrees"],
                            c["n_disagree"]), reverse=True)
    return out


def orientation_stats(pairs: list) -> dict:
    """Pure mechanical data-quality signal over (claim, evidence) text pairs:
    field lengths and how often the claim field dwarfs the evidence field (a
    possible premise/hypothesis orientation or mapping artifact) + empty fields."""
    import statistics
    if not pairs:
        return {}
    cl = [len(c or "") for c, _ in pairs]
    el = [len(e or "") for _, e in pairs]
    return {
        "n": len(pairs),
        "median_claim_len": int(statistics.median(cl)),
        "median_evidence_len": int(statistics.median(el)),
        "claim_gt_2x_evidence": sum(1 for c, e in pairs
                                    if (e or "").strip() and len(c or "") > 2 * len(e or "")),
        "empty_claim": sum(1 for c, _ in pairs if not (c or "").strip()),
        "empty_evidence": sum(1 for _, e in pairs if not (e or "").strip()),
    }


def _load_rows(dataset: str) -> list | None:
    p = _RUNS / f"re_{dataset}.json"
    if not p.exists():
        return None
    return json.loads(p.read_text())["rows"]


def _load_text(dataset: str, limit: int = 100) -> dict:
    from scifact_runner import load_verify
    _spec, exs = load_verify(dataset, limit)
    return {ex.id: ex for ex in exs}


def build_candidates(top: int = 20):
    datasets = [ds for ds in ("vitaminc", "nli_fever") if _load_rows(ds) is not None]
    if not datasets:
        print("no re_<dataset>.json artifacts found")
        return
    per_ds = {}
    all_cands = []
    for ds in datasets:
        rows = _load_rows(ds)
        cands = extract_candidates(rows)
        text = _load_text(ds)
        for c in cands:
            c["dataset"] = ds
            c["case_id"] = f"{ds}:{c['item_id']}"
            ex = text.get(c["item_id"])
            c["claim"] = ex.claim if ex else ""
            c["evidence"] = ex.evidence if ex else ""
            c["empty_field"] = not c["claim"].strip() or not c["evidence"].strip()
        per_ds[ds] = {"rows": len(rows), "candidates": cands,
                      "orientation": orientation_stats([(ex.claim, ex.evidence) for ex in text.values()])}
        all_cands.extend(cands)
    # mechanical summary
    def summarize(cands):
        from collections import Counter
        et = Counter(c["error_type"] for c in cands)
        return {
            "n": len(cands), "by_type": dict(et),
            "consistent": sum(1 for c in cands if c["consistent_disagreement"]),
            "calibrated_still_disagrees": sum(1 for c in cands if c["calibrated_still_disagrees"]),
        }

    all_cands.sort(key=lambda c: (c["consistent_disagreement"], c["calibrated_still_disagrees"],
                                  c["n_disagree"]), reverse=True)
    top_cands = all_cands[:top]
    _write_report(per_ds, all_cands, top_cands, summarize)
    _write_annotation_template(top_cands)


def _pf(preds):
    return "/".join(str(preds[f]) for f in _FAMILIES)


def _write_report(per_ds, all_cands, top_cands, summarize):
    md = [
        "# Gold-label & task-underdetermination audit — candidates\n",
        "**Audit-prep only.** Purely mechanical extraction from captured run artifacts "
        "(`re_<dataset>.json`): no model calls, no judgment, no relabeling, no change to "
        "prompts / routing / evaluator. Each case is a item where the DeepSeek prediction "
        "disagrees with the benchmark gold label under one or more of the three FIXED "
        "prompt families (baseline / evidence-strict / entailment-direct). The point is to "
        "let a human decide whether the LABEL is clean before any further solver fixing.\n",
        "Mechanical flags (NOT verdicts): *consistent disagreement* = every answered prompt "
        "family disagrees with gold; *calibrated-prompt still disagrees* = the family "
        "specifically calibrated to fix that error mode (evidence-strict for gold-NEI "
        "over-commitment, entailment-direct for gold-committed over-abstention) still "
        "disagrees -- i.e. prompt calibration did not rescue the gold.\n",
        "## Summary (mechanical counts)\n",
        "| dataset | items | error candidates | gold_NEI_model_commits | gold_committed_model_NEI | direction_flip | consistent disagreement | calibrated still disagrees |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for ds, d in per_ds.items():
        s = summarize(d["candidates"])
        bt = s["by_type"]
        md.append(f"| {ds} | {d['rows']} | {s['n']} | {bt.get('gold_NEI_model_commits', 0)} | "
                  f"{bt.get('gold_committed_model_NEI', 0)} | {bt.get('direction_flip', 0)} | "
                  f"{s['consistent']} | {s['calibrated_still_disagrees']} |")
    md += [
        "",
        f"Total error candidates across datasets: **{len(all_cands)}**; of these, "
        f"**{sum(1 for c in all_cands if c['consistent_disagreement'])}** are consistent "
        f"disagreements (all prompts wrong vs gold) and "
        f"**{sum(1 for c in all_cands if c['calibrated_still_disagrees'])}** survive their "
        "calibrated prompt -- the strongest label-suspicion candidates.",
        "",
        "## Data-quality / orientation observations (mechanical)\n",
        "Field lengths and empty fields per dataset (claim = the field mapped from the "
        "dataset's claim/hypothesis column; evidence = the evidence/premise column):\n",
        "| dataset | median claim len | median evidence len | claim > 2x evidence | empty claim | empty evidence |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for ds, d in per_ds.items():
        o = d.get("orientation", {})
        md.append(f"| {ds} | {o.get('median_claim_len')} | {o.get('median_evidence_len')} | "
                  f"{o.get('claim_gt_2x_evidence')} | {o.get('empty_claim')} | {o.get('empty_evidence')} |")
    md += [
        "",
        "> MECHANICAL FLAG (for human verification, NOT auto-corrected): where the **claim** "
        "field is systematically much longer than the **evidence** field, the dataset's "
        "premise/hypothesis columns may be oriented opposite to the verify-task assumption "
        "(\"does EVIDENCE support CLAIM\"). Feeding a short evidence against a long multi-fact "
        "claim would mechanically push the solver toward NEI -- a candidate "
        "LABEL_MAPPING_ARTIFACT that a human should confirm before any solver fixing. Empty "
        "claim/evidence fields are also flagged as data artifacts.",
        "",
        "## Audit taxonomy (human-assigned only)\n",
    ]
    for t in TAXONOMY:
        md.append(f"- **{t}** — {_TAX_DEF[t]}")
    md += [
        "",
        "## Top candidates (ranked by mechanical suspicion; grouped by error type)\n",
        "Fill `human_audit_label` from the taxonomy in "
        "`goldlabel_audit_annotations.jsonl` (template generated alongside).\n",
    ]
    groups = ("gold_NEI_model_commits", "gold_committed_model_NEI", "direction_flip")
    gtitle = {"gold_NEI_model_commits": "gold = NOT_ENOUGH_INFO, model committed (SUPPORTS/REFUTES)",
              "gold_committed_model_NEI": "gold = SUPPORTS/REFUTES, model abstained (NEI)",
              "direction_flip": "gold = SUPPORTS/REFUTES, model predicted the opposite"}
    for grp in groups:
        members = [c for c in top_cands if c["error_type"] == grp]
        if not members:
            continue
        md.append(f"### {gtitle[grp]} — {len(members)} of top {len(top_cands)}\n")
        for c in members:
            md += [
                f"#### `{c['case_id']}`",
                f"- **gold**: {c['gold']} | **preds (baseline/evidence-strict/entailment-direct)**: {_pf(c['preds'])}",
                f"- **changed across prompts**: {c['changed_across_prompts']} | "
                f"**consistent disagreement**: {c['consistent_disagreement']} | "
                f"**calibrated ({c['calibrated_family']}) still disagrees**: {c['calibrated_still_disagrees']}",
                f"- **claim**: {c['claim']}",
                f"- **evidence**: {c['evidence']}",
            ]
            if c.get("empty_field"):
                md.append("- **MECHANICAL FLAG**: empty claim/evidence field (data/mapping artifact)")
            md += [
                "- **human_audit_label**: ______  | **comment**: ______ | **confidence (0-1)**: ____",
                "",
            ]
    md += [
        "## How to annotate\n",
        "1. For each `case_id`, read claim + evidence + gold + the three predictions.\n"
        "2. Assign ONE taxonomy label in `goldlabel_audit_annotations.jsonl` "
        "(`human_audit_label`), add a short `comment`, and a `confidence` 0-1.\n"
        "3. Re-run `python goldlabel_audit.py --score` AFTER annotating to compute "
        "adjusted/clean-label accuracy (it refuses to score until annotations exist).\n",
        "## Honesty / limits\n",
        "- Mechanical extraction only; no automatic judgment; gold labels are NOT "
        "reinterpreted here. Predictions are the captured DeepSeek outputs (mildly "
        "non-deterministic across runs). Claim/evidence are public dataset text. No core, "
        "prompt, routing, or evaluator change.",
    ]
    _REPORTS.mkdir(parents=True, exist_ok=True)
    (_REPORTS / "goldlabel_audit_candidates.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"candidates report -> goldlabel_audit_candidates.md ({len(top_cands)} of {len(all_cands)})")


def _write_annotation_template(top_cands):
    if _ANNOT.exists():
        print(f"annotation file already exists, not overwriting: {_ANNOT.name}")
        return
    lines = []
    for c in top_cands:
        lines.append(json.dumps({
            "case_id": c["case_id"], "dataset": c["dataset"], "gold": c["gold"],
            "preds": c["preds"], "error_type": c["error_type"],
            "human_audit_label": "", "comment": "", "confidence": "",
        }, ensure_ascii=False))
    _ANNOT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"annotation template -> {_ANNOT.name} ({len(top_cands)} blank rows)")


def score_with_annotations():
    """Compute adjusted metrics -- ONLY after the human has filled annotations."""
    if not _ANNOT.exists():
        print("no annotation file; run --candidates first, then annotate")
        return
    annots = [json.loads(l) for l in _ANNOT.read_text().splitlines() if l.strip()]
    filled = [a for a in annots if str(a.get("human_audit_label", "")).strip()]
    if not filled:
        print("annotations exist but none are filled yet; "
              "fill human_audit_label in goldlabel_audit_annotations.jsonl first. "
              "Refusing to compute adjusted accuracy on empty annotations.")
        return
    # only reached once a human has annotated
    from collections import Counter
    questionable = {"GOLD_LABEL_QUESTIONABLE", "UNDERDETERMINED", "PARTIAL_SUPPORT_ONLY",
                    "REQUIRES_OUTSIDE_KNOWLEDGE", "BENCHMARK_CONVENTION", "LABEL_MAPPING_ARTIFACT"}
    by_label = Counter(a["human_audit_label"] for a in filled)
    n_questionable = sum(v for k, v in by_label.items() if k in questionable)
    n_model_wrong = by_label.get("MODEL_CLEARLY_WRONG", 0)
    md = [
        "# Gold-label audit — adjusted scoring (post-annotation)\n",
        f"Annotated cases: {len(filled)}.\n",
        "| human label | count |", "| --- | --- |",
        *[f"| {k} | {v} |" for k, v in sorted(by_label.items())],
        "",
        f"- benchmark-convention / questionable-label disagreements: **{n_questionable}**",
        f"- truly-wrong solver cases (MODEL_CLEARLY_WRONG): **{n_model_wrong}**",
        "",
        "Note: adjusted accuracy is computed only over the annotated candidate set; a full "
        "clean-label re-score requires annotating all error candidates, not just the top set.",
    ]
    (_REPORTS / "goldlabel_audit_adjusted.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"adjusted scoring -> goldlabel_audit_adjusted.md "
          f"(questionable={n_questionable}, model_wrong={n_model_wrong})")


def main() -> int:
    ap = argparse.ArgumentParser(description="Gold-label audit prep (mechanical extraction).")
    ap.add_argument("--candidates", action="store_true", help="extract candidates + report + template")
    ap.add_argument("--top", type=int, default=20)
    ap.add_argument("--score", action="store_true", help="compute adjusted metrics (needs annotations)")
    args = ap.parse_args()
    if args.score:
        score_with_annotations(); return 0
    build_candidates(top=args.top); return 0


if __name__ == "__main__":
    raise SystemExit(main())
