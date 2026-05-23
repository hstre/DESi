"""Aufgabe 8 — contamination probe.

A consistency probe contaminates the protected benchmark pools if
any of the sentences it *introduces* — manipulation fixtures and
synthetic GROUP_C polysemy probes — already appear there. If so,
shipping a TENSION layer based on this probe's vocabulary would
silently re-classify existing benchmark cases.

The probe checks exact-string membership across six pools:
v1.5 main, v1.9 tools, v2.3 multistep, v3.4 frame benchmark,
v3.5 invariance, and the v3.8 context-probe artifact.
"""
from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass
from typing import Any

from ..benchmark import ALL_CASES as MAIN_CASES
from ..benchmark_multistep import ALL_MULTISTEP_CASES
from ..frame_benchmark import ALL_FRAME_CASES
from ..frame_invariance import ALL_GROUPS as INV_GROUPS
from ..tools.benchmark import ALL_TOOL_CASES
from .corpus import build_corpus
from .enums import CorpusGroup
from .manipulation import MANIPULATIONS


_REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
_V38_REPORT = _REPO_ROOT / "artifacts" / "v3_8" / "report.json"


def _v38_texts() -> tuple[str, ...]:
    data = json.loads(_V38_REPORT.read_text(encoding="utf-8"))
    out: list[str] = [t["text"] for t in data["targets"]]
    for fi in data["false_inheritance_outcomes"]:
        # The fixture text isn't stored on the outcome itself, but
        # contained sentences are well-known from the v3.8 source.
        # We re-import the constant rather than re-encode them here
        # to keep one source of truth.
        pass
    from .corpus import _lookup_v38_fn_text  # noqa: PLC0415
    for fi in data["false_inheritance_outcomes"]:
        out.append(_lookup_v38_fn_text(data, fi["case_id"]))
    return tuple(out)


def _benchmark_pools() -> dict[str, tuple[str, ...]]:
    inv_texts: list[str] = []
    for g in INV_GROUPS:
        inv_texts.append(g.canonical_text)
        inv_texts.extend(g.paraphrases)
    return {
        "v1_5_main": tuple(c.text for c in MAIN_CASES),
        "v1_9_tools": tuple(c.text for c in ALL_TOOL_CASES),
        "v2_3_multistep": tuple(c.text for c in ALL_MULTISTEP_CASES),
        "v3_4_frame": tuple(c.text for c in ALL_FRAME_CASES),
        "v3_5_invariance": tuple(inv_texts),
        "v3_8_context_probe": _v38_texts(),
    }


@dataclass(frozen=True)
class ContaminationHit:
    sentence: str
    source_label: str    # which v3.9 module introduced it
    pool: str            # which protected pool it leaked into

    def to_dict(self) -> dict[str, str]:
        return {
            "sentence": self.sentence,
            "source_label": self.source_label,
            "pool": self.pool,
        }


@dataclass(frozen=True)
class ContaminationResult:
    introduced_count: int
    checked_pool_count: int
    hits: tuple[ContaminationHit, ...]
    contamination_risk: float
    per_pool_hits: dict[str, int]
    per_source_hits: dict[str, int]

    def to_dict(self) -> dict[str, Any]:
        return {
            "introduced_count": self.introduced_count,
            "checked_pool_count": self.checked_pool_count,
            "hits": [h.to_dict() for h in self.hits],
            "contamination_risk": self.contamination_risk,
            "per_pool_hits": dict(self.per_pool_hits),
            "per_source_hits": dict(self.per_source_hits),
        }


def _introduced_sentences() -> tuple[tuple[str, str], ...]:
    """Every sentence this probe *introduces*: manipulation
    fixtures + synthetic GROUP_C polysemy probes. Corpus cases
    sourced from v3.5/v3.8 artifacts are excluded because they
    already live in those benchmark pools by construction."""
    pairs: list[tuple[str, str]] = []
    for m in MANIPULATIONS:
        pairs.append((m.text, f"manipulation:{m.case_id}"))
    for c in build_corpus():
        if c.group is CorpusGroup.GROUP_C and c.source == (
            "synthetic polysemy"
        ):
            pairs.append((c.text, f"corpus:{c.case_id}"))
    return tuple(pairs)


def probe_contamination() -> ContaminationResult:
    pools = _benchmark_pools()
    pool_sets: dict[str, frozenset[str]] = {
        name: frozenset(texts) for name, texts in pools.items()
    }
    introduced = _introduced_sentences()
    hits: list[ContaminationHit] = []
    per_pool: dict[str, int] = {name: 0 for name in pools}
    per_source: dict[str, int] = {}
    for sentence, source in introduced:
        for pool_name, pool_set in pool_sets.items():
            if sentence in pool_set:
                hits.append(ContaminationHit(
                    sentence=sentence,
                    source_label=source,
                    pool=pool_name,
                ))
                per_pool[pool_name] += 1
                per_source[source] = per_source.get(source, 0) + 1
    introduced_count = len(introduced)
    risk = (
        round(len(hits) / introduced_count, 6)
        if introduced_count else 0.0
    )
    return ContaminationResult(
        introduced_count=introduced_count,
        checked_pool_count=len(pools),
        hits=tuple(hits),
        contamination_risk=risk,
        per_pool_hits=dict(sorted(per_pool.items())),
        per_source_hits=dict(sorted(per_source.items())),
    )


__all__ = [
    "ContaminationHit",
    "ContaminationResult",
    "probe_contamination",
]
