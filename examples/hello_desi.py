"""hello_desi - the simplest possible DESi run. NO API key needed.

What this shows, in plain terms:
  * DESi loads and runs fully offline by default.
  * DESi produces a byte-stable "replay hash": the same input always
    gives the same hash (this is how DESi makes results reproducible).
  * DESi's determinism check is clean.

Run it with:

    python examples/hello_desi.py

It makes no live LLM calls and writes nothing.
"""
from __future__ import annotations

from desi.core.determinism_scanner import high_risk_hit_count
from desi.core.replay_kernel import replay_hash
from desi.runtime_config import live_calls_enabled, offline_mode


def main() -> None:
    print("Hello from DESi - running fully offline.\n")

    print(f"  offline mode        : {offline_mode()}")
    print(f"  live LLM calls       : "
          f"{'enabled' if live_calls_enabled() else 'disabled'}")
    print(f"  determinism clean    : {high_risk_hit_count() == 0}")

    example = {"claim": "the sky is blue", "evidence": ["daytime"]}
    h1 = replay_hash(example)
    h2 = replay_hash(example)
    print("\n  Replay demo (same input -> same hash):")
    print(f"    run 1 hash : {h1[:16]}...")
    print(f"    run 2 hash : {h2[:16]}...")
    print(f"    identical  : {h1 == h2}")

    print(
        "\nThat's it. DESi did not call any model and changed nothing.\n"
        "DESi records and re-checks HOW statements are formed; it does\n"
        "not replace ChatGPT/Claude/DeepSeek. Try: `desi doctor`.")


if __name__ == "__main__":
    main()
