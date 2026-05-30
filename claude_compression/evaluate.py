"""Evaluation A (raw chat) vs B (DESi state) — deterministic, fixture-based.

For each fixture we measure, per the brief:
  * Originaltoken, State-Token, Kompressionsrate
  * Erinnerungsqualität / Rekonstruktion von Architekturentscheidungen / Verlust wichtiger
    Informationen: each measured as recall of the FIXTURE'S OWN pre-registered ground-truth
    markers against the extracted state (NOT against the extractor's own output).
  * Konsistenz: round-trip of the rehydrated block back to a DesiState equals the original.

EXPLICIT honesty: the brief's third success criterion — "Claude in the new chat remains
workable" — requires a second Claude session. I cannot do that here. It is reported as
`UNTESTED_in_this_env`, not silently inflated.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

from extractor import extract_state  # noqa: E402
from fixtures import ALL_FIXTURES  # noqa: E402
from rehydrate import parse, rehydrate  # noqa: E402
from state import MAX_STATE_TOKENS, token_count  # noqa: E402

_REPORTS = _HERE / "reports"
_RESULTS = _HERE / "results"

# success thresholds (per the brief)
SUCCESS_COMPRESSION = 0.90    # >90% token saving
RECALL_DECISIONS_MIN = 0.80   # "essential architecture decisions preserved"


def _toks(words: str) -> set:
    return {w for w in re.findall(r"[a-z0-9][a-z0-9\-]+", (words or "").lower()) if len(w) > 2}


def _recall(ground_items, extracted_items, jaccard_thresh: float = 0.30) -> dict:
    """Recall = fraction of ground-truth items lexically covered by any extracted item.
    A ground-truth item is COVERED if its content tokens have Jaccard >= thresh with any
    extracted item. Deterministic and conservative."""
    if not ground_items:
        return {"covered": 0, "total": 0, "recall": 1.0, "missing": []}
    covered, missing = 0, []
    for g in ground_items:
        gt = _toks(g)
        if not gt:
            continue
        best = 0.0
        for e in extracted_items:
            et = _toks(e)
            if not et:
                continue
            j = len(gt & et) / len(gt | et)
            if j > best:
                best = j
        if best >= jaccard_thresh:
            covered += 1
        else:
            missing.append(g)
    total = len([g for g in ground_items if _toks(g)])
    return {"covered": covered, "total": total,
            "recall": round(covered / total, 3) if total else 1.0,
            "missing": missing}


def evaluate_fixture(fx) -> dict:
    chat = fx["chat"]
    raw_text = "\n".join(m["content"] for m in chat)
    raw_tokens = token_count(raw_text)
    state = extract_state(chat)
    rh = rehydrate(state)
    state_tokens = state.token_size()
    rehydrate_tokens = rh["token_size"]
    compression = round(1.0 - state_tokens / raw_tokens, 4) if raw_tokens else 0.0

    # per-field recall vs the fixture's PRE-REGISTERED ground truth
    gt = fx["ground_truth"]
    per_field = {f: _recall(gt[f], getattr(state, f)) for f in gt}
    decision_recall = per_field["architecture_decisions"]["recall"]
    overall_recall = round(
        sum(p["covered"] for p in per_field.values())
        / max(1, sum(p["total"] for p in per_field.values())), 3)

    # consistency: rehydrated block -> parsed state == original (set-equality per field)
    round_trip = parse(rh["state_block"])
    consistency = all(set(getattr(round_trip, f)) == set(getattr(state, f)) for f in gt)

    # missing-info inventory (what the state lost, by field)
    missing = {f: per_field[f]["missing"] for f in gt if per_field[f]["missing"]}

    # success per the brief (workability deliberately unmeasured here)
    success = {
        "compression_gt_90pct": compression > SUCCESS_COMPRESSION,
        "architecture_decisions_preserved": decision_recall >= RECALL_DECISIONS_MIN,
        "claude_workable_in_new_chat": "UNTESTED_in_this_env",
    }
    fits_budget = state.fits_budget()
    return {
        "fixture": fx["id"],
        "raw_tokens": raw_tokens,
        "state_tokens": state_tokens,
        "rehydrate_tokens": rehydrate_tokens,
        "compression": compression,
        "budget_max": MAX_STATE_TOKENS,
        "fits_500_budget": fits_budget,
        "recall_overall": overall_recall,
        "recall_architecture_decisions": decision_recall,
        "per_field_recall": per_field,
        "missing_info": missing,
        "consistency_roundtrip": consistency,
        "success": success,
        "rehydrated_block_excerpt": rh["state_block"][:240],
    }


def run() -> dict:
    _REPORTS.mkdir(parents=True, exist_ok=True)
    _RESULTS.mkdir(parents=True, exist_ok=True)
    rows = [evaluate_fixture(fx) for fx in ALL_FIXTURES]
    with open(_RESULTS / "evaluation.jsonl", "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    _report(rows)
    n = len(rows)
    avg_comp = sum(r["compression"] for r in rows) / n
    avg_dec = sum(r["recall_architecture_decisions"] for r in rows) / n
    avg_overall = sum(r["recall_overall"] for r in rows) / n
    print(f"compression-prototype: N={n} avg_compression={round(avg_comp,3)} "
          f"avg_decision_recall={round(avg_dec,3)} avg_overall_recall={round(avg_overall,3)} "
          f"budget_OK={sum(1 for r in rows if r['fits_500_budget'])}/{n}")
    return {"n": n, "rows": rows}


def _report(rows):
    n = len(rows)
    long_rows = [r for r in rows if r["raw_tokens"] >= 700]
    short_rows = [r for r in rows if r["raw_tokens"] < 700]
    workable = "**UNTESTED in this environment** — requires a second Claude session"
    all_consistent = all(r["consistency_roundtrip"] for r in rows)

    def avg(rs, k):
        return round(sum(r[k] for r in rs) / len(rs), 3) if rs else None

    md = [
        "# DESi Compression Layer for Claude — evaluation report\n",
        "Prototype scope (per the brief): state extraction, context compression, rehydration. "
        "**Out of scope:** Concept Gates, Governance Core, mutation layer, evolution memory, "
        "agent systems, self-improvement. Deterministic, offline, no LLM call.\n",
        "## Honest headline (read before the numbers)\n",
        "- On these fixtures, the prototype **does NOT reproduce the paper's ~9900→269 regime**. "
        "Short research dialogs (≤400 tokens) yield negative compression — the structured state "
        "is larger than the raw chat. A longer concatenated session (~800 tokens) gives +31% "
        "compression but overshoots the 500-token budget and drops decision recall. The paper's "
        "headline number was measured on transcripts an order of magnitude longer than my "
        "fixtures here.",
        "- Reported here for the brief: the trend across input lengths, the per-field "
        "preservation, and the honest losses — not a single number.",
        "",
        f"## Aggregate split by input length (N={n})\n",
        "| regime | n | mean raw | mean state | mean compression | mean decision recall | all fit 500 |",
        "| --- | --- | --- | --- | --- | --- | --- |",
        f"| short (<700 raw tokens) | {len(short_rows)} | {avg(short_rows,'raw_tokens')} | "
        f"{avg(short_rows,'state_tokens')} | {avg(short_rows,'compression')} | "
        f"{avg(short_rows,'recall_architecture_decisions')} | "
        f"{all(r['fits_500_budget'] for r in short_rows) if short_rows else '—'} |",
        f"| long (≥700 raw tokens) | {len(long_rows)} | {avg(long_rows,'raw_tokens')} | "
        f"{avg(long_rows,'state_tokens')} | {avg(long_rows,'compression')} | "
        f"{avg(long_rows,'recall_architecture_decisions')} | "
        f"{all(r['fits_500_budget'] for r in long_rows) if long_rows else '—'} |",
        f"- rehydration round-trip consistent across ALL fixtures: **{all_consistent}**",
        "",
        "## Per-fixture results\n",
        "| fixture | raw_tok | state_tok | compression | recall (decisions / overall) | fits 500 | consistent |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for r in rows:
        md.append(f"| `{r['fixture']}` | {r['raw_tokens']} | {r['state_tokens']} | "
                  f"{r['compression']} | {r['recall_architecture_decisions']} / "
                  f"{r['recall_overall']} | {r['fits_500_budget']} | {r['consistency_roundtrip']} |")
    md += [
        "",
        "## Per-field recall (vs fixture ground truth)\n",
        "| fixture | goals | problems | findings | discarded | decisions | conflicts | refs |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for r in rows:
        pf = r["per_field_recall"]
        md.append(f"| `{r['fixture']}` | {pf['active_goals']['recall']} | "
                  f"{pf['open_problems']['recall']} | {pf['confirmed_findings']['recall']} | "
                  f"{pf['discarded_hypotheses']['recall']} | "
                  f"{pf['architecture_decisions']['recall']} | "
                  f"{pf['open_conflicts']['recall']} | {pf['references']['recall']} |")
    md += [
        "",
        "## Success criteria (per the brief)\n",
        f"1. >90% token saving — **FAIL** on every regime tested (short: {avg(short_rows,'compression')}; "
        f"long: {avg(long_rows,'compression') if long_rows else '—'}). The paper's >90% lived on much "
        "longer inputs.",
        f"2. Essential architecture decisions preserved — **"
        f"{'PASS' if (avg(rows,'recall_architecture_decisions') or 0) >= 0.80 else 'FAIL'}** "
        f"(mean decision recall {avg(rows,'recall_architecture_decisions')}, threshold ≥0.80).",
        f"3. Claude workable in the new chat — {workable}.",
        "",
        "## What is lost (honest, per fixture)\n",
    ]
    for r in rows:
        if r["missing_info"]:
            md.append(f"### `{r['fixture']}`")
            for f, items in r["missing_info"].items():
                md.append(f"- **{f}:** " + "; ".join(f"“{x}”" for x in items))
            md.append("")
        else:
            md.append(f"- `{r['fixture']}`: no ground-truth items missing.\n")
    md += [
        "## Honest limits\n",
        "- **Workability untested.** Criterion 3 needs a second Claude session that ingests only "
        "the rehydrated block and continues the work. That two-session A/B is out of scope of a "
        "local prototype; it is reported as UNTESTED, not silently inflated.",
        "- **Lexical extractor.** The extractor uses fixed lexical/structural cues (no embeddings, "
        "no LLM). Paraphrastic or implicit content is missed; reflected directly in the per-field "
        "recall numbers, not patched.",
        "- **Three fixtures.** A 3-fixture probe is a feasibility check, not a population estimate. "
        "Real chat traffic would expose failure modes these fixtures do not.",
        "- **Compression ratio depends on input length.** The paper's ~9900→269 number was on "
        "long DriftBench transcripts. Short chats compress less; the per-fixture column shows the "
        "honest range.",
        "- **Reproducibility note.** Token counts use the same offline static tokenizer "
        "(`minishlab/potion-base-8M`) as the prior Wikipedia probes; results are deterministic.",
        "",
        "## What this is NOT claiming\n",
        "- No claims about AGI, alignment, or general problem-solving. This is one experimental "
        "context-compression layer for LLM-assisted research work.",
    ]
    (_REPORTS / "evaluation_report.md").write_text("\n".join(md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    run()
