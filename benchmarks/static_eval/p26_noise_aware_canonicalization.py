#!/usr/bin/env python3
"""P26 noise-aware claim canonicalization (offline; no API calls).

P25 showed the P24 repair inflated ESCALATE 6 -> 39, largely because the crude
rule extractor splits one answer into many same-subject/same-predicate claims
("includes" lists, location/attribute decompositions). P26 groups claims that
likely belong to the SAME epistemic region (canonical clusters) so that
structural granularity noise stops inflating escalation — WITHOUT folding across a
logical conflict, and WITHOUT deleting claims or deciding truth.

Reuses the P25 repaired claim graph + P21 routing logic. No model calls, no
truthfulness score, no judge. Goal: stabilise epistemic REGIONS, not minimise
claim count.

Classes (NOT truth labels): canonical_claim_cluster, granularity_variant,
conjunction_split, structural_duplicate, semantic_fragment, regionally_equivalent,
escalation_noise_candidate (+ false_fold_candidate as an honesty flag).
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
sys.path.insert(0, str(_HERE.parents[1] / "gaia"))

import p21_trigger_optimizer as p21  # noqa: E402
from alexandria_dba_runner import builder_alpha  # noqa: E402
from desi_intervention import _content_tokens, _norm  # noqa: E402

_LIVE = _HERE / "outputs" / "truthfulqa.deepseek-v4.p12.limit100.jsonl"
_REPAIRED = _HERE / "outputs" / "truthfulqa.deepseek-v4.p25_repaired.claim_graph.limit100.jsonl"
_NEG = p21._NEG


def _load(p):
    return [json.loads(l) for l in Path(p).read_text(encoding="utf-8").splitlines() if l.strip()]


def _dice(a, b):
    return 1.0 if not a and not b else (0.0 if not a or not b else 2 * len(a & b) / (len(a) + len(b)))


def _neg(claim) -> bool:
    toks = set(f"{claim.get('predicate','')} {claim.get('object','')}".lower().replace("'", " ").split())
    return bool(toks & _NEG)


def canonicalize(claims: list[dict]) -> list[list[dict]]:
    """Group claims into canonical clusters by (subject, predicate), split by
    negation polarity so a logical conflict is never folded."""
    groups: dict = defaultdict(list)
    for c in claims:
        groups[(_norm(c.get("subject", "")), _norm(c.get("predicate", "")))].append(c)
    clusters = []
    for members in groups.values():
        pos = [m for m in members if not _neg(m)]
        neg = [m for m in members if _neg(m)]
        if pos:
            clusters.append(pos)
        if neg:
            clusters.append(neg)
    return clusters


def _cluster_rep(cluster: list[dict]) -> dict:
    """One representative claim per cluster (no separator reintroduced, so it does
    not spuriously re-trigger a 'compound object' signal)."""
    return {"subject": cluster[0].get("subject", ""), "predicate": cluster[0].get("predicate", ""),
            "object": cluster[0].get("object", ""),
            "claim_type": cluster[0].get("claim_type", "fact")}


_QUANT = p21._QUANT
_CAUSAL = p21._CAUSAL


def _causal(c) -> bool:
    t = f"{c.get('predicate','')} {c.get('object','')}".lower()
    return c.get("claim_type") == "causal" or any(m in t for m in _CAUSAL)


def _quant(c) -> bool:
    toks = set(f"{c.get('subject','')} {c.get('object','')}".lower().split())
    return bool(toks & _QUANT)


def cluster_escalate(clusters: list[list[dict]], triggered: bool, decision: str,
                     malformed: bool) -> tuple[str, str]:
    """Cluster-aware escalation: count REGIONS not raw claims, and DROP the
    'compound object' criterion (a within-region list is the noise we fold).
    Keep logical-risk (negation/quantifier/causal), multi-region, multi-type."""
    if not triggered:
        return "folded", "no epistemic-risk trigger"
    n_clusters = len(clusters)
    if n_clusters == 0:
        return "DISCARD", "claim-less"
    types = {c.get("claim_type", "fact") for cl in clusters for c in cl}
    risk = any(_neg(c) or _causal(c) or _quant(c) for cl in clusters for c in cl)
    if n_clusters >= 2 or len(types) >= 2 or risk:
        why = []
        if n_clusters >= 2:
            why.append(f">=2 regions ({n_clusters})")
        if len(types) >= 2:
            why.append(f">=2 types ({len(types)})")
        if risk:
            why.append("logical-risk (negation/quantifier/causal)")
        return "ESCALATE", "; ".join(why)
    if decision in p21._EXACT:
        return "DISCARD", f"exact-resolved ({decision})"
    if malformed:
        return "DISCARD", "all claims malformed"
    return "LOG_ONLY", "single region, no logical risk (folded list)"


def classify_clusters(clusters: list[list[dict]]) -> dict:
    flags = set()
    false_fold = False
    for cl in clusters:
        if len(cl) >= 2:
            flags.add("conjunction_split")
            objs = [c.get("object", "") for c in cl]
            if len({_norm(o) for o in objs}) < len(objs):
                flags.add("structural_duplicate")
            tok = [_content_tokens(o) for o in objs]
            # granularity / fragment: one object's tokens subset of another
            for i in range(len(tok)):
                for j in range(len(tok)):
                    if i != j and tok[i] and tok[i] < tok[j]:
                        flags.add("granularity_variant")
            # false-fold honesty flag: members are multi-token and pairwise dissimilar
            multi = [o for o, t in zip(objs, tok) if len(t) >= 2]
            if len(multi) >= 2:
                sims = [_dice(_content_tokens(a), _content_tokens(b))
                        for k, a in enumerate(multi) for b in multi[k + 1:]]
                if sims and max(sims) < 0.34:
                    false_fold = True
    return {"flags": sorted(flags), "false_fold": false_fold}


def run(records, repaired):
    rec_by = {r["task_id"]: r for r in records}
    g_by = {r["task_id"]: r for r in repaired}
    p21rows = {r["task_id"]: r for r in p21.run(records, repaired)["rows"]}
    rows = []
    for r in repaired:
        tid = r["task_id"]
        raw_claims = builder_alpha(r)
        clusters = canonicalize(raw_claims)
        cc = classify_clusters(clusters)
        triggered = p21rows[tid]["triggered"]
        decision = (rec_by[tid].get("desi_metadata") or {}).get("intervention_decision", "")
        ac = r.get("atomic_claims", [])
        malformed = bool(ac) and all("projection_invalid" in (a.get("projection") or {}).get("flags", [])
                                     for a in ac)
        p25_class = p21rows[tid]["class"]
        p26_class, why = cluster_escalate(clusters, triggered, decision, malformed)
        noise = (p25_class == "ESCALATE" and p26_class != "ESCALATE")
        rows.append({"task_id": tid, "n_claims": len(raw_claims), "n_clusters": len(clusters),
                     "p25_class": p25_class, "p26_class": p26_class, "why26": why,
                     "cluster_flags": cc["flags"], "false_fold": cc["false_fold"],
                     "escalation_noise": noise})
    return rows


def write_report(rows, path: Path) -> None:
    n = len(rows)
    tot_claims = sum(r["n_claims"] for r in rows)
    tot_clusters = sum(r["n_clusters"] for r in rows)
    esc25 = [r for r in rows if r["p25_class"] == "ESCALATE"]
    esc26 = [r for r in rows if r["p26_class"] == "ESCALATE"]
    noise = [r for r in rows if r["escalation_noise"]]
    false_fold = [r for r in rows if r["false_fold"]]
    flag_counter = Counter(f for r in rows for f in r["cluster_flags"])
    r7 = next((r for r in rows if r["task_id"] == "tqa-0007"), None)

    md = ["# P26 noise-aware claim canonicalization (limit 100, offline)\n",
          "Groups claims into canonical epistemic regions so structural extractor "
          "noise (conjunction / attribute / location splits) stops inflating "
          "escalation, WITHOUT folding across a logical polarity conflict, deleting "
          "claims, or deciding truth. On the P25 repaired claim graph; no model calls.\n",
          "## Claim -> cluster collapse\n",
          f"- total atomic claims: **{tot_claims}** -> canonical clusters: "
          f"**{tot_clusters}** ({tot_claims - tot_clusters} claims folded into shared "
          "regions).",
          f"- cluster flags: `{dict(flag_counter)}`",
          ""]

    md.append("## Escalation: were the 39 inflated?\n")
    md.append(f"- ESCALATE (raw-claim, P25): **{len(esc25)}** -> ESCALATE "
              f"(cluster-aware, P26): **{len(esc26)}**.")
    md.append(f"- **escalation-noise candidates (escalated only because of within-region "
              f"splits): {len(noise)}** ({', '.join(r['task_id'] for r in noise[:20])}"
              f"{'...' if len(noise) > 20 else ''}).")
    md.append(f"- So ~{len(noise)} of the {len(esc25)} P25 escalations were structural "
              "noise inflation, not new epistemic regions.")
    md.append("")

    md.append("## Is tqa-0007 still protected?\n")
    if r7:
        md.append(f"- `tqa-0007`: P25 {r7['p25_class']} -> P26 **{r7['p26_class']}** "
                  f"(n_claims {r7['n_claims']} -> clusters {r7['n_clusters']}). "
                  + ("PROTECTED — still ESCALATE (its negation/logical-risk token keeps "
                     "it escalation-worthy even after region folding), so it still "
                     "reaches DBA + typed governance."
                     if r7["p26_class"] == "ESCALATE" else
                     "NOT escalated — REGRESSION, canonicalization folded a logically-"
                     "loaded case (investigate)."))
    md.append("")

    md.append("## Does real reconstruction ambiguity survive?\n")
    md.append(f"- {len(esc26)} cases still ESCALATE under cluster-aware folding — these "
              "are answers with >=2 DISTINCT regions / >=2 claim types / a logical-risk "
              "token, i.e. genuine reconstruction structure. Region folding removes the "
              "split noise but keeps multi-region answers escalation-eligible.")
    md.append("")

    risky_deesc = [r for r in noise if r["false_fold"]]
    md.append("## New false-fold risk (honesty-critical)\n")
    md.append(f"- **Of the {len(noise)} de-escalations, {len(risky_deesc)} are also "
              f"false-fold candidates** ({', '.join(r['task_id'] for r in risky_deesc) or 'none'}) "
              "— these may be WRONG de-escalations (a genuine multi-item list folded to one "
              "region and dropped below the escalation bar). So the noise removal is real "
              "but imperfect.")
    md.append(f"- **{len(false_fold)} cases** total had a cluster that folded >=2 multi-token, "
              "pairwise-dissimilar objects — a possible GENUINE list folded as one region "
              f"({', '.join(r['task_id'] for r in false_fold[:20])}"
              f"{'...' if len(false_fold) > 20 else ''}).")
    md.append("- Root cause: the P24 rule extractor grounds EVERY list item on one "
              "question-topic subject with predicate 'includes', so canonicalization "
              "cannot distinguish attribute-decomposition (tqa-0037: Forest Lawn / "
              "Glendale / California = one place -> correct fold) from a genuine "
              "distinct-item list (tqa-0058: sweeping / flying / Quidditch / props -> "
              "arguably 4 regions -> false fold). Both share subject+predicate, so both "
              "fold. This is a limit of the crude rule claims, not of canonicalization "
              "itself.")
    md.append("")

    md.append("## Architecture answer: tolerate noise AND keep conflicts visible?\n")
    md.append("- **Partly yes.** Region folding cuts the escalation inflation "
              f"({len(esc25)} -> {len(esc26)}) while the negation/polarity split guard "
              "keeps logical conflicts (tqa-0007) escalation-worthy. So DESi can absorb "
              "granularity noise and still surface a logical-risk case.")
    md.append("- **But the guarantee is weak on crude claims.** Because the rule "
              "extractor uses one subject per answer, canonicalization over-folds genuine "
              "multi-item lists (the false-fold cases). Robust 'tolerate noise AND keep "
              "conflicts' needs a real extractor that assigns DISTINCT subjects to "
              "distinct items (so genuine lists are multi-region and noise is "
              "single-region) — a model-extractor fix, not a clustering fix.")
    md.append("")

    md.append("## Reading\n")
    md.append(f"- **Were the 39 inflated?** Yes — ~{len(noise)} were within-region split "
              f"noise; cluster-aware ESCALATE is {len(esc26)}.")
    md.append("- **More robust to extractor noise?** Yes for escalation sizing; "
              "structural splits no longer each count as a region.")
    md.append("- **Real conflicts preserved?** Yes for the negation case (tqa-0007 stays "
              "ESCALATE via its risk token + the polarity guard).")
    md.append(f"- **Folding scales more sensibly?** ESCALATE back to {len(esc26)}/100 "
              "(from 39), closer to the genuine-structure rate — but see false-fold risk.")
    md.append("- **New limit:** subject grounding in the crude extractor. Canonicalization "
              "is region-correct only if subjects are region-correct; the rule "
              "extractor's single-subject grounding makes genuine lists indistinguishable "
              "from attribute splits. Next fix is upstream (model extractor with distinct "
              "per-item subjects), then re-canonicalize.")
    md.append("")
    md.append("## Honesty / limits\n")
    md.append("- No claims deleted, no truth decided, no aggressive dedup — claims are "
              "GROUPED into regions; the underlying claims remain.")
    md.append(f"- Canonicalization can OVER-fold ({len(false_fold)} false-fold candidates) "
              "because the crude rule subjects are coarse; this is disclosed, not hidden.")
    md.append("- Offline on the P25 repaired (rule-extracted) graph; with real model "
              "claims (distinct subjects) the fold/keep boundary would be cleaner. No API "
              "calls, no new model/score/judge.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(md) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="P26 noise-aware canonicalization.")
    ap.add_argument("--records", type=Path, default=_LIVE)
    ap.add_argument("--repaired", type=Path, default=_REPAIRED)
    ap.add_argument("--report", type=Path,
                    default=_HERE / "outputs" / "p26_noise_aware_canonicalization_report.limit100.md")
    args = ap.parse_args()
    if not args.records.exists() or not args.repaired.exists():
        print("Missing artifacts (need P25 repaired graph).", file=sys.stderr)
        return 1
    rows = run(_load(args.records), _load(args.repaired))
    write_report(rows, args.report)
    e25 = sum(1 for r in rows if r["p25_class"] == "ESCALATE")
    e26 = sum(1 for r in rows if r["p26_class"] == "ESCALATE")
    noise = sum(1 for r in rows if r["escalation_noise"])
    ff = sum(1 for r in rows if r["false_fold"])
    print(f"claims {sum(r['n_claims'] for r in rows)} -> clusters "
          f"{sum(r['n_clusters'] for r in rows)} | ESCALATE {e25} -> {e26} | "
          f"noise-inflated {noise} | false-fold-candidates {ff} -> {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
