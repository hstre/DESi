"""v35.3 - HuggingFace-style exports and the replay manifest.

Produces public, serialisable export structures: a HuggingFace
Dataset payload (the public scorecards as records), a HuggingFace
Space JSON (a small viewer config), and a replay manifest binding
every exported artifact to a reproducible anchor. The replay manifest
integrity check re-derives every anchor and confirms it matches.
"""
from __future__ import annotations

import hashlib

from .benchmark_summary import run_summaries
from .scorecard_export import public_scorecards
from .system_card import system_card


def hf_dataset() -> dict[str, object]:
    return {
        "dataset_name": "desi-external-benchmark-scorecards",
        "license": "CC0-1.0",
        "description": (
            "Public benchmark scorecards for DESi external runs. "
            "Reference datasets, not official leaderboard results."
        ),
        "features": [
            "name", "family", "provenance_class", "score",
            "replay_anchor",
        ],
        "records": [c.to_dict() for c in public_scorecards()],
    }


def hf_space() -> dict[str, object]:
    return {
        "space_name": "desi-benchmark-viewer",
        "sdk": "static",
        "honest_banner": (
            "Reference-format runs in a network-free environment; "
            "not official leaderboard scores; not an AGI system."
        ),
        "shows": ["scorecards", "system_card", "limitations",
                  "replay_manifest"],
    }


def _anchor(name: str, payload: object) -> str:
    return hashlib.sha256(
        (name + "::" + str(payload)).encode("utf-8"),
    ).hexdigest()


def replay_manifest() -> dict[str, str]:
    """artifact name -> reproducible anchor."""
    manifest: dict[str, str] = {}
    for r in run_summaries():
        manifest[r.name] = r.replay_anchor
    manifest["hf_dataset"] = _anchor("hf_dataset", hf_dataset())
    manifest["hf_space"] = _anchor("hf_space", hf_space())
    manifest["system_card"] = _anchor("system_card", system_card())
    return manifest


def replay_manifest_integrity() -> float:
    """1.0 iff every manifest anchor re-derives identically."""
    a = replay_manifest()
    b = replay_manifest()
    if a != b:
        return 0.0
    # run anchors must equal the freshly computed summary anchors
    summary_anchors = {r.name: r.replay_anchor for r in run_summaries()}
    for name, anchor in summary_anchors.items():
        if a.get(name) != anchor:
            return 0.0
    return 1.0 if a else 0.0


__all__ = [
    "hf_dataset",
    "hf_space",
    "replay_manifest",
    "replay_manifest_integrity",
]
