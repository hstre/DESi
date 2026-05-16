"""10 lookalike paraphrases that should produce a real frame shift —
Aufgabe 7.

The patchability assessor must NOT absorb these. Each carries
``expected_frame`` (what the v3.4 detector should say given the
text) and ``decoy_for_frame`` (the frame the patch candidate is
*trying* to recover).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..frames import FrameKind


@dataclass(frozen=True)
class NegativeControlCase:
    nc_id: str
    text: str
    expected_frame: FrameKind
    decoy_for_frame: FrameKind

    def to_dict(self) -> dict[str, Any]:
        return {
            "nc_id": self.nc_id,
            "text": self.text,
            "expected_frame": self.expected_frame.value,
            "decoy_for_frame": self.decoy_for_frame.value,
        }


NEGATIVE_CONTROLS: tuple[NegativeControlCase, ...] = (
    # Looks like info-theoretic (Shannon entropy in bits) but is
    # actually a metaphorical statement.
    NegativeControlCase(
        nc_id="NC01",
        text=(
            "Like a poet, my brain processes Shannon entropy in bits "
            "of fleeting memory."
        ),
        expected_frame=FrameKind.METAPHORICAL,
        decoy_for_frame=FrameKind.INFORMATION_THEORETIC,
    ),
    # Looks like info-theoretic but is metaphor.
    NegativeControlCase(
        nc_id="NC02",
        text=(
            "Metaphorically, the brain has channel capacity for "
            "Shannon entropy."
        ),
        expected_frame=FrameKind.METAPHORICAL,
        decoy_for_frame=FrameKind.INFORMATION_THEORETIC,
    ),
    # Looks like causal but really authority.
    NegativeControlCase(
        nc_id="NC03",
        text=(
            "The vendor says heavy rainfall causes localised flooding."
        ),
        expected_frame=FrameKind.AUTHORITY_SPEECH,
        decoy_for_frame=FrameKind.EMPIRICAL_CAUSAL,
    ),
    # Looks like causal but really metaphor.
    NegativeControlCase(
        nc_id="NC04",
        text=(
            "Loosely speaking, anxiety led to a heart of stone."
        ),
        expected_frame=FrameKind.METAPHORICAL,
        decoy_for_frame=FrameKind.EMPIRICAL_CAUSAL,
    ),
    # Looks like ontological but really tool-computable.
    NegativeControlCase(
        nc_id="NC05",
        text=(
            "Is the same object 2 + 2 = 4 ?"
        ),
        expected_frame=FrameKind.TOOL_COMPUTABLE,
        decoy_for_frame=FrameKind.ONTOLOGICAL_DISTINGUISHABILITY,
    ),
    # Looks like authority but really tool-computable.
    NegativeControlCase(
        nc_id="NC06",
        text=(
            "Calculate 17 * 23, the professor says nothing."
        ),
        expected_frame=FrameKind.TOOL_COMPUTABLE,
        decoy_for_frame=FrameKind.AUTHORITY_SPEECH,
    ),
    # Looks like info-theoretic with bits but really tool.
    NegativeControlCase(
        nc_id="NC07",
        text=(
            "Compute 8 bits + 4 bits = ? in plain arithmetic."
        ),
        expected_frame=FrameKind.TOOL_COMPUTABLE,
        decoy_for_frame=FrameKind.INFORMATION_THEORETIC,
    ),
    # Looks like causal but really authority chain.
    NegativeControlCase(
        nc_id="NC08",
        text=(
            "According to the auditor, drought resulted in crop failure."
        ),
        expected_frame=FrameKind.AUTHORITY_SPEECH,
        decoy_for_frame=FrameKind.EMPIRICAL_CAUSAL,
    ),
    # Looks like metaphor but is formal logic with marker.
    NegativeControlCase(
        nc_id="NC09",
        text=(
            "Frame: formal logic. Like a syllogism the proof closes."
        ),
        expected_frame=FrameKind.FORMAL_LOGIC,
        decoy_for_frame=FrameKind.METAPHORICAL,
    ),
    # Looks like thermo but is metaphor with explicit marker.
    NegativeControlCase(
        nc_id="NC10",
        text=(
            "Frame: metaphorical. The market's temperature heat is rising."
        ),
        expected_frame=FrameKind.METAPHORICAL,
        decoy_for_frame=FrameKind.THERMODYNAMIC,
    ),
)


__all__ = ["NEGATIVE_CONTROLS", "NegativeControlCase"]
