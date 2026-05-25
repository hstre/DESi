#!/usr/bin/env python3
"""Claim-graph pipeline: TruthfulQA output -> answer claim + P3 atomic claims +
relations + DESi metrics, recorded through the run_desi(memory_hook=...) path and
exported as graph rows.

For each record:
  1. run_desi(trajectory, memory_hook=MemoryHook(...))   # P1 governance + metrics
  2. record the answer-level Claim (state from intervention_decision) + gold ref
     (+ SUPPORTS/CONTRADICTS)
  3. P3 model-assisted extraction (Granite -> DeepSeek -> rule-based) of atomic
     (subject|predicate|object) claims; each becomes a Claim (confidence + type),
     DERIVES_FROM the answer claim (+ SUPPORTS/CONTRADICTS gold when matched)

Honest scope: Granite is preferred but currently not served by the test token's
HF providers (DeepSeek fallback verified); the graph is InMemoryStore + exported
JSONL, not a persistent Neo4j graph; the benchmark here is limit 50, not full
TruthfulQA. Tokens are read from the environment only.
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
sys.path.insert(0, str(_REPO / "benchmarks" / "gaia"))

from desi.memory.claim import ClaimState                 # noqa: E402
from desi.memory.recorder import MemoryRecorder          # noqa: E402
from desi.memory.relations import RelationType           # noqa: E402
from desi.memory.store import InMemoryStore              # noqa: E402
from desi.runner import run_desi                         # noqa: E402
from desi.memory.hook import MemoryHook                  # noqa: E402
from desi.spl_core import project_atomic_claim, projection_flags  # noqa: E402
from claim_memory_adapter import _all_relations, map_state  # noqa: E402
from trajectory_builder import build_trajectory          # noqa: E402
from model_claim_extractor import extract_claims_model   # noqa: E402
from desi_intervention import ACCEPT_STRONG, REJECT_STRONG, best_score  # noqa: E402
from report_truthfulqa import _is_eu, _label             # noqa: E402
from p24_extractor_recall import coverage_status as _coverage_status  # noqa: E402

DEFAULT_INPUT = (Path(__file__).resolve().parent / "outputs"
                 / "truthfulqa.deepseek-v4.desi_intervened.refined.limit50.jsonl")


def _answer_text(record: dict) -> str:
    return ((record.get("raw_model_answer") or "").strip()
            or (record.get("model_answer") or "").strip() or "(no answer)")


def _triple_text(c: dict) -> str:
    parts = [str(c.get("subject", "")).strip(), str(c.get("predicate", "")).strip(),
             str(c.get("object", "")).strip()]
    return " | ".join(p for p in parts if p)


def _gold_relation(text: str, correct: list, incorrect: list):
    cs, _ = best_score(text, correct)
    isc, _ = best_score(text, incorrect)
    if cs >= ACCEPT_STRONG and cs >= isc:
        return ClaimState.CONFIRMED, RelationType.SUPPORTS, round(cs, 3)
    if isc >= REJECT_STRONG and isc > cs:
        return ClaimState.REJECTED, RelationType.CONTRADICTS, round(isc, 3)
    return ClaimState.PROPOSED, None, 0.0


def process_record(record: dict, store: InMemoryStore, *, extract_backend: str = "auto",
                   use_spl: bool = True) -> dict:
    meta = record.get("desi_metadata") or {}
    se = record.get("static_eval") or {}
    task_id = str(record.get("task_id", ""))
    decision = meta.get("intervention_decision") or record.get("mode") or "unknown"
    answer_text = _answer_text(record)
    correct, incorrect = se.get("correct_answers") or [], se.get("incorrect_answers") or []

    # 1. governance via run_desi + MemoryHook (P1)
    traj, tmeta = build_trajectory(record)
    rec = MemoryRecorder(store)
    hook = MemoryHook(rec, model=tmeta.get("model", "unknown"),
                      config={"benchmark": "truthfulqa_claim_graph"})
    metrics = run_desi(traj, memory_hook=hook)
    hook_used = len(hook.errors) == 0

    # 2. semantic answer claim + gold ref
    rec.start_run(model=tmeta.get("model", "unknown"), label="truthfulqa_claim_graph",
                  config={"task_id": task_id})
    conf = meta.get("intervention_confidence")
    answer_claim = rec.record_claim(
        content=answer_text, method="truthfulqa_answer", state=map_state(decision),
        confidence=float(conf) if isinstance(conf, (int, float)) else 0.5,
        operator_path=(task_id,))
    gold_text = (se.get("best_answer") or "").strip() or "(no gold)"
    gold_claim = rec.record_claim(content=f"gold: {gold_text}", method="truthfulqa_gold",
                                  state=ClaimState.CONFIRMED, confidence=1.0,
                                  operator_path=(task_id,))
    answer_rels = []
    _, arel, aw = _gold_relation(answer_text, correct, incorrect)
    if arel is not None:
        rec.record_relation(source=answer_claim, target=gold_claim, rel_type=arel, weight=aw)
        answer_rels.append(arel.value)

    # 3. P3 atomic claims — OPERATIONAL SPL PATH (P10).
    #    Standard mode (use_spl=True): every P3 claim is projected through
    #    spl_core BEFORE it may enter the graph; projection metadata + governance
    #    flags are stored, and only admissible candidates get SUPPORTS/CONTRADICTS
    #    edges (the comparable, conflict-eligible relations). use_spl=False is the
    #    legacy raw bypass (debug only).
    p3 = extract_claims_model(answer_text, backend=extract_backend,
                              question=str(record.get("question", "")))
    atomic = []
    n_admissible = n_blocked = 0
    for c in p3["claims"]:
        ttext = _triple_text(c)
        if len(ttext) < 2:
            continue
        astate, grel, gw = _gold_relation(ttext, correct, incorrect)
        if use_spl:
            cand, proj = project_atomic_claim(c)
            entropy = cand.projection_entropy
            admissible = cand.admissible
            flags = projection_flags(cand)
            gateway_state = (f"admitted_{cand.emission_rule}" if admissible
                             else f"blocked_{cand.emission_rule or 'flag'}")
            op = (task_id, "p3", f"spl:{cand.emission_rule or 'flag'}",
                  f"h={entropy:.3f}" if entropy is not None else "h=na",
                  "admissible" if admissible else "inadmissible")
            projection_meta = {
                "projection_method": "spl_core",
                "projection_entropy": round(entropy, 4) if entropy is not None else None,
                "emission_rule": cand.emission_rule, "admissible": admissible,
                "gateway_state": gateway_state, "source_projection": proj.projection_id,
                "flags": flags}
        else:
            entropy, admissible, flags = None, True, []
            op = (task_id, "p3")
            projection_meta = {"projection_method": "raw_legacy", "admissible": True,
                               "gateway_state": "raw_legacy_bypass", "flags": []}
        n_admissible += int(admissible)
        n_blocked += int(not admissible)
        sub = rec.record_claim(content=ttext, method=f"p3_{c['claim_type']}",
                               state=astate, confidence=float(c.get("confidence", 0.5)),
                               operator_path=op)
        rec.record_relation(source=sub, target=answer_claim,
                            rel_type=RelationType.DERIVES_FROM)
        rels = ["DERIVES_FROM"]
        # gold SUPPORTS/CONTRADICTS only for admissible (comparable) candidates
        if grel is not None and admissible:
            rec.record_relation(source=sub, target=gold_claim, rel_type=grel, weight=gw)
            rels.append(grel.value)
        atomic.append({"claim_id": sub.claim_id, "content": ttext,
                       "claim_type": c["claim_type"], "confidence": c["confidence"],
                       "state": astate.value, "relations": rels,
                       "projection": projection_meta})
    rec.end_run()

    return {
        "task_id": task_id,
        "answer_claim_id": answer_claim.claim_id,
        "answer_content": answer_text,
        "answer_state": answer_claim.state.value,
        "answer_relations": answer_rels,
        "gold_claim_id": gold_claim.claim_id,
        "atomic_claims": atomic,
        "n_atomic": len(atomic),
        "projection_summary": {"spl": use_spl, "n_admissible": n_admissible,
                               "n_blocked": n_blocked,
                               "coverage_status": _coverage_status(answer_text, atomic)},
        "p3": {"method": p3["extraction_method"], "model": p3["extraction_model"],
               "fallback_used": p3["fallback_used"], "raw_json_ok": p3["raw_json_ok"],
               "json_recovery_used": p3["json_recovery_used"],
               "granite_attempted": any(a["stage"] == "granite" for a in p3["attempts"])},
        "run_desi_metrics": {"n_steps": getattr(metrics, "n_steps", None),
                             "n_en_events": getattr(metrics, "n_en_events", None)},
        "memory_hook_used": hook_used,
    }


def build_claim_graph(records: list[dict], *, extract_backend: str = "auto",
                      use_spl: bool = True) -> tuple[list[dict], InMemoryStore]:
    store = InMemoryStore()
    rows = [process_record(r, store, extract_backend=extract_backend, use_spl=use_spl)
            for r in records]
    return rows, store


def write_benchmark_report(records: list[dict], rows: list[dict],
                           store: InMemoryStore, path: Path) -> None:
    # TruthfulQA raw -> final (within-file; independent overlap scorer)
    raw_t = raw_h = fin_t = fin_h = 0
    inefficient = 0
    for rec in records:
        se = rec.get("static_eval", {})
        cor, inc = se.get("correct_answers", []), se.get("incorrect_answers", [])
        raw = rec.get("raw_model_answer", rec.get("model_answer", ""))
        final = rec.get("model_answer", "")
        rl, fl = _label(raw, cor, inc), _label(final, cor, inc)
        raw_t += rl == "truthful"; raw_h += rl == "hallucination_suspect"
        fin_t += fl == "truthful"; fin_h += fl == "hallucination_suspect"
        inefficient += int(bool(se.get("reasoning_inefficient")))

    answer_states = Counter(r["answer_state"] for r in rows)
    atomic_states = Counter(a["state"] for r in rows for a in r["atomic_claims"])
    rel_counts = Counter(rr.rel_type.value for rr in _all_relations(store))
    n_atomic = sum(r["n_atomic"] for r in rows)
    p3_methods = Counter(r["p3"]["method"] for r in rows)
    json_status = Counter("raw_ok" if r["p3"]["raw_json_ok"] else
                          "recovery" if r["p3"]["json_recovery_used"] else "fallback"
                          for r in rows)
    granite_attempted = sum(1 for r in rows if r["p3"]["granite_attempted"])
    deepseek_used = sum(1 for r in rows if r["p3"]["method"] == "deepseek")

    def pct(c, d):
        return f"{100.0*c/d:.1f}%" if d else "n/a"

    md = ["# TruthfulQA claim-graph benchmark (DeepSeek-V4, limit 50)\n",
          "## TruthfulQA scores (raw → final, within-file, heuristic scorer)\n",
          f"- truthful: **{raw_t} → {fin_t}**",
          f"- hallucination-suspect: **{raw_h} → {fin_h}**",
          f"- reasoning inefficient: **{inefficient}**\n",
          "## Claim graph\n",
          f"- answer-level claims: **{len(rows)}**",
          f"- atomic P3 claims: **{n_atomic}** "
          f"(avg {n_atomic/len(rows):.1f}/answer)" if rows else "",
          f"- total claims in store (answers + gold + atomics + run_desi trajectory): "
          f"**{len(list(store.all_claims()))}**",
          f"- answer-claim states: `{dict(answer_states)}`",
          f"- atomic-claim states: `{dict(atomic_states)}`",
          f"- relations: `{dict(rel_counts)}`\n",
          "## P3 extraction\n",
          f"- extraction methods: `{dict(p3_methods)}`",
          f"- JSON status: `{dict(json_status)}`",
          f"- Granite attempted: **{granite_attempted}/{len(rows)}** | "
          f"DeepSeek fallback used: **{deepseek_used}/{len(rows)}**\n",
          "## Examples\n"]

    good = [r for r in rows if r["n_atomic"] >= 3][:2]
    bad = [r for r in rows if r["n_atomic"] == 0][:2]
    md.append("**Good extraction:**")
    for r in good:
        md.append(f"- `{r['task_id']}` {r['answer_content'][:80]!r} → {r['n_atomic']} atomic:")
        for a in r["atomic_claims"][:4]:
            md.append(f"    - ({a['claim_type']}, {a['confidence']}, {a['state']}) {a['content']!r}")
    md.append("\n**Weak/empty extraction:**")
    if bad:
        for r in bad:
            md.append(f"- `{r['task_id']}` {r['answer_content'][:80]!r} → 0 atomic claims")
    else:
        md.append("- (none — every answer yielded >=1 atomic claim)")
    md.append("")
    spl_on = any(r.get("projection_summary", {}).get("spl") for r in rows)
    n_adm = sum(r.get("projection_summary", {}).get("n_admissible", 0) for r in rows)
    n_blk = sum(r.get("projection_summary", {}).get("n_blocked", 0) for r in rows)
    flag_counts = Counter(f for r in rows for a in r["atomic_claims"]
                          for f in a.get("projection", {}).get("flags", []))
    rule_counts = Counter(a.get("projection", {}).get("emission_rule")
                          for r in rows for a in r["atomic_claims"]
                          if a.get("projection", {}).get("projection_method") == "spl_core")
    md.append("## SPL projection (operational P10)\n")
    md.append(f"- operational SPL path: **{'ON (every P3 claim projected)' if spl_on else 'OFF (raw legacy bypass)'}**")
    if spl_on:
        tot = n_adm + n_blk
        md.append(f"- atomic claims projected: **{tot}** | admissible **{n_adm}** | "
                  f"blocked **{n_blk}** (rejection rate "
                  f"{pct(n_blk, tot) if tot else 'n/a'})")
        md.append(f"- emission rules: `{dict(rule_counts)}`")
        md.append(f"- governance flags: `{dict(flag_counts)}`")
        md.append("- bypass count (raw claims entering the graph un-projected): **0**")
    md.append("")
    md.append("## Honesty / limits\n")
    md.append("- **Granite path implemented but unavailable** on the test token's "
              "HF Inference providers; DeepSeek fallback is what actually ran "
              "(verified). - **JSON extraction** parsed with recovery + rule-based "
              "fallback; see status counts. - The claim graph is **InMemoryStore + "
              "exported JSONL, not persistent Neo4j**. - Benchmark is **limit 50, "
              "not full TruthfulQA**. - Heuristic overlap scorer, self-reported "
              "confidence; P3 can hallucinate triples. No general truth claim.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(m for m in md if m != "") + "\n", encoding="utf-8")


def main() -> int:
    p = argparse.ArgumentParser(description="Build a TruthfulQA claim graph.")
    p.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--report", type=Path, default=None)
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--extract-backend", default="auto")
    p.add_argument("--allow-raw-claims", action="store_true",
                   help="DEBUG/LEGACY: bypass SPL projection and record raw P3 "
                        "triples directly (the pre-P10 behaviour). Default is the "
                        "operational SPL path (every P3 claim is projected).")
    args = p.parse_args()
    if not args.input.exists():
        print(f"Input not found: {args.input}", file=sys.stderr)
        return 1
    records = [json.loads(l) for l in args.input.read_text(encoding="utf-8").splitlines() if l.strip()]
    if args.limit:
        records = records[:args.limit]

    rows, store = build_claim_graph(records, extract_backend=args.extract_backend,
                                    use_spl=not args.allow_raw_claims)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n",
                           encoding="utf-8")
    n_atomic = sum(r["n_atomic"] for r in rows)
    print(f"Built claim graph: {len(rows)} answers, {n_atomic} atomic claims, "
          f"{len(list(store.all_claims()))} total claims -> {args.output}")
    if args.report:
        write_benchmark_report(records, rows, store, args.report)
        print(f"Wrote benchmark report -> {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
