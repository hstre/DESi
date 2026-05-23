"""Aufgabe 7 — contamination probe.

The inheritance mechanism is parameterised by fixture phrases
(``Frame: …``, ``Section: …``, domain tokens). A patch that
would deploy this mechanism cannot reach into the protected
benchmark pools and silently re-frame cases there.

This module measures, for every fixture phrase used by the
simulator, how many protected-pool texts already contain that
phrase. Any non-zero hit is a contamination risk: the
phrase would re-label real benchmark cases the moment the
mechanism shipped.

The five protected pools (v1.5 / v1.9 / v2.3 / v3.4 / v3.5) are
the exact same set used by the v3.7 probe.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..benchmark import ALL_CASES as MAIN_CASES
from ..benchmark_multistep import ALL_MULTISTEP_CASES
from ..frame_benchmark import ALL_FRAME_CASES
from ..frame_invariance import ALL_GROUPS as INV_GROUPS
from ..tools.benchmark import ALL_TOOL_CASES
from .inheritance import (
    _DOMAIN_TOKENS,
    _EXPLICIT_FRAME_PHRASES,
    _SECTION_PHRASES,
)


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
    """One probed phrase: per-benchmark hits + aggregate risk."""

    phrase: str
    signal: str             # "explicit_frame" / "section_header" / …
    per_benchmark_hits: dict[str, int]
    contamination_risk: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "phrase": self.phrase,
            "signal": self.signal,
            "per_benchmark_hits": dict(self.per_benchmark_hits),
            "contamination_risk": self.contamination_risk,
        }


def _probe_phrase(phrase: str, signal: str,
                  pools: dict[str, tuple[str, ...]]) -> ContaminationResult:
    low_phrase = phrase.lower()
    per: dict[str, int] = {}
    hits = 0
    total = 0
    for name, texts in sorted(pools.items()):
        local = sum(1 for t in texts if low_phrase in t.lower())
        per[name] = local
        hits += local
        total += len(texts)
    risk = round(hits / total, 6) if total > 0 else 0.0
    return ContaminationResult(
        phrase=phrase, signal=signal,
        per_benchmark_hits=per, contamination_risk=risk,
    )


def probe_all_fixtures() -> tuple[ContaminationResult, ...]:
    """Run the contamination probe over every fixture phrase used
    by the inheritance simulator."""
    pools = _benchmark_text_pools()
    out: list[ContaminationResult] = []
    for phrase, _ in _EXPLICIT_FRAME_PHRASES:
        out.append(_probe_phrase(phrase, "explicit_frame", pools))
    for phrase, _ in _SECTION_PHRASES:
        out.append(_probe_phrase(phrase, "section_header", pools))
    for tokens in _DOMAIN_TOKENS.values():
        for tok in tokens:
            out.append(_probe_phrase(tok, "domain_repetition", pools))
    return tuple(out)


def aggregate_contamination(
    results: tuple[ContaminationResult, ...]
) -> dict[str, Any]:
    """Reduce probe results to the summary fields the report needs."""
    total = len(results)
    zero = sum(1 for r in results if r.contamination_risk == 0.0)
    any_hit = total - zero
    max_risk = max((r.contamination_risk for r in results), default=0.0)
    by_signal: dict[str, dict[str, int]] = {}
    for r in results:
        bucket = by_signal.setdefault(
            r.signal, {"total": 0, "zero": 0, "nonzero": 0},
        )
        bucket["total"] += 1
        if r.contamination_risk == 0.0:
            bucket["zero"] += 1
        else:
            bucket["nonzero"] += 1
    return {
        "total_phrases": total,
        "zero_risk_phrases": zero,
        "nonzero_risk_phrases": any_hit,
        "max_contamination_risk": max_risk,
        "by_signal": by_signal,
    }


__all__ = [
    "ContaminationResult",
    "aggregate_contamination",
    "probe_all_fixtures",
]
