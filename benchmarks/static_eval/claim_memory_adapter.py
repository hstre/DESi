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
    args = p.parse_args()
    if not args.input.exists():
        print(f"Input not found: {args.input}", file=sys.stderr)
        return 1

    records = _load_records(args.input, args.limit)
    store, exports = build_from_records(records, model=args.model,
                                        config={"input": args.input.name,
                                                "limit": args.limit or len(records)})
    args.output.parent.mkdir(parents=True, exist_ok=True)
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
