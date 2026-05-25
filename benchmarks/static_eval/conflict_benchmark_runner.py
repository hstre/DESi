#!/usr/bin/env python3
"""Run the conflict detector against the targeted benchmark, comparing P5
(no predicate typing) vs P6 (predicate typing + temporal + unit normalisation)
on the identical dataset. Heuristic benchmark only — no ontology, no world model.
No network, no secrets.
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


def run(predicate_types: bool = True) -> tuple[list[dict], InMemoryStore, dict]:
    gs = groups()
    store = InMemoryStore()
    rec = MemoryRecorder(store)
    rec.start_run(model="conflict_benchmark",
                  label="p6" if predicate_types else "p5",
                  config={"predicate_types": predicate_types})
    claims_by_id, recorded, conflicts, results = {}, {}, [], []

    def _state(s):
        return ClaimState(s) if s in {x.value for x in ClaimState} else ClaimState.PROPOSED

    for g in gs:
        a = {**g["a"], "_id": g["id"] + "_a"}
        b = {**g["b"], "_id": g["id"] + "_b"}
        claims_by_id[a["_id"]], claims_by_id[b["_id"]] = a, b
        for c in (a, b):
            recorded[c["_id"]] = rec.record_claim(
                content=f"{c['subject']} | {c['predicate']} | {c['object']}",
                method=f"benchmark_{g['category']}", state=_state(c.get("state", "proposed")),
                confidence=0.7, operator_path=(g["id"],))
        cf = conflict_between(a, b, predicate_types=predicate_types)
        detected = cf.level if cf else "compatible"
        if cf:
            conflicts.append(cf)
            rec.record_relation(source=recorded[cf.a], target=recorded[cf.b],
                                rel_type=RelationType.CONTRADICTS,
                                weight=0.9 if cf.level == "contradiction" else 0.4)
        results.append({"id": g["id"], "category": g["category"], "expected": g["expected"],
                        "detected": detected, "correct": detected == g["expected"],
                        "rule": cf.rule if cf else "-",
                        "reason": cf.reason if cf else "no conflict"})
    rec.end_run()
    return results, store, governance_signals(claims_by_id, conflicts)


def _prf(results: list[dict], cls: str) -> tuple[int, int, int, float, float]:
    tp = sum(1 for r in results if r["expected"] == cls and r["detected"] == cls)
    fp = sum(1 for r in results if r["detected"] == cls and r["expected"] != cls)
    fn = sum(1 for r in results if r["expected"] == cls and r["detected"] != cls)
    return tp, fp, fn, (tp / (tp + fp) if tp + fp else 0.0), (tp / (tp + fn) if tp + fn else 0.0)


def _metrics(results):
    n = len(results)
    exact = sum(1 for r in results if r["correct"])
    c = _prf(results, "contradiction")
    p = _prf(results, "potential")
    mv = [r for r in results if r["category"] == "multi_valued"]
    mv_fp = sum(1 for r in mv if r["detected"] != "compatible")
    tmp = [r for r in results if r["category"] == "temporal"]
    tmp_ok = sum(1 for r in tmp if r["correct"])
    return {"n": n, "exact": exact, "c": c, "p": p, "mv_fp": (mv_fp, len(mv)),
            "tmp": (tmp_ok, len(tmp))}


def write_compare_report(p5, p6, p6_store, p6_gov, path: Path) -> None:
    m5, m6 = _metrics(p5), _metrics(p6)

    def row(name, f5, f6):
        return f"| {name} | {f5} | {f6} |"

    md = ["# Conflict benchmark: P5 (no predicate typing) vs P6 (predicate typing)\n",
          f"- pairs: **{m6['n']}**\n",
          "| metric | P5 | P6 |", "| --- | --- | --- |",
          row("exact-match", f"{m5['exact']}/{m5['n']}", f"{m6['exact']}/{m6['n']}"),
          row("contradiction precision", f"{m5['c'][3]:.2f}", f"{m6['c'][3]:.2f}"),
          row("contradiction recall", f"{m5['c'][4]:.2f}", f"{m6['c'][4]:.2f}"),
          row("potential precision", f"{m5['p'][3]:.2f}", f"{m6['p'][3]:.2f}"),
          row("potential recall", f"{m5['p'][4]:.2f}", f"{m6['p'][4]:.2f}"),
          row("multi-valued FP rate", f"{m5['mv_fp'][0]}/{m5['mv_fp'][1]}",
              f"{m6['mv_fp'][0]}/{m6['mv_fp'][1]}"),
          row("temporal correct", f"{m5['tmp'][0]}/{m5['tmp'][1]}",
              f"{m6['tmp'][0]}/{m6['tmp'][1]}"),
          ""]

    md.append("## P6 per category (expected → detected)\n")
    md.append("| category | n | exact | detected breakdown |")
    md.append("| --- | --- | --- | --- |")
    by_cat = defaultdict(list)
    for r in p6:
        by_cat[r["category"]].append(r)
    for cat in ("negation", "numeric", "temporal", "attribute",
                "multi_valued", "paraphrase", "uncertain"):
        rs = by_cat.get(cat, [])
        if rs:
            ex = sum(1 for r in rs if r["correct"])
            md.append(f"| {cat} | {len(rs)} | {ex}/{len(rs)} | "
                      f"`{dict(Counter(r['detected'] for r in rs))}` |")
    md.append("")

    md.append("## What P6 fixed\n")
    fixed = [(r5, r6) for r5, r6 in zip(p5, p6) if r5["detected"] != r6["detected"]]
    for r5, r6 in fixed[:10]:
        md.append(f"- `{r6['id']}` [{r6['category']}] {r5['detected']} → **{r6['detected']}** "
                  f"(now {'correct' if r6['correct'] else 'still off'}; rule {r6['rule']})")
    md.append("")
    md.append("## Remaining mismatches in P6\n")
    for r in [r for r in p6 if not r["correct"]][:8]:
        md.append(f"- `{r['id']}` [{r['category']}] expected **{r['expected']}**, "
                  f"got **{r['detected']}** ({r['rule']})")
    md.append("")
    rej = [cid for cid, g in p6_gov.items() if "rejected_vs_confirmed" in g.get("flags", [])]
    md.append("## Governance (mark only)\n")
    md.append(f"- claims with conflict-derived risk: **{len(p6_gov)}**")
    md.append(f"- REJECTED-vs-CONFIRMED flagged: **{len(rej)} claims**\n")
    md.append("## Honesty / limits\n")
    md.append("Predicate typing is keyword-based (no ontology). Multi-valued is "
              "inferred from predicate keywords (`has`, `contains`, `described as`, "
              "…); a contradiction on a multi-valued predicate would be missed. "
              "Temporal handles before/after with a shared reference only. Unit "
              "normalisation covers a few cases (celsius, percent). Still heuristic, "
              "same-subject only, no world model; labels are a human reading.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(md) + "\n", encoding="utf-8")


def main() -> int:
    p = argparse.ArgumentParser(description="P5-vs-P6 conflict benchmark.")
    p.add_argument("--report", type=Path, default=Path(__file__).resolve().parent
                   / "outputs" / "conflict_benchmark_p6_report.md")
    args = p.parse_args()
    p5, _, _ = run(predicate_types=False)
    p6, p6_store, p6_gov = run(predicate_types=True)
    write_compare_report(p5, p6, p6_store, p6_gov, args.report)
    m5, m6 = _metrics(p5), _metrics(p6)
    print(f"P5 exact {m5['exact']}/{m5['n']} mv_fp {m5['mv_fp'][0]}/{m5['mv_fp'][1]} "
          f"temporal {m5['tmp'][0]}/{m5['tmp'][1]} | "
          f"P6 exact {m6['exact']}/{m6['n']} mv_fp {m6['mv_fp'][0]}/{m6['mv_fp'][1]} "
          f"temporal {m6['tmp'][0]}/{m6['tmp'][1]}; "
          f"contradiction P/R P5={m5['c'][3]:.2f}/{m5['c'][4]:.2f} "
          f"P6={m6['c'][3]:.2f}/{m6['c'][4]:.2f}. Report -> {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
