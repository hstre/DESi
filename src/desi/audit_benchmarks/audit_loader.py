"""v37.0 - audit scenario loader (network-free).

Loads locally-vendored synthetic audit scenarios in the style of ACCA
/ CPA audit cases. These are NOT official exam content and NO official
examination results are claimed. Every scenario is bound to the
dataset version, provenance and content hash for replay.
"""
from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass
from functools import lru_cache

from desi.external_benchmarks.dataset_hashing import content_hash

_DATASET = (
    pathlib.Path(__file__).resolve().parent
    / "datasets" / "audit_scenarios_ref.json"
)


@dataclass(frozen=True)
class AuditScenario:
    scenario_id: str
    style: str
    financial_claims: tuple[dict, ...]
    footnotes: tuple[dict, ...]
    narrative_claims: tuple[dict, ...]
    cross_refs: tuple[dict, ...]


@lru_cache(maxsize=1)
def _payload() -> dict:
    return json.loads(_DATASET.read_text(encoding="utf-8"))


def dataset_hash() -> str:
    return content_hash(_payload())


def dataset_version() -> str:
    return _payload()["version"]


def provenance() -> str:
    return _payload()["provenance"]


@lru_cache(maxsize=1)
def scenarios() -> tuple[AuditScenario, ...]:
    p = _payload()
    return tuple(
        AuditScenario(
            scenario_id=s["scenario_id"],
            style=s["style"],
            financial_claims=tuple(s.get("financial_claims", [])),
            footnotes=tuple(s.get("footnotes", [])),
            narrative_claims=tuple(s.get("narrative_claims", [])),
            cross_refs=tuple(s.get("cross_refs", [])),
        )
        for s in p["scenarios"]
    )


__all__ = [
    "AuditScenario",
    "dataset_hash",
    "dataset_version",
    "provenance",
    "scenarios",
]
