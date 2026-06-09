"""Multi-model A/B sweep on case4 (long research dialog).

Tests whether the long-input result reproduces across model families.
Each model is run on BOTH variants; identical prompts (same hashes), same
evaluator (Jaccard 0.25, unchanged), same ground truth. Failures (no access,
rate limit, refusals) are recorded explicitly, never hidden or simulated.

Models selected to span the major frontier vendors + a representative open
model. Each is identified by OpenRouter slug.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_HERE / "ab_evidence"))
sys.path.insert(0, str(_HERE / "claude_compression"))

import backend  # noqa: E402
from build_state import load_ground_truth  # noqa: E402
from evaluate_response import evaluate  # noqa: E402
from prompts import variant_A_messages, variant_B_messages  # noqa: E402

CASE = "case4_long_research"

# OpenRouter slugs. Cover frontier families + one strong open model.
MODELS = [
    "anthropic/claude-opus-4.5",
    "anthropic/claude-sonnet-4.5",
    "anthropic/claude-haiku-4.5",
    "openai/gpt-5",
    "openai/gpt-4o",
    "google/gemini-2.5-pro",
    "google/gemini-2.5-flash",
    "meta-llama/llama-3.3-70b-instruct",
    "deepseek/deepseek-chat-v3",
    "mistralai/mistral-large",
    "qwen/qwen-2.5-72b-instruct",
]

_OUT = _HERE / "ab_evidence" / "results" / "multimodel_sweep.json"


def _try_call(system, messages, model):
    try:
        return backend.call_messages(system, messages, model=model, max_tokens=2048)
    except Exception as e:
        return {"error": str(e)[:300], "backend": "openrouter", "model": model,
                "text": "", "latency_ms": None, "input_tokens": None, "output_tokens": None}


def run():
    a = variant_A_messages(CASE)
    b = variant_B_messages(CASE)
    gt = load_ground_truth(CASE)
    results = []
    for model in MODELS:
        print(f"  -> {model}", flush=True)
        rec = {"model": model}
        rec["variant_A"] = {"response": _try_call(a["system"], a["messages"], model)}
        rec["variant_A"]["evaluation"] = evaluate(rec["variant_A"]["response"]["text"], gt) \
            if not rec["variant_A"]["response"].get("error") else None
        time.sleep(0.5)  # be nice to the proxy
        rec["variant_B"] = {"response": _try_call(b["system"], b["messages"], model)}
        rec["variant_B"]["evaluation"] = evaluate(rec["variant_B"]["response"]["text"], gt) \
            if not rec["variant_B"]["response"].get("error") else None
        results.append(rec)
        time.sleep(0.5)
    out = {"case": CASE, "models": results}
    _OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nWrote {_OUT}", flush=True)
    return out


if __name__ == "__main__":
    run()
