"""v24.3 - automatic citation generation.

Turns graph provenance into citations for claims and metrics, so
every number a paper reports can be traced to its sprint, the
claim it supports and the replay hash that validates it.
"""
from __future__ import annotations

from dataclasses import dataclass

from .queries import (
    claim_ids, generating_sprints, metric_names,
    metric_replay_hashes, metric_sprints,
    metric_supported_claims, replay_hashes_of,
)


@dataclass(frozen=True)
class Citation:
    subject: str
    kind: str  # "claim" | "metric"
    sprints: tuple[str, ...]
    text: str

    def to_dict(self) -> dict[str, object]:
        return {
            "subject": self.subject,
            "kind": self.kind,
            "sprints": list(self.sprints),
            "text": self.text,
        }


def claim_citation(claim_id: str) -> Citation:
    sprints = generating_sprints(claim_id)
    rh = replay_hashes_of(claim_id)
    text = (
        f"{claim_id} [{', '.join(sprints)}] "
        f"(validated: {', '.join(rh)})"
    )
    return Citation(claim_id, "claim", sprints, text)


def metric_citation(metric: str) -> Citation:
    sprints = metric_sprints(metric)
    claims = metric_supported_claims(metric)
    rh = metric_replay_hashes(metric)
    text = (
        f"{metric} [{', '.join(sprints)}] supports "
        f"{', '.join(claims)} (validated: {', '.join(rh)})"
    )
    return Citation(metric, "metric", sprints, text)


def citations() -> tuple[Citation, ...]:
    cs = [claim_citation(c) for c in claim_ids()]
    cs += [metric_citation(m) for m in metric_names()]
    return tuple(cs)


def metric_derivation_visibility() -> float:
    """Fraction of metrics whose derivation is visible in the
    graph - producing sprint, supported claim and validating
    replay hash, in [0, 1]."""
    metrics = metric_names()
    if not metrics:
        return 0.0
    visible = sum(
        1 for m in metrics
        if metric_sprints(m)
        and metric_supported_claims(m)
        and metric_replay_hashes(m)
    )
    return round(visible / len(metrics), 6)


def references_section() -> str:
    lines = [
        "## References (auto-generated from the epistemic "
        "graph)",
        "",
    ]
    for c in citations():
        lines.append(f"- {c.text}")
    lines.append("")
    return "\n".join(lines)


__all__ = [
    "Citation",
    "citations",
    "claim_citation",
    "metric_citation",
    "metric_derivation_visibility",
    "references_section",
]
