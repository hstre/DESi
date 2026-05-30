"""LongMemEval A/B run: 15 stratified items, ~109k tokens per item, Sonnet 4.5 + GPT-4o.

For each item:
  - Variant A (full history):  system + all haystack_sessions concatenated + question
  - Variant B (state only):    system + only answer_session_ids sessions (~3k) + question

The "state" here is LongMemEval's own annotated evidence sessions — not our structured
DESi-state. That's an honest difference: B = "kuratierter Volltext-Auszug", not
"structured claims/decisions". But it tests the SAME idea (relevant subset vs full).

Evaluation: LLM-as-judge against the dataset's annotated 'answer'. We use a small,
deterministic judge: another GPT-4o call comparing model_answer vs gold_answer, scoring
0/0.5/1 (wrong/partial/correct). Honest: any LLM-judge has noise; we report agreement
across the two evaluators (judge runs).
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parents[0] / "claude_compression"))

import backend  # noqa: E402

SUBSET = _HERE / "data" / "longmemeval_s_stratified15.json"
OUT = _HERE / "results" / "longmemeval_sweep.json"

MODELS = ("anthropic/claude-sonnet-4.5", "openai/gpt-4o")
JUDGE_MODEL = "openai/gpt-4o"

SYSTEM = (
    "You are continuing a long-running conversation. The user will ask a question that "
    "depends on what was said earlier in this conversation. Use ONLY the conversation history "
    "below to answer. If the answer is not in the history, say 'I don't know'."
)


def _build_messages(item, mode):
    """mode: 'A' = full history; 'B' = only evidence sessions."""
    sessions = item["haystack_sessions"]
    session_ids = item["haystack_session_ids"]
    evidence_set = set(item["answer_session_ids"])
    if mode == "A":
        chosen = list(zip(sessions, session_ids))
    else:
        chosen = [(s, sid) for s, sid in zip(sessions, session_ids) if sid in evidence_set]
    # flatten into a single user message labelling sessions
    parts = ["=== CONVERSATION HISTORY ==="]
    for sess, sid in chosen:
        parts.append(f"\n--- session {sid} ---")
        for turn in sess:
            role = turn.get("role", "user").upper()
            parts.append(f"{role}: {turn.get('content','')}")
    parts.append("\n=== CURRENT QUESTION ===")
    parts.append(item["question"])
    return [{"role": "user", "content": "\n".join(parts)}]


def _call(system, messages, model, max_tokens=512):
    try:
        return backend.call_messages(system, messages, model=model, max_tokens=max_tokens)
    except Exception as e:
        return {"error": str(e)[:300], "model": model, "text": "",
                "latency_ms": None, "input_tokens": None, "output_tokens": None}


JUDGE_SYSTEM = (
    "You are an impartial grader. Compare a MODEL ANSWER to the GOLD ANSWER for a question. "
    "Respond with EXACTLY one line in this format:\n"
    "SCORE: <0|0.5|1>\n"
    "where 1 = correct (semantically equivalent to gold), 0.5 = partially correct (touches "
    "the right facts but misses or adds material), 0 = wrong or refuses to answer ('I don't know')."
)


def _judge(question, gold, response_text):
    msg = [{"role": "user", "content":
            f"QUESTION:\n{question}\n\nGOLD ANSWER:\n{gold}\n\nMODEL ANSWER:\n{response_text or '(empty)'}"}]
    r = _call(JUDGE_SYSTEM, msg, JUDGE_MODEL, max_tokens=24)
    text = r.get("text", "") or ""
    # parse SCORE: X
    score = None
    for line in text.splitlines():
        if line.upper().startswith("SCORE:"):
            try:
                score = float(line.split(":", 1)[1].strip())
                if score not in (0.0, 0.5, 1.0):
                    score = round(score * 2) / 2  # snap to {0, 0.5, 1}
            except Exception:
                pass
            break
    return {"raw_judge_text": text, "score": score}


def run():
    items = json.loads(SUBSET.read_text())
    results = []
    for i, item in enumerate(items, 1):
        print(f"\n[{i}/{len(items)}] {item['question_id']} [{item['question_type']}] "
              f"A={item['A_tokens']} B={item['B_tokens']}", flush=True)
        item_res = {
            "question_id": item["question_id"],
            "question_type": item["question_type"],
            "question": item["question"],
            "gold_answer": item["answer"],
            "n_sessions": item["n_sessions"],
            "n_evidence_sessions": item["n_evidence_sessions"],
            "A_input_tokens": item["A_tokens"],
            "B_input_tokens": item["B_tokens"],
            "runs": [],
        }
        for model in MODELS:
            for mode in ("A", "B"):
                print(f"  -> {model} variant_{mode}", flush=True)
                msgs = _build_messages(item, mode)
                r = _call(SYSTEM, msgs, model)
                judged = _judge(item["question"], item["answer"], r.get("text", ""))
                item_res["runs"].append({
                    "model": model, "variant": mode,
                    "response_text": r.get("text", ""),
                    "input_tokens": r.get("input_tokens"),
                    "output_tokens": r.get("output_tokens"),
                    "latency_ms": r.get("latency_ms"),
                    "error": r.get("error"),
                    "judge_score": judged["score"],
                    "judge_raw": judged["raw_judge_text"],
                })
                time.sleep(0.6)
        results.append(item_res)
        # incremental save in case anything dies
        OUT.write_text(json.dumps({"items": results}, indent=2, ensure_ascii=False) + "\n",
                       encoding="utf-8")

    print(f"\nWrote {OUT}", flush=True)


if __name__ == "__main__":
    run()
