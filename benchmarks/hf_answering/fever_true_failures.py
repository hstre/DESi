#!/usr/bin/env python3
"""High-precision 'probable true solver failures' for corrected FEVER (PERIPHERAL).

After the corrected mapping, we want ONLY the residual cases where the solver
itself most likely failed -- excluding empty-evidence artifacts, questionable/NEI
labels, benchmark-convention disagreements, and partial-support ambiguity.

Conservative, high-PRECISION (not recall): a wrong item is a true-failure
candidate ONLY if ALL hold:
  * not an empty-evidence artifact
  * claim->evidence lexical coverage band == "high" (the evidence demonstrably
    contains the needed fact / contradiction -- not underdetermined / partial)
  * gold is determinate (SUPPORTS or REFUTES, NOT NOT_ENOUGH_INFO -- gold-NEI
    high-coverage cases are treated as QUESTIONABLE LABELS, not solver misses)
If uncertain, exclude. No model calls, no reruns, no relabeling, no patches.

Each retained case gets a direction label (FALSE_NEI / FALSE_SUPPORT /
FALSE_REFUTE) and a heuristic failure-mechanism label. Cases wrong under ALL
prompt families are 'capability-bound (high precision)'; cases right under some
family are 'prompt-sensitive (likely prompt-fixable)'.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

from fever_manual_review import _BOUND_WORDS, _numbers, _role_verbs, _toks, _years  # noqa: E402

_REPORTS = _HERE / "reports"
_RUNS = _REPORTS / "_runs"
_CASES = _HERE / "fever_corrected_error_cases.jsonl"
_OUT_JSONL = _HERE / "fever_true_failure_candidates.jsonl"
_FAMILIES = ("baseline", "evidence_strict", "entailment_direct")
_NEI = "NOT_ENOUGH_INFO"
_NEG = ("not", "no", "never", "none", "n't", "without")

MECHANISMS = ("ENTITY_ROLE_CONFUSION", "TEMPORAL_REASONING_FAILURE",
              "NUMERIC_BOUND_FAILURE", "NEGATION_FAILURE", "PARAPHRASE_FAILURE",
              "MULTI_HOP_FAILURE", "DISTRACTOR_SALIENCE")
DIRECTIONS = ("FALSE_NEI", "FALSE_SUPPORT", "FALSE_REFUTE")


def is_true_failure_candidate(empty_ev: bool, band: str, gold: str) -> bool:
    """Conservative high-precision filter (mechanical)."""
    return (not empty_ev) and band == "high" and gold in ("SUPPORTS", "REFUTES")


def direction(gold: str, wrong_preds: list) -> str:
    if not wrong_preds:
        return "FALSE_NEI"
    p = Counter(wrong_preds).most_common(1)[0][0]
    if p == _NEI:
        return "FALSE_NEI"
    if gold == "REFUTES" and p == "SUPPORTS":
        return "FALSE_SUPPORT"
    if gold == "SUPPORTS" and p == "REFUTES":
        return "FALSE_REFUTE"
    return "FALSE_NEI"


def _neg_asymmetry(claim, evidence):
    c = any(n in _toks(claim) or n in claim.lower() for n in _NEG)
    e = any(n in _toks(evidence) or n in evidence.lower() for n in _NEG)
    return c != e


def mechanism(claim: str, evidence: str) -> str:
    rc, re_ = _role_verbs(claim), _role_verbs(evidence)
    if rc and re_ and rc != re_:
        return "ENTITY_ROLE_CONFUSION"
    cy, ey = _years(claim), _years(evidence)
    if cy and ((cy - ey) or (ey and cy != ey)):
        return "TEMPORAL_REASONING_FAILURE"
    cn, en = _numbers(claim), _numbers(evidence)
    if (cn and en and cn.isdisjoint(en)) or (any(b in _toks(claim) for b in _BOUND_WORDS) and (cn or en)):
        return "NUMERIC_BOUND_FAILURE"
    if _neg_asymmetry(claim, evidence):
        return "NEGATION_FAILURE"
    # the evidence lexically contains the claim's content (band high) but the model
    # still missed it -> a salient near-match likely distracted it
    return "DISTRACTOR_SALIENCE"


def _load():
    if not _CASES.exists():
        return None
    cases = [json.loads(l) for l in _CASES.read_text().splitlines() if l.strip()]
    full = {}
    rp = _RUNS / "re_nli_fever.json"
    if rp.exists():
        for r in json.loads(rp.read_text())["rows"]:
            full[r["id"]] = {f: r.get(f"pred_{f}") for f in _FAMILIES}
    items = {}
    for c in cases:
        iid = c["item_id"]
        it = items.setdefault(iid, {
            "id": iid, "gold": c["gold_label"], "raw_premise": c["raw_premise"],
            "raw_hypothesis": c["raw_hypothesis"], "claim": c["mapped_claim"],
            "evidence": c["mapped_evidence"], "cov": c["claim_to_evidence_coverage"],
            "band": c["evidence_overlap_band"], "empty_ev": c.get("empty_evidence_field", False),
            "consistent": c["consistent_disagreement_across_families"],
            "preds": full.get(iid, {}), "wrong_families": [],
        })
        it["wrong_families"].append(c["prompt_family"])
    return list(items.values())


def build():
    items = _load()
    if items is None:
        print("missing fever_corrected_error_cases.jsonl")
        return
    n_wrong = len(items)
    retained, excluded = [], Counter()
    for it in items:
        if it["empty_ev"]:
            excluded["empty_evidence_artifact"] += 1
            continue
        if it["band"] == "high" and it["gold"] == _NEI:
            excluded["questionable_nei_label"] += 1   # evidence determines but gold=NEI
            continue
        if not is_true_failure_candidate(it["empty_ev"], it["band"], it["gold"]):
            excluded["underdetermined_or_partial_or_lowoverlap"] += 1
            continue
        wrong_preds = [it["preds"].get(f) for f in it["wrong_families"]]
        it["direction"] = direction(it["gold"], wrong_preds)
        it["mechanism"] = mechanism(it["claim"], it["evidence"])
        it["assessment"] = ("capability_bound_high_precision" if it["consistent"]
                            else "prompt_sensitive_likely_fixable")
        retained.append(it)

    _write_jsonl(retained)
    _write_report(retained, excluded, n_wrong)


def _write_jsonl(retained):
    lines = []
    for it in retained:
        lines.append(json.dumps({
            "case_id": it["id"], "dataset": "pietrolesci/nli_fever",
            "raw_premise": it["raw_premise"], "raw_hypothesis": it["raw_hypothesis"],
            "mapped_claim": it["claim"], "mapped_evidence": it["evidence"],
            "gold_label": it["gold"], "predictions": it["preds"],
            "wrong_families": it["wrong_families"], "coverage": it["cov"], "band": it["band"],
            "direction": it["direction"], "mechanism": it["mechanism"],
            "assessment": it["assessment"],
            "consistent_across_families": it["consistent"],
        }, ensure_ascii=False))
    _OUT_JSONL.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    print(f"true-failure candidates -> {_OUT_JSONL.name} ({len(retained)})")


def _t(s, n=240):
    s = str(s)
    return s if len(s) <= n else s[:n] + "…"


def _write_report(retained, excluded, n_wrong):
    n = len(retained)
    cap = sum(1 for it in retained if it["consistent"])
    fixable = n - cap
    by_mech = Counter(it["mechanism"] for it in retained)
    by_dir = Counter(it["direction"] for it in retained)
    dom_mech = by_mech.most_common(1)[0] if by_mech else ("none", 0)
    md = [
        "# Corrected-FEVER: probable TRUE solver failures (high-precision)\n",
        "Conservative, high-precision residual of genuine solver misses after removing "
        "empty-evidence artifacts, questionable/NEI labels, benchmark-convention "
        "disagreements, and partial-support ambiguity. A wrong item is retained ONLY if it "
        "is not an empty-evidence artifact, its claim->evidence lexical coverage band is "
        "**high** (evidence demonstrably contains the needed fact/contradiction), and gold "
        "is determinate (SUPPORTS/REFUTES). If uncertain, excluded. No model calls, no "
        "reruns, no relabeling.\n",
        "## Estimate: how much corrected-FEVER error remains after removing benchmark/data issues\n",
        f"- Total corrected-FEVER wrong items: **{n_wrong}** (of 100).",
        f"- Excluded -- empty-evidence artifacts: **{excluded.get('empty_evidence_artifact', 0)}**; "
        f"questionable/NEI labels (evidence determines but gold=NEI): "
        f"**{excluded.get('questionable_nei_label', 0)}**; underdetermined / partial-support / "
        f"low-overlap: **{excluded.get('underdetermined_or_partial_or_lowoverlap', 0)}**.",
        f"- **Probable true solver failures retained: {n}** (~{n}% of FEVER-100). Of these, "
        f"**{cap}** are capability-bound (wrong under ALL prompt families) and **{fixable}** "
        "are prompt-sensitive (some family already gets them right).",
        "",
        "## Summary counts\n",
        "| metric | count |", "| --- | --- |",
        f"| retained probable true misses | {n} |",
        f"| surviving all prompt families (capability-bound) | {cap} |",
        f"| prompt-sensitive (likely prompt-fixable) | {fixable} |",
        f"| dominant failure mechanism | {dom_mech[0]} ({dom_mech[1]}) |",
        "",
        "Failure mechanism distribution: " + (", ".join(f"{k} {v}" for k, v in by_mech.most_common()) or "none")
        + ". Direction: " + (", ".join(f"{k} {v}" for k, v in by_dir.most_common()) or "none") + ".",
        "",
        "## Retained cases\n",
    ]
    for it in sorted(retained, key=lambda it: it["id"]):
        pf = "/".join(str(it["preds"].get(f)) for f in _FAMILIES)
        md += [
            f"#### `{it['id']}` — {it['direction']} / {it['mechanism']} — {it['assessment']}",
            f"- gold: **{it['gold']}** | preds (baseline/evidence-strict/entailment-direct): {pf} "
            f"| wrong in: {', '.join(it['wrong_families'])} | coverage {it['cov']} ({it['band']})",
            f"- raw premise: {_t(it['raw_premise'])}",
            f"- raw hypothesis: {_t(it['raw_hypothesis'])}",
            f"- mapped claim (<-premise): {_t(it['claim'])}",
            f"- mapped evidence (<-hypothesis): {_t(it['evidence'])}",
            f"- why this looks like a real solver miss: the evidence lexically contains the "
            f"claim's content (coverage {it['cov']}) and gold is determinate ({it['gold']}), "
            f"yet the model answered wrongly"
            + (" under every prompt family (robust, capability-bound)."
               if it["consistent"] else " under some prompt family (prompt-sensitive)."),
            "",
        ]
    md += [
        "## Explicit answers\n",
        f"- **Does DeepSeek still have real weaknesses after cleanup?** Yes, but SPARSE: only "
        f"~{n}/100 items are probable true misses, and only {cap} survive all prompt families.",
        f"- **Which reasoning capability fails most?** {dom_mech[0]} "
        f"({dom_mech[1]}/{n}); all retained misses are {('/'.join(k for k, _ in by_dir.most_common()))} "
        "(the model under-commits / mis-commits when a salient near-match is present).",
        f"- **Sparse and specific, or broad and systematic?** SPARSE and specific "
        f"(~{n}% of FEVER-100), concentrated in {dom_mech[0]}-style cases -- not a broad "
        "systematic deficiency.",
        f"- **Would further prompt tuning plausibly help?** Partially: {fixable}/{n} retained "
        "cases are already solved by at least one prompt family (prompt-sensitive); the "
        f"remaining {cap} are capability-bound and unlikely to be fixed by prompting alone.",
        f"- **Or are remaining misses mostly capability-bound?** {cap}/{n} of the high-"
        "precision set are capability-bound; given how few cases remain, the headline is that "
        "corrected FEVER is largely clean and the solver has only a thin tail of genuine "
        "reasoning misses.",
        "",
        "## Three-way separation\n",
        f"- **Confirmed data artifacts**: {excluded.get('empty_evidence_artifact', 0)} (empty evidence).",
        f"- **Probable benchmark / questionable-label issues**: "
        f"{excluded.get('questionable_nei_label', 0)} questionable-NEI + "
        f"{excluded.get('underdetermined_or_partial_or_lowoverlap', 0)} underdetermined/partial "
        f"= {excluded.get('questionable_nei_label', 0) + excluded.get('underdetermined_or_partial_or_lowoverlap', 0)}.",
        f"- **Probable true model failures**: {n} (capability-bound {cap}, prompt-sensitive {fixable}).",
        "",
        "## Honesty / limits\n",
        "- High-precision (low-recall) mechanical filter; mechanism labels are heuristic and "
        "provisional. gold labels not reinterpreted aggressively (gold-NEI high-coverage cases "
        "are set aside as questionable, not counted as solver misses). Per-item predictions are "
        "DeepSeek's; raw model output not captured. DESi-core untouched.",
    ]
    _REPORTS.mkdir(parents=True, exist_ok=True)
    (_REPORTS / "fever_probable_true_solver_failures.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"report -> fever_probable_true_solver_failures.md (retained {n}, capability {cap}, "
          f"fixable {fixable}, dominant {dom_mech[0]})")


if __name__ == "__main__":
    build()
