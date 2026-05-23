"""Aufgabe 7 — runtime benchmark for the FRAME_TENSION_LAYER.

Forty cases evenly split across the four ``FrameConsistency``
outcomes. Each case is a deterministic ``(claim_text,
inherited_context_text, expected_consistency)`` triple; the layer
is expected to reach **100% accuracy** on every category.

Pairs were chosen so the v3.4 ``FrameDetector`` fires exactly one
bucket per side (where a single frame is intended) or none
(where ``UNDECIDABLE`` is intended) — so the benchmark verifies
the layer logic without leaning on detector quirks.
"""
from __future__ import annotations

from dataclasses import dataclass

from .consistency import FrameConsistency


@dataclass(frozen=True)
class LayerCase:
    case_id: str
    claim_text: str
    inherited_context_text: str
    expected: FrameConsistency

    def to_dict(self) -> dict[str, str]:
        return {
            "case_id": self.case_id,
            "claim_text": self.claim_text,
            "inherited_context_text": self.inherited_context_text,
            "expected": self.expected.value,
        }


_CONFIRMED: tuple[LayerCase, ...] = (
    LayerCase(
        case_id="CF01",
        claim_text="Heat flow in joules per second drives the engine.",
        inherited_context_text="Frame: thermodynamic",
        expected=FrameConsistency.CONFIRMED,
    ),
    LayerCase(
        case_id="CF02",
        claim_text="Channel capacity in bits per use bounds throughput.",
        inherited_context_text="Frame: information-theoretic",
        expected=FrameConsistency.CONFIRMED,
    ),
    LayerCase(
        case_id="CF03",
        claim_text="Loosely speaking, the city sings like a poet.",
        inherited_context_text="Frame: metaphorical",
        expected=FrameConsistency.CONFIRMED,
    ),
    LayerCase(
        case_id="CF04",
        claim_text="By modus ponens the syllogism is valid.",
        inherited_context_text="Frame: formal logic",
        expected=FrameConsistency.CONFIRMED,
    ),
    LayerCase(
        case_id="CF05",
        claim_text="The minister stated the new policy is final.",
        inherited_context_text="Frame: authority",
        expected=FrameConsistency.CONFIRMED,
    ),
    LayerCase(
        case_id="CF06",
        claim_text="The drought led to widespread crop failure.",
        inherited_context_text="Frame: empirical causal",
        expected=FrameConsistency.CONFIRMED,
    ),
    LayerCase(
        case_id="CF07",
        claim_text="Calculate the sum 12 + 7 carefully.",
        inherited_context_text="Frame: tool computable",
        expected=FrameConsistency.CONFIRMED,
    ),
    LayerCase(
        case_id="CF08",
        claim_text=(
            "Numerically identical objects are indistinguishable in "
            "every property."
        ),
        inherited_context_text="Frame: ontological distinguishability",
        expected=FrameConsistency.CONFIRMED,
    ),
    LayerCase(
        case_id="CF09",
        claim_text="Figuratively, the city breathes like a lung.",
        inherited_context_text="Frame: metaphorical",
        expected=FrameConsistency.CONFIRMED,
    ),
    LayerCase(
        case_id="CF10",
        claim_text="Every x is a y; therefore every x is also z.",
        inherited_context_text="Frame: formal logic",
        expected=FrameConsistency.CONFIRMED,
    ),
)


_TENSION: tuple[LayerCase, ...] = (
    LayerCase(
        case_id="TN01",
        claim_text="Heat flow in joules per second drives the engine.",
        inherited_context_text="Frame: information-theoretic",
        expected=FrameConsistency.TENSION,
    ),
    LayerCase(
        case_id="TN02",
        claim_text="Channel capacity in bits per use bounds throughput.",
        inherited_context_text="Frame: thermodynamic",
        expected=FrameConsistency.TENSION,
    ),
    LayerCase(
        case_id="TN03",
        claim_text="Loosely speaking, the bird sings like a poet.",
        inherited_context_text="Frame: information-theoretic",
        expected=FrameConsistency.TENSION,
    ),
    LayerCase(
        case_id="TN04",
        claim_text="Shannon channel capacity bounds bits per use.",
        inherited_context_text="Frame: metaphorical",
        expected=FrameConsistency.TENSION,
    ),
    LayerCase(
        case_id="TN05",
        claim_text="Heat flow in joules per second matters here.",
        inherited_context_text="Frame: metaphorical",
        expected=FrameConsistency.TENSION,
    ),
    LayerCase(
        case_id="TN06",
        claim_text="Loosely speaking, the river runs like a song.",
        inherited_context_text="Frame: thermodynamic",
        expected=FrameConsistency.TENSION,
    ),
    LayerCase(
        case_id="TN07",
        claim_text="By modus ponens the proof holds without exception.",
        inherited_context_text="Frame: empirical causal",
        expected=FrameConsistency.TENSION,
    ),
    LayerCase(
        case_id="TN08",
        claim_text="The drought led to widespread crop failure.",
        inherited_context_text="Frame: formal logic",
        expected=FrameConsistency.TENSION,
    ),
    LayerCase(
        case_id="TN09",
        claim_text="The minister stated the bridge collapsed yesterday.",
        inherited_context_text="Frame: empirical causal",
        expected=FrameConsistency.TENSION,
    ),
    LayerCase(
        case_id="TN10",
        claim_text="Calculate the sum 12 + 7 carefully.",
        inherited_context_text="Frame: information-theoretic",
        expected=FrameConsistency.TENSION,
    ),
)


