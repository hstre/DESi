#!/usr/bin/env python3
"""P0 adapter: turn a TruthfulQA run record into a real DESi memory Claim.

Reuses the existing claim/memory layer in ``src/desi/memory`` (no new claim
model): each benchmark answer becomes a ``Claim`` recorded through
``MemoryRecorder`` into an ``InMemoryStore``, with the intervention decision
mapped to a ``ClaimState`` and a relation to the task's gold truth. This is the
first step of the reintegration plan (P0) — it does not yet build a persistent
graph; it produces a deterministic in-memory claim set + export.

Decision → ClaimState:
  accept_supported                       -> CONFIRMED
  accept_uncertain / accept_low_confidence-> PROPOSED
  reject_known_false / reject_contradictory-> REJECTED
  reject_low_confidence / reject_unsupported_certainty / downgrade_low_evidence -> PROPOSED
  abstain / abstain_truncated / abstain_inefficient -> PROPOSED (no WITHHELD state exists)

Relations (answer-claim → per-task gold-truth claim):
  matches a correct answer   -> SUPPORTS
  matches an incorrect answer -> CONTRADICTS  (no REFUTES type exists)
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "src"))            # for desi.*
sys.path.insert(0, str(Path(__file__).resolve().parent))  # for desi_intervention

from desi.core.replay_kernel import replay_hash          # noqa: E402
from desi.memory.claim import ClaimState                 # noqa: E402
from desi.memory.recorder import MemoryRecorder          # noqa: E402
from desi.memory.relations import RelationType           # noqa: E402
from desi.memory.store import InMemoryStore              # noqa: E402
from desi_intervention import ACCEPT_STRONG, REJECT_STRONG, best_score  # noqa: E402

_STATE_MAP = {
    "accept_supported": ClaimState.CONFIRMED,
    "accept_uncertain": ClaimState.PROPOSED,
    "accept_low_confidence": ClaimState.PROPOSED,
    "reject_known_false": ClaimState.REJECTED,
    "reject_contradictory": ClaimState.REJECTED,
    "reject_low_confidence": ClaimState.PROPOSED,
    "reject_unsupported_certainty": ClaimState.PROPOSED,
    "downgrade_low_evidence": ClaimState.PROPOSED,
    "abstain": ClaimState.PROPOSED,
    "abstain_truncated": ClaimState.PROPOSED,
    "abstain_inefficient": ClaimState.PROPOSED,
}


def map_state(decision: str) -> ClaimState:
    return _STATE_MAP.get(decision, ClaimState.PROPOSED)


def _answer_content(record: dict) -> str:
    raw = (record.get("raw_model_answer") or "").strip()
    ans = (record.get("model_answer") or "").strip()
    return raw or ans or "(no answer)"


def record_claim_for(recorder: MemoryRecorder, record: dict) -> dict:
    """Record one answer-claim (+ gold relation) into the active run; return export dict."""
    meta = record.get("desi_metadata") or {}
    se = record.get("static_eval") or {}
    task_id = str(record.get("task_id", ""))
    decision = meta.get("intervention_decision") or record.get("mode") or "unknown"
    content = _answer_content(record)
    conf = meta.get("intervention_confidence")
    conf = float(conf) if isinstance(conf, (int, float)) else 0.5
    model = meta.get("model") or meta.get("resolved_model") or "unknown"

    claim = recorder.record_claim(
        content=content, method=f"truthfulqa:{model}", state=map_state(decision),
        confidence=conf, operator_path=(task_id,),
    )

    # Per-task gold-truth reference claim (the established correct answer).
    gold_text = (se.get("best_answer") or "").strip() or "(no gold)"
    gold = recorder.record_claim(
        content=f"gold: {gold_text}", method="truthfulqa_gold",
        state=ClaimState.CONFIRMED, confidence=1.0, operator_path=(task_id,),
    )

    correct = se.get("correct_answers") or []
    incorrect = se.get("incorrect_answers") or []
    cs, _ = best_score(content, correct)
    isc, _ = best_score(content, incorrect)
    relations: list[dict] = []
    if cs >= ACCEPT_STRONG and cs >= isc:
        recorder.record_relation(source=claim, target=gold,
                                 rel_type=RelationType.SUPPORTS, weight=round(cs, 3))
        relations.append({"rel_type": "SUPPORTS", "target_claim_id": gold.claim_id,
                          "weight": round(cs, 3)})
    elif isc >= REJECT_STRONG and isc > cs:
        recorder.record_relation(source=claim, target=gold,
                                 rel_type=RelationType.CONTRADICTS, weight=round(isc, 3))
        relations.append({"rel_type": "CONTRADICTS", "target_claim_id": gold.claim_id,
                          "weight": round(isc, 3)})

    return {
        "task_id": task_id,
        "claim_id": claim.claim_id,
        "claim_state": claim.state.value,
        "claim_content": content,
        "provenance": {
            "source": claim.provenance.source,
            "run_id": claim.provenance.run_id,
            "operator_path": list(claim.provenance.operator_path),
        },
        "relations": relations,
        "intervention_decision": decision,
        "replay_hash": replay_hash({
            "task_id": task_id, "content": content,
            "state": claim.state.value, "decision": decision,
        }),
    }


def build_from_records(records: list[dict], *, model: str = "unknown",
                       label: str = "truthfulqa",
                       config: dict | None = None) -> tuple[InMemoryStore, list[dict]]:
    store = InMemoryStore()
    recorder = MemoryRecorder(store)
    recorder.start_run(model=model, label=label, config=config or {})
    exports = [record_claim_for(recorder, r) for r in records]
    recorder.end_run()
    return store, exports


def _all_relations(store: InMemoryStore) -> list:
    """Collect every relation once (by its source claim)."""
    out = []
    for c in store.all_claims():
        out.extend(store.relations_for(c.claim_id, direction="out"))
    return out


# --------------------------------------------------------------------------- #
# P1: record via the run_desi(..., memory_hook=...) governance path
# --------------------------------------------------------------------------- #
def record_claims_via_memory_hook(record: dict, store: InMemoryStore) -> dict:
    """P1 path: build a Trajectory, run run_desi with a MemoryHook (which writes
    the trajectory's focus claims), then record the benchmark answer/gold
    semantics through the same recorder. Returns an export dict with hook info.

    NOTE: run_desi+MemoryHook writes only *trajectory-derived* claims
    (content = focus_claim_id, state PROPOSED, DERIVES_FROM edges). It does NOT
    write the answer/gold semantics — those are recorded by the adapter below.
    This split is reported explicitly; the hook is genuinely used (not faked).
    """
    from trajectory_builder import build_trajectory
    from desi.runner import run_desi
    from desi.memory.hook import MemoryHook

    traj, tmeta = build_trajectory(record)
    recorder = MemoryRecorder(store)

    before = {c.claim_id for c in store.all_claims()}
    hook = MemoryHook(recorder, model=tmeta.get("model", "unknown"),
                      config={"benchmark": "truthfulqa", "task_id": tmeta["task_id"]})
    metrics = run_desi(traj, memory_hook=hook)  # hook writes trajectory claims
    hook_ids = sorted({c.claim_id for c in store.all_claims()} - before)
    hook_used = len(hook.errors) == 0 and len(hook_ids) > 0

    # Benchmark answer/gold semantics via the SAME recorder, in a fresh run.
    recorder.start_run(model=tmeta.get("model", "unknown"),
                       label="truthfulqa_semantic",
                       config={"benchmark": "truthfulqa", "task_id": tmeta["task_id"]})
    export = record_claim_for(recorder, record)
    recorder.end_run()

    export["memory_hook_used"] = hook_used
    export["hook_errors"] = len(hook.errors)
    export["hook_claim_ids"] = hook_ids
    export["run_desi_metrics"] = {
        "n_steps": getattr(metrics, "n_steps", None),
        "n_en_events": getattr(metrics, "n_en_events", None),
    }
    export["claims_source"] = (
        f"run_desi+MemoryHook wrote {len(hook_ids)} trajectory claim(s) "
        "(PROPOSED, content=focus_id, DERIVES_FROM); adapter wrote the semantic "
        "answer+gold claims (state + SUPPORTS/CONTRADICTS)"
    )
    export["trajectory_meta"] = tmeta
    return export


def build_from_records_via_hook(records: list[dict], *, model: str = "unknown"
                                ) -> tuple[InMemoryStore, list[dict]]:
    store = InMemoryStore()
    exports = [record_claims_via_memory_hook(r, store) for r in records]
    return store, exports


def write_hook_report(p0_store: InMemoryStore, p0_exports: list[dict],
                      p1_store: InMemoryStore, p1_exports: list[dict],
                      path: Path) -> None:
    def states(exports):
        return dict(Counter(e["claim_state"] for e in exports))

    def rels(store):
        return dict(Counter(r.rel_type.value for r in _all_relations(store)))

    p1_hook_used = sum(1 for e in p1_exports if e.get("memory_hook_used"))
    p1_hook_claims = sum(len(e.get("hook_claim_ids", [])) for e in p1_exports)
    p1_steps = sum((e.get("run_desi_metrics") or {}).get("n_steps") or 0 for e in p1_exports)

    md = ["# Claim memory: P0 (direct recorder) vs P1 (run_desi memory_hook)\n",
          f"- Records: **{len(p0_exports)}** (P0) / **{len(p1_exports)}** (P1)\n",
          "| metric | P0 direct | P1 via memory_hook |",
          "| --- | --- | --- |",
          f"| total claims in store | {len(list(p0_store.all_claims()))} | {len(list(p1_store.all_claims()))} |",
          f"| answer-claim states | `{states(p0_exports)}` | `{states(p1_exports)}` |",
          f"| relations in store | `{rels(p0_store)}` | `{rels(p1_store)}` |",
          f"| MemoryHook used | n/a (direct recorder) | {p1_hook_used}/{len(p1_exports)} tasks |",
          f"| claims written by run_desi hook | 0 (run_desi not used for claims) | {p1_hook_claims} (trajectory focus claims) |",
          f"| run_desi steps governed | 0 | {p1_steps} |",
          ""]
    md.append("## How claims were written\n")
    md.append("- **P0:** answer + gold claims written **directly** via "
              "`MemoryRecorder` in one run; `run_desi` not involved.")
    md.append("- **P1:** `run_desi(trajectory, memory_hook=MemoryHook(...))` is "
              "genuinely called per task. The hook writes the **trajectory's "
              "focus claims** (state PROPOSED, content = focus id) + a "
              "`DERIVES_FROM` edge, and `run_desi` returns DeterministicMetrics. "
              "The **answer/gold semantics** (CONFIRMED/REJECTED + "
              "SUPPORTS/CONTRADICTS) are then recorded by the adapter through the "
              "same recorder — because the stock MemoryHook does not map a "
              "benchmark decision to a ClaimState (it only mirrors trajectory "
              "focus). This is stated explicitly, not hidden.")
    md.append("")
    md.append("## Equivalence of the semantic layer\n")
    same_states = states(p0_exports) == states(p1_exports)
    md.append(f"- Answer-claim states identical P0 vs P1: **{same_states}** "
              "(the semantic recording is the same code path; P1 only adds the "
              "run_desi/hook trajectory layer on top).")
    md.append("")
    md.append("> P1 is closer to the DESi core: claims now enter through the "
              "`run_desi` governance lifecycle (Run + OperatorEvents + replay-safe "
              "hook), not only a side-channel recorder call. The remaining gap is "
              "that the hook does not yet carry benchmark answer→ClaimState "
              "semantics; bridging that inside a custom hook is the next step.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(md) + "\n", encoding="utf-8")


def write_report(store: InMemoryStore, exports: list[dict], path: Path) -> None:
    claims = list(store.all_claims())
    answer_states = Counter(e["claim_state"] for e in exports)
    rel_counts = Counter(r["rel_type"] for e in exports for r in e["relations"])
    decisions = Counter(e["intervention_decision"] for e in exports)

    def example(state: str) -> str:
        for e in exports:
            if e["claim_state"] == state:
                return f"`{e['task_id']}` ({e['claim_id']}) — {e['claim_content'][:60]!r}"
        return "(none)"

    md = [f"# TruthfulQA claim-memory export (P0)\n",
          f"- Benchmark answers recorded as claims: **{len(exports)}**",
          f"- Total claims in store (answers + gold refs): **{len(claims)}**\n",
          "## Answer-claim states\n", "| state | count |", "| --- | --- |"]
    md += [f"| {s} | {c} |" for s, c in sorted(answer_states.items())]
    md.append("\n## Relations (answer → gold truth)\n")
    md.append(f"- SUPPORTS: **{rel_counts.get('SUPPORTS', 0)}**")
    md.append(f"- CONTRADICTS: **{rel_counts.get('CONTRADICTS', 0)}**")
    md.append(f"- (no REFUTES relation type exists in src/desi/memory; CONTRADICTS is used)\n")
    md.append(f"## Intervention decisions\n\n`{dict(decisions)}`\n")
    md.append("## Examples\n")
    md.append(f"- **CONFIRMED** (truthful, supported): {example('confirmed')}")
    md.append(f"- **PROPOSED** (uncertain/abstained): {example('proposed')}")
    md.append(f"- **REJECTED** (known-false): {example('rejected')}")
    md.append("")
    md.append("> This is the first MemoryStore export, **not** a persistent claim "
              "graph. Claims live in an in-process `InMemoryStore`; relations are "
              "recorded but not yet exported to the v24 epistemic graph / Neo4j. "
              "Provenance source is the recorder default `desi`; the TruthfulQA "
              "task_id is carried in `provenance.operator_path`.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(md) + "\n", encoding="utf-8")


def _load_records(path: Path, limit: int | None) -> list[dict]:
    recs = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    return recs[:limit] if limit else recs


def main() -> int:
    p = argparse.ArgumentParser(description="Record TruthfulQA answers as DESi claims (P0).")
    p.add_argument("--input", type=Path, required=True, help="An existing run JSONL.")
    p.add_argument("--output", type=Path, required=True, help="Claim-memory export JSONL.")
    p.add_argument("--report", type=Path, default=None, help="Markdown report path.")
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--model", default="deepseek/deepseek-v4-pro")
    p.add_argument("--via-hook", action="store_true",
                   help="Use the P1 run_desi(memory_hook=...) path and write a "
                        "P0-vs-P1 comparison report.")
    args = p.parse_args()
    if not args.input.exists():
        print(f"Input not found: {args.input}", file=sys.stderr)
        return 1

    records = _load_records(args.input, args.limit)
    args.output.parent.mkdir(parents=True, exist_ok=True)

    if args.via_hook:
        p1_store, p1_exports = build_from_records_via_hook(records, model=args.model)
        args.output.write_text(
            "\n".join(json.dumps(e, ensure_ascii=False) for e in p1_exports) + "\n",
            encoding="utf-8")
        used = sum(1 for e in p1_exports if e.get("memory_hook_used"))
        print(f"P1: recorded {len(p1_exports)} answer-claims via run_desi+hook "
              f"({len(list(p1_store.all_claims()))} total claims; "
              f"hook used on {used}/{len(p1_exports)}) -> {args.output}")
        if args.report:
            p0_store, p0_exports = build_from_records(records, model=args.model)
            write_hook_report(p0_store, p0_exports, p1_store, p1_exports, args.report)
            print(f"Wrote P0-vs-P1 report -> {args.report}")
        return 0

    store, exports = build_from_records(records, model=args.model,
                                        config={"input": args.input.name,
                                                "limit": args.limit or len(records)})
    args.output.write_text("\n".join(json.dumps(e, ensure_ascii=False) for e in exports) + "\n",
                           encoding="utf-8")
    print(f"Recorded {len(exports)} answer-claims "
          f"({len(list(store.all_claims()))} total claims) -> {args.output}")
    if args.report:
        write_report(store, exports, args.report)
        print(f"Wrote report -> {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
