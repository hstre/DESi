"""Aufgabe 7 — adversarial manipulation set.

Twenty hand-crafted cases where the outer context **deliberately**
tries to recategorise an inner sentence into a frame it does not
belong to. The probe should detect the inconsistency rather than
silently inherit the outer label.

Each fixture carries the misleading outer plus the inner sentence
that genuinely belongs to another frame. Detection means the
classifier returns either ``FRAME_TENSION`` or ``FRAME_CONFLICT``
(never ``FRAME_CONFIRMED``).
"""
from __future__ import annotations

from dataclasses import dataclass

from ..frames import FrameKind
from .consistency import classify
from .enums import FrameConsistency
from .inner_extractor import extract_inner_frame
from .outer_extractor import extract_outer_frame


@dataclass(frozen=True)
class ManipulationCase:
    case_id: str
    text: str
    ctx_1: str
    ctx_2: str
    ctx_3: str
    misleading_outer: FrameKind
    true_inner: FrameKind

    def to_dict(self) -> dict[str, object]:
        return {
            "case_id": self.case_id,
            "text": self.text,
            "ctx_1": self.ctx_1,
            "ctx_2": self.ctx_2,
            "ctx_3": self.ctx_3,
            "misleading_outer": self.misleading_outer.value,
            "true_inner": self.true_inner.value,
        }


