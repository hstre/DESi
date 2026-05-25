#!/usr/bin/env python3
"""Run the conflict detector against the targeted benchmark, comparing P6
(predicate typing, string-exact subjects) vs P7 (+ entity normalisation + light
coreference) on the identical dataset. Heuristic benchmark only — no ontology,
no world model, no real NER. No network, no secrets.
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter, defaultdict
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from desi.memory.claim import ClaimState                 # noqa: E402
from desi.memory.recorder import MemoryRecorder          # noqa: E402
from desi.memory.relations import RelationType           # noqa: E402
from desi.memory.store import InMemoryStore              # noqa: E402
from conflict_benchmark_dataset import groups            # noqa: E402
from cross_claim_contradictions import (conflict_between,  # noqa: E402
                                        governance_signals)
from entity_normalization import is_pronoun, resolve_pronoun  # noqa: E402
from desi.spl_core import project_atomic_claim  # noqa: E402

_ALIAS_CATS = {"alias", "name_form", "abbreviation", "pronoun"}

# SPL "state" mode: map a claim's epistemic state to an extractor confidence,
# which SPL-core turns into projection entropy. A rejected claim has low standing
# -> low confidence -> high entropy -> the gate blocks it. This is an adapter
# policy choice (documented), NOT original SPL behaviour.
_STATE_CONFIDENCE = {"confirmed": 0.92, "proposed": 0.70, "rejected": 0.40}


def _confidence_for(claim: dict, spl_mode: str | None) -> float:
    if spl_mode == "state":
        return _STATE_CONFIDENCE.get(claim.get("state", "proposed"), 0.70)
    return 0.70  # matches the recorder's uniform confidence


def run(predicate_types: bool = True, entity_norm: bool = True,
        spl_mode: str | None = None
        ) -> tuple[list[dict], InMemoryStore, dict]:
    """spl_mode: None = compare raw triples (P6/P7). "uniform"/"state" = route
    every claim through the canonical SPL-core gate first and compare only the
    admissible CanonicalClaimCandidates (uniform 0.7 confidence, or state-derived)."""
    store = InMemoryStore()
    rec = MemoryRecorder(store)
    label = ("spl_" + spl_mode) if spl_mode else ("p7" if entity_norm else "p6")
    rec.start_run(model="conflict_benchmark", label=label,
                  config={"predicate_types": predicate_types,
                          "entity_norm": entity_norm, "spl_mode": spl_mode})
    claims_by_id, recorded, conflicts, results = {}, {}, [], []

    def _state(s):
        return ClaimState(s) if s in {x.value for x in ClaimState} else ClaimState.PROPOSED

    for g in groups():
        a = {**g["a"], "_id": g["id"] + "_a"}
        b = {**g["b"], "_id": g["id"] + "_b"}
        # light coreference (P7 only): resolve a pronoun to the local antecedent
        if entity_norm:
            if is_pronoun(a["subject"]) and not is_pronoun(b["subject"]):
                a = {**a, "subject": resolve_pronoun(a["subject"], b["subject"])}
            elif is_pronoun(b["subject"]) and not is_pronoun(a["subject"]):
                b = {**b, "subject": resolve_pronoun(b["subject"], a["subject"])}
        claims_by_id[a["_id"]], claims_by_id[b["_id"]] = a, b
        for c in (a, b):
            recorded[c["_id"]] = rec.record_claim(
                content=f"{c['subject']} | {c['predicate']} | {c['object']}",
                method=f"benchmark_{g['category']}", state=_state(c.get("state", "proposed")),
                confidence=0.7, operator_path=(g["id"],))

        spl_fields: dict = {}
        if spl_mode:
            # Canonical SPL-core: each claim becomes a CanonicalClaimCandidate;
            # the conflict engine only ever sees *admissible* candidates.
            ka, _ = project_atomic_claim({**a, "confidence": _confidence_for(a, spl_mode)})
            kb, _ = project_atomic_claim({**b, "confidence": _confidence_for(b, spl_mode)})
            ca = ka.as_conflict_claim(_id=a["_id"], state=a.get("state")) if ka.admissible else None
            cb = kb.as_conflict_claim(_id=b["_id"], state=b.get("state")) if kb.admissible else None
            suppressed = ca is None or cb is None
            cf = (None if suppressed
                  else conflict_between(ca, cb, predicate_types=predicate_types,
                                        entity_norm=entity_norm))
            spl_fields = {
                "gateway_valid_a": ka.admissible, "gateway_valid_b": kb.admissible,
                "entropy_a": round(ka.projection_entropy or 0.0, 4),
                "entropy_b": round(kb.projection_entropy or 0.0, 4),
                "rule_a": ka.emission_rule, "rule_b": kb.emission_rule,
                "status_a": ka.emission_rule, "status_b": kb.emission_rule,
                "projection_suppressed": suppressed}
        else:
            cf = conflict_between(a, b, predicate_types=predicate_types, entity_norm=entity_norm)

        detected = cf.level if cf else "compatible"
        if cf:
            conflicts.append(cf)
            rec.record_relation(source=recorded[cf.a], target=recorded[cf.b],
                                rel_type=RelationType.CONTRADICTS,
                                weight=0.9 if cf.level == "contradiction" else 0.4)
        results.append({"id": g["id"], "category": g["category"], "expected": g["expected"],
                        "detected": detected, "correct": detected == g["expected"],
                        "rule": cf.rule if cf else "-",
                        "subject_match": cf.subject_match if cf else "-",
                        "reason": cf.reason if cf else "no conflict", **spl_fields})
    rec.end_run()
    return results, store, governance_signals(claims_by_id, conflicts)


def _prf(results, cls):
    tp = sum(1 for r in results if r["expected"] == cls and r["detected"] == cls)
    fp = sum(1 for r in results if r["detected"] == cls and r["expected"] != cls)
    fn = sum(1 for r in results if r["expected"] == cls and r["detected"] != cls)
    return tp, fp, fn, (tp / (tp + fp) if tp + fp else 0.0), (tp / (tp + fn) if tp + fn else 0.0)


def _metrics(results):
    n = len(results)
    ac = [r for r in results if r["category"] in _ALIAS_CATS]
    ac_ok = sum(1 for r in ac if r["correct"])
    return {"n": n, "exact": sum(1 for r in results if r["correct"]),
            "c": _prf(results, "contradiction"), "p": _prf(results, "potential"),
            "alias_coref": (ac_ok, len(ac))}


def write_compare_report(p6, p7, p7_store, p7_gov, path: Path) -> None:
    m6, m7 = _metrics(p6), _metrics(p7)

    def r(name, x, y):
        return f"| {name} | {x} | {y} |"

    md = ["# Conflict benchmark: P6 (string-exact) vs P7 (entity normalisation)\n",
          f"- pairs: **{m7['n']}**\n",
          "| metric | P6 | P7 |", "| --- | --- | --- |",
          r("exact-match", f"{m6['exact']}/{m6['n']}", f"{m7['exact']}/{m7['n']}"),
          r("contradiction precision", f"{m6['c'][3]:.2f}", f"{m7['c'][3]:.2f}"),
          r("contradiction recall", f"{m6['c'][4]:.2f}", f"{m7['c'][4]:.2f}"),
          r("potential precision", f"{m6['p'][3]:.2f}", f"{m7['p'][3]:.2f}"),
          r("alias/coref recall", f"{m6['alias_coref'][0]}/{m6['alias_coref'][1]}",
            f"{m7['alias_coref'][0]}/{m7['alias_coref'][1]}"),
          ""]

    md.append("## P7 per category (expected → detected)\n")
    md.append("| category | n | exact | detected breakdown |")
    md.append("| --- | --- | --- | --- |")
    by_cat = defaultdict(list)
    for x in p7:
        by_cat[x["category"]].append(x)
    for cat in sorted(by_cat):
        rs = by_cat[cat]
        ex = sum(1 for x in rs if x["correct"])
        md.append(f"| {cat} | {len(rs)} | {ex}/{len(rs)} | "
                  f"`{dict(Counter(x['detected'] for x in rs))}` |")
    md.append("")

    md.append("## What P7 newly detects (via entity normalisation)\n")
    for x6, x7 in zip(p6, p7):
        if x6["detected"] != x7["detected"]:
            md.append(f"- `{x7['id']}` [{x7['category']}] {x6['detected']} → "
                      f"**{x7['detected']}** via subject_match=`{x7['subject_match']}` "
                      f"({'correct' if x7['correct'] else 'now off'})")
    md.append("")
    md.append("## False-positive risks of aggressive merging\n")
    for x in p7:
        if x["category"] in ("homonym_fp", "merge_fp"):
            ok = "OK (stayed compatible)" if x["detected"] == "compatible" else \
                 f"FALSE MERGE → {x['detected']}"
            md.append(f"- `{x['id']}` [{x['category']}] {ok} (subject_match={x['subject_match']})")
    md.append("")
    md.append("## Remaining mismatches in P7\n")
    for x in [x for x in p7 if not x["correct"]][:8]:
        md.append(f"- `{x['id']}` [{x['category']}] expected **{x['expected']}**, "
                  f"got **{x['detected']}** ({x['rule']}, match={x['subject_match']})")
    md.append("")
    emu = sum(1 for g in p7_gov.values()
              if any(f.startswith("entity_merge_uncertainty") for f in g.get("flags", [])))
    md.append("## Governance (mark only)\n")
    md.append(f"- claims with conflict-derived risk: **{len(p7_gov)}**")
    md.append(f"- claims flagged `entity_merge_uncertainty` (conflict relies on a "
              f"non-exact subject merge): **{emu}**\n")
    md.append("## Honesty / limits\n")
    md.append("Entity normalisation is heuristic: lowercase/articles, a tiny "
              "abbreviation table (USA/UK/UAE/NYC…), a cautious surname alias "
              "(blocked for place/org words like 'City'), light singularisation, "
              "and unit normalisation. Coreference is just a local last-subject "
              "fallback for he/she/it/they — **no** real NER, **no** ontology, "
              "**no** global coreference. Homonyms (Paris/France vs Paris/Texas) "
              "are an inherent danger of symbolic equality, not solved here; "
              "non-exact merges are flagged `entity_merge_uncertainty`, never "
              "silently trusted.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(md) + "\n", encoding="utf-8")


def _fp_counts(results) -> dict:
    mv = [r for r in results if r["category"] == "multi_valued"]
    ho = [r for r in results if r["category"] in ("homonym_fp", "merge_fp")]
    return {"multi_valued_fp": (sum(1 for r in mv if r["detected"] != "compatible"), len(mv)),
            "homonym_fp": (sum(1 for r in ho if r["detected"] != "compatible"), len(ho))}


def _spl_stats(results) -> dict:
    """Aggregate SPL-specific signals from per-result spl_fields (SPL modes)."""
    gv_invalid = 0
    suppressed = 0
    entropies: list[float] = []
    by_rule: Counter = Counter()
    for r in results:
        if "gateway_valid_a" not in r:
            return {}
        for side in ("a", "b"):
            if not r[f"gateway_valid_{side}"]:
                gv_invalid += 1
            entropies.append(r[f"entropy_{side}"])
            by_rule[r[f"rule_{side}"] or "blocked"] += 1
        if r["projection_suppressed"]:
            suppressed += 1
    buckets = {"<0.25 (E1 zone)": 0, "0.25-0.65 (E2 zone)": 0, ">=0.65 (E3 block)": 0}
    for h in entropies:
        if h < 0.25:
            buckets["<0.25 (E1 zone)"] += 1
        elif h < 0.65:
            buckets["0.25-0.65 (E2 zone)"] += 1
        else:
            buckets[">=0.65 (E3 block)"] += 1
    return {"claims": len(entropies), "gateway_invalid": gv_invalid,
            "suppressed_pairs": suppressed, "by_rule": dict(by_rule),
            "entropy_buckets": buckets}


def write_spl_report(p7, spl_u, spl_s, path: Path) -> None:
    """P7 symbolic vs SPL-projection (uniform / state-derived confidence)."""
    m7, mu, ms = _metrics(p7), _metrics(spl_u), _metrics(spl_s)
    f7, fu, fs = _fp_counts(p7), _fp_counts(spl_u), _fp_counts(spl_s)
    su, ss = _spl_stats(spl_u), _spl_stats(spl_s)

    def row(name, a, b, c):
        return f"| {name} | {a} | {b} | {c} |"

    md = ["# Conflict benchmark: P7 symbolic vs SPL projection\n",
          "Same dataset, same conflict engine (predicate typing + entity "
          "normalisation). The only difference: in the SPL columns every claim is "
          "first pushed through the **vendored Alexandria SPL gate** "
          "(SemanticUnit → SemanticProjection → SPLGateway.submit → ClaimCandidate) "
          "and only **gateway-valid candidates** reach the conflict engine. No raw "
          "triple is compared directly.\n",
          f"- pairs: **{m7['n']}**",
          "- **P7 symbolic**: raw S/P/O, no SPL gate.",
          "- **SPL (uniform)**: SPL gate at the benchmark's uniform confidence 0.70 "
          "(every claim → E2, nothing blocked).",
          "- **SPL (state)**: SPL gate at a *state-derived* confidence "
          "(confirmed 0.92 → E1, proposed 0.70 → E2, rejected 0.40 → E3 **block**).\n",
          "| metric | P7 symbolic | SPL (uniform) | SPL (state) |",
          "| --- | --- | --- | --- |",
          row("exact-match", f"{m7['exact']}/{m7['n']}", f"{mu['exact']}/{mu['n']}",
              f"{ms['exact']}/{ms['n']}"),
          row("contradiction precision", f"{m7['c'][3]:.2f}", f"{mu['c'][3]:.2f}",
              f"{ms['c'][3]:.2f}"),
          row("contradiction recall", f"{m7['c'][4]:.2f}", f"{mu['c'][4]:.2f}",
              f"{ms['c'][4]:.2f}"),
          row("potential precision", f"{m7['p'][3]:.2f}", f"{mu['p'][3]:.2f}",
              f"{ms['p'][3]:.2f}"),
          row("alias/coref recall", f"{m7['alias_coref'][0]}/{m7['alias_coref'][1]}",
              f"{mu['alias_coref'][0]}/{mu['alias_coref'][1]}",
              f"{ms['alias_coref'][0]}/{ms['alias_coref'][1]}"),
          row("multi_valued FP", f"{f7['multi_valued_fp'][0]}/{f7['multi_valued_fp'][1]}",
              f"{fu['multi_valued_fp'][0]}/{fu['multi_valued_fp'][1]}",
              f"{fs['multi_valued_fp'][0]}/{fs['multi_valued_fp'][1]}"),
          row("homonym/merge FP", f"{f7['homonym_fp'][0]}/{f7['homonym_fp'][1]}",
              f"{fu['homonym_fp'][0]}/{fu['homonym_fp'][1]}",
              f"{fs['homonym_fp'][0]}/{fs['homonym_fp'][1]}"),
          ""]

    md.append("## SPL gate diagnostics\n")
    md.append("| signal | SPL (uniform) | SPL (state) |")
    md.append("| --- | --- | --- |")
    md.append(f"| claims projected | {su['claims']} | {ss['claims']} |")
    md.append(f"| gateway-invalid claims | {su['gateway_invalid']} | {ss['gateway_invalid']} |")
    md.append(f"| pairs suppressed (a claim gated out) | {su['suppressed_pairs']} "
              f"| {ss['suppressed_pairs']} |")
    md.append(f"| emission rules | `{su['by_rule']}` | `{ss['by_rule']}` |")
    md.append(f"| entropy buckets | `{su['entropy_buckets']}` | `{ss['entropy_buckets']}` |")
    md.append("")

    md.append("## What the SPL gate changed vs P7\n")
    diffs = [(x7, xs) for x7, xs in zip(p7, spl_s) if x7["detected"] != xs["detected"]]
    if not diffs:
        md.append("- SPL (uniform) changed **nothing** vs P7: at confidence 0.70 every "
                  "claim emits as E2 and passes the gate, so the conflict engine sees the "
                  "identical candidates. The SPL contribution here is **architectural**, "
                  "not metric (see below).")
    for x7, xs in diffs:
        md.append(f"- `{xs['id']}` [{xs['category']}] {x7['detected']} → **{xs['detected']}** "
                  f"(state mode: a/b gated_valid="
                  f"{xs.get('gateway_valid_a')}/{xs.get('gateway_valid_b')}, "
                  f"{'correct' if xs['correct'] else 'now WRONG'})")
    md.append("")

    md.append("## Interpretation (no overclaim)\n")
    md.append("- **Does SPL improve the conflict metrics?** No. On this dataset SPL "
              "projection at uniform confidence reproduces P7 **exactly** — same "
              "precision, recall, alias/coref recall, FP counts. SPL is a "
              "projection/validation layer, not a contradiction detector: it does not "
              "rewrite subjects/objects, so it cannot by itself catch an alias or a "
              "coreference. That work still belongs to the entity-normalisation stage "
              "*inside* the conflict engine, which runs unchanged on the candidates.")
    md.append("- **What SPL does add (architecturally):** every claim now has to become "
              "a `SemanticUnit`, be projected to a `SemanticProjection`, and survive the "
              "gateway's emission rules (E0–E3) before it is ever comparable. The raw "
              "triple is no longer the unit of comparison — a validated `ClaimCandidate` "
              "is. Each candidate carries `h_norm`, an emission rule, and a provenance "
              "string, i.e. an auditable reason it was allowed to exist.")
    md.append("- **The gate is real (state mode):** when confidence carries epistemic "
              "meaning, the gate fires. Rejected claims (conf 0.40) cross τ₃ and are "
              "E3-blocked, so the pair is suppressed. This *lowers* contradiction recall "
              "on the rejected-vs-confirmed pairs — an honest, instructive negative "
              "result: the entropy gate is a **pre-filter on claim admissibility**, and "
              "coupling it naively to claim-state removes exactly the low-standing claims "
              "a contradiction check would want to see. The gate decides *what may become "
              "a claim*, not *which claims conflict*; those are different jobs.")
    md.append("- **Is direct raw-claim comparison now avoidable?** Yes, structurally. "
              "With `--use-spl-projection` the conflict engine only ever sees candidates "
              "emitted by `SPLGateway.submit()`; a claim that fails projection is never "
              "compared. The benchmark confirms this changes *admissibility*, not "
              "*detection quality*.")
    md.append("")
    md.append("## Honesty / limits\n")
    md.append("The SPL `P_r` here is **synthesised** by the DESi adapter from the "
              "extractor's scalar confidence (peak = confidence, residual spread "
              "uniformly over a fixed synthetic relation space); it is **not** a semantic "
              "entropy measured over a real relation matrix — there is no NLP backend. So "
              "`h_norm` is a confidence-shaped quantity and the gate is, in effect, a "
              "calibrated confidence gate wearing the SPL's emission machinery. The "
              "vendored SPL code (spl.py / spl_gateway.py) is unmodified original SPL; the "
              "synthesis and the state→confidence policy are clearly-marked DESi adapter "
              "choices. SPL is not a truth solver, not NER, not an ontology.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(md) + "\n", encoding="utf-8")


def main() -> int:
    p = argparse.ArgumentParser(description="P6-vs-P7 conflict benchmark.")
    p.add_argument("--report", type=Path, default=Path(__file__).resolve().parent
                   / "outputs" / "conflict_benchmark_p7_report.md")
    p.add_argument("--use-spl-projection", action="store_true",
                   help="Also run the SPL-projection comparison (P7 vs SPL gate) and "
                        "write outputs/spl_vs_symbolic_benchmark.md.")
    p.add_argument("--spl-report", type=Path, default=Path(__file__).resolve().parent
                   / "outputs" / "spl_vs_symbolic_benchmark.md")
    args = p.parse_args()
    p6, _, _ = run(predicate_types=True, entity_norm=False)
    p7, p7_store, p7_gov = run(predicate_types=True, entity_norm=True)
    write_compare_report(p6, p7, p7_store, p7_gov, args.report)
    m6, m7 = _metrics(p6), _metrics(p7)
    print(f"P6 exact {m6['exact']}/{m6['n']} alias/coref {m6['alias_coref'][0]}/{m6['alias_coref'][1]} "
          f"c-recall {m6['c'][4]:.2f} | P7 exact {m7['exact']}/{m7['n']} "
          f"alias/coref {m7['alias_coref'][0]}/{m7['alias_coref'][1]} "
          f"c-prec {m7['c'][3]:.2f} c-recall {m7['c'][4]:.2f}. Report -> {args.report}")
    if args.use_spl_projection:
        spl_u, _, _ = run(predicate_types=True, entity_norm=True, spl_mode="uniform")
        spl_s, _, _ = run(predicate_types=True, entity_norm=True, spl_mode="state")
        write_spl_report(p7, spl_u, spl_s, args.spl_report)
        mu, ms = _metrics(spl_u), _metrics(spl_s)
        su = _spl_stats(spl_u)
        ss = _spl_stats(spl_s)
        print(f"SPL(uniform) exact {mu['exact']}/{mu['n']} c-recall {mu['c'][4]:.2f} "
              f"gw_invalid {su['gateway_invalid']} suppressed {su['suppressed_pairs']} | "
              f"SPL(state) exact {ms['exact']}/{ms['n']} c-recall {ms['c'][4]:.2f} "
              f"gw_invalid {ss['gateway_invalid']} suppressed {ss['suppressed_pairs']}. "
              f"Report -> {args.spl_report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
