"""Contamination probe — Aufgabe 6.

For each candidate, count how many texts in the five protected
benchmarks contain *every* token of the candidate. ``contamination_risk
> 0`` disqualifies the candidate even if precision and coverage are
otherwise clean.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..benchmark import ALL_CASES as MAIN_CASES
from ..benchmark_multistep import ALL_MULTISTEP_CASES
from ..frame_benchmark import ALL_FRAME_CASES
from ..frame_invariance import ALL_GROUPS as INV_GROUPS
from ..tools.benchmark import ALL_TOOL_CASES
from .candidates import Candidate


def _hits(text: str, tokens: tuple[str, ...]) -> bool:
    low = text.lower()
    return all(tok in low for tok in tokens)


def _benchmark_text_pools() -> dict[str, tuple[str, ...]]:
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
    }


@dataclass(frozen=True)
class ContaminationResult:
    candidate_id: str
    per_benchmark_hits: dict[str, int]
    contamination_risk: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "per_benchmark_hits": dict(self.per_benchmark_hits),
            "contamination_risk": self.contamination_risk,
        }


def probe(
    candidate: Candidate,
    *,
    excluded_case_ids: frozenset[str] = frozenset(),
) -> ContaminationResult:
    """Aufgabe 6 — hits/total over the five protected pools.

    ``excluded_case_ids`` lets the caller subtract the v3.5 polysemy
    failures themselves from the v3.4/v3.5 pools — those are the
    *targets* the patch is supposed to fix, so they should not be
    counted as contamination."""
    pools = _benchmark_text_pools()
    total_pool = 0
    hits = 0
    per: dict[str, int] = {}
    for name, texts in sorted(pools.items()):
        local_hits = 0
        for t in texts:
            # Skip texts the caller asked us to ignore (by exact
            # text match — the case-id mapping is heterogeneous).
            if t in excluded_case_ids:
                continue
            total_pool += 1
            if _hits(t, candidate.tokens):
                local_hits += 1
        per[name] = local_hits
        hits += local_hits
    risk = round(hits / total_pool, 6) if total_pool > 0 else 0.0
    return ContaminationResult(
        candidate_id=candidate.candidate_id,
        per_benchmark_hits=per,
        contamination_risk=risk,
    )


def excluded_polysemy_texts() -> frozenset[str]:
    """Texts that are the polysemy targets themselves. The probe
    treats them as 'expected to match' rather than contamination."""
    from .extractor import extract_polysemy_targets
    return frozenset(t.text for t in extract_polysemy_targets())


__all__ = [
    "ContaminationResult",
    "excluded_polysemy_texts",
    "probe",
]