MANIPULATIONS: tuple[ManipulationCase, ...] = (
    ManipulationCase(
        case_id="M01",
        text="Shannon entropy of the message distribution is one bit.",
        ctx_1="We measure heat flow in joules per second.",
        ctx_2="Section: Thermodynamics — Heat and Energy",
        ctx_3="Frame: thermodynamic",
        misleading_outer=FrameKind.THERMODYNAMIC,
        true_inner=FrameKind.INFORMATION_THEORETIC,
    ),
    ManipulationCase(
        case_id="M02",
        text="The market is nervous about next quarter.",
        ctx_1="All inferences obey modus ponens here.",
        ctx_2="Section: Formal Logic — Proof Theory",
        ctx_3="Frame: formal logic",
        misleading_outer=FrameKind.FORMAL_LOGIC,
        true_inner=FrameKind.METAPHORICAL,
    ),
    ManipulationCase(
        case_id="M03",
        text="Justice cannot be measured.",
        ctx_1="The following question expects a numerical answer.",
        ctx_2="Section: Computation — Arithmetic and Dates",
        ctx_3="Frame: tool computable",
        misleading_outer=FrameKind.TOOL_COMPUTABLE,
        true_inner=FrameKind.METAPHORICAL,
    ),
    ManipulationCase(
        case_id="M04",
        text="Heat flow in joules per second drives the engine.",
        ctx_1="Channel capacity is measured in bits per use.",
        ctx_2="Section: Information Theory — Coding and Bits",
        ctx_3="Frame: information-theoretic",
        misleading_outer=FrameKind.INFORMATION_THEORETIC,
        true_inner=FrameKind.THERMODYNAMIC,
    ),
    ManipulationCase(
        case_id="M05",
        text="The minister stated the bridge collapsed yesterday.",
        ctx_1="We catalogue observed cause-effect chains.",
        ctx_2="Section: Empirical Causality — Cause and Effect",
        ctx_3="Frame: empirical causal",
        misleading_outer=FrameKind.EMPIRICAL_CAUSAL,
        true_inner=FrameKind.AUTHORITY_SPEECH,
    ),
    ManipulationCase(
        case_id="M06",
        text=(
            "Every raven observed has been black; therefore the next "
            "raven observed is black by universal instantiation."
        ),
        ctx_1="We catalogue observed cause-effect chains.",
        ctx_2="Section: Empirical Causality — Cause and Effect",
        ctx_3="Frame: empirical causal",
        misleading_outer=FrameKind.EMPIRICAL_CAUSAL,
        true_inner=FrameKind.FORMAL_LOGIC,
    ),
    ManipulationCase(
        case_id="M07",
        text=(
            "Hesperus and Phosphorus name the same celestial body "
            "as an identity statement."
        ),
        ctx_1="We measure heat flow in joules per second.",
        ctx_2="Section: Thermodynamics — Heat and Energy",
        ctx_3="Frame: thermodynamic",
        misleading_outer=FrameKind.THERMODYNAMIC,
        true_inner=FrameKind.ONTOLOGICAL_DISTINGUISHABILITY,
    ),
    ManipulationCase(
        case_id="M08",
        text="The poet's smile, like a delicate flame.",
        ctx_1="All inferences obey modus ponens here.",
        ctx_2="Section: Formal Logic — Proof Theory",
        ctx_3="Frame: formal logic",
        misleading_outer=FrameKind.FORMAL_LOGIC,
        true_inner=FrameKind.METAPHORICAL,
    ),
    ManipulationCase(
        case_id="M09",
        text=(
            "Please compute the Shannon entropy of a biased coin "
            "with p=0.3 in nats for me."
        ),
        ctx_1="The following report is a third-party statement.",
        ctx_2="Section: Speech Acts — Reported Statements",
        ctx_3="Frame: authority",
        misleading_outer=FrameKind.AUTHORITY_SPEECH,
        true_inner=FrameKind.TOOL_COMPUTABLE,
    ),
    ManipulationCase(
        case_id="M10",
        text=(
            "A loaded coin's Shannon entropy in bits drops as the "
            "bias grows toward unity."
        ),
        ctx_1="We measure heat flow in joules per second.",
        ctx_2="Section: Thermodynamics — Heat and Energy",
        ctx_3="Frame: thermodynamic",
        misleading_outer=FrameKind.THERMODYNAMIC,
        true_inner=FrameKind.INFORMATION_THEORETIC,
    ),
    ManipulationCase(
        case_id="M11",
        text="According to the report, inflation will fall.",
        ctx_1="The following question expects a numerical answer.",
        ctx_2="Section: Computation — Arithmetic and Dates",
        ctx_3="Frame: tool computable",
        misleading_outer=FrameKind.TOOL_COMPUTABLE,
        true_inner=FrameKind.AUTHORITY_SPEECH,
    ),
    ManipulationCase(
        case_id="M12",
        text="Hope is a thing with feathers, like a small bird.",
        ctx_1="The following question expects a numerical answer.",
        ctx_2="Section: Computation — Arithmetic and Dates",
        ctx_3="Frame: tool computable",
        misleading_outer=FrameKind.TOOL_COMPUTABLE,
        true_inner=FrameKind.METAPHORICAL,
    ),
    ManipulationCase(
        case_id="M13",
        text="The lemma reduces by modus ponens to a theorem.",
        ctx_1="The following report is a third-party statement.",
        ctx_2="Section: Speech Acts — Reported Statements",
        ctx_3="Frame: authority",
        misleading_outer=FrameKind.AUTHORITY_SPEECH,
        true_inner=FrameKind.FORMAL_LOGIC,
    ),
    ManipulationCase(
        case_id="M14",
        text="Heat flow from hot to cold drives the cycle.",
        ctx_1="Identity statements concern referential sameness.",
        ctx_2="Section: Ontology — Identity and Reference",
        ctx_3="Frame: ontological distinguishability",
        misleading_outer=FrameKind.ONTOLOGICAL_DISTINGUISHABILITY,
        true_inner=FrameKind.THERMODYNAMIC,
    ),
    ManipulationCase(
        case_id="M15",
        text=(
            "The mutual information of two coupled channels obeys "
            "Shannon's symmetry constraint."
        ),
        ctx_1="The following report is a third-party statement.",
        ctx_2="Section: Speech Acts — Reported Statements",
        ctx_3="Frame: authority",
        misleading_outer=FrameKind.AUTHORITY_SPEECH,
        true_inner=FrameKind.INFORMATION_THEORETIC,
    ),
    ManipulationCase(
        case_id="M16",
        text="The minister stated the new policy starts in March.",
        ctx_1="We will speak loosely in the next paragraph.",
        ctx_2="Section: Rhetorical Devices — Metaphor and Simile",
        ctx_3="Frame: metaphorical",
        misleading_outer=FrameKind.METAPHORICAL,
        true_inner=FrameKind.AUTHORITY_SPEECH,
    ),
    ManipulationCase(
        case_id="M17",
        text="The poet's smile is like a small flame.",
        ctx_1="We catalogue observed cause-effect chains.",
        ctx_2="Section: Empirical Causality — Cause and Effect",
        ctx_3="Frame: empirical causal",
        misleading_outer=FrameKind.EMPIRICAL_CAUSAL,
        true_inner=FrameKind.METAPHORICAL,
    ),
    ManipulationCase(
        case_id="M18",
        text="The axiom yields the theorem by universal instantiation.",
        ctx_1="Channel capacity is measured in bits per use.",
        ctx_2="Section: Information Theory — Coding and Bits",
        ctx_3="Frame: information-theoretic",
        misleading_outer=FrameKind.INFORMATION_THEORETIC,
        true_inner=FrameKind.FORMAL_LOGIC,
    ),
    ManipulationCase(
        case_id="M19",
        text="Calculate the area of a circle with radius five.",
        ctx_1="We will speak loosely in the next paragraph.",
        ctx_2="Section: Rhetorical Devices — Metaphor and Simile",
        ctx_3="Frame: metaphorical",
        misleading_outer=FrameKind.METAPHORICAL,
        true_inner=FrameKind.TOOL_COMPUTABLE,
    ),
    ManipulationCase(
        case_id="M20",
        text="The morning star is identical to the evening star.",
        ctx_1="Channel capacity is measured in bits per use.",
        ctx_2="Section: Information Theory — Coding and Bits",
        ctx_3="Frame: information-theoretic",
        misleading_outer=FrameKind.INFORMATION_THEORETIC,
        true_inner=FrameKind.ONTOLOGICAL_DISTINGUISHABILITY,
    ),
)


