#!/usr/bin/env python3
"""DESi atomic-claim → SPL projection adapter (benchmark glue).

P9 CHANGE: this no longer owns any entropy / gateway / P_r logic. After the
SPL consolidation (P9) it is a thin wrapper over the canonical
`desi.spl_core.project_atomic_claim`. There is now ONE entropy model and ONE
admissibility gateway, both in `src/desi/spl_core/`. This file only reshapes the
canonical candidate into the P8 output dict so existing benchmark code / reports
keep working.

THIS FILE IS DESi GLUE, NOT ORIGINAL SPL. The unmodified original Alexandria SPL
remains vendored under `vendor/alexandria_spl/` and is used by
`spl_core_benchmark.py` only as a reference oracle to prove the canonical core
reproduces it (zero compatibility drift). See
`artifacts/architecture/spl_consolidation_analysis.md`.

No network, no secrets.
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO / "src") not in sys.path:
    sys.path.insert(0, str(_REPO / "src"))

from desi.spl_core import (  # noqa: E402
    DEFAULT_RELATION_SPACE_SIZE,
    CanonicalThresholds,
    project_atomic_claim,
)

# Re-exported for callers that imported it from here pre-P9.
DEFAULT_CONFIDENCE = 0.7


def _emission_status(emission_rule: str | None, admissible: bool) -> str:
    if emission_rule == "E0":
        return "structural_violation"
    if emission_rule == "E3":
        return "ambiguous"
    if emission_rule in ("E1", "E2"):
        return "ready_for_claim"
    return "flag" if emission_rule is None else "unknown"


def project_atomic_claim_to_candidate(
    claim: dict,
    *,
    relation_space_size: int = DEFAULT_RELATION_SPACE_SIZE,
    thresholds: CanonicalThresholds | None = None,
) -> dict:
    """Project one atomic claim through the canonical SPL-core and return the
    P8-compatible dict. `gateway_valid` == canonical `admissible`."""
    cand, proj = project_atomic_claim(
        claim, relation_space_size=relation_space_size, thresholds=thresholds)
    has_candidate = cand.emission_rule in ("E1", "E2")  # something was emitted
    return {
        "semantic_unit": {
            "unit_id": cand.unit_id,
            "source_text": cand.content,
            "source_ref": cand.source_ref,
            "fragmentation_signal": "desi_spl_adapter",
        },
        "semantic_projection": proj.to_dict(),
        "claim_candidate": ({
            "subject": cand.subject,
            "relation": cand.predicate,   # Alexandria/P8 key name
            "object": cand.object,
            "relation_score": cand.confidence,
            "emission_rule": cand.emission_rule,
            "h_norm": cand.projection_entropy,
            "candidate_id": cand.candidate_id,
        } if has_candidate else None),
        "projection_entropy": cand.projection_entropy,
        "projection_method": "spl_adapter",
        "gateway_valid": cand.admissible,
        "errors": list(cand.errors),
        "emission_status": _emission_status(cand.emission_rule, cand.admissible),
        "emission_rule": cand.emission_rule,
    }


def _smoke() -> int:
    samples = [
        {"subject": "Abraham Lincoln", "predicate": "birth year", "object": "1809", "confidence": 0.9},
        {"subject": "the Earth", "predicate": "is", "object": "flat", "confidence": 0.7},
        {"subject": "the suspect", "predicate": "was in", "object": "London", "confidence": 0.45},
        {"subject": "", "predicate": "", "object": "", "confidence": 0.7},
    ]
    print(f"relation_space_size={DEFAULT_RELATION_SPACE_SIZE} (delegating to desi.spl_core)")
    for c in samples:
        r = project_atomic_claim_to_candidate(c)
        cand = r["claim_candidate"]
        rel = cand["relation"] if cand else "-"
        print(
            f"  conf={c.get('confidence'):.2f} '{c['subject']}|{c['predicate']}|{c['object']}'"
            f" -> status={r['emission_status']} rule={r['emission_rule']}"
            f" h_norm={r['projection_entropy']:.3f} gateway_valid={r['gateway_valid']}"
            f" rel={rel!r} errors={r['errors']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(_smoke())
