"""A/B scaling sweep: case4 / case5 / case6 — same model (Sonnet 4.5), same evaluator.

Measures whether the A->B preservation gap widens with chat length. The state-vs-chat ratio
is reported as-is (pre-run prediction was ~0.25 at case5 and ~0.15 at case6; actual was 0.35
and 0.37 — sublinearity hypothesis WEAKLY supported / partially refuted, documented honestly).
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
from build_state import load_ground_truth  # noqa: E402
from evaluate_response import evaluate  # noqa: E402
from prompts import variant_A_messages, variant_B_messages  # noqa: E402

CASES = ("case4_long_research", "case5_long_research", "case6_long_research")
MODEL = "anthropic/claude-sonnet-4.5"
SPOT_CHECK_MODEL = "openai/gpt-4o"

_OUT = _HERE / "results" / "scaling_sweep.json"


def _call(system, messages, model):
    try:
        return backend.call_messages(system, messages, model=model, max_tokens=2048)
    except Exception as e:
        return {"error": str(e)[:300], "model": model, "text": "", "latency_ms": None,
                "input_tokens": None, "output_tokens": None}


def _run_one(case_id: str, model: str) -> dict:
    a = variant_A_messages(case_id)
    b = variant_B_messages(case_id)
    gt = load_ground_truth(case_id)
    rA = _call(a["system"], a["messages"], model)
    time.sleep(0.5)
    rB = _call(b["system"], b["messages"], model)
    time.sleep(0.5)
    evA = evaluate(rA["text"], gt) if rA.get("text") else None
    evB = evaluate(rB["text"], gt) if rB.get("text") else None
    return {"case": case_id, "model": model, "variant_A": {"response": rA, "evaluation": evA},
            "variant_B": {"response": rB, "evaluation": evB}}


def run():
    results = []
    for case_id in CASES:
        print(f"  -> {case_id} ({MODEL})", flush=True)
        results.append(_run_one(case_id, MODEL))
    print(f"  -> case6 spot-check ({SPOT_CHECK_MODEL})", flush=True)
    results.append(_run_one(CASES[-1], SPOT_CHECK_MODEL))
    _OUT.write_text(json.dumps({"runs": results}, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")
    print(f"\nWrote {_OUT}", flush=True)
    return {"runs": results}


if __name__ == "__main__":
    run()
