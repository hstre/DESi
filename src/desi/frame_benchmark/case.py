"""FrameBenchmarkCase schema — Aufgabe 8."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from ..frames import FrameKind
from ..memory.claim import ClaimState


class FrameCategory(str, Enum):
    A_THERMO_VS_INFO = "A_thermo_vs_info"
    B_METAPHOR_VS_LITERAL = "B_metaphor_vs_literal"
    C_ONTOLOGICAL_DISTINGUISHABILITY = "C_ontological_distinguishability"
    D_AUTHORITY_SPEECH = "D_authority_speech"
    E_TOOL_COMPUTABLE = "E_tool_computable"
    F_FORMAL_LOGIC = "F_formal_logic"
    G_EMPIRICAL_CAUSAL = "G_empirical_causal"
    H_UNDECLARED_OR_CONFLICT = "H_undeclared_or_conflict"


@dataclass(frozen=True)
class FrameBenchmarkCase:
    case_id: str
    category: FrameCategory
    text: str
    expected_frame: FrameKind
    expected_state: ClaimState
    expected_allowed_pipeline: tuple[str, ...]
    expected_blocked_pipeline: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "category": self.category.value,
            "text": self.text,
            "expected_frame": self.expected_frame.value,
            "expected_state": self.expected_state.value,
            "expected_allowed_pipeline":
                list(self.expected_allowed_pipeline),
            "expected_blocked_pipeline":
                list(self.expected_blocked_pipeline),
        }


__all__ = ["FrameBenchmarkCase", "FrameCategory"]
