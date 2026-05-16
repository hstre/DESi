"""Aufgabe 3 / 4 — load the v5.3 RAW corpus artifact.

The RAW corpus is the v5.2 evaluation corpus *before* any
manual conclusion edits. It was committed under
``artifacts/v5_3/raw_corpus.json`` alongside the v5.3
bias-audit artifacts. v5.4 reads it unchanged: no
substitutions, no paraphrases, no exclusions.
"""
from __future__ import annotations

import json
import pathlib

from ..taxonomy_generalization.corpus import (
    GeneralizationChain,
)


_REPO = pathlib.Path(__file__).resolve().parents[3]
_RAW_ARTIFACT = (
    _REPO / "artifacts" / "v5_3" / "raw_corpus.json"
)


def load_raw_chains() -> tuple[GeneralizationChain, ...]:
    doc = json.loads(_RAW_ARTIFACT.read_text(encoding="utf-8"))
    out: list[GeneralizationChain] = []
    for entry in doc["chains"]:
        out.append(GeneralizationChain(
            chain_id=entry["chain_id"],
            domain=entry["domain"],
            text=entry["text"],
            ground_truth=entry["ground_truth"],
            rationale=entry["rationale"],
        ))
    return tuple(out)


def raw_chain_count() -> int:
    doc = json.loads(_RAW_ARTIFACT.read_text(encoding="utf-8"))
    return int(doc["chain_count"])


__all__ = ["load_raw_chains", "raw_chain_count"]
