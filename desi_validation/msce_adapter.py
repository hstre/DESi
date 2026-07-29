from __future__ import annotations

from typing import Any

from .models import CandidateUpdate, EpistemicItem, EvidenceAnchor, ItemType


def candidate_from_msce(payload: dict[str, Any]) -> CandidateUpdate:
    """Map an MSCE-style L3 proposal into the neutral DESi contract.

    This adapter deliberately accepts plain dictionaries so it can sit outside
    the MSCE codebase. Field aliases can be adjusted when the concrete MSCE
    object schema is pinned during integration.
    """

    observations = payload.get("observations", [])
    inferences = payload.get("inferences", [])
    assumptions = payload.get("assumptions", [])

    items: list[EpistemicItem] = []
    for kind, values in (
        (ItemType.OBSERVATION, observations),
        (ItemType.INFERENCE, inferences),
        (ItemType.ASSUMPTION, assumptions),
    ):
        for index, value in enumerate(values):
            if isinstance(value, str):
                value = {"text": value}
            items.append(
                EpistemicItem(
                    item_id=str(value.get("id", f"{kind.value}-{index + 1}")),
                    item_type=kind,
                    text=str(value.get("text", "")),
                    evidence_ids=tuple(str(item) for item in value.get("evidence_ids", [])),
                )
            )

    anchors = tuple(
        EvidenceAnchor.from_dict(anchor)
        for anchor in payload.get("evidence", payload.get("evidence_anchors", []))
    )

    return CandidateUpdate(
        candidate_id=str(payload.get("candidate_id", payload.get("update_id", ""))),
        claim=str(payload.get("claim", payload.get("l3_candidate", ""))),
        items=tuple(items),
        evidence=anchors,
        source_trace_ids=tuple(
            str(item) for item in payload.get("source_trace_ids", payload.get("trace_ids", []))
        ),
        policy_ids=tuple(str(item) for item in payload.get("policy_ids", [])),
        applicability_boundary=str(
            payload.get("applicability_boundary", payload.get("applicability", ""))
        ),
        proposed_target=str(payload.get("proposed_target", "L3")),
        metadata={"source_system": "MSCE", **dict(payload.get("metadata", {}))},
    )
