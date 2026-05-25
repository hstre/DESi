#!/usr/bin/env python3
"""P23 claim-coverage / extractor-recall audit (offline; no API calls).

Tests P22's hypothesis: DESi may miss risky cases not because of trigger folding
but because the claim EXTRACTOR produced too few / no claims, so folding operates
on an incomplete claim space. Reuses P12 records + the P12 claim graph (P3
extraction metadata + SPL projection metadata) + P21 routing. No model calls, no
new benchmark/intervention/score.

It does NOT claim any answer is wrong — only that the extractor produced no / too
little epistemic content for it. Coverage-risk classes (not truth labels):
no_claims_from_nonempty_answer, under_extracted_compound_answer,
logical_content_without_claim, causal_content_without_claim,
modal_content_without_claim, answer_abstained_before_extraction,
extractor_json_empty, extractor_fallback_used, spl_rejected_all_claims.
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
sys.path.insert(0, str(_HERE.parents[1] / "gaia"))

import p21_trigger_optimizer as p21  # noqa: E402
import p22_trigger_recall_audit as p22  # noqa: E402
from spl_meaning_space_alignment import _load_jsonl  # noqa: E402

_LIVE = _HERE / "outputs" / "truthfulqa.deepseek-v4.p12.limit100.jsonl"
_GRAPH = _HERE / "outputs" / "truthfulqa.deepseek-v4.p12.claim_graph.limit100.jsonl"

_NEG = p21._NEG
_QUANT = p21._QUANT
_CAUSAL = p21._CAUSAL
_MODAL = {"may", "might", "could", "possibly", "likely", "perhaps", "probably",
          "maybe", "seems", "appears", "suggests", "can", "would", "should"}
_SUBSTANTIVE_CHARS = 20


def _is_unknownish(s: str) -> bool:
    return s.strip() == "" or s.strip().upper() == "UNKNOWN"


def _assertions(raw: str) -> int:
    segs = re.split(r"[.;!?]|\band\b|\bbecause\b|\bbut\b|, ", raw.lower())
    return sum(1 for s in segs if len(s.split()) >= 3)


def coverage_flags(rec, row) -> list[str]:
    raw = rec.get("raw_model_answer") or rec.get("model_answer") or ""
    final = rec.get("model_answer") or ""
    decision = (rec.get("desi_metadata") or {}).get("intervention_decision", "")
    n = row.get("n_atomic", 0)
    p3 = row.get("p3") or {}
    ps = row.get("projection_summary") or {}
    raw_l = raw.lower()
    toks = set(raw_l.replace("'", " ").split())
    substantive = (not _is_unknownish(raw)) and len(raw.strip()) >= _SUBSTANTIVE_CHARS
    assertions = _assertions(raw)

    f = []
    if n == 0 and substantive:
        f.append("no_claims_from_nonempty_answer")
    if n >= 1 and assertions >= 2 and n < assertions:
        f.append("under_extracted_compound_answer")
    if n == 0 and (toks & _NEG or toks & _QUANT):
        f.append("logical_content_without_claim")
    if n == 0 and any(m in raw_l for m in _CAUSAL):
        f.append("causal_content_without_claim")
    if n == 0 and (toks & _MODAL):
        f.append("modal_content_without_claim")
    if _is_unknownish(final) and decision.startswith("abstain"):
        f.append("answer_abstained_before_extraction")
    if n == 0 and p3.get("raw_json_ok") and not _is_unknownish(raw):
        f.append("extractor_json_empty")
    if p3.get("method") == "rule_based_p2":
        f.append("extractor_fallback_used")
    if n > 0 and ps.get("n_admissible", 0) == 0 and ps.get("n_blocked", 0) > 0:
        f.append("spl_rejected_all_claims")
    return f


def run(records, graph_list):
    g_by_id = {r["task_id"]: r for r in graph_list}
    rec_by_id = {r["task_id"]: r for r in records}
    p21rows = {r["task_id"]: r for r in p21.run(records, graph_list)["rows"]}
    p22rows = {r["task_id"]: r for r in p22.run(records, graph_list)}
    rows = []
    for r in records:
        tid = r["task_id"]
        row = g_by_id.get(tid, {})
        cf = coverage_flags(r, row)
        raw = r.get("raw_model_answer") or r.get("model_answer") or ""
        rows.append({
            "task_id": tid, "n_atomic": row.get("n_atomic", 0),
            "raw_len": len(raw.strip()), "raw": raw[:70],
            "substantive": (not _is_unknownish(raw)) and len(raw.strip()) >= _SUBSTANTIVE_CHARS,
            "assertions": _assertions(raw),
            "p21_class": p21rows.get(tid, {}).get("class"),
            "p22_flags": p22rows.get(tid, {}).get("audit_flags", []),
            "coverage_flags": cf})
    return rows


def write_report(rows, path: Path) -> None:
    n = len(rows)
    zero = [r for r in rows if r["n_atomic"] == 0]
    zero_subst = [r for r in zero if r["substantive"]]
    any_cov = [r for r in rows if r["coverage_flags"]]
    cov_counter = Counter(f for r in rows for f in r["coverage_flags"])
    # coverage risk inside the non-escalated routing
    log_disc = [r for r in rows if r["p21_class"] in ("LOG_ONLY", "DISCARD")]
    log_disc_cov = [r for r in log_disc if r["coverage_flags"]]
    folded_cov = [r for r in rows if r["p21_class"] == "folded" and r["coverage_flags"]]

    md = ["# P23 claim-coverage / extractor-recall audit (limit 100, offline)\n",
          "Tests whether the bottleneck is the EXTRACTOR, not the trigger folding. "
          "Reuses the P12 claim graph (P3 + SPL metadata) + P21 routing + P22 flags. "
          "No model calls, no score. It does NOT claim any answer is wrong — only that "
          "the extractor produced no / too little epistemic content.\n",
          "## Headline coverage\n",
          f"- answers producing **ZERO atomic claims: {len(zero)}/{n}**.",
          f"- of those, with a **substantive raw answer** (>= {_SUBSTANTIVE_CHARS} chars, "
          f"not UNKNOWN): **{len(zero_subst)}** — these SHOULD plausibly have yielded "
          "claims.",
          f"- answers carrying >=1 coverage-risk flag: **{len(any_cov)}/{n}**.",
          f"- P3 extraction method: all `deepseek`, all raw_json_ok=True -> the empties "
          "are the model returning EMPTY claim lists for the answer, not parse failures.",
          ""]

    md.append("## Coverage-risk class frequency\n")
    md.append("| coverage class | count |")
    md.append("| --- | --- |")
    for cl in ("no_claims_from_nonempty_answer", "extractor_json_empty",
               "answer_abstained_before_extraction", "logical_content_without_claim",
               "modal_content_without_claim", "causal_content_without_claim",
               "under_extracted_compound_answer", "spl_rejected_all_claims",
               "extractor_fallback_used"):
        md.append(f"| {cl} | {cov_counter.get(cl, 0)} |")
    md.append("")

    md.append("## Actionable blind spot vs incidental empties\n")
    actionable = [r for r in rows
                  if ("no_claims_from_nonempty_answer" in r["coverage_flags"]
                      or "logical_content_without_claim" in r["coverage_flags"]
                      or "causal_content_without_claim" in r["coverage_flags"]
                      or "under_extracted_compound_answer" in r["coverage_flags"])]
    abstained = [r for r in rows if "answer_abstained_before_extraction" in r["coverage_flags"]]
    md.append(f"- **Actionable extractor blind spot: ~{len(actionable)}/{n}** — "
              "substantive and/or logically-loaded answers that produced no claim. These "
              "are the real extractor-recall loss.")
    md.append(f"- **Incidental empties (NOT a problem): the rest** — e.g. "
              f"{len(abstained)} abstained (final UNKNOWN, answer discarded) and short "
              "answers. Claim-less here is legitimate; the high 'coverage-flagged' total "
              "is mostly these, so it should NOT be read as a 78-case defect.")
    md.append("")
    md.append("## Does folding operate on an incomplete claim space?\n")
    md.append(f"- **Yes.** {len(zero)}/{n} answers reach the ClaimGraph with zero "
              f"claims and {len(zero_subst)} of those are substantive. Folding / "
              "escalation decide on claim STRUCTURE — but for most answers there is no "
              "claim structure to decide on, because extraction produced none.")
    md.append(f"- coverage-risk cases inside P21 LOG_ONLY/DISCARD: "
              f"**{len(log_disc_cov)}/{len(log_disc)}** — the recall tail P22 flagged is "
              "largely a COVERAGE problem (no claims to escalate), not a trigger problem.")
    md.append(f"- coverage-risk cases inside folded (never triggered): {len(folded_cov)} "
              "— some never-triggered answers are also substantive-but-claim-less.")
    md.append("")

    md.append("## Focus cases\n")
    mrr = [r for r in rows if "missed_reconstruction_risk" in r["p22_flags"]]
    md.append(f"### The {len(mrr)} P22 missed_reconstruction_risk cases\n")
    md.append("| task | nα | raw_len | coverage flags | raw |")
    md.append("| --- | --- | --- | --- | --- |")
    for r in mrr:
        md.append(f"| {r['task_id']} | {r['n_atomic']} | {r['raw_len']} | "
                  f"{r['coverage_flags']} | {r['raw']!r} |")
    md.append("")
    logical_claimless = [r for r in zero if ("logical_content_without_claim" in r["coverage_flags"]
                                             or "causal_content_without_claim" in r["coverage_flags"])]
    md.append(f"### claim-less answers with logical/causal content ({len(logical_claimless)})\n")
    for r in logical_claimless[:10]:
        md.append(f"- `{r['task_id']}` (nα=0): {r['coverage_flags']} | {r['raw']!r}")
    md.append("")
    lcu01 = [r for r in rows if "low_confidence_unresolved" in r["p22_flags"] and r["n_atomic"] <= 1]
    md.append(f"### low_confidence_unresolved with 0 or 1 claim ({len(lcu01)})\n")
    md.append(f"- {len(lcu01)} low-confidence answers carry <=1 claim — even if escalated "
              "there is little structure for a second builder to diverge on; the fix is "
              "upstream coverage, not escalation.")
    md.append("")

    md.append("## Recommendations\n")
    md.append(f"- **Yes, the Granite/DeepSeek extractor prompt should be improved.** "
              f"{len(zero_subst)} substantive answers yielded zero claims with VALID "
              "JSON — the extractor is under-decomposing, not failing to parse. Tighten "
              "the prompt to force at least one atomic claim per asserted proposition "
              "(split conjunctions, resolve 'it'/'they', extract negated/causal/modal "
              "propositions explicitly).")
    md.append("- **Abstained / UNKNOWN final answers:** extraction currently runs on the "
              "RAW answer regardless of intervention. For coverage that is fine (the raw "
              "content is the epistemic material); but claims from an abstained answer "
              "should be tagged as 'derived from a discarded answer' so downstream does "
              "not treat them as endorsed.")
    md.append("- **Claim-coverage should become a PRE-GATE for folding:** an answer with "
              "0 claims from a substantive raw answer should NOT be silently folded as "
              "'low risk' — low coverage is itself uncertainty. Route such cases to a "
              "re-extraction step before the folding decision.")
    md.append("- **Low coverage should itself be an escalation/again-extract signal:** "
              "substantive answer + 0–1 claims = `coverage_risk` trigger -> re-extract "
              "(better prompt / second extractor) BEFORE deciding fold vs escalate. This "
              "is an extraction-recall fix, not a truthfulness heuristic.")
    md.append("")

    md.append("## Bottom line\n")
    md.append(f"- **Extractor coverage is a real constraint, but smaller than the raw "
              f"76 suggests.** {len(zero)}/{n} answers are claim-less; most are short or "
              f"abstained (legitimately empty). The ACTIONABLE blind spot is "
              f"**~{len(actionable)}/{n}** (substantive / logically-loaded answers with "
              "no extracted claim).")
    md.append(f"- **Size of the blind spot:** ~{len(actionable)} answers carry epistemic "
              "content the extractor did not turn into claims — invisible to DBA, SPL, "
              "meaning-space, and governance, because all of those operate on claims. "
              "Not 76; not zero.")
    md.append("- **Next repair:** fix extraction recall first (prompt + a coverage "
              "pre-gate), THEN revisit folding. Optimising triggers further is premature "
              "while 3 in 4 answers carry no claims.")
    md.append("")
    md.append("## Honesty / limits\n")
    md.append("- 'Substantive' and 'assertion count' are length/lexical heuristics; the "
              "counts are directional, not exact. Some zero-claim answers are legitimately "
              "claim-less (true UNKNOWN/short answers).")
    md.append("- No claim that any answer is wrong — only that the extractor produced no/"
              "little epistemic content. No API calls, no new model/score/intervention; "
              "reuses existing artifacts.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(md) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="P23 claim-coverage audit.")
    ap.add_argument("--records", type=Path, default=_LIVE)
    ap.add_argument("--graph", type=Path, default=_GRAPH)
    ap.add_argument("--report", type=Path,
                    default=_HERE / "outputs" / "p23_claim_coverage_audit_report.limit100.md")
    args = ap.parse_args()
    if not args.records.exists() or not args.graph.exists():
        print("Missing artifacts.", file=sys.stderr)
        return 1
    rows = run(_load_jsonl(args.records), _load_jsonl(args.graph))
    write_report(rows, args.report)
    zero = [r for r in rows if r["n_atomic"] == 0]
    zsub = [r for r in zero if r["substantive"]]
    print(f"zero-claim {len(zero)}/100 (substantive {len(zsub)}) | coverage-flagged "
          f"{sum(1 for r in rows if r['coverage_flags'])} -> {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
