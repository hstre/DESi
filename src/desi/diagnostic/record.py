"""DeficitRecord — one detected weakness in the v2.1 diagnostic.

Aufgabe 3 mandates eleven required fields. ``replay_hash`` makes
the record deterministic: two diagnostic runs that observed the same
underlying data produce byte-identical ``DeficitRecord`` instances
(modulo timestamps, which are excluded from the hash).
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

from .categories import DeficitCategory
from .knobs import DEFAULT_INVENTORY, KnobInventory


def _canonical(payload: dict[str, Any]) -> str:
    """Same canonical-JSON discipline as the rest of the project."""
    return json.dumps(
        payload, sort_keys=True, separators=(",", ":"), default=str,
    )


@dataclass(frozen=True)
class DeficitRecord:
    """One reproducible weakness finding.

    Required fields per the directive: ``deficit_id``, ``category``,
    ``source_module``, ``source_case_ids``, ``frequency``,
    ``severity_score``, ``confidence_score``, ``is_actionable``,
    ``candidate_knobs``, ``rationale``, ``replay_hash``.

    Plus the v2.1-internal ``self_reference`` boolean for Aufgabe 8.
    """

    deficit_id: str
    category: DeficitCategory
    source_module: str
    source_case_ids: tuple[str, ...]
    frequency: int
    severity_score: float
    confidence_score: float
    is_actionable: bool
    candidate_knobs: tuple[str, ...]
    rationale: str
    replay_hash: str
    self_reference: bool = False

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    @classmethod
    def build(
        cls,
        *,
        category: DeficitCategory,
        source_module: str,
        source_case_ids: tuple[str, ...],
        frequency: int,
        severity_score: float,
        confidence_score: float,
        is_actionable: bool,
        candidate_knobs: tuple[str, ...],
        rationale: str,
        self_reference: bool = False,
        inventory: KnobInventory = DEFAULT_INVENTORY,
    ) -> "DeficitRecord":
        unknown = [k for k in candidate_knobs if not inventory.is_known(k)]
        if unknown:
            raise ValueError(
                "candidate_knobs contains unknown knobs "
                f"(violates Aufgabe 7): {unknown!r}",
            )
        sorted_ids = tuple(sorted(source_case_ids))
        sorted_knobs = tuple(sorted(candidate_knobs))
        deficit_id = _make_deficit_id(
            category, source_module, sorted_ids,
        )
        replay_hash = _make_replay_hash(
            category=category,
            source_module=source_module,
            source_case_ids=sorted_ids,
            frequency=frequency,
            severity_score=severity_score,
            confidence_score=confidence_score,
            is_actionable=is_actionable,
            candidate_knobs=sorted_knobs,
            rationale=rationale,
            self_reference=self_reference,
        )
        return cls(
            deficit_id=deficit_id,
            category=category,
            source_module=source_module,
            source_case_ids=sorted_ids,
            frequency=frequency,
            severity_score=round(severity_score, 6),
            confidence_score=round(confidence_score, 6),
            is_actionable=is_actionable,
            candidate_knobs=sorted_knobs,
            rationale=rationale,
            replay_hash=replay_hash,
            self_reference=self_reference,
        )

    # ------------------------------------------------------------------
    # Invariants
    # ------------------------------------------------------------------

    def __post_init__(self) -> None:
        if not 0.0 <= self.severity_score <= 1.0:
            raise ValueError(
                f"severity_score out of [0,1]: {self.severity_score}",
            )
        if not 0.0 <= self.confidence_score <= 1.0:
            raise ValueError(
                f"confidence_score out of [0,1]: {self.confidence_score}",
            )
        if self.frequency < 0:
            raise ValueError(f"frequency must be >= 0: {self.frequency}")

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        return {
            "deficit_id": self.deficit_id,
            "category": self.category.value,
            "source_module": self.source_module,
            "source_case_ids": list(self.source_case_ids),
            "frequency": self.frequency,
            "severity_score": self.severity_score,
            "confidence_score": self.confidence_score,
            "is_actionable": self.is_actionable,
            "candidate_knobs": list(self.candidate_knobs),
            "rationale": self.rationale,
            "self_reference": self.self_reference,
            "replay_hash": self.replay_hash,
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_deficit_id(
    category: DeficitCategory,
    source_module: str,
    source_case_ids: tuple[str, ...],
) -> str:
    raw = _canonical({
        "c": category.value, "m": source_module,
        "i": list(source_case_ids),
    })
    return "df_" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:10]


def _make_replay_hash(**fields: Any) -> str:
    payload = {
        k: (v.value if hasattr(v, "value") else
            list(v) if isinstance(v, tuple) else v)
        for k, v in fields.items()
    }
    raw = _canonical(payload).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


__all__ = ["DeficitRecord"]
