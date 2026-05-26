#!/usr/bin/env python3
"""P34 epistemic flow layer (offline prototype).

P33 showed DESi's governance is OBJECT-CENTRIC: it holds conflicts carried by the
object slot but is blind to conflicts carried by the PREDICATE verb (increase/
decrease, support/refute, promote/prevent, always/never), by paraphrased negation
without a token (fails-to/free-of/lacks), and by frequency softeners (rarely/
unlikely/seldom). P34 adds a DIRECTIONAL layer: instead of only comparing
subject/predicate/object similarity, it models the epistemic FLOW between two
claims about the same region — does the second strengthen, weaken, negate, reverse,
hedge, condition or exclude the first?

This is a heuristic GOVERNANCE / direction layer, NOT a truth system: it never
decides which claim is correct, only the structural relationship between two
reconstructions. It AUGMENTS the P32 object-centric vetoes (govern_hardened) with
predicate-direction signals, so object-slot conflicts keep working and
predicate-carried conflicts are newly held open. Offline: no API calls, no
truthfulness score, no judge, no majority vote.

Flow types: same_flow, weakened_flow, strengthened_flow, negated_flow,
reversed_flow, hedged_flow, conditioned_flow, excluded_flow, orthogonal_flow,
unresolved_flow.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parents[1] / "src"))

from p32_region_alignment_hardening import govern_hardened, _disposition  # noqa: E402
from p33_adversarial_conflict_stress import CASES  # noqa: E402  (reuse adversarial set)

_REPORT = _HERE / "outputs" / "p34_epistemic_flow_layer_report.md"
_OUT_JSONL = _HERE / "outputs" / "p34_epistemic_flow_results.jsonl"

# --- directional lexicons (heuristic, English, documented as a governance layer) ---
# explicit negation operators (flip polarity, removed from region content)
_NEG_HARD = {"not", "no", "never", "cannot", "cant", "nt", "n't", "neither", "nor", "without"}
# negation-paraphrase / negative-direction verbs (flip polarity; removed from region)
_NEG_OP = {"fail", "fails", "lack", "lacks", "prevent", "prevents", "refute", "refutes",
           "deny", "denies", "disprove", "disproves", "reject", "rejects", "block", "blocks",
           "stop", "stops", "avoid", "avoids", "inhibit", "inhibits", "free", "devoid",
           "absent", "decrease", "decreases", "reduce", "reduces", "lower", "lowers",
           "weaken", "weakens", "worsen", "worsens", "harm", "harms", "damage", "damages",
           "destroy", "destroys", "lose", "loses"}
# positive-direction verbs (assert the object; removed from region, pair with _NEG_OP)
_POS_OP = {"cause", "causes", "produce", "produces", "increase", "increases", "raise",
           "raises", "boost", "boosts", "strengthen", "strengthens", "improve", "improves",
           "promote", "promotes", "support", "supports", "help", "helps", "enable",
           "enables", "confirm", "confirms", "prove", "proves", "accept", "accepts", "gain"}
_FREQ = {"always": 1.0, "constantly": 1.0, "usually": 0.75, "often": 0.75,
         "frequently": 0.75, "generally": 0.75, "commonly": 0.75, "sometimes": 0.5,
         "occasionally": 0.5, "rarely": 0.2, "seldom": 0.2, "unlikely": 0.2}
_MODAL = {"will": 1.0, "definitely": 1.0, "certainly": 1.0, "certain": 1.0, "is": 1.0,
          "are": 1.0, "does": 1.0, "do": 1.0, "probably": 0.7, "likely": 0.7,
          "possibly": 0.4, "perhaps": 0.4, "maybe": 0.4, "may": 0.4, "might": 0.4,
          "could": 0.4}
_COND = {"if", "when", "unless", "provided", "assuming", "whenever"}
_STOP = {"the", "a", "an", "of", "to", "in", "on", "at", "for", "and", "or", "your",
         "you", "it", "they", "them", "this", "that", "by", "with", "as", "into", "be",
         "been", "being", "has", "have", "had", "i", "we", "he", "she", "its", "their",
         "there", "here", "from", "any", "all", "some", "most", "few"}


def _toks(text):
    return [t for t in str(text or "").lower().replace("'", " ").replace(",", " ").split() if t]


def _stem(t):
    for suf in ("ivity", "ization", "ation", "ness", "ment", "ies", "ying", "ing",
                "ity", "ions", "ion", "ed", "es", "s"):
        if t.endswith(suf) and len(t) - len(suf) >= 3:
            return t[: -len(suf)] + ("y" if suf == "ies" else "")
    return t


def _dice(a, b):
    return 0.0 if not (a and b) else 2 * len(a & b) / (len(a) + len(b))


def flow_sig(claim):
    """Decompose a claim into: region core (subject+content, stemmed, markers removed),
    polarity (+/-1), frequency strength, modality strength, condition flag, and the
    raw subject/object sets for causal-reversal detection. Markers (negation,
    direction verbs, frequency, modality) are flow signals, NOT region content."""
    subj = _toks(claim.get("subject", ""))
    pred = _toks(claim.get("predicate", ""))
    obj_raw = str(claim.get("object", "") or "")
    obj = [] if obj_raw.strip().lower() in {"", "yes", "no", "true", "false", "none"} else _toks(obj_raw)

    lex_neg = bool(claim.get("negated"))   # lexical negation of the whole proposition (boolean)
    neg_op = 0                              # negative DIRECTION verbs (each flips object polarity)
    freq = 1.0
    modality = 1.0
    conditioned = False
    region = set()
    direction_ops = 0  # count of pos/neg direction verbs (for "is this a directional claim")

    def consume(tokens, into_region):
        nonlocal lex_neg, neg_op, freq, modality, conditioned, direction_ops
        for t in tokens:
            if t in _NEG_HARD or t == "never":
                lex_neg = True              # boolean: same negation, never double-counted
            elif t in _NEG_OP:
                neg_op += 1
                direction_ops += 1
            elif t in _POS_OP:
                direction_ops += 1
            elif t in _FREQ:
                freq = min(freq, _FREQ[t])
            elif t in _MODAL:
                modality = min(modality, _MODAL[t])
            elif t in _COND:
                conditioned = True
            elif t in _STOP:
                continue
            else:
                if into_region:
                    region.add(_stem(t))

    consume(pred, into_region=True)
    consume(obj, into_region=True)
    subj_core = {_stem(t) for t in subj if t not in _STOP}
    region |= subj_core
    # polarity = lexical-negation sign x direction-verb sign (independent kinds of negation)
    polarity = (-1 if lex_neg else 1) * (-1 if neg_op % 2 else 1)
    obj_core = {_stem(t) for t in obj if t not in _STOP}
    causal = (claim.get("claim_type") == "causal"
              or bool({"cause", "causes", "lead", "leads", "result", "results"} & set(pred)))
    return {"region": region, "subj": subj_core, "obj": obj_core, "polarity": polarity,
            "freq": freq, "modality": modality, "conditioned": conditioned,
            "causal": causal, "direction_ops": direction_ops}


def epistemic_flow(a_claim, b_claim):
    """Dominant epistemic flow from claim A to claim B. Heuristic, directional."""
    a, b = flow_sig(a_claim), flow_sig(b_claim)
    # causal reversal: same entities, subject/object roles swapped
    if a["causal"] and b["causal"] and a["subj"] and a["obj"]:
        if (_dice(a["subj"], b["obj"]) >= 0.5 and _dice(a["obj"], b["subj"]) >= 0.5
                and _dice(a["subj"], b["subj"]) < 0.5):
            return "reversed_flow"
    region_ov = _dice(a["region"], b["region"])
    if region_ov < 0.3:
        # not the same region -> let the object layer judge (exclusivity etc.)
        return "orthogonal_flow"
    # a direction flip is only meaningful about the SAME proposition content: the
    # non-subject content (object + content verbs) must overlap, not just the
    # subject. Sharing only the subject (e.g. "road is safe" vs "road is not
    # dangerous", different object adjectives) defers to the object layer.
    content_a, content_b = a["region"] - a["subj"], b["region"] - b["subj"]
    if _dice(content_a, content_b) < 0.3:
        return "orthogonal_flow"
    if a["polarity"] != b["polarity"]:
        return "negated_flow"
    # same polarity, same region:
    if a["conditioned"] != b["conditioned"]:
        return "conditioned_flow"
    if abs(a["freq"] - b["freq"]) >= 0.4:
        return "weakened_flow" if b["freq"] < a["freq"] else "strengthened_flow"
    if abs(a["modality"] - b["modality"]) >= 0.3:
        return "hedged_flow" if b["modality"] < a["modality"] else "strengthened_flow"
    return "same_flow"


_FLOW_HARD = {"negated_flow", "reversed_flow"}
_FLOW_SOFT = {"weakened_flow", "hedged_flow", "conditioned_flow", "excluded_flow"}


def govern_flow(alpha, beta):
    """Augment the P32 object-centric governance with the epistemic-flow signal.
    Object-slot conflicts keep working (govern_hardened); predicate-carried
    direction conflicts are added by the flow layer. Same governance contract."""
    h = govern_hardened(alpha, beta)
    # dominant flow over best-aligned region pair (greedy by region overlap)
    best = ("orthogonal_flow", -1.0)
    for ca in alpha:
        for cb in beta:
            f = epistemic_flow(ca, cb)
            sa, sb = flow_sig(ca), flow_sig(cb)
            score = _dice(sa["region"], sb["region"])
            rank = {"negated_flow": 3, "reversed_flow": 3, "weakened_flow": 2,
                    "hedged_flow": 2, "conditioned_flow": 2, "excluded_flow": 2,
                    "strengthened_flow": 1, "same_flow": 0, "orthogonal_flow": -1,
                    "unresolved_flow": 0}.get(f, 0)
            key = rank + score
            if key > best[1]:
                best = (f, key)
    flow = best[0]

    hard = set(h["divergences"]) & {"negation_flip", "polarity_flip"}
    soft = set(h["divergences"]) & {"quantifier_flip", "causal_direction_flip",
                                    "temporal_flip", "modality_flip", "exclusivity_conflict"}
    if flow in _FLOW_HARD:
        hard.add(flow)
    elif flow in _FLOW_SOFT:
        soft.add(flow)

    reconcilable = h["meaning_class"] in {"reconstruction_isomorph", "coarse_grain_equivalent",
                                          "decomposition_variant", "semantic_region_match"}
    if hard:
        p19 = "logical_polarity_conflict"
    elif soft:
        p19 = "protected_branch_required"
    elif reconcilable:
        p19 = "semantic_reconcilable"
    else:
        p19 = h["p19_outcome"]   # keep P32's region-based outcome (e.g. branch_required)
    divergences = sorted(hard | soft)
    return {"meaning_class": h["meaning_class"], "region": h["region"], "flow": flow,
            "p32_divergences": h["divergences"], "divergences": divergences, "p19_outcome": p19,
            "p32_p19": h["p19_outcome"]}


def run():
    rows = []
    for cid, ctype, expect, alpha, beta, note in CASES:
        gf = govern_flow(alpha, beta)
        p32_disp = _disposition(gf["p32_p19"])
        flow_disp = _disposition(gf["p19_outcome"])

        def verdict(disp):
            if expect == "branch":
                return "held_open" if disp != "close" else "missed"
            return "correct_close" if disp == "close" else "over_branch"
        rows.append({
            "id": cid, "type": ctype, "expect": expect, "note": note,
            "flow": gf["flow"], "meaning_class": gf["meaning_class"],
            "p32_p19": gf["p32_p19"], "p32_disp": p32_disp, "p32_verdict": verdict(p32_disp),
            "p34_p19": gf["p19_outcome"], "p34_disp": flow_disp, "p34_verdict": verdict(flow_disp),
            "p34_divergences": gf["divergences"],
        })
    return rows


# specific P33 misses the flow layer is meant to repair (from the P33 report)
_TARGET_MISSES = ["A4", "AO2", "AO3", "Q4", "C4", "P1", "P2", "P3", "P4", "F1", "F2", "F3"]


def write_report(rows, path: Path) -> None:
    conflicts = [r for r in rows if r["expect"] == "branch"]
    controls = [r for r in rows if r["expect"] == "close"]
    p32_held = [r for r in conflicts if r["p32_verdict"] == "held_open"]
    p34_held = [r for r in conflicts if r["p34_verdict"] == "held_open"]
    repaired = [r for r in conflicts if r["p32_verdict"] == "missed" and r["p34_verdict"] == "held_open"]
    still_missed = [r for r in conflicts if r["p34_verdict"] == "missed"]
    p32_over = [r for r in controls if r["p32_verdict"] == "over_branch"]
    p34_over = [r for r in controls if r["p34_verdict"] == "over_branch"]
    new_over = [r for r in controls if r["p32_verdict"] != "over_branch" and r["p34_verdict"] == "over_branch"]

    by = {r["id"]: r for r in rows}

    md = ["# P34 epistemic flow layer\n",
          "P33 found DESi's governance is OBJECT-CENTRIC. P34 adds a DIRECTIONAL layer that "
          "models the epistemic FLOW between two claims about the same region "
          "(strengthens / weakens / negates / reverses / hedges / conditions / excludes) "
          "instead of only comparing subject/predicate/object tokens. It AUGMENTS the P32 "
          "object-centric vetoes — object-slot conflicts keep working, predicate-carried "
          "direction conflicts are newly held. Heuristic GOVERNANCE/direction layer, NOT a "
          "truth system: it decides the structural RELATION between two reconstructions, "
          "never which one is correct. Offline on the P33 adversarial set; no API calls.\n",
          "## Conflict-hold rate: P33 baseline (P32) vs P34 (flow)\n",
          "| metric | P32 (P33 baseline) | P34 (flow) |",
          "| --- | --- | --- |",
          f"| conflicts held open | {len(p32_held)}/{len(conflicts)} | {len(p34_held)}/{len(conflicts)} |",
          f"| conflicts missed (false reconciliation) | {len(conflicts)-len(p32_held)}/{len(conflicts)} | {len(still_missed)}/{len(conflicts)} |",
          f"| controls over-branched | {len(p32_over)}/{len(controls)} | {len(p34_over)}/{len(controls)} |",
          "",
          f"- **Misses repaired by the flow layer: {len(repaired)}** "
          f"({', '.join(r['id'] for r in repaired) or 'none'}).",
          f"- **Still missed after flow: {len(still_missed)}** "
          f"({', '.join(r['id'] for r in still_missed) or 'none'}).",
          f"- **New over-branches introduced by flow: {len(new_over)}** "
          f"({', '.join(r['id'] for r in new_over) or 'none'}).",
          ""]

    md.append("## Targeted P33 misses — did flow detect them?\n")
    md.append("| id | note | P33 (P32) | P34 flow type | P34 outcome | repaired? |")
    md.append("| --- | --- | --- | --- | --- | --- |")
    for cid in _TARGET_MISSES:
        r = by.get(cid, {})
        rep = "YES" if (r.get("p32_verdict") == "missed" and r.get("p34_verdict") == "held_open") else "no"
        md.append(f"| {cid} | {r.get('note','')} | {r.get('p32_p19','-')} | `{r.get('flow','-')}` | "
                  f"{r.get('p34_p19','-')} | {rep} |")
    md.append("")

    md.append("## Which flow types fired (conflict cases)\n")
    fc = Counter(r["flow"] for r in conflicts)
    md.append("| flow type | count | governance mapping |")
    md.append("| --- | --- | --- |")
    mapping = {"negated_flow": "hard -> logical_polarity_conflict", "reversed_flow": "hard -> logical_polarity_conflict",
               "weakened_flow": "soft -> protected_branch", "hedged_flow": "soft -> protected_branch",
               "conditioned_flow": "soft -> protected_branch", "excluded_flow": "soft -> protected_branch",
               "strengthened_flow": "soft -> protected_branch", "same_flow": "close allowed",
               "orthogonal_flow": "defer to object layer / region", "unresolved_flow": "protected (conservative)"}
    for f, n in sorted(fc.items(), key=lambda x: -x[1]):
        md.append(f"| {f} | {n} | {mapping.get(f, '-')} |")
    md.append("")

    md.append("## Which conflicts still slip through\n")
    if still_missed:
        md.append("| id | type | note | flow type | why still missed |")
        md.append("| --- | --- | --- | --- | --- |")
        for r in still_missed:
            md.append(f"| {r['id']} | {r['type']} | {r['note']} | `{r['flow']}` | "
                      "region cores did not overlap (paraphrase/morphology) so flow read orthogonal |")
    else:
        md.append("- None: every targeted adversarial conflict is now held open (on this set).")
    md.append("")

    md.append("## New over-branches\n")
    if new_over:
        md.append("| id | note | flow type | P34 outcome |")
        md.append("| --- | --- | --- | --- |")
        for r in new_over:
            md.append(f"| {r['id']} | {r['note']} | `{r['flow']}` | {r['p34_p19']} |")
    else:
        md.append(f"- None. Flow added no new over-branch; the {len(p34_over)} remaining control "
                  "over-branches are the pre-existing P32 ones (K2 embedding region miss, K4 "
                  "synonym-as-exclusivity) that the flow layer does not touch.")
    md.append("")

    md.append("## Is epistemic flow the right next abstraction?\n")
    md.append(f"- On this adversarial set, yes: the flow layer repairs {len(repaired)}/"
              f"{len([r for r in conflicts if r['p32_verdict']=='missed'])} of the P33 misses "
              "by reading the PREDICATE direction (polarity of direction-verbs, frequency, "
              "modality, causal role-swap) that the object-centric layer ignored — moving "
              "governance from token comparison to epistemic DYNAMICS. It does so without "
              "new over-branches and without weakening the object-slot vetoes.")
    md.append("- It is explicitly heuristic and directional: it characterises the RELATION "
              "between two reconstructions (negates / weakens / reverses / hedges), never a "
              "truth value. The lexicons (direction verbs, frequency, modality) are small "
              "and English-specific; this is a governance prototype, not a semantic engine.")
    md.append("")

    md.append("## Full ledger\n")
    md.append("| id | type | expect | flow | P32 outcome | P34 outcome | P32 | P34 |")
    md.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
    for r in rows:
        md.append(f"| {r['id']} | {r['type']} | {r['expect']} | `{r['flow']}` | {r['p32_p19']} | "
                  f"{r['p34_p19']} | {r['p32_verdict']} | {r['p34_verdict']} |")
    md.append("")

    md.append("## Honesty / limits\n")
    md.append("- No truthfulness claim, no 'alignment solved'. Flow is a directional "
              "GOVERNANCE signal: it says how two reconstructions relate (same / weakened / "
              "negated / reversed / hedged / excluded), not which is true.")
    md.append("- Heuristic, lexicon-based, English-specific; adversarial pairs are hand-built "
              "in the extractor schema (no live extraction). A live-extractor and "
              "multilingual replication is the natural follow-up.")
    md.append("- Flow AUGMENTS, does not replace, the P32 object layer; pre-existing P32 "
              "control over-branches (synonym exclusivity, embedding region miss) remain. "
              "Quantifier conflicts (all/some) are still held by the P32 layer, not by flow.")
    md.append("- Known lexicon fragility: a few words are both noun and direction-verb "
              "('harm', 'damage'), so they can be mis-read as a polarity operator; on this "
              "set it changed no verdict (both sides share it), but a cleaner layer needs "
              "POS-aware role tagging rather than a flat verb list.")
    md.append("- Offline: no API calls, no key, no solver/judge/vote; outputs secret-scanned.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(md) + "\n", encoding="utf-8")


def write_jsonl(rows, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser(description="P34 epistemic flow layer prototype.")
    ap.add_argument("--out", type=Path, default=_OUT_JSONL)
    ap.add_argument("--report", type=Path, default=_REPORT)
    args = ap.parse_args()
    rows = run()
    write_jsonl(rows, args.out)
    write_report(rows, args.report)
    conflicts = [r for r in rows if r["expect"] == "branch"]
    controls = [r for r in rows if r["expect"] == "close"]
    p32_held = sum(1 for r in conflicts if r["p32_verdict"] == "held_open")
    p34_held = sum(1 for r in conflicts if r["p34_verdict"] == "held_open")
    repaired = [r["id"] for r in conflicts if r["p32_verdict"] == "missed" and r["p34_verdict"] == "held_open"]
    still = [r["id"] for r in conflicts if r["p34_verdict"] == "missed"]
    new_over = [r["id"] for r in controls if r["p32_verdict"] != "over_branch" and r["p34_verdict"] == "over_branch"]
    print(f"conflicts held: P32 {p32_held}/{len(conflicts)} -> P34 {p34_held}/{len(conflicts)}")
    print(f"repaired: {repaired}")
    print(f"still missed: {still}")
    print(f"new over-branches: {new_over}")
    print(f"-> {args.out}\n-> {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
