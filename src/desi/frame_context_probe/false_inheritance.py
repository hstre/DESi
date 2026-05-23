"""Aufgabe 6 — false-inheritance probe.

Ten fixture cases where the **outer context layers lie**: section
header or document frame point at one frame, but the sentence
itself belongs to a different frame. A naïve context-inheritance
mechanism will silently absorb the wrong frame; the probe records
both the would-be inherited frame and the ground-truth frame so
the gap is measurable.

These are deliberately *mixed* — they are not failures of the
v3.4 detector. They are stress-tests for the **inheritance
hypothesis** itself.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..frames import FrameKind
from .extractor import ContextWindow
from .inheritance import InheritanceResult, simulate


@dataclass(frozen=True)
class FalseInheritanceCase:
    case_id: str
    text: str
    misleading_window: ContextWindow
    misleading_frame: FrameKind   # what naïve inheritance would yield
    ground_truth_frame: FrameKind  # what the sentence actually is
    note: str


NEGATIVE_CONTROLS: tuple[FalseInheritanceCase, ...] = (
    FalseInheritanceCase(
        case_id="FN01",
        text="The poet's entropy in bits is a delicate thing.",
        misleading_window=ContextWindow(
            ctx_0="The poet's entropy in bits is a delicate thing.",
            ctx_1="Channel capacity is measured in bits per use.",
            ctx_2="Section: Information Theory — Coding and Bits",
            ctx_3="Frame: information-theoretic",
        ),
        misleading_frame=FrameKind.INFORMATION_THEORETIC,
        ground_truth_frame=FrameKind.METAPHORICAL,
        note=(
            "Document frame says info-theoretic; sentence is plainly "
            "metaphorical."
        ),
    ),
    FalseInheritanceCase(
        case_id="FN02",
        text=(
            "Mutual information about the lover's heart suggests new "
            "entropy bounds."
        ),
        misleading_window=ContextWindow(
            ctx_0=(
                "Mutual information about the lover's heart suggests "
                "new entropy bounds."
            ),
            ctx_1="Channel capacity is measured in bits per use.",
            ctx_2="Section: Information Theory — Coding and Bits",
            ctx_3="Frame: information-theoretic",
        ),
        misleading_frame=FrameKind.INFORMATION_THEORETIC,
        ground_truth_frame=FrameKind.METAPHORICAL,
        note=(
            "Domain tokens are info-theoretic but the referent is "
            "the lover's heart."
        ),
    ),
    FalseInheritanceCase(
        case_id="FN03",
        text="Entropy of an isolated system never decreases.",
        misleading_window=ContextWindow(
            ctx_0="Entropy of an isolated system never decreases.",
            ctx_1="Channel capacity is measured in bits per use.",
            ctx_2="Section: Information Theory — Coding and Bits",
            ctx_3="Frame: information-theoretic",
        ),
        misleading_frame=FrameKind.INFORMATION_THEORETIC,
        ground_truth_frame=FrameKind.THERMODYNAMIC,
        note=(
            "Thermodynamic 2nd-law statement embedded in an "
            "information-theoretic section."
        ),
    ),
    FalseInheritanceCase(
        case_id="FN04",
        text="The Shannon entropy of a fair coin is exactly one bit.",
        misleading_window=ContextWindow(
            ctx_0=(
                "The Shannon entropy of a fair coin is exactly one bit."
            ),
            ctx_1="We measure heat flow in joules per second.",
            ctx_2="Section: Thermodynamics — Heat and Energy",
            ctx_3="Frame: thermodynamic",
        ),
        misleading_frame=FrameKind.THERMODYNAMIC,
        ground_truth_frame=FrameKind.INFORMATION_THEORETIC,
        note=(
            "Information-theoretic claim embedded in a thermo "
            "section."
        ),
    ),
    FalseInheritanceCase(
        case_id="FN05",
        text="Heat flows from hot to cold by the second law.",
        misleading_window=ContextWindow(
            ctx_0="Heat flows from hot to cold by the second law.",
            ctx_1="We will speak loosely in the next paragraph.",
            ctx_2="Section: Rhetorical Devices — Metaphor and Simile",
            ctx_3="Frame: metaphorical",
        ),
        misleading_frame=FrameKind.METAPHORICAL,
        ground_truth_frame=FrameKind.THERMODYNAMIC,
        note=(
            "Plain physical law inside a rhetorical-devices section."
        ),
    ),
    FalseInheritanceCase(
        case_id="FN06",
        text=(
            "Her smile carried an entropy of a fair coin, exactly "
            "one bit."
        ),
        misleading_window=ContextWindow(
            ctx_0=(
                "Her smile carried an entropy of a fair coin, exactly "
                "one bit."
            ),
            ctx_1="Channel capacity is measured in bits per use.",
            ctx_2="Section: Information Theory — Coding and Bits",
            ctx_3="Frame: information-theoretic",
        ),
        misleading_frame=FrameKind.INFORMATION_THEORETIC,
        ground_truth_frame=FrameKind.METAPHORICAL,
        note=(
            "Info-theoretic surface form attached to a poetic "
            "subject (smile)."
        ),
    ),
    FalseInheritanceCase(
        case_id="FN07",
        text="All swans are white; therefore the next swan is white.",
        misleading_window=ContextWindow(
            ctx_0=(
                "All swans are white; therefore the next swan is white."
            ),
            ctx_1="We catalogue observed cause-effect chains.",
            ctx_2="Section: Empirical Causality — Cause and Effect",
            ctx_3="Frame: empirical causal",
        ),
        misleading_frame=FrameKind.EMPIRICAL_CAUSAL,
        ground_truth_frame=FrameKind.FORMAL_LOGIC,
        note=(
            "Formal-logic universal-instantiation pattern dropped "
            "into an empirical section."
        ),
    ),
    FalseInheritanceCase(
        case_id="FN08",
        text="The minister stated that the bill will reduce inflation.",
        misleading_window=ContextWindow(
            ctx_0=(
                "The minister stated that the bill will reduce "
                "inflation."
            ),
            ctx_1="We catalogue observed cause-effect chains.",
            ctx_2="Section: Empirical Causality — Cause and Effect",
            ctx_3="Frame: empirical causal",
        ),
        misleading_frame=FrameKind.EMPIRICAL_CAUSAL,
        ground_truth_frame=FrameKind.AUTHORITY_SPEECH,
        note=(
            "Reported-speech act dressed up as an empirical claim."
        ),
    ),
    FalseInheritanceCase(
        case_id="FN09",
        text="Compute the entropy of a fair die in nats.",
        misleading_window=ContextWindow(
            ctx_0="Compute the entropy of a fair die in nats.",
            ctx_1="The following report is a third-party statement.",
            ctx_2="Section: Speech Acts — Reported Statements",
            ctx_3="Frame: authority",
        ),
        misleading_frame=FrameKind.AUTHORITY_SPEECH,
        ground_truth_frame=FrameKind.TOOL_COMPUTABLE,
        note=(
            "Compute-imperative wrapped in an authority-speech "
            "section."
        ),
    ),
    FalseInheritanceCase(
        case_id="FN10",
        text="The morning star is the evening star.",
        misleading_window=ContextWindow(
            ctx_0="The morning star is the evening star.",
            ctx_1="We measure heat flow in joules per second.",
            ctx_2="Section: Thermodynamics — Heat and Energy",
            ctx_3="Frame: thermodynamic",
        ),
        misleading_frame=FrameKind.THERMODYNAMIC,
        ground_truth_frame=FrameKind.ONTOLOGICAL_DISTINGUISHABILITY,
        note=(
            "Frege's identity statement filed under thermodynamics."
        ),
    ),
)


@dataclass(frozen=True)
class FalseInheritanceOutcome:
    case_id: str
    inheritance: InheritanceResult
    ground_truth_frame: FrameKind
    misleading_frame: FrameKind

    @property
    def absorbed_misleading_frame(self) -> bool:
        """Did naïve inheritance silently take the misleading frame?"""
        return self.inheritance.inherited_frame is self.misleading_frame

    @property
    def correct_against_ground_truth(self) -> bool:
        return (
            self.inheritance.inherited_frame is self.ground_truth_frame
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "case_id": self.case_id,
            "ground_truth_frame": self.ground_truth_frame.value,
            "misleading_frame": self.misleading_frame.value,
            "inheritance": self.inheritance.to_dict(),
            "absorbed_misleading_frame": self.absorbed_misleading_frame,
            "correct_against_ground_truth": (
                self.correct_against_ground_truth
            ),
        }


def run_false_inheritance() -> tuple[FalseInheritanceOutcome, ...]:
    out: list[FalseInheritanceOutcome] = []
    for nc in NEGATIVE_CONTROLS:
        res = simulate(
            window=nc.misleading_window,
            case_id=f"fn:{nc.case_id}",
            expected_frame=nc.ground_truth_frame,
        )
        out.append(FalseInheritanceOutcome(
            case_id=nc.case_id,
            inheritance=res,
            ground_truth_frame=nc.ground_truth_frame,
            misleading_frame=nc.misleading_frame,
        ))
    return tuple(out)


__all__ = [
    "FalseInheritanceCase",
    "FalseInheritanceOutcome",
    "NEGATIVE_CONTROLS",
    "run_false_inheritance",
]
