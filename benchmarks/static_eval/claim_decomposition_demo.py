#!/usr/bin/env python3
"""P2 demo: decompose TruthfulQA answers into atomic sub-claims and store them
through the same run_desi(memory_hook=...) / MemoryRecorder path as P1.

Each sub-claim becomes its own ``Claim`` (own claim_id, ClaimState, provenance)
with a ``DERIVES_FROM`` edge to the parent answer-claim, plus connective-based
edges (``because`` -> SUPPORTS, ``but``/``while`` -> REFINES). Sub-claim states
are set by the same heuristic gold match as the intervention (CONFIRMED /
REJECTED / PROPOSED). Heuristic prototype — see the generated report for limits.
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
from desi.runner import run_desi                         # noqa: E402
from desi.memory.hook import MemoryHook                  # noqa: E402
from desi_intervention import ACCEPT_STRONG, REJECT_STRONG, best_score  # noqa: E402
from freetext_claim_extractor import extract_subclaims   # noqa: E402
from trajectory_builder import build_trajectory          # noqa: E402

DEFAULT_INPUT = (Path(__file__).resolve().parent / "outputs"
                 / "truthfulqa.deepseek-v4.desi_intervened.refined.limit50.jsonl")
CANONICAL = {
    "task_id": "demo-vw",
    "question": "Where and when was Virginia Woolf born?",
    "raw_model_answer": "Virginia Woolf was born in London in 1882 and became a famous writer.",
    "model_answer": "Virginia Woolf was born in London in 1882 and became a famous writer.",
    "desi_metadata": {"model": "demo", "intervention_decision": "accept_uncertain"},
    "static_eval": {"best_answer": "", "correct_answers": [], "incorrect_answers": []},
}


def _answer_text(record: dict) -> str:
    return ((record.get("raw_model_answer") or "").strip()
            or (record.get("model_answer") or "").strip() or "(no answer)")


def _state_for(text: str, correct: list, incorrect: list) -> ClaimState:
    cs, _ = best_score(text, correct)
    isc, _ = best_score(text, incorrect)
    if cs >= ACCEPT_STRONG and cs >= isc:
        return ClaimState.CONFIRMED
    if isc >= REJECT_STRONG and isc > cs:
        return ClaimState.REJECTED
    return ClaimState.PROPOSED


def decompose_and_store(record: dict, store: InMemoryStore) -> dict:
    answer = _answer_text(record)
    se = record.get("static_eval") or {}
    correct, incorrect = se.get("correct_answers") or [], se.get("incorrect_answers") or []
    subclaims = extract_subclaims(answer)

    traj, tmeta = build_trajectory(record)
    rec = MemoryRecorder(store)
    hook = MemoryHook(rec, model=tmeta.get("model", "unknown"),
                      config={"benchmark": "truthfulqa_subclaims"})
    metrics = run_desi(traj, memory_hook=hook)  # P1 governance path

    rec.start_run(model=tmeta.get("model", "unknown"), label="truthfulqa_subclaims",
                  config={"task_id": tmeta["task_id"]})
    parent = rec.record_claim(content=answer, method="truthfulqa_answer",
                              state=ClaimState.PROPOSED, operator_path=(tmeta["task_id"],))
    subs = []
    prev = None
    for sc in subclaims:
        st = _state_for(sc.text, correct, incorrect)
        sub = rec.record_claim(content=sc.text, method=f"freetext:{sc.kind}",
                               state=st, operator_path=(tmeta["task_id"],))
        rels = [{"rel_type": "DERIVES_FROM", "target": parent.claim_id}]
        rec.record_relation(source=sub, target=parent, rel_type=RelationType.DERIVES_FROM)
        if sc.connective == "because" and prev is not None:
            rec.record_relation(source=sub, target=prev, rel_type=RelationType.SUPPORTS)
            rels.append({"rel_type": "SUPPORTS", "target": prev.claim_id})
        elif sc.connective in ("but", "while") and prev is not None:
            rec.record_relation(source=sub, target=prev, rel_type=RelationType.REFINES)
            rels.append({"rel_type": "REFINES", "target": prev.claim_id})
        subs.append({"text": sc.text, "kind": sc.kind, "connective": sc.connective,
                     "claim_id": sub.claim_id, "state": st.value, "relations": rels})
        prev = sub
    rec.end_run()
    return {"task_id": tmeta["task_id"], "answer": answer,
            "parent_claim_id": parent.claim_id, "n_subclaims": len(subs),
            "subclaims": subs, "hook_used": len(hook.errors) == 0,
            "run_desi_metrics": {"n_steps": getattr(metrics, "n_steps", None)}}


def _pick_real(input_path: Path, n: int) -> list[dict]:
    if not input_path.exists():
        return []
    out = []
    for line in input_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        if len(extract_subclaims(_answer_text(rec))) >= 2:  # multi-clause answers
            out.append(rec)
        if len(out) >= n:
            break
    return out


def write_report(results: list[dict], store: InMemoryStore, path: Path) -> None:
    total_sub = sum(r["n_subclaims"] for r in results)
    multi = sum(1 for r in results if r["n_subclaims"] >= 2)
    kinds = Counter(s["kind"] for r in results for s in r["subclaims"])
    states = Counter(s["state"] for r in results for s in r["subclaims"])

    md = ["# Free-text claim decomposition (P2 prototype)\n",
          f"- Demo answers: **{len(results)}**",
          f"- Sub-claims produced: **{total_sub}** "
          f"(answers split into >=2 sub-claims: {multi}/{len(results)})",
          f"- Total claims in store (incl. parents + run_desi trajectory): "
          f"**{len(list(store.all_claims()))}**",
          f"- Sub-claim kinds: `{dict(kinds)}` | states: `{dict(states)}`\n",
          "## Examples (answer → atomic sub-claims)\n"]
    for r in results:
        md.append(f"**`{r['task_id']}`**: {r['answer'][:120]!r}")
        for s in r["subclaims"]:
            rel = ", ".join(f"{x['rel_type']}" for x in s["relations"])
            md.append(f"  - [{s['kind']} / {s['connective'] or '-'} / {s['state']}] "
                      f"{s['text']!r}  ({rel})")
        md.append("")

    md.append("## What works (surprisingly well for ~80 lines of rules)\n")
    md.append("- `X and Y` / `X while Y` splits with **subject propagation** "
              "(verb-initial clause inherits the prior subject).")
    md.append("- The **year heuristic**: `born in <Place> in <Year>` cleanly "
              "yields a separate `<subject> birth year = <Year>` claim and a "
              "place clause without the year.")
    md.append("- Independent factual conjuncts (`A and B`) become two checkable "
              "claims that can take **different** states.\n")
    md.append("## Where the rule-based approach fails (documented, not hidden)\n")
    md.append("- **Pronoun subjects** are not resolved: `... but it cannot ...` "
              "keeps `it` instead of the entity.")
    md.append("- **`because of <noun>`** produces a fragment (`of atmospheric "
              "pressure`), not a proposition — only `because <clause>` works.")
    md.append("- **No real parsing**: nested clauses, relative clauses, lists, "
              "negation scope, coreference, and multi-sentence entities are missed "
              "or mis-split.")
    md.append("- **Subject heuristic** keys on leading capitalization, so "
              "sentence-initial common words or lowercase entities break it.\n")
    md.append("## Honesty\n")
    md.append("This is a **heuristic P2 prototype**, not a semantic parser and not "
              "an LLM extractor. It demonstrates the *shape* of atomic claims and "
              "that they flow into the existing claim/memory layer; a robust "
              "extractor (model-assisted) is future work.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(md) + "\n", encoding="utf-8")


def main() -> int:
    p = argparse.ArgumentParser(description="P2 free-text claim decomposition demo.")
    p.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    p.add_argument("--n-real", type=int, default=4)
    p.add_argument("--report", type=Path,
                   default=Path(__file__).resolve().parent / "outputs"
                   / "freetext_claim_decomposition_report.md")
    args = p.parse_args()

    demo_records = [CANONICAL] + _pick_real(args.input, args.n_real)
    store = InMemoryStore()
    results = [decompose_and_store(r, store) for r in demo_records]
    write_report(results, store, args.report)
    total_sub = sum(r["n_subclaims"] for r in results)
    print(f"Decomposed {len(results)} answers into {total_sub} sub-claims "
          f"({len(list(store.all_claims()))} total claims). Report -> {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
