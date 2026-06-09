"""Pressure-zone A/B: case6 (baseline) → case7a (30k padded) → case7b (60k padded).

Variant B uses the SAME state (case6 GT) at every pressure level — only A grows.
Sonnet 4.5 across all three; GPT-4o spot-check on case7b only.
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

CASES = ("case6_long_research", "case7a_padded_30k", "case7b_padded_60k")
MODEL = "anthropic/claude-sonnet-4.5"
SPOT_CHECK_MODEL = "openai/gpt-4o"

_OUT = _HERE / "results" / "pressure_sweep.json"


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
    print(f"  -> case7b spot-check ({SPOT_CHECK_MODEL})", flush=True)
    results.append(_run_one("case7b_padded_60k", SPOT_CHECK_MODEL))
    _OUT.write_text(json.dumps({"runs": results}, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")
    print(f"\nWrote {_OUT}", flush=True)


if __name__ == "__main__":
    run()
