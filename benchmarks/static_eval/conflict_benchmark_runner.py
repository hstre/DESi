#!/usr/bin/env python3
"""Run the P4 conflict detector against the targeted P5 benchmark dataset.

Writes the pair claims + detected conflict relations into an InMemoryStore,
derives governance signals (mark only), compares detected vs expected per pair,
and writes a metrics report. Heuristic benchmark only — no ontology, no world
model. No network, no secrets.
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

_LEVELS = ("contradiction", "potential", "compatible")


def run() -> tuple[list[dict], InMemoryStore, dict]:
    gs = groups()
    store = InMemoryStore()
    rec = MemoryRecorder(store)
    rec.start_run(model="conflict_benchmark", label="p5_conflict_benchmark", config={})
    claims_by_id, recorded = {}, {}
    conflicts, results = [], []

    def _state(s):
        return ClaimState(s) if s in {x.value for x in ClaimState} else ClaimState.PROPOSED

    for g in gs:
        a = {**g["a"], "_id": g["id"] + "_a"}
        b = {**g["b"], "_id": g["id"] + "_b"}
        claims_by_id[a["_id"]] = a
        claims_by_id[b["_id"]] = b
        for c in (a, b):
            recorded[c["_id"]] = rec.record_claim(
                content=f"{c['subject']} | {c['predicate']} | {c['object']}",
                method=f"benchmark_{g['category']}", state=_state(c.get("state", "proposed")),
                confidence=0.7, operator_path=(g["id"],))
        cf = conflict_between(a, b)
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
    gov = governance_signals(claims_by_id, conflicts)
    return results, store, gov


def _prf(results: list[dict], cls: str) -> tuple[int, int, int, float, float]:
    tp = sum(1 for r in results if r["expected"] == cls and r["detected"] == cls)
    fp = sum(1 for r in results if r["detected"] == cls and r["expected"] != cls)
    fn = sum(1 for r in results if r["expected"] == cls and r["detected"] != cls)
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    rec = tp / (tp + fn) if (tp + fn) else 0.0
    return tp, fp, fn, prec, rec


def write_report(results: list[dict], store: InMemoryStore, gov: dict, path: Path) -> None:
    n = len(results)
    exact = sum(1 for r in results if r["correct"])
    c_tp, c_fp, c_fn, c_prec, c_rec = _prf(results, "contradiction")
    p_tp, p_fp, p_fn, p_prec, p_rec = _prf(results, "potential")
    mv = [r for r in results if r["category"] == "multi_valued"]
    mv_fp = sum(1 for r in mv if r["detected"] != "compatible")

    md = ["# Targeted conflict benchmark (P5)\n",
          f"- pairs: **{n}** | exact-match (detected == expected): "
          f"**{exact}/{n} = {100.0*exact/n:.0f}%**\n",
          "## Contradiction / potential metrics\n",
          f"- **contradiction**: TP={c_tp} FP={c_fp} FN={c_fn} | "
          f"precision **{c_prec:.2f}**, recall **{c_rec:.2f}**",
          f"- **potential**: TP={p_tp} FP={p_fp} FN={p_fn} | "
          f"precision **{p_prec:.2f}**, recall **{p_rec:.2f}**",
          f"- **multi-valued false positives** (flagged though compatible): "
          f"**{mv_fp}/{len(mv)}**\n",
          "## Per category (expected → detected)\n",
          "| category | n | exact | detected breakdown |", "| --- | --- | --- | --- |"]
    by_cat = defaultdict(list)
    for r in results:
        by_cat[r["category"]].append(r)
    for cat in ("negation", "numeric", "temporal", "attribute",
                "multi_valued", "paraphrase", "uncertain"):
        rs = by_cat.get(cat, [])
        if not rs:
            continue
        ex = sum(1 for r in rs if r["correct"])
        det = Counter(r["detected"] for r in rs)
        md.append(f"| {cat} | {len(rs)} | {ex}/{len(rs)} | `{dict(det)}` |")
    md.append("")

    md.append("## Good detections (correct)\n")
    for r in [r for r in results if r["correct"] and r["detected"] != "compatible"][:5]:
        md.append(f"- `{r['id']}` [{r['category']}→{r['detected']}/{r['rule']}] {r['reason']}")
    md.append("\n## Bad detections (mismatch)\n")
    for r in [r for r in results if not r["correct"]][:8]:
        md.append(f"- `{r['id']}` [{r['category']}] expected **{r['expected']}**, "
                  f"got **{r['detected']}** ({r['rule']})")
    md.append("")

    md.append("## Governance (mark only, never overwrite)\n")
    rej_conf = [cid for cid, gsig in gov.items()
                if "rejected_vs_confirmed" in gsig.get("flags", [])]
    md.append(f"- claims with conflict-derived risk: **{len(gov)}**")
    md.append(f"- REJECTED-vs-CONFIRMED contradictions flagged: "
              f"**{len(rej_conf)} claims**")
    for cid in rej_conf[:4]:
        g = gov[cid]
        md.append(f"    - {cid}: risk={g['epistemic_risk_score']} band={g['confidence_band']}")
    md.append("")

    md.append("## Robust vs. dangerous rules\n")
    md.append("- **Robust:** `negation` (is/is not, can/cannot), `numeric` "
              "single-value mismatch, and antonym `attribute` (hot/cold, "
              "true/false, possible/impossible, safe/dangerous, legal/illegal) — "
              "high precision on same-subject pairs.")
    md.append("- **Dangerous / FP-prone:** `different-object` → `potential`. The "
              "detector cannot tell a **multi-valued compatible** pair (Libra "
              "diplomatic/charming) from a genuinely **uncertain** one (suspect in "
              "London/Paris) — both are same subject+predicate, different object. "
              "It honestly labels both `potential`, so multi-valued pairs become "
              "potential false positives.")
    md.append("- **Gaps:** temporal `before/after` is not an antonym pair, so it "
              "falls to `potential` instead of `contradiction` (recall gap); "
              "contractions and coreference/paraphrase with different surface "
              "subjects are out of scope.\n")
    md.append("## Honesty / limits\n")
    md.append("Heuristic benchmark of a heuristic detector: **no ontology, no "
              "world model, no general truth solver**. Labels are a reasonable "
              "human reading, not ground truth. `potential` is represented in the "
              "closed DESi enum as a low-weight CONTRADICTS edge. Governance marks "
              "risk; it never rewrites a claim's stored state.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(md) + "\n", encoding="utf-8")


def main() -> int:
    p = argparse.ArgumentParser(description="Run the P5 conflict benchmark.")
    p.add_argument("--report", type=Path, default=Path(__file__).resolve().parent
                   / "outputs" / "conflict_benchmark_report.md")
    args = p.parse_args()
    results, store, gov = run()
    write_report(results, store, gov, args.report)
    exact = sum(1 for r in results if r["correct"])
    c_tp, c_fp, c_fn, c_prec, c_rec = _prf(results, "contradiction")
    print(f"Benchmark: {exact}/{len(results)} exact; contradiction "
          f"precision={c_prec:.2f} recall={c_rec:.2f}. Report -> {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