_CONFLICT: tuple[LayerCase, ...] = (
    LayerCase(
        case_id="CO01",
        claim_text="By modus ponens the syllogism is valid.",
        inherited_context_text="Frame: tool computable",
        expected=FrameConsistency.CONFLICT,
    ),
    LayerCase(
        case_id="CO02",
        claim_text="Heat flow in joules per second drives the engine.",
        inherited_context_text="Frame: ontological distinguishability",
        expected=FrameConsistency.CONFLICT,
    ),
    LayerCase(
        case_id="CO03",
        claim_text=(
            "Numerically identical objects are indistinguishable."
        ),
        inherited_context_text="Frame: thermodynamic",
        expected=FrameConsistency.CONFLICT,
    ),
    LayerCase(
        case_id="CO04",
        claim_text="By modus ponens the syllogism is valid.",
        inherited_context_text="Frame: authority",
        expected=FrameConsistency.CONFLICT,
    ),
    LayerCase(
        case_id="CO05",
        claim_text="The drought led to widespread crop failure.",
        inherited_context_text="Frame: ontological distinguishability",
        expected=FrameConsistency.CONFLICT,
    ),
    LayerCase(
        case_id="CO06",
        claim_text=(
            "Numerically identical objects are indistinguishable."
        ),
        inherited_context_text="Frame: formal logic",
        expected=FrameConsistency.CONFLICT,
    ),
    LayerCase(
        case_id="CO07",
        claim_text="Calculate the sum 12 + 7 carefully.",
        inherited_context_text="Frame: ontological distinguishability",
        expected=FrameConsistency.CONFLICT,
    ),
    LayerCase(
        case_id="CO08",
        claim_text="The minister stated the new policy is final.",
        inherited_context_text="Frame: tool computable",
        expected=FrameConsistency.CONFLICT,
    ),
    LayerCase(
        case_id="CO09",
        claim_text="Loosely speaking, the bird sings like a poet.",
        inherited_context_text="Frame: formal logic",
        expected=FrameConsistency.CONFLICT,
    ),
    LayerCase(
        case_id="CO10",
        claim_text=(
            "Numerically identical objects are indistinguishable."
        ),
        inherited_context_text="Frame: authority",
        expected=FrameConsistency.CONFLICT,
    ),
)


_UNDECIDABLE: tuple[LayerCase, ...] = (
    LayerCase(
        case_id="UD01",
        claim_text="This sentence has nothing diagnostic in it.",
        inherited_context_text="Frame: thermodynamic",
        expected=FrameConsistency.UNDECIDABLE,
    ),
    LayerCase(
        case_id="UD02",
        claim_text="Heat flow in joules per second drives the engine.",
        inherited_context_text="A bland sentence without frame cues.",
        expected=FrameConsistency.UNDECIDABLE,
    ),
    LayerCase(
        case_id="UD03",
        claim_text="A wholly neutral statement about the weather.",
        inherited_context_text="Another wholly neutral sentence.",
        expected=FrameConsistency.UNDECIDABLE,
    ),
    LayerCase(
        case_id="UD04",
        # "entropy" alone fires both thermo and info buckets with no
        # explicit marker → inner is internally conflicted → UNDECIDABLE.
        claim_text="Entropy increases over time in this regime.",
        inherited_context_text="Frame: information-theoretic",
        expected=FrameConsistency.UNDECIDABLE,
    ),
    LayerCase(
        case_id="UD05",
        claim_text="Channel capacity in bits per use bounds throughput.",
        inherited_context_text="Entropy alone with no disambiguator.",
        expected=FrameConsistency.UNDECIDABLE,
    ),
    LayerCase(
        case_id="UD06",
        claim_text="A bland sentence with no frame cues at all.",
        inherited_context_text="Frame: information-theoretic",
        expected=FrameConsistency.UNDECIDABLE,
    ),
    LayerCase(
        case_id="UD07",
        claim_text="Channel capacity in bits per use bounds throughput.",
        inherited_context_text="Plain text without diagnostic terms.",
        expected=FrameConsistency.UNDECIDABLE,
    ),
    LayerCase(
        case_id="UD08",
        claim_text="A perfectly ordinary sentence.",
        inherited_context_text="Frame: metaphorical",
        expected=FrameConsistency.UNDECIDABLE,
    ),
    LayerCase(
        case_id="UD09",
        claim_text="Loosely speaking, the night was calm.",
        inherited_context_text="An undiagnostic line.",
        expected=FrameConsistency.UNDECIDABLE,
    ),
    LayerCase(
        case_id="UD10",
        # Both sides internally conflicted by "entropy".
        claim_text="Entropy is central here without further detail.",
        inherited_context_text="Entropy is what we discuss below.",
        expected=FrameConsistency.UNDECIDABLE,
    ),
)


ALL_LAYER_CASES: tuple[LayerCase, ...] = (
    _CONFIRMED + _TENSION + _CONFLICT + _UNDECIDABLE
)


__all__ = ["ALL_LAYER_CASES", "LayerCase"]
