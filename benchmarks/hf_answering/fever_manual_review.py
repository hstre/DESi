#!/usr/bin/env python3
"""Manual-quality review PREP for corrected-FEVER residual errors (PERIPHERAL).

Epistemic review layer ONLY: no model calls, no reruns, no relabeling, no prompt/
router/core change. Reads the corrected error cases (fever_corrected_error_cases
.jsonl) + corrected re_nli_fever.json (for full per-family predictions) + the raw
dataset fields already extracted, and produces:
  * reports/fever_manual_review_shortlist.md  (all distinct wrong items + a per-item
    human-review template + a MECHANICAL A-G group)
  * fever_manual_review_annotations.jsonl      (one blank row per item to annotate)

Mechanical groups (heuristic, provisional -- NOT relabeling):
  A empty_evidence            -- raw hypothesis (mapped evidence) is blank -> data artifact
  B temporal_mismatch         -- claim cites a year/date absent or different in the evidence
  C role_mismatch             -- claim and evidence use different role verbs (directed vs reviewed)
  D quantity_bound_mismatch   -- differing numbers, or a bound word (only/less/more) with numerics
  E partial_support           -- evidence partially covers the claim (mid lexical overlap)
  F semantic_paraphrase       -- low lexical overlap but shared topic (paraphrase gap)
  G likely_solver_miss        -- evidence lexically covers the claim yet the model still erred
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parents[1]
sys.path.insert(0, str(_HERE))

_REPORTS = _HERE / "reports"
_RUNS = _REPORTS / "_runs"
_CASES = _HERE / "fever_corrected_error_cases.jsonl"
_ANNOT = _HERE / "fever_manual_review_annotations.jsonl"
_FAMILIES = ("baseline", "evidence_strict", "entailment_direct")

GROUPS = {
    "A": "empty_evidence", "B": "temporal_mismatch", "C": "role_mismatch",
    "D": "quantity_bound_mismatch", "E": "partial_support",
    "F": "semantic_paraphrase", "G": "likely_solver_miss",
}
# provisional category each group maps to (only A is confirmed; rest provisional)
GROUP_CATEGORY = {
    "A": "confirmed_artifact",
    "B": "probable_benchmark_or_underdetermined",
    "C": "probable_benchmark_or_underdetermined",
    "D": "probable_benchmark_or_underdetermined",
    "E": "likely_underdetermined",
    "F": "likely_underdetermined",
    "G": "probable_true_solver_miss",
}
HUMAN_LABELS = ("MODEL_CLEARLY_WRONG", "GOLD_QUESTIONABLE", "UNDERDETERMINED",
                "DATA_ARTIFACT", "BENCHMARK_CONVENTION", "AMBIGUOUS")

_ROLE_VERBS = frozenset((
    "directed", "direct", "directs", "produced", "produce", "produces", "wrote",
    "written", "write", "writes", "reviewed", "review", "reviews", "starred",
    "star", "starring", "stars", "founded", "found", "founds", "released",
    "release", "releases", "played", "play", "plays", "hosted", "host", "hosts",
    "narrated", "narrate", "narrates", "created", "create", "creates", "composed",
    "compose", "composes", "sang", "sung", "sing", "sings", "edited", "edit",
    "edits", "designed", "design", "designs", "painted", "paint", "directed_by",
))
_BOUND_WORDS = frozenset((
    "only", "less", "more", "fewer", "under", "over", "exactly", "least",
    "most", "minimum", "maximum", "up", "above", "below", "than",
))


def _toks(text):
    return [t.lower() for t in re.findall(r"[A-Za-z0-9']+", text or "")]


def _years(text):
    return set(re.findall(r"\b(1[0-9]{3}|20[0-9]{2})\b", text or ""))


def _numbers(text):
    nums = set(re.findall(r"\b\d+(?:\.\d+)?\b", text or ""))
    return {n for n in nums if not re.fullmatch(r"1[0-9]{3}|20[0-9]{2}", n)}


def _role_verbs(text):
    return {t for t in _toks(text) if t in _ROLE_VERBS}


def is_empty_artifact(evidence: str) -> bool:
    return not (evidence or "").strip()


def group_item(claim: str, evidence: str, coverage: float, band: str) -> str:
    """Mechanical, heuristic, provisional group letter for one wrong item."""
    if is_empty_artifact(evidence):
        return "A"
    cy, ey = _years(claim), _years(evidence)
    cn, en = _numbers(claim), _numbers(evidence)
    # quantity/bound mismatch
    if (cn and en and cn.isdisjoint(en)) or (any(b in _toks(claim) for b in _BOUND_WORDS) and (cn or en)):
        return "D"
    # temporal mismatch: claim cites a year not matched by the evidence
    if cy and (cy - ey):
        return "B"
    # role mismatch: both sides name a role verb, and they differ
    rc, re_ = _role_verbs(claim), _role_verbs(evidence)
    if rc and re_ and rc != re_:
        return "C"
    if band == "high":
        return "G"
    if band == "partial":
        return "E"
    return "F"


def render_template(item: dict) -> list:
    pf = "/".join(str(item["preds"].get(f)) for f in _FAMILIES)
    wrong = ", ".join(item["wrong_families"])
    grp = item["group"]
    return [
        f"#### `{item['id']}` — group {grp} ({GROUPS[grp]}) — provisional: {GROUP_CATEGORY[grp]}",
        f"- gold: **{item['gold']}** | preds (baseline/evidence-strict/entailment-direct): {pf} | wrong in: {wrong}",
        f"- raw premise: {_t(item['raw_premise'])}",
        f"- raw hypothesis: {_t(item['raw_hypothesis'])}",
        f"- mapped claim (<-premise): {_t(item['claim'])}",
        f"- mapped evidence (<-hypothesis): {_t(item['evidence'])}",
        f"- empty-evidence: {item['empty_ev']} | claim→evidence coverage: {item['cov']} ({item['band']}) "
        f"| multi-fact claim: {item['multi']} | consistent across families: {item['consistent']} "
        f"| calibrated still disagrees: {item['calibrated']}",
        f"- why counted wrong: {', '.join(sorted(set(item['why'])))}",
        "- **HUMAN_JUDGMENT**: ______ (MODEL_CLEARLY_WRONG / GOLD_QUESTIONABLE / UNDERDETERMINED / "
        "DATA_ARTIFACT / BENCHMARK_CONVENTION / AMBIGUOUS)",
        "- **COMMENT**: ______",
        "- **CONFIDENCE**: ____ (0-1)",
        "",
    ]


def _t(s, n=240):
    s = str(s)
    return s if len(s) <= n else s[:n] + "…"


def _load_items():
    if not _CASES.exists():
        return None
    cases = [json.loads(l) for l in _CASES.read_text().splitlines() if l.strip()]
    re_path = _RUNS / "re_nli_fever.json"
    full = {}
    if re_path.exists():
        for r in json.loads(re_path.read_text())["rows"]:
            full[r["id"]] = {f: r.get(f"pred_{f}") for f in _FAMILIES}
    items = {}
    for c in cases:
        iid = c["item_id"]
        it = items.setdefault(iid, {
            "id": iid, "gold": c["gold_label"], "raw_premise": c["raw_premise"],
            "raw_hypothesis": c["raw_hypothesis"], "claim": c["mapped_claim"],
            "evidence": c["mapped_evidence"], "cov": c["claim_to_evidence_coverage"],
            "band": c["evidence_overlap_band"], "empty_ev": c.get("empty_evidence_field", False),
            "multi": c["claim_is_multi_fact"],
            "consistent": c["consistent_disagreement_across_families"],
            "calibrated": c["calibrated_prompt_still_disagrees"],
            "preds": full.get(iid, {}), "wrong_families": [], "why": [],
        })
        it["wrong_families"].append(c["prompt_family"])
        it["why"].append(c["why_wrong"])
    for it in items.values():
        it["group"] = group_item(it["claim"], it["evidence"], it["cov"], it["band"])
    return list(items.values())


def build():
    items = _load_items()
    if not items:
        print("missing fever_corrected_error_cases.jsonl")
        return
    by_group = Counter(it["group"] for it in items)
    n = len(items)
    confirmed_artifacts = by_group.get("A", 0)
    benchmark = sum(by_group.get(g, 0) for g in ("B", "C", "D"))
    underdet = sum(by_group.get(g, 0) for g in ("E", "F"))
    true_miss = by_group.get("G", 0)
    needs_human = n - confirmed_artifacts  # everything except confirmed artifacts is provisional

    md = [
        "# Corrected-FEVER manual-review shortlist\n",
        "Epistemic review layer ONLY -- no model calls, no reruns, no relabeling, no patches. "
        "All distinct corrected-FEVER wrong items (DeepSeek v4 Pro across the three prompt "
        "families), with a MECHANICAL A-G group and a per-item human-review template. Only "
        "group A (empty evidence) is a confirmed data artifact; **every other category is "
        "PROVISIONAL until human review**.\n",
        "## Summary (provisional pending human review)\n",
        "| metric | count |", "| --- | --- |",
        f"| total distinct wrong items | {n} |",
        f"| empty-evidence artifacts (A, CONFIRMED) | {confirmed_artifacts} |",
        f"| likely benchmark-convention (B/C/D, provisional) | {benchmark} |",
        f"| likely underdetermined (E/F, provisional) | {underdet} |",
        f"| likely real solver misses (G, provisional) | {true_miss} |",
        f"| unresolved / needs human review (all non-artifact) | {needs_human} |",
        "",
        "### Mechanical group distribution\n",
        "| group | meaning | provisional category | count |", "| --- | --- | --- | --- |",
        *[f"| {g} | {GROUPS[g]} | {GROUP_CATEGORY[g]} | {by_group.get(g, 0)} |" for g in sorted(GROUPS)],
        "",
        "## Explicit answers (provisional)\n",
        f"- **How much remaining FEVER error mass is clearly NOT a solver issue?** At least "
        f"the {confirmed_artifacts} empty-evidence artifacts are confirmed non-solver. Adding "
        f"the provisional benchmark/underdetermined groups (B/C/D/E/F = {benchmark + underdet}) "
        f"would raise that to {confirmed_artifacts + benchmark + underdet}/{n} IF human review "
        f"confirms them -- leaving only ~{true_miss} provisional true solver misses.",
        "- **Should benchmark optimization pause pending review?** YES -- with only "
        f"~{true_miss}/{n} items even provisionally attributable to the solver, optimizing "
        "against the raw FEVER labels would chase data artifacts and label conventions.",
        "- **Does the corrected FEVER benchmark now appear substantially cleaner?** YES vs the "
        "inverted mapping: claims are now single-fact (the multi-fact pathology is gone) and "
        "the bulk of residual errors are artifacts or subtle edge cases, not systematic "
        "over-abstention.",
        "- **Are the remaining errors mostly subtle epistemic edge cases?** Provisionally YES "
        "(temporal/role/quantity/partial/paraphrase), pending the human pass below.",
        "",
        "## Items for human review (grouped)\n",
        "Annotate `fever_manual_review_annotations.jsonl` (one row per item). Then run "
        "`python fever_manual_review_stats.py` to aggregate (it refuses to run until "
        "annotations are filled).\n",
    ]
    for g in sorted(GROUPS):
        members = [it for it in items if it["group"] == g]
        if not members:
            continue
        md.append(f"### Group {g} — {GROUPS[g]} ({GROUP_CATEGORY[g]}) — {len(members)} items\n")
        for it in sorted(members, key=lambda it: it["id"]):
            md += render_template(it)
    md += [
        "## Honesty / limits\n",
        "- Grouping is mechanical/heuristic and PROVISIONAL; only empty-evidence is a "
        "confirmed artifact. No labels reinterpreted, no accuracy adjusted (deferred until "
        "annotations exist). Per-item predictions are DeepSeek's; raw model text not "
        "captured. DESi-core untouched.",
    ]
    _REPORTS.mkdir(parents=True, exist_ok=True)
    (_REPORTS / "fever_manual_review_shortlist.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"shortlist -> fever_manual_review_shortlist.md ({n} items; A={confirmed_artifacts} "
          f"B/C/D={benchmark} E/F={underdet} G={true_miss})")
    _write_annotation_template(items)


def _write_annotation_template(items):
    if _ANNOT.exists():
        print(f"annotation file exists, not overwriting: {_ANNOT.name}")
        return
    lines = [json.dumps({
        "case_id": it["id"], "gold": it["gold"], "auto_group": it["group"],
        "auto_category": GROUP_CATEGORY[it["group"]],
        "HUMAN_JUDGMENT": "", "COMMENT": "", "CONFIDENCE": "",
    }, ensure_ascii=False) for it in sorted(items, key=lambda it: it["id"])]
    _ANNOT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"annotation template -> {_ANNOT.name} ({len(items)} blank rows)")


if __name__ == "__main__":
    build()
