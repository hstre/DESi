"""Minimal live-LLM example.

Reads the committed REAL OpenRouter capture (deterministic replay) and
reports the deterministic governance grading. No network call is made
here: live outputs are captured once, then evaluated deterministically.

Set OPENROUTER_API_KEY and use desi.live_llm_validation.capture_response
to capture fresh live outputs; the evaluation below replays the
committed captures.

    python examples/live_llm_example.py
"""
from __future__ import annotations

from desi.live_llm_validation import samples
from desi.live_llm_validation_granite import results


def main() -> None:
    print("v38.0 captured live samples (replayed, not re-called):")
    for s in samples():
        print(f"  {s['task_id']}: {s['raw_content']!r} "
              f"(model {s['model_version']}, cost ${s['usage']['cost']})")

    print("\nv38.1 Granite structured grading (deterministic):")
    for r in results():
        print(f"  {r.task_id}: compliant={r.compliant} "
              f"hallucinated={r.hallucinated}")
    print("\nLLM outputs are observed stochastic evidence, graded "
          "deterministically; never treated as canonical truth.")


if __name__ == "__main__":
    main()
