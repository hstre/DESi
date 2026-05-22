"""v37.3 - creative accounting case loader + check.

Loads the adversarial scenarios (network-free) and flags creative
accounting from an explicit signal. A clean control scenario carries
no signals, so DESi must not fabricate a conflict.
"""
from __future__ import annotations

import json
import pathlib
from functools import lru_cache

from desi.external_benchmarks.dataset_hashing import content_hash

_DATASET = (
    pathlib.Path(__file__).resolve().parent
    / "datasets" / "adversarial_semantics_ref.json"
)


@lru_cache(maxsize=1)
def _payload() -> dict:
    return json.loads(_DATASET.read_text(encoding="utf-8"))


def dataset_hash() -> str:
    return content_hash(_payload())


def provenance() -> str:
    return _payload()["provenance"]


def adversarial_scenarios() -> tuple[dict, ...]:
    return tuple(_payload()["scenarios"])


def creative_accounting_flag(signals: dict) -> bool:
    return bool(signals.get("creative_accounting"))


__all__ = [
    "adversarial_scenarios",
    "creative_accounting_flag",
    "dataset_hash",
    "provenance",
]
