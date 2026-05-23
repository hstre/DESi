"""Minimal replay example.

Shows that the replay kernel produces a byte-stable hash for an
object: identical input -> identical hash, no PRNG, no timestamps.

    python examples/replay_example.py
"""
from __future__ import annotations

from desi.core.replay_kernel import canonical_json, replay_hash


def main() -> None:
    artifact = {
        "phase": "example",
        "metrics": {"replay_stability": 1.0, "node_reduction": 0.417},
        "verdict": "EXAMPLE_OK",
    }
    h1 = replay_hash(artifact)
    h2 = replay_hash(artifact)
    print("canonical form:")
    print(canonical_json(artifact))
    print("replay_hash (run 1):", h1)
    print("replay_hash (run 2):", h2)
    print("replay-stable:", h1 == h2)


if __name__ == "__main__":
    main()
