"""v27.0 - typed research claims.

A claim is a typed, paper-anchored epistemic unit. Each claim
carries its source paper id, its class (closed taxonomy) and its
text. Classification is descriptive only - it never implies
quality, correctness or ranking.
"""
from __future__ import annotations

from dataclasses import dataclass

from .taxonomy import ClaimClass, is_claim_class


@dataclass(frozen=True)
class Claim:
    claim_id: str
    paper_id: str
    claim_class: str
    text: str

    def __post_init__(self) -> None:
        if not is_claim_class(self.claim_class):
            raise ValueError(
                f"unknown claim_class: {self.claim_class}"
            )

    def is_limitation(self) -> bool:
        return self.claim_class == ClaimClass.LIMITATION.value

    def is_open_question(self) -> bool:
        return self.claim_class == ClaimClass.OPEN_QUESTION.value

    def is_well_formed(self) -> bool:
        return bool(
            self.claim_id
            and self.paper_id
            and self.text.strip()
            and is_claim_class(self.claim_class)
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "claim_id": self.claim_id,
            "paper_id": self.paper_id,
            "claim_class": self.claim_class,
            "text": self.text,
        }

    def sort_key(self) -> str:
        return self.claim_id


__all__ = [
    "Claim",
]