@dataclass(frozen=True)
class ManipulationOutcome:
    case_id: str
    detected_inner: FrameKind | None
    detected_outer: FrameKind | None
    classification: FrameConsistency
    misleading_outer: FrameKind
    true_inner: FrameKind

    @property
    def detected_manipulation(self) -> bool:
        # Detection = the classifier did NOT silently confirm the
        # outer reading. FRAME_CONFIRMED on a manipulation fixture
        # is the failure mode the probe is built to catch.
        return self.classification is not FrameConsistency.FRAME_CONFIRMED

    def to_dict(self) -> dict[str, object]:
        return {
            "case_id": self.case_id,
            "detected_inner": (
                self.detected_inner.value if self.detected_inner else None
            ),
            "detected_outer": (
                self.detected_outer.value if self.detected_outer else None
            ),
            "classification": self.classification.value,
            "misleading_outer": self.misleading_outer.value,
            "true_inner": self.true_inner.value,
            "detected_manipulation": self.detected_manipulation,
        }


def run_manipulation_suite() -> tuple[ManipulationOutcome, ...]:
    out: list[ManipulationOutcome] = []
    for m in MANIPULATIONS:
        inner = extract_inner_frame(m.text)
        outer = extract_outer_frame(m.ctx_1, m.ctx_2, m.ctx_3).frame
        cls = classify(inner, outer)
        out.append(ManipulationOutcome(
            case_id=m.case_id,
            detected_inner=inner,
            detected_outer=outer,
            classification=cls,
            misleading_outer=m.misleading_outer,
            true_inner=m.true_inner,
        ))
    return tuple(out)


def manipulation_detection_rate(
    outcomes: tuple[ManipulationOutcome, ...]
) -> float:
    if not outcomes:
        return 0.0
    detected = sum(1 for o in outcomes if o.detected_manipulation)
    return round(detected / len(outcomes), 6)


__all__ = [
    "MANIPULATIONS",
    "ManipulationCase",
    "ManipulationOutcome",
    "manipulation_detection_rate",
    "run_manipulation_suite",
]
