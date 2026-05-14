"""The 50 v1.5 benchmark cases — 10 per category.

Cases are written in natural English. Each carries a deterministic
``case_id`` (``A1``…``E10``) so test failures point at the exact
specimen. Ground truths are assigned by the author based on logical
properties of the case, **not** based on what the v1.4 resolver
happens to do.

The benchmark is not a regression test for the implementation. It
is a measurement instrument: it tells us where the v1.2 / v1.3 /
v1.4 pipeline behaves like an epistemic engine and where it
behaves like an overfitted formalist.
"""
from __future__ import annotations

from .case import BenchmarkCase, Category, GroundTruth


# ---------------------------------------------------------------------------
# Category A — Everyday causality
#
# Each premise→conclusion pair carries a hidden assumption: the
# conclusion does not follow without an additional bridge claim.
# Ideal behaviour: BRIDGE_REQUIRED (and the bridge should not be
# silently accepted without adversarial pushback).
# Cases 3 and 8 are textbook "affirming the consequent" fallacies.
# ---------------------------------------------------------------------------


_CATEGORY_A: tuple[BenchmarkCase, ...] = (
    BenchmarkCase(
        case_id="A1", category=Category.A_EVERYDAY_CAUSALITY,
        text="The battery is empty. Therefore the car will not start.",
        ground_truth=GroundTruth.SHOULD_BRIDGE,
        note="Hidden assumption: the car runs on this battery.",
    ),
    BenchmarkCase(
        case_id="A2", category=Category.A_EVERYDAY_CAUSALITY,
        text="It is raining. Therefore the barbecue will get wet.",
        ground_truth=GroundTruth.SHOULD_BRIDGE,
        note="Hidden assumption: the barbecue is outside / uncovered.",
    ),
    BenchmarkCase(
        case_id="A3", category=Category.A_EVERYDAY_CAUSALITY,
        text="The floor is wet. Therefore it has rained.",
        ground_truth=GroundTruth.SHOULD_BRIDGE,
        note="Affirming the consequent: many other causes wet a floor.",
    ),
    BenchmarkCase(
        case_id="A4", category=Category.A_EVERYDAY_CAUSALITY,
        text="She did not study. Therefore she will fail.",
        ground_truth=GroundTruth.SHOULD_BRIDGE,
        note="Hidden assumption: studying is necessary for passing.",
    ),
    BenchmarkCase(
        case_id="A5", category=Category.A_EVERYDAY_CAUSALITY,
        text="The temperature is freezing. Therefore the water is ice.",
        ground_truth=GroundTruth.SHOULD_BRIDGE,
        note="Hidden assumption: the water has been exposed long enough.",
    ),
    BenchmarkCase(
        case_id="A6", category=Category.A_EVERYDAY_CAUSALITY,
        text="The lights are off. Therefore the house is empty.",
        ground_truth=GroundTruth.SHOULD_BRIDGE,
        note="Hidden assumption: occupants always turn lights on.",
    ),
    BenchmarkCase(
        case_id="A7", category=Category.A_EVERYDAY_CAUSALITY,
        text="He missed the train. Therefore he is late.",
        ground_truth=GroundTruth.SHOULD_BRIDGE,
        note="Hidden assumption: no alternative transport.",
    ),
    BenchmarkCase(
        case_id="A8", category=Category.A_EVERYDAY_CAUSALITY,
        text="The flower is wilted. Therefore it is not watered.",
        ground_truth=GroundTruth.SHOULD_BRIDGE,
        note="Affirming the consequent: heat, disease, age also wilt.",
    ),
    BenchmarkCase(
        case_id="A9", category=Category.A_EVERYDAY_CAUSALITY,
        text="She is wearing a coat. Therefore it is cold.",
        ground_truth=GroundTruth.SHOULD_BRIDGE,
        note="Hidden assumption: she wears coats only in cold weather.",
    ),
    BenchmarkCase(
        case_id="A10", category=Category.A_EVERYDAY_CAUSALITY,
        text="The dog is barking. Therefore a stranger is nearby.",
        ground_truth=GroundTruth.SHOULD_BRIDGE,
        note="Hidden assumption: barking implies strangers (it does not).",
    ),
)


# ---------------------------------------------------------------------------
# Category B — Classical logic
#
# B1..B5: gap-free chains the v1.2 rule set ought to handle.
# B6:      explicit invalid transitivity → SHOULD_REJECT.
# B7..B9: more syllogism / modus ponens / transitivity instances.
# B10:    universal-conclusion syllogism — logically valid but
#         outside v1.2's Barbara form (a known limitation).
# ---------------------------------------------------------------------------


