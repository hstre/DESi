"""v24.3 - automatic scientific traceability.

For each claim, assembles a traceability record straight from
the graph - the sprints that produced it, the methods and
fixtures it derives from, the replay hashes that validate it and
the limitations that scope it. A claim is traceable when that
chain is complete.
"""
from __future__ import annotations

from dataclasses import dataclass

from desi.scientific_rendering import forbidden_hits

from .queries import (
    claim_ids, claim_text, fixtures_of, generating_sprints,
    limitations_of, methods_of, replay_hashes_of,
)


@dataclass(frozen=True)
class TraceRecord:
    claim_id: str
    text: str
    sprints: tuple[str, ...]
    methods: tuple[str, ...]
    fixtures: tuple[str, ...]
    replay_hashes: tuple[str, ...]
    limitations: tuple[str, ...]

    def is_complete(self) -> bool:
        return (
            bool(self.sprints)
            and bool(self.methods or self.fixtures)
            and bool(self.replay_hashes)
            and bool(self.limitations)
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "claim_id": self.claim_id,
            "text": self.text,
            "sprints": list(self.sprints),
            "methods": list(self.methods),
            "fixtures": list(self.fixtures),
            "replay_hashes": list(self.replay_hashes),
            "limitations": list(self.limitations),
            "is_complete": self.is_complete(),
        }


def trace_records() -> tuple[TraceRecord, ...]:
    return tuple(
        TraceRecord(
            cid, claim_text(cid), generating_sprints(cid),
            methods_of(cid), fixtures_of(cid),
            replay_hashes_of(cid), limitations_of(cid),
        )
        for cid in claim_ids()
    )


def is_traceable(claim_id: str) -> bool:
    for r in trace_records():
        if r.claim_id == claim_id:
            return r.is_complete()
    raise KeyError(claim_id)


def scientific_traceability() -> float:
    """Fraction of claims with a complete traceability chain, in
    [0, 1]."""
    records = trace_records()
    if not records:
        return 0.0
    complete = sum(1 for r in records if r.is_complete())
    return round(complete / len(records), 6)


def traceability_section() -> str:
    """Auto-generated, sandbox-honest provenance appendix derived
    entirely from the graph."""
    lines = [
        "## Provenance Appendix (auto-derived from the "
        "epistemic graph)",
        "",
    ]
    for r in trace_records():
        lines.append(
            f"- **{r.claim_id}** [{', '.join(r.sprints)}] - "
            f"methods: {', '.join(r.methods) or 'n/a'}; "
            f"fixtures: {', '.join(r.fixtures) or 'n/a'}; "
            f"scope: {', '.join(r.limitations)}; "
            f"validated by {len(r.replay_hashes)} replay "
            f"hashes."
        )
    lines.append("")
    return "\n".join(lines)


def section_forbidden_hits() -> tuple[str, ...]:
    return forbidden_hits(traceability_section())


__all__ = [
    "TraceRecord",
    "is_traceable",
    "scientific_traceability",
    "section_forbidden_hits",
    "trace_records",
    "traceability_section",
]
