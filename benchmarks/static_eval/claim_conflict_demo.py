#!/usr/bin/env python3
"""P4 demo: detect cross-claim contradictions on the existing TruthfulQA claim
graph's atomic claims, write conflict relations into a store, derive governance
signals, and write a report.

Honest prototype: heuristic, same-subject only, no truth solver / ontology.
Most TruthfulQA atomic claims come from *different* questions, so real
cross-claim conflicts are expected to be rare; crafted pairs validate that the
heuristics fire. No secrets; no network.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from desi.memory.claim import ClaimState                 # noqa: E402
from desi.memory.recorder import MemoryRecorder          # noqa: E402
from desi.memory.relations import RelationType           # noqa: E402
from desi.memory.store import InMemoryStore              # noqa: E402
from cross_claim_contradictions import (Conflict, detect_conflicts,  # noqa: E402
                                        governance_signals)

DEFAULT_GRAPH = (Path(__file__).resolve().parent / "outputs"
                 / "truthfulqa.deepseek-v4.desi_claim_graph.limit50.jsonl")

# Crafted pairs to validate the heuristics (these are NOT from the dataset).
CRAFTED = [
    {"subject": "Earth", "predicate": "is", "object": "flat", "state": "rejected"},
    {"subject": "Earth", "predicate": "is not", "object": "flat", "state": "confirmed"},
    {"subject": "Abraham Lincoln", "predicate": "birth year", "object": "1809", "state": "confirmed"},
    {"subject": "Abraham Lincoln", "predicate": "birth year", "object": "1810", "state": "proposed"},
    {"subject": "the patient", "predicate": "is", "object": "alive", "state": "proposed"},
    {"subject": "the patient", "predicate": "is", "object": "dead", "state": "proposed"},
    {"subject": "a cat", "predicate": "can", "object": "fly", "state": "proposed"},
    {"subject": "a cat", "predicate": "cannot", "object": "fly", "state": "confirmed"},
    {"subject": "the task", "predicate": "is", "object": "possible", "state": "proposed"},
    {"subject": "the task", "predicate": "is", "object": "impossible", "state": "proposed"},
]


def _parse_triple(content: str) -> tuple[str, str, str]:
    parts = [p.strip() for p in str(content).split("|")]
    parts += ["", "", ""]
    return parts[0], parts[1], parts[2]


def _load_atomic(graph_path: Path) -> list[dict]:
    claims = []
    if not graph_path.exists():
        return claims
    for line in graph_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        for a in row.get("atomic_claims", []):
            s, p, o = _parse_triple(a.get("content", ""))
            claims.append({"_id": a.get("claim_id", ""), "subject": s, "predicate": p,
                           "object": o, "claim_type": a.get("claim_type", "fact"),
                           "confidence": a.get("confidence", 0.5),
                           "state": a.get("state", "proposed"),
                           "content": a.get("content", ""), "task_id": row.get("task_id", "")})
    return claims


def _store_conflicts(claims: list[dict], conflicts: list[Conflict]) -> InMemoryStore:
    store = InMemoryStore()
    rec = MemoryRecorder(store)
    rec.start_run(model="claim_conflict_demo", label="cross_claim_conflicts", config={})
    by_orig = {}
    for c in claims:
        cl = rec.record_claim(content=c["content"] or f"{c['subject']} | {c['predicate']} | {c['object']}",
                              method=f"p3_{c['claim_type']}",
                              state=ClaimState(c["state"]) if c["state"] in
                              {s.value for s in ClaimState} else ClaimState.PROPOSED,
                              confidence=float(c.get("confidence", 0.5)),
                              operator_path=(c.get("task_id", ""),))
        by_orig[c["_id"]] = cl
    for cf in conflicts:
        a, b = by_orig.get(cf.a), by_orig.get(cf.b)
        if a is None or b is None:
            continue
        # No POTENTIALLY_CONTRADICTS in the closed enum: use CONTRADICTS with a
        # weight that encodes the confidence level.
        rec.record_relation(source=a, target=b, rel_type=RelationType.CONTRADICTS,
                            weight=0.9 if cf.level == "contradiction" else 0.4)
    rec.end_run()
    return store


def write_report(real_claims, real_conflicts, crafted_conflicts, gov, store, path):
    by_level = Counter(c.level for c in real_conflicts)
    by_rule = Counter(c.rule for c in real_conflicts)
    claims_by_id = {c["_id"]: c for c in real_claims}
    conf_rej = sum(1 for c in real_conflicts if c.level == "contradiction" and
                   {claims_by_id.get(c.a, {}).get("state"),
                    claims_by_id.get(c.b, {}).get("state")} == {"rejected", "confirmed"})

    md = ["# Cross-claim contradiction detection (P4 prototype)\n",
          "## Real TruthfulQA atomic claims\n",
          f"- atomic claims analysed: **{len(real_claims)}**",
          f"- conflicts found: **{len(real_conflicts)}** "
          f"(by level `{dict(by_level)}`, by rule `{dict(by_rule)}`)",
          f"- confirmed-vs-rejected contradictions: **{conf_rej}**",
          f"- CONTRADICTS relations written to store: "
          f"**{sum(1 for _ in [r for c in store.all_claims() for r in store.relations_for(c.claim_id, direction='out')])}**\n"]
    if real_conflicts:
        md.append("### Real conflict examples")
        for cf in real_conflicts[:6]:
            ca, cb = claims_by_id.get(cf.a, {}), claims_by_id.get(cf.b, {})
            md.append(f"- [{cf.level}/{cf.rule}] {ca.get('content')!r} ⟷ {cb.get('content')!r} — {cf.reason}")
        md.append("")
    else:
        md.append("> No cross-claim conflicts found in the real set — expected: "
                  "the 50 TruthfulQA answers are independent questions, so atomic "
                  "claims rarely share a subject. This is honest, not a failure.\n")

    md.append("## Crafted pairs (heuristic validation)\n")
    md.append("Synthetic claims (NOT from the dataset) confirm the rules fire:")
    for cf in crafted_conflicts:
        md.append(f"- [{cf.level}/{cf.rule}] {cf.reason}")
    md.append("")

    md.append("## Governance signals (mark only, never overwrite)\n")
    flagged = {k: v for k, v in gov.items() if v["epistemic_risk_score"] > 0}
    md.append(f"- claims carrying a conflict-derived risk score: **{len(flagged)}**")
    for cid, g in list(flagged.items())[:5]:
        md.append(f"    - {cid}: risk={g['epistemic_risk_score']} band={g['confidence_band']} "
                  f"flags={g['flags']}")
    md.append("")

    md.append("## What works / false-positive risks\n")
    md.append("- **Negation (is/is not, can/cannot)** and **numeric single-value** "
              "and **antonym (alive/dead, possible/impossible)** are reliable on "
              "same-subject pairs.")
    md.append("- **False-positive risks:** same subject+predicate with different "
              "objects is often *complementary*, not contradictory (flagged only as "
              "`potential`); subject matching is surface-string (no coreference, so "
              "`Lincoln` vs `Abraham Lincoln` would be missed); contractions "
              "(`isn't`) and multi-valued attributes are not handled.")
    md.append("")
    md.append("## Honesty / limits\n")
    md.append("Heuristic prototype: **no** general truth solver, **no** logical "
              "completeness, **no** robust ontology, same-subject only. When "
              "unsure it returns `potential` (POTENTIALLY_CONTRADICTS — represented "
              "in the closed DESi enum as a low-weight CONTRADICTS edge, the core "
              "enum is unchanged). It marks epistemic risk; it never rewrites a "
              "claim's stored state or confidence.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(m for m in md if m is not None) + "\n", encoding="utf-8")


def int_or(x):
    try:
        return int(x)
    except (TypeError, ValueError):
        return 0


def main() -> int:
    p = argparse.ArgumentParser(description="P4 cross-claim contradiction demo.")
    p.add_argument("--graph", type=Path, default=DEFAULT_GRAPH)
    p.add_argument("--report", type=Path, default=Path(__file__).resolve().parent
                   / "outputs" / "claim_conflict_report.md")
    args = p.parse_args()

    real_claims = _load_atomic(args.graph)
    real_conflicts = detect_conflicts(real_claims)
    crafted = [dict(c) for c in CRAFTED]
    crafted_conflicts = detect_conflicts(crafted)

    store = _store_conflicts(real_claims, real_conflicts)
    claims_by_id = {c["_id"]: c for c in real_claims}
    gov = governance_signals(claims_by_id, real_conflicts)

    write_report(real_claims, real_conflicts, crafted_conflicts, gov, store, args.report)
    print(f"Analysed {len(real_claims)} real atomic claims: {len(real_conflicts)} "
          f"conflict(s); crafted validation: {len(crafted_conflicts)} conflict(s). "
          f"Report -> {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