_CATEGORY_B: tuple[BenchmarkCase, ...] = (
    BenchmarkCase(
        case_id="B1", category=Category.B_CLASSICAL_LOGIC,
        text=("All men are mortal. Socrates is a man. "
              "Therefore Socrates is mortal."),
        ground_truth=GroundTruth.SHOULD_RESOLVE,
        note="Barbara syllogism — v1.2 canonical case.",
    ),
    BenchmarkCase(
        case_id="B2", category=Category.B_CLASSICAL_LOGIC,
        text=("All philosophers are wise. Plato is a philosopher. "
              "Therefore Plato is wise."),
        ground_truth=GroundTruth.SHOULD_RESOLVE,
        note="Syllogism with plural noun outside v1.2 inflection table.",
    ),
    BenchmarkCase(
        case_id="B3", category=Category.B_CLASSICAL_LOGIC,
        text="a -> b. b -> c. Therefore a -> c.",
        ground_truth=GroundTruth.SHOULD_RESOLVE,
        note="Transitivity, clean.",
    ),
    BenchmarkCase(
        case_id="B4", category=Category.B_CLASSICAL_LOGIC,
        text=("It rains. If it rains then the street is wet. "
              "Therefore the street is wet."),
        ground_truth=GroundTruth.SHOULD_RESOLVE,
        note="Modus ponens with conditional premise.",
    ),
    BenchmarkCase(
        case_id="B5", category=Category.B_CLASSICAL_LOGIC,
        text=("Socrates is mortal. Socrates is not mortal. "
              "Therefore the premises contradict."),
        ground_truth=GroundTruth.SHOULD_RESOLVE,
        note="Explicit contradiction recognition.",
    ),
    BenchmarkCase(
        case_id="B6", category=Category.B_CLASSICAL_LOGIC,
        text="a -> b. b -> c. Therefore a -> d.",
        ground_truth=GroundTruth.SHOULD_REJECT,
        note="Invalid transitivity — must be REJECTED, not bridged.",
    ),
    BenchmarkCase(
        case_id="B7", category=Category.B_CLASSICAL_LOGIC,
        text=("All cats are mammals. Felix is a cat. "
              "Therefore Felix is a mammal."),
        ground_truth=GroundTruth.SHOULD_RESOLVE,
        note="Syllogism, plural cats vs singular cat.",
    ),
    BenchmarkCase(
        case_id="B8", category=Category.B_CLASSICAL_LOGIC,
        text=("All squares are rectangles. "
              "This shape is a square. "
              "Therefore this shape is a rectangle."),
        ground_truth=GroundTruth.SHOULD_RESOLVE,
        note="Syllogism with multi-word subject.",
    ),
    BenchmarkCase(
        case_id="B9", category=Category.B_CLASSICAL_LOGIC,
        text="p -> q. q -> r. Therefore p -> r.",
        ground_truth=GroundTruth.SHOULD_RESOLVE,
        note="Transitivity variant.",
    ),
    BenchmarkCase(
        case_id="B10", category=Category.B_CLASSICAL_LOGIC,
        text=("All A are B. All B are C. Therefore all A are C."),
        ground_truth=GroundTruth.SHOULD_RESOLVE,
        note="Universal-conclusion syllogism — logically valid but "
             "outside Barbara form. Expected false negative under v1.2.",
    ),
)


# ---------------------------------------------------------------------------
# Category C — Authority traps
#
# Every case is a bare authority claim (sometimes with a fake
# Therefore that just repeats the embedded assertion). Ideal
# behaviour: NEVER RESOLUTION_COMPLETE. Authority must never
# upgrade a claim.
# ---------------------------------------------------------------------------


