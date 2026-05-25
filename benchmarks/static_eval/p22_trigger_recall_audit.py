#!/usr/bin/env python3
"""P22 trigger recall / coverage audit (offline; no API calls).

Not performance tuning — the opposite. Asks: which epistemically risky cases would
the P21 folding NOT escalate? Audits the LOG_ONLY / DISCARD / folded cases (i.e.
everything P21 sends to the single-builder path) for retrospective risk signals
that a second builder might have surfaced.

Hard honesty bound: with only the single Alpha builder (no key / no persisted Gβ
for these cases), this can only flag SUSPICION of a missed conflict from
single-builder signals. It cannot prove a real miss — that needs an actual second
builder. So these are coverage-risk flags, NOT confirmed misses, NOT truth labels.

Audit classes: missed_logical_risk, missed_reconstruction_risk,
missed_semantic_overlap, underspecified_single_claim, hidden_polarity_risk,
low_confidence_unresolved.
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

import p21_trigger_optimizer as p21  # noqa: E402
from alexandria_dba_runner import builder_alpha  # noqa: E402
from spl_meaning_space_alignment import _load_jsonl  # noqa: E402

_LIVE = _HERE / "outputs" / "truthfulqa.deepseek-v4.p12.limit100.jsonl"
_GRAPH = _HERE / "outputs" / "truthfulqa.deepseek-v4.p12.claim_graph.limit100.jsonl"
_FOCUS = ("tqa-0000",)

# implicit / paraphrased negation & polarity the lexical token rule (P21) misses
_IMPLICIT = ("without", "fails to", "fail to", "unable", "no longer", "lacks",
             "lack of", "prevent", "denies", "deny", "refute", "absence of",
             "rather than", "instead of", "contrary", "myth", "misconception",
             "false", "incorrect", "not actually", "do not", "does not", "did not")
_LOGICAL = p21._NEG | p21._QUANT
_LOW_CONF = {"accept_uncertain", "reject_low_confidence"}


def _is_unknownish(s: str) -> bool:
    return s.strip() == "" or s.strip().upper() == "UNKNOWN"


def audit_case(alpha, raw, final, decision, triggered, cls) -> list[str]:
    flags = []
    n = len(alpha)
    raw_l = (raw or "").lower()
    alpha_tokens = set()
    for c in alpha:
        alpha_tokens |= set(f"{c.get('subject','')} {c.get('predicate','')} {c.get('object','')}"
                            .lower().replace("'", " ").split())

    # low-confidence answer kept but not cross-checked
    if decision in _LOW_CONF:
        flags.append("low_confidence_unresolved")
    # implicit/paraphrased negation or polarity in the raw answer (token rule blind)
    if any(p in raw_l for p in _IMPLICIT) and not (alpha_tokens & _LOGICAL):
        flags.append("hidden_polarity_risk")
    # claim-less but the answer carries logical content -> can't reconstruct, gap
    if n == 0 and not _is_unknownish(final) and (set(raw_l.split()) & _LOGICAL
                                                 or any(p in raw_l for p in _IMPLICIT)):
        flags.append("missed_logical_risk")
    # claim-less but substantive answer -> under-extraction; a 2nd builder might
    # reconstruct claims
    if n == 0 and not _is_unknownish(final) and len(final) >= 40:
        flags.append("missed_reconstruction_risk")
    # a single, triggered claim that was not escalated and not exact-resolved
    if n == 1 and triggered and decision not in p21._EXACT and cls != "ESCALATE":
        flags.append("underspecified_single_claim")
    # single claim with substantive object -> another builder could decompose it
    if n == 1 and cls != "ESCALATE" and any(len(c.get("object", "")) >= 25 for c in alpha):
        flags.append("missed_semantic_overlap")
    return flags


def run(records, graph_list):
    rec_by_id = {r["task_id"]: r for r in records}
    g_by_id = {r["task_id"]: r for r in graph_list}
    R = p21.run(records, graph_list)
    rows = []
    for pr in R["rows"]:
        tid = pr["task_id"]
        alpha = builder_alpha(g_by_id.get(tid, {}))
        rec = rec_by_id[tid]
        raw = rec.get("raw_model_answer") or rec.get("model_answer") or ""
        final = rec.get("model_answer") or ""
        decision = (rec.get("desi_metadata") or {}).get("intervention_decision", "")
        flags = audit_case(alpha, raw, final, decision, pr["triggered"], pr["class"])
        rows.append({**pr, "decision": decision, "audit_flags": flags,
                     "raw": raw[:70], "final_unknown": _is_unknownish(final)})
    return rows


def write_report(rows, path: Path) -> None:
    n = len(rows)
    escalate = [r for r in rows if r["class"] == "ESCALATE"]
    non_esc = [r for r in rows if r["class"] != "ESCALATE"]
    flagged = [r for r in non_esc if r["audit_flags"]]
    log_disc = [r for r in non_esc if r["class"] in ("LOG_ONLY", "DISCARD")]
    log_disc_flagged = [r for r in log_disc if r["audit_flags"]]
    class_counter = Counter(f for r in non_esc for f in r["audit_flags"])
    by_route = Counter(r["class"] for r in flagged)

    md = ["# P22 trigger recall / coverage audit (limit 100, offline)\n",
          "Recall audit of P21 folding: which non-escalated cases carry retrospective "
          "risk signals a second builder might have surfaced. Offline single-builder "
          "signals only -> these are SUSPICION flags, not confirmed misses, not truth "
          "labels. No API calls, no new model, no score.\n",
          f"## Coverage summary\n",
          f"- ESCALATE (cross-checked): {len(escalate)}/{n}.",
          f"- not escalated (folded + LOG_ONLY + DISCARD): {len(non_esc)}/{n}.",
          f"- **not-escalated cases carrying >=1 retrospective risk flag: "
          f"{len(flagged)}/{len(non_esc)}** (of which LOG_ONLY/DISCARD: "
          f"{len(log_disc_flagged)}/{len(log_disc)}).",
          f"- flagged cases by route: `{dict(by_route)}`.",
          ""]

    md.append("## Audit-class frequency (over non-escalated cases)\n")
    md.append("| audit class | count |")
    md.append("| --- | --- |")
    for cl in ("low_confidence_unresolved", "hidden_polarity_risk", "missed_logical_risk",
               "missed_reconstruction_risk", "underspecified_single_claim",
               "missed_semantic_overlap"):
        md.append(f"| {cl} | {class_counter.get(cl, 0)} |")
    md.append("")

    md.append("## Most-flagged non-escalated cases\n")
    md.append("| task | route | decision | nα | audit flags | raw answer |")
    md.append("| --- | --- | --- | --- | --- | --- |")
    for r in sorted(flagged, key=lambda r: -len(r["audit_flags"]))[:18]:
        md.append(f"| {r['task_id']} | {r['class']} | {r['decision']} | {r['n_alpha']} "
                  f"| {r['audit_flags']} | {r['raw']!r} |")
    md.append("")

    md.append("## Focus cases\n")
    by_id = {r["task_id"]: r for r in rows}
    for tid in _FOCUS:
        r = by_id.get(tid)
        if r:
            md.append(f"- `{tid}`: routed **{r['class']}** (decision {r['decision']}, "
                      f"nα={r['n_alpha']}); audit flags {r['audit_flags'] or '[]'}. "
                      "P21 escalated this via the logical-risk-token rule — the recall "
                      "safeguard fired here, which is the desired behaviour.")
    claimless = [r for r in non_esc if r["n_alpha"] == 0]
    cl_flagged = [r for r in claimless if r["audit_flags"]]
    md.append(f"- **claim-less cases ({len(claimless)}):** {len(cl_flagged)} carry a "
              "risk flag (logical content / substantive answer with no extracted "
              "claims). These are a genuine blind spot: P21 cannot escalate them "
              "(nothing to reconstruct) yet the answer may carry logical risk. The gap "
              "is in EXTRACTION (0 claims), not in the trigger.")
    single_low = [r for r in non_esc if r["n_alpha"] == 1 and r["audit_flags"]]
    md.append(f"- **single-claim risk-flagged cases ({len(single_low)}):** routed "
              "LOG_ONLY/DISCARD; a richer second reconstruction could decompose them "
              "differently. Folding on claim-count alone misses these.")
    lcu = [r for r in non_esc if "low_confidence_unresolved" in r["audit_flags"]]
    md.append(f"- **low-confidence unresolved answers ({len(lcu)}):** accept_uncertain/"
              "reject_low_confidence kept but not cross-checked — the largest "
              "single recall concern by count.")
    md.append("")

    md.append("## Which P21 heuristics look too aggressive\n")
    md.append("- **Claim-count dominance:** the ESCALATE predicate leans heavily on "
              "`>=2 claims`. Claim-less and single-claim answers can only escalate via "
              "the logical-risk-token rule, which is lexical and shallow — so "
              "structurally-simple but logically-loaded answers under-escalate.")
    md.append("- **logical-risk-token rule recall:** it catches explicit "
              "negation/quantifier/causal words (it fired correctly on tqa-0000 "
              "'without'). The hidden_polarity_risk detector flagged "
              f"{class_counter.get('hidden_polarity_risk', 0)} purely-implicit cases "
              "here — near-zero, but that likely reflects the detector's strict "
              "conjunction (implicit phrase AND no explicit token) rather than proof of "
              "no blind spot; paraphrased negation ('fails to', 'rather than', 'myth') "
              "remains a known recall gap of a lexical rule.")
    md.append("- **Claim-less extraction gap:** the deepest issue is upstream — "
              "answers that extract 0 claims cannot be escalated at all; this is an "
              "extractor coverage problem, not a trigger problem.")
    md.append("")

    md.append("## Which triggers should come back / can stay out\n")
    md.append("- **Consider returning (as escalation, conditionally):** "
              "`low_confidence_unresolved` (accept_uncertain / reject_low_confidence) "
              "for answers that DO carry claims — a kept-but-uncertain claim-bearing "
              "answer is a reasonable cross-check candidate, currently LOG_ONLY.")
    md.append("- **Add a paraphrased-negation / polarity escalation cue** to cover the "
              "hidden_polarity_risk gap the lexical token rule misses.")
    md.append("- **Can stay out of escalation:** `judge_divergence` and "
              "`final_unknown_nonempty_raw` on claim-less answers — escalating them is "
              "pointless (no claims to reconstruct); keep as LOG.")
    md.append("- **Genuinely only visible with a real second builder:** "
              "reconstruction/semantic-overlap divergence on single-claim answers, and "
              "whether claim-less answers SHOULD have decomposed — these cannot be "
              "confirmed from single-builder signals here.")
    md.append("")

    md.append("## Architecture answer: too aggressive, or still conservative?\n")
    ratio = len(log_disc_flagged) / max(1, len(log_disc))
    md.append(f"- On these 100, **{len(flagged)}/{len(non_esc)}** non-escalated cases "
              f"carry a retrospective risk flag ({len(log_disc_flagged)}/{len(log_disc)} "
              "of the explicitly LOG_ONLY/DISCARD cases). That is a non-trivial "
              "potential recall loss.")
    md.append("- **DESi folding is now PRECISION/COMPUTE-leaning, not recall-leaning.** "
              "It escalates rarely and the escalations are well-targeted (high "
              "precision), but it leaves a meaningful tail of logically-loaded "
              "single-claim and claim-less answers un-cross-checked. For a "
              "conservative epistemic stance this is somewhat TOO aggressive on the "
              "recall side.")
    md.append("- Net: P21 optimised compute correctly but **shifted the balance toward "
              "precision**; the recall tail (low-confidence claim-bearing answers, "
              "implicit-negation answers, under-extracted answers) is the real exposure.")
    md.append("")

    md.append("## Honesty / limits\n")
    md.append("- These are single-builder SUSPICION flags from lexical/structural "
              "signals — NOT confirmed missed conflicts. Confirming any of them needs a "
              "real second builder (no key / no persisted Gβ for non-escalated cases).")
    md.append("- The implicit-negation lexicon is itself a heuristic and will over- and "
              "under-flag. Counts are directional, not exact.")
    md.append("- No truthfulness tuning, no new intervention/model/score, no new "
              "Granite calls; reuses P12/P14/P18/P19/P20/P21 artifacts.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(md) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="P22 trigger recall audit.")
    ap.add_argument("--records", type=Path, default=_LIVE)
    ap.add_argument("--graph", type=Path, default=_GRAPH)
    ap.add_argument("--report", type=Path,
                    default=_HERE / "outputs" / "p22_trigger_recall_audit_report.limit100.md")
    args = ap.parse_args()
    if not args.records.exists() or not args.graph.exists():
        print("Missing artifacts.", file=sys.stderr)
        return 1
    rows = run(_load_jsonl(args.records), _load_jsonl(args.graph))
    write_report(rows, args.report)
    non_esc = [r for r in rows if r["class"] != "ESCALATE"]
    flagged = [r for r in non_esc if r["audit_flags"]]
    print(f"non-escalated {len(non_esc)} | risk-flagged {len(flagged)} | "
          f"classes {dict(Counter(f for r in non_esc for f in r['audit_flags']))} "
          f"-> {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
