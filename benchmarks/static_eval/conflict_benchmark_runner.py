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

_ALIAS_CATS = {"alias", "name_form", "abbreviation", "pronoun"}


def run(predicate_types: bool = True, entity_norm: bool = True
        ) -> tuple[list[dict], InMemoryStore, dict]:
    store = InMemoryStore()
    rec = MemoryRecorder(store)
    rec.start_run(model="conflict_benchmark",
                  label=("p7" if entity_norm else "p6"),
                  config={"predicate_types": predicate_types, "entity_norm": entity_norm})
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
                        "reason": cf.reason if cf else "no conflict"})
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


def main() -> int:
    p = argparse.ArgumentParser(description="P6-vs-P7 conflict benchmark.")
    p.add_argument("--report", type=Path, default=Path(__file__).resolve().parent
                   / "outputs" / "conflict_benchmark_p7_report.md")
    args = p.parse_args()
    p6, _, _ = run(predicate_types=True, entity_norm=False)
    p7, p7_store, p7_gov = run(predicate_types=True, entity_norm=True)
    write_compare_report(p6, p7, p7_store, p7_gov, args.report)
    m6, m7 = _metrics(p6), _metrics(p7)
    print(f"P6 exact {m6['exact']}/{m6['n']} alias/coref {m6['alias_coref'][0]}/{m6['alias_coref'][1]} "
          f"c-recall {m6['c'][4]:.2f} | P7 exact {m7['exact']}/{m7['n']} "
          f"alias/coref {m7['alias_coref'][0]}/{m7['alias_coref'][1]} "
          f"c-prec {m7['c'][3]:.2f} c-recall {m7['c'][4]:.2f}. Report -> {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