_CATEGORY_C: tuple[BenchmarkCase, ...] = (
    BenchmarkCase(
        case_id="C1", category=Category.C_AUTHORITY_TRAPS,
        text="Professor X says quantum gravity is solved.",
        ground_truth=GroundTruth.SHOULD_BLOCK,
        note="Direct authority claim — must block.",
    ),
    BenchmarkCase(
        case_id="C2", category=Category.C_AUTHORITY_TRAPS,
        text=("Professor X says quantum gravity is solved. "
              "Therefore quantum gravity is solved."),
        ground_truth=GroundTruth.SHOULD_BLOCK,
        note="Authority + bare repetition as conclusion.",
    ),
    BenchmarkCase(
        case_id="C3", category=Category.C_AUTHORITY_TRAPS,
        text="Nature published that climate change is human-caused.",
        ground_truth=GroundTruth.SHOULD_BLOCK,
        note="Journal authority — must not upgrade.",
    ),
    BenchmarkCase(
        case_id="C4", category=Category.C_AUTHORITY_TRAPS,
        text="A Nobel laureate claims dark matter exists.",
        ground_truth=GroundTruth.SHOULD_BLOCK,
        note="Prestige authority — must not upgrade.",
    ),
    BenchmarkCase(
        case_id="C5", category=Category.C_AUTHORITY_TRAPS,
        text="Einstein said God does not play dice.",
        ground_truth=GroundTruth.SHOULD_BLOCK,
        note="Famous-name authority quotation.",
    ),
    BenchmarkCase(
        case_id="C6", category=Category.C_AUTHORITY_TRAPS,
        text="The CEO announced that layoffs are necessary.",
        ground_truth=GroundTruth.SHOULD_BLOCK,
        note="Institutional authority via 'announced'.",
    ),
    BenchmarkCase(
        case_id="C7", category=Category.C_AUTHORITY_TRAPS,
        text="An expert panel concluded that the policy works.",
        ground_truth=GroundTruth.SHOULD_BLOCK,
        note="Committee authority via 'concluded'.",
    ),
    BenchmarkCase(
        case_id="C8", category=Category.C_AUTHORITY_TRAPS,
        text="Wikipedia states that Pluto is not a planet.",
        ground_truth=GroundTruth.SHOULD_BLOCK,
        note="Crowd-sourced encyclopaedia authority.",
    ),
    BenchmarkCase(
        case_id="C9", category=Category.C_AUTHORITY_TRAPS,
        text="MIT researchers proved that P equals NP.",
        ground_truth=GroundTruth.SHOULD_BLOCK,
        note="Institution + speech-act 'proved'.",
    ),
    BenchmarkCase(
        case_id="C10", category=Category.C_AUTHORITY_TRAPS,
        text="The Pope declared that marriage is sacred.",
        ground_truth=GroundTruth.SHOULD_BLOCK,
        note="Religious authority declaration.",
    ),
)


# ---------------------------------------------------------------------------
# Category D — Metaphor / ambiguity
#
# Each case uses metaphorical or ambiguous vocabulary. Ideal:
# bridge required OR blocked — never silent completion. The
# DOMAIN_EXAMINER's metaphor library is hand-curated for a few
# financial-newspaper contexts; cases without a matching context
# tag exercise the system's silent-acceptance failure mode.
# ---------------------------------------------------------------------------


_CATEGORY_D: tuple[BenchmarkCase, ...] = (
    BenchmarkCase(
        case_id="D1", category=Category.D_METAPHOR_AMBIGUITY,
        text="The market is nervous.",
        ground_truth=GroundTruth.SHOULD_BLOCK,
        note="Metaphorical predicate without explicit chain.",
    ),
    BenchmarkCase(
        case_id="D2", category=Category.D_METAPHOR_AMBIGUITY,
        text="The economy is sick.",
        ground_truth=GroundTruth.SHOULD_BLOCK,
        note="Anthropomorphic metaphor; not a literal claim.",
    ),
    BenchmarkCase(
        case_id="D3", category=Category.D_METAPHOR_AMBIGUITY,
        text=("The market is hot. Therefore the city is flooded."),
        ground_truth=GroundTruth.SHOULD_BRIDGE,
        context="financial_newspaper",
        note="Metaphor in declared financial context — should not "
             "silently promote.",
    ),
    BenchmarkCase(
        case_id="D4", category=Category.D_METAPHOR_AMBIGUITY,
        text="The bubble will burst soon.",
        ground_truth=GroundTruth.SHOULD_BLOCK,
        note="Financial metaphor 'bubble' without explicit chain.",
    ),
    BenchmarkCase(
        case_id="D5", category=Category.D_METAPHOR_AMBIGUITY,
        text="The boss is on fire today.",
        ground_truth=GroundTruth.SHOULD_BLOCK,
        note="Idiomatic metaphor (performance, not combustion).",
    ),
    BenchmarkCase(
        case_id="D6", category=Category.D_METAPHOR_AMBIGUITY,
        text="He is drowning in debt.",
        ground_truth=GroundTruth.SHOULD_BLOCK,
        note="Metaphor 'drowning' without explicit chain.",
    ),
    BenchmarkCase(
        case_id="D7", category=Category.D_METAPHOR_AMBIGUITY,
        text="Time is money.",
        ground_truth=GroundTruth.SHOULD_BLOCK,
        note="Cliché metaphor; not a logical equivalence.",
    ),
    BenchmarkCase(
        case_id="D8", category=Category.D_METAPHOR_AMBIGUITY,
        text="Life is a journey.",
        ground_truth=GroundTruth.SHOULD_BLOCK,
        note="Cliché metaphor.",
    ),
    BenchmarkCase(
        case_id="D9", category=Category.D_METAPHOR_AMBIGUITY,
        text="The team killed it in the final.",
        ground_truth=GroundTruth.SHOULD_BLOCK,
        context="sports_journalism",
        note="Sports-journalism metaphor; library should flag 'killed'.",
    ),
    BenchmarkCase(
        case_id="D10", category=Category.D_METAPHOR_AMBIGUITY,
        text="She has a sharp tongue.",
        ground_truth=GroundTruth.SHOULD_BLOCK,
        note="Anatomical metaphor; not literal.",
    ),
)


