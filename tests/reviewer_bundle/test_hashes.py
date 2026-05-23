"""Pin every replay_hash the reviewer bundle cites."""
from __future__ import annotations

import json
import pathlib

from desi.rule_patch_protocol import (
    RulePatchProtocol,
    causal_chain_v2_7_candidate,
    compute_benchmark_hashes,
    fake_rule_without_guards_candidate,
)


_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


# Hashes the reviewer bundle promises in plain text.
_PINNED: dict[str, str] = {
    "v2.8 reconstruction": "1f4d9dfe44cb16e1",
    "v2.8 fail case": "d83d81ab8417c022",
    "v2.0 sandbox": "21a692fb35c8f368",
    "v2.1 diagnostic": "099bc9b4f67e0382",
    "v2.2 depth sandbox": "9d4a5938c938710e",
    "v2.4 bridge audit": "11d8471f0dd39767",
    "v2.5 rule audit": "cf417bc8e490646c",
    "v2.6 causal probe": "d061c7c66ccb5d7f",
    "v3.0 self audit": "95407f59155fb84a",
    "v3.1 audit": "3dbdf57f882a981a",
    "v3.1 anchors": "15ba5f929b38bde8",
}


def test_v28_reconstruction_replay_hash_pinned() -> None:
    rec = RulePatchProtocol().run(causal_chain_v2_7_candidate())
    assert rec.replay_hash == _PINNED["v2.8 reconstruction"]


def test_v28_fail_case_replay_hash_pinned() -> None:
    rec = RulePatchProtocol().run(fake_rule_without_guards_candidate())
    assert rec.replay_hash == _PINNED["v2.8 fail case"]


def test_compute_benchmark_hashes_stable_across_two_calls() -> None:
    a = compute_benchmark_hashes()
    b = compute_benchmark_hashes()
    assert a == b


def test_every_pinned_hash_appears_in_some_artifact() -> None:
    """Every hash the bundle promises must show up at the
    ``replay_hash`` field of at least one artefact on disk."""
    artifact_root = _REPO_ROOT / "artifacts"
    seen: set[str] = set()
    for p in artifact_root.rglob("*.json"):
        try:
            payload = json.loads(p.read_text())
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict) and "replay_hash" in payload:
            seen.add(payload["replay_hash"])
    missing = [
        (name, h) for name, h in _PINNED.items() if h not in seen
    ]
    assert not missing, f"hashes not in any artefact: {missing}"