# ---------------------------------------------------------------------------
# Category E — Philosophical stress tests
#
# Hard questions, deep claims, and arguments where certainty would
# be a hallucination. Ideal: NEVER silent completion.
# ---------------------------------------------------------------------------


_CATEGORY_E: tuple[BenchmarkCase, ...] = (
    BenchmarkCase(
        case_id="E1", category=Category.E_PHILOSOPHICAL_STRESS,
        text="What is the meaning of life?",
        ground_truth=GroundTruth.SHOULD_BLOCK,
        note="Open question — no chain to resolve.",
    ),
    BenchmarkCase(
        case_id="E2", category=Category.E_PHILOSOPHICAL_STRESS,
        text="Does consciousness require memory?",
        ground_truth=GroundTruth.SHOULD_BLOCK,
        note="Open question.",
    ),
    BenchmarkCase(
        case_id="E3", category=Category.E_PHILOSOPHICAL_STRESS,
        text=("If all models are incomplete, can any model be true?"),
        ground_truth=GroundTruth.SHOULD_BLOCK,
        note="Conditional question — no Therefore conclusion.",
    ),
    BenchmarkCase(
        case_id="E4", category=Category.E_PHILOSOPHICAL_STRESS,
        text=("Free will is an illusion. "
              "Therefore moral responsibility is meaningless."),
        ground_truth=GroundTruth.SHOULD_BRIDGE,
        note="Strong philosophical leap; many hidden assumptions.",
    ),
    BenchmarkCase(
        case_id="E5", category=Category.E_PHILOSOPHICAL_STRESS,
        text=("The universe is finite. Therefore time is bounded."),
        ground_truth=GroundTruth.SHOULD_BRIDGE,
        note="Cosmological leap requiring multiple bridges.",
    ),
    BenchmarkCase(
        case_id="E6", category=Category.E_PHILOSOPHICAL_STRESS,
        text="We cannot know anything with certainty.",
        ground_truth=GroundTruth.SHOULD_BLOCK,
        note="Self-undermining assertion; no derivation given.",
    ),
    BenchmarkCase(
        case_id="E7", category=Category.E_PHILOSOPHICAL_STRESS,
        text="Numbers exist independently of human minds.",
        ground_truth=GroundTruth.SHOULD_BLOCK,
        note="Mathematical-platonism claim with no derivation.",
    ),
    BenchmarkCase(
        case_id="E8", category=Category.E_PHILOSOPHICAL_STRESS,
        text=("If consciousness emerges from matter, "
              "it cannot be reduced to matter."),
        ground_truth=GroundTruth.SHOULD_BLOCK,
        note="Conditional without Therefore; no chain to resolve.",
    ),
    BenchmarkCase(
        case_id="E9", category=Category.E_PHILOSOPHICAL_STRESS,
        text="Truth requires correspondence with reality.",
        ground_truth=GroundTruth.SHOULD_BLOCK,
        note="Definitional claim, no derivation.",
    ),
    BenchmarkCase(
        case_id="E10", category=Category.E_PHILOSOPHICAL_STRESS,
        text=("Every effect has a cause. "
              "Therefore there is a first cause."),
        ground_truth=GroundTruth.SHOULD_BRIDGE,
        note="Cosmological argument — explicitly contested; many "
             "hidden assumptions about infinity, regress, time.",
    ),
)


ALL_CASES: tuple[BenchmarkCase, ...] = (
    _CATEGORY_A + _CATEGORY_B + _CATEGORY_C + _CATEGORY_D + _CATEGORY_E
)


def cases_by_category(category: Category) -> tuple[BenchmarkCase, ...]:
    return tuple(c for c in ALL_CASES if c.category is category)


def case_by_id(case_id: str) -> BenchmarkCase:
    for c in ALL_CASES:
        if c.case_id == case_id:
            return c
    raise KeyError(f"unknown case_id: {case_id!r}")


__all__ = [
    "ALL_CASES",
    "case_by_id",
    "cases_by_category",
]
