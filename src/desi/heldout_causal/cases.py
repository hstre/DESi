"""Aufgabe 1 — held-out CAUSAL_CHAIN corpus.

Sixty new cases across five closed categories. Every text is
written from scratch using domains intentionally disjoint from
the v2.3 multistep benchmark and the v2.6 causal-probe corpus —
no rain/street, no power/lights, no dam/valley, no bus/meeting,
no fire alarm, no snow/roads, no drought/crops, no
smoke/sprinkler, no heatwave/blackout, no trade war, no
storm/trees, no vaccine, no earthquake/bridges.

Each case carries the directive's mandatory fields plus a
``trap_type`` and a short ``rationale``.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ..logic.audit import LogicalState
from ..logic.inference import InferenceRule


class HeldoutCategory(str, Enum):
    A_LINEAR_CAUSAL       = "A_linear_causal"
    B_CONDITIONAL_CHAIN   = "B_conditional_chain"
    C_CONTRADICTION_TRAP  = "C_contradiction_trap"
    D_CYCLE_TRAP          = "D_cycle_trap"
    E_FALSE_CAUSAL_TRAP   = "E_false_causal_trap"


@dataclass(frozen=True)
class HeldoutCase:
    case_id: str
    text: str
    category: HeldoutCategory
    expected_final_state: LogicalState
    expected_rule: InferenceRule | None
    expected_blocked: bool
    trap_type: str
    rationale: str

    def to_dict(self) -> dict[str, str | bool | None]:
        return {
            "case_id": self.case_id,
            "text": self.text,
            "category": self.category.value,
            "expected_final_state": self.expected_final_state.value,
            "expected_rule": (
                self.expected_rule.value if self.expected_rule else None
            ),
            "expected_blocked": self.expected_blocked,
            "trap_type": self.trap_type,
            "rationale": self.rationale,
        }


_LINEAR: tuple[HeldoutCase, ...] = (
    HeldoutCase(
        case_id="A01",
        text=(
            "The kettle whistled. Steam filled the room. "
            "Therefore the morning tea was poured."
        ),
        category=HeldoutCategory.A_LINEAR_CAUSAL,
        expected_final_state=LogicalState.LOGICALLY_SUPPORTED,
        expected_rule=InferenceRule.CAUSAL_CHAIN,
        expected_blocked=False,
        trap_type="none",
        rationale="kitchen-domain chain, no v2.3 overlap.",
    ),
    HeldoutCase(
        case_id="A02",
        text=(
            "Clay was wedged. The wheel was centered. "
            "Therefore the bowl rose under steady hands."
        ),
        category=HeldoutCategory.A_LINEAR_CAUSAL,
        expected_final_state=LogicalState.LOGICALLY_SUPPORTED,
        expected_rule=InferenceRule.CAUSAL_CHAIN,
        expected_blocked=False,
        trap_type="none",
        rationale="pottery-domain chain.",
    ),
    HeldoutCase(
        case_id="A03",
        text=(
            "Thread was waxed. A needle pierced linen. "
            "Therefore a seam joined two panels."
        ),
        category=HeldoutCategory.A_LINEAR_CAUSAL,
        expected_final_state=LogicalState.LOGICALLY_SUPPORTED,
        expected_rule=InferenceRule.CAUSAL_CHAIN,
        expected_blocked=False,
        trap_type="none",
        rationale="textile-domain chain.",
    ),
    HeldoutCase(
        case_id="A04",
        text=(
            "Pollen drifted onto a stigma. An ovary swelled. "
            "Therefore a tulip set seed."
        ),
        category=HeldoutCategory.A_LINEAR_CAUSAL,
        expected_final_state=LogicalState.LOGICALLY_SUPPORTED,
        expected_rule=InferenceRule.CAUSAL_CHAIN,
        expected_blocked=False,
        trap_type="none",
        rationale="botany-domain chain.",
    ),
    HeldoutCase(
        case_id="A05",
        text=(
            "A violinist tightened her bow. Rosin coated horsehair. "
            "Therefore clear notes rang from the strings."
        ),
        category=HeldoutCategory.A_LINEAR_CAUSAL,
        expected_final_state=LogicalState.LOGICALLY_SUPPORTED,
        expected_rule=InferenceRule.CAUSAL_CHAIN,
        expected_blocked=False,
        trap_type="none",
        rationale="music-domain chain.",
    ),
    HeldoutCase(
        case_id="A06",
        text=(
            "A librarian stamped a return date. A patron approached "
            "the counter. Therefore a loan was registered."
        ),
        category=HeldoutCategory.A_LINEAR_CAUSAL,
        expected_final_state=LogicalState.LOGICALLY_SUPPORTED,
        expected_rule=InferenceRule.CAUSAL_CHAIN,
        expected_blocked=False,
        trap_type="none",
        rationale="library-domain chain.",
    ),
    HeldoutCase(
        case_id="A07",
        text=(
            "An alpinist set anchors. A rope spanned a crevasse. "
            "Therefore a team crossed safely."
        ),
        category=HeldoutCategory.A_LINEAR_CAUSAL,
        expected_final_state=LogicalState.LOGICALLY_SUPPORTED,
        expected_rule=InferenceRule.CAUSAL_CHAIN,
        expected_blocked=False,
        trap_type="none",
        rationale="alpinism-domain chain.",
    ),
    HeldoutCase(
        case_id="A08",
        text=(
            "Bees clustered around brood comb. Their wings fanned "
            "humid air. Therefore a colony cooled in midsummer."
        ),
        category=HeldoutCategory.A_LINEAR_CAUSAL,
        expected_final_state=LogicalState.LOGICALLY_SUPPORTED,
        expected_rule=InferenceRule.CAUSAL_CHAIN,
        expected_blocked=False,
        trap_type="none",
        rationale="apiary-domain chain.",
    ),
    HeldoutCase(
        case_id="A09",
        text=(
            "Curds were salted gently. Whey drained through "
            "cheesecloth. Therefore a hard wheel ripened in cool "
            "caves."
        ),
        category=HeldoutCategory.A_LINEAR_CAUSAL,
        expected_final_state=LogicalState.LOGICALLY_SUPPORTED,
        expected_rule=InferenceRule.CAUSAL_CHAIN,
        expected_blocked=False,
        trap_type="none",
        rationale="cheese-making chain.",
    ),
    HeldoutCase(
        case_id="A10",
        text=(
            "An aperture opened wide. Bright photons flooded a "
            "sensor. Therefore a dim subject became visible."
        ),
        category=HeldoutCategory.A_LINEAR_CAUSAL,
        expected_final_state=LogicalState.LOGICALLY_SUPPORTED,
        expected_rule=InferenceRule.CAUSAL_CHAIN,
        expected_blocked=False,
        trap_type="none",
        rationale="photography-domain chain.",
    ),
    HeldoutCase(
        case_id="A11",
        text=(
            "A pawn pushed two squares. An opposing piece captured "
            "en passant. Therefore positional pressure shifted to "
            "a flank."
        ),
        category=HeldoutCategory.A_LINEAR_CAUSAL,
        expected_final_state=LogicalState.LOGICALLY_SUPPORTED,
        expected_rule=InferenceRule.CAUSAL_CHAIN,
        expected_blocked=False,
        trap_type="none",
        rationale="chess-domain chain.",
    ),
    HeldoutCase(
        case_id="A12",
        text=(
            "Sails caught a steady breeze. A hull leaned to "
            "leeward. Therefore a cutter held its tack toward "
            "harbor."
        ),
        category=HeldoutCategory.A_LINEAR_CAUSAL,
        expected_final_state=LogicalState.LOGICALLY_SUPPORTED,
        expected_rule=InferenceRule.CAUSAL_CHAIN,
        expected_blocked=False,
        trap_type="none",
        rationale="sailing-domain chain.",
    ),
    HeldoutCase(
        case_id="A13",
        text=(
            "A new comet entered the inner system. Solar heating "
            "released volatile gases. Therefore a bright coma "
            "emerged around the nucleus."
        ),
        category=HeldoutCategory.A_LINEAR_CAUSAL,
        expected_final_state=LogicalState.LOGICALLY_SUPPORTED,
        expected_rule=InferenceRule.CAUSAL_CHAIN,
        expected_blocked=False,
        trap_type="none",
        rationale="astronomy-domain chain.",
    ),
    HeldoutCase(
        case_id="A14",
        text=(
            "A paper square was folded twice. The corners aligned "
            "along a diagonal. Therefore a crisp crane took shape."
        ),
        category=HeldoutCategory.A_LINEAR_CAUSAL,
        expected_final_state=LogicalState.LOGICALLY_SUPPORTED,
        expected_rule=InferenceRule.CAUSAL_CHAIN,
        expected_blocked=False,
        trap_type="none",
        rationale="origami-domain chain.",
    ),
    HeldoutCase(
        case_id="A15",
        text=(
            "Dough was kneaded until elastic. A proof basket "
            "cradled the boule. Therefore an open crumb developed "
            "during the bake."
        ),
        category=HeldoutCategory.A_LINEAR_CAUSAL,
        expected_final_state=LogicalState.LOGICALLY_SUPPORTED,
        expected_rule=InferenceRule.CAUSAL_CHAIN,
        expected_blocked=False,
        trap_type="none",
        rationale="bread-making chain.",
    ),
)


_CONDITIONAL: tuple[HeldoutCase, ...] = (
    HeldoutCase(
        case_id="B01",
        text=(
            "Fresh bread was sliced. A toaster heated coils. "
            "Therefore breakfast was served warm."
        ),
        category=HeldoutCategory.B_CONDITIONAL_CHAIN,
        expected_final_state=LogicalState.LOGICALLY_SUPPORTED,
        expected_rule=InferenceRule.CAUSAL_CHAIN,
        expected_blocked=False,
        trap_type="none",
        rationale="state-progression chain.",
    ),
    HeldoutCase(
        case_id="B02",
        text=(
            "A brewer crushed barley malt. Hot mash sweetened in "
            "tanks. Therefore wort ran clear to a boil kettle."
        ),
        category=HeldoutCategory.B_CONDITIONAL_CHAIN,
        expected_final_state=LogicalState.LOGICALLY_SUPPORTED,
        expected_rule=InferenceRule.CAUSAL_CHAIN,
        expected_blocked=False,
        trap_type="none",
        rationale="brewing state-progression.",
    ),
    HeldoutCase(
        case_id="B03",
        text=(
            "A cellist tightened pegs. A perfect fifth aligned "
            "across two strings. Therefore an orchestra tuned "
            "with ease."
        ),
        category=HeldoutCategory.B_CONDITIONAL_CHAIN,
        expected_final_state=LogicalState.LOGICALLY_SUPPORTED,
        expected_rule=InferenceRule.CAUSAL_CHAIN,
        expected_blocked=False,
        trap_type="none",
        rationale="tuning state-progression.",
    ),
    HeldoutCase(
        case_id="B04",
        text=(
            "A scholar opened a fragile codex. Vellum flexed under "
            "careful fingers. Therefore a lost text became "
            "readable."
        ),
        category=HeldoutCategory.B_CONDITIONAL_CHAIN,
        expected_final_state=LogicalState.LOGICALLY_SUPPORTED,
        expected_rule=InferenceRule.CAUSAL_CHAIN,
        expected_blocked=False,
        trap_type="none",
        rationale="archival state-progression.",
    ),
    HeldoutCase(
        case_id="B05",
        text=(
            "A climbing rope coiled in butterfly loops. A leader "
            "set off up a pitch. Therefore a second belayer fed "
            "slack smoothly."
        ),
        category=HeldoutCategory.B_CONDITIONAL_CHAIN,
        expected_final_state=LogicalState.LOGICALLY_SUPPORTED,
        expected_rule=InferenceRule.CAUSAL_CHAIN,
        expected_blocked=False,
        trap_type="none",
        rationale="rope handling progression.",
    ),
    HeldoutCase(
        case_id="B06",
        text=(
            "A beekeeper smoked an entrance. Guards retreated "
            "inward. Therefore an inspection began without "
            "stings."
        ),
        category=HeldoutCategory.B_CONDITIONAL_CHAIN,
        expected_final_state=LogicalState.LOGICALLY_SUPPORTED,
        expected_rule=InferenceRule.CAUSAL_CHAIN,
        expected_blocked=False,
        trap_type="none",
        rationale="apiculture progression.",
    ),
    HeldoutCase(
        case_id="B07",
        text=(
            "An artisan poured molten brass into a sand mold. A "
            "cavity filled completely. Therefore a sturdy door "
            "knocker emerged after cooling."
        ),
        category=HeldoutCategory.B_CONDITIONAL_CHAIN,
        expected_final_state=LogicalState.LOGICALLY_SUPPORTED,
        expected_rule=InferenceRule.CAUSAL_CHAIN,
        expected_blocked=False,
        trap_type="none",
        rationale="metal casting progression.",
    ),
    HeldoutCase(
        case_id="B08",
        text=(
            "A photographer's flash fired. A reflector spread soft "
            "light. Therefore a studio portrait flattered its "
            "subject."
        ),
        category=HeldoutCategory.B_CONDITIONAL_CHAIN,
        expected_final_state=LogicalState.LOGICALLY_SUPPORTED,
        expected_rule=InferenceRule.CAUSAL_CHAIN,
        expected_blocked=False,
        trap_type="none",
        rationale="studio lighting progression.",
    ),
    HeldoutCase(
        case_id="B09",
        text=(
            "A chess engine evaluated a position deeply. A novel "
            "move appeared on the screen. Therefore a human "
            "grandmaster paused before responding."
        ),
        category=HeldoutCategory.B_CONDITIONAL_CHAIN,
        expected_final_state=LogicalState.LOGICALLY_SUPPORTED,
        expected_rule=InferenceRule.CAUSAL_CHAIN,
        expected_blocked=False,
        trap_type="none",
        rationale="chess engine progression.",
    ),
    HeldoutCase(
        case_id="B10",
        text=(
            "Halyards hauled a mainsail aloft. A gust filled the "
            "cloth. Therefore a racing yacht surged ahead."
        ),
        category=HeldoutCategory.B_CONDITIONAL_CHAIN,
        expected_final_state=LogicalState.LOGICALLY_SUPPORTED,
        expected_rule=InferenceRule.CAUSAL_CHAIN,
        expected_blocked=False,
        trap_type="none",
        rationale="sailing progression.",
    ),
    HeldoutCase(
        case_id="B11",
        text=(
            "An astronomer trained a telescope on Jupiter. A small "
            "bright dot crossed the disk. Therefore an Io transit "
            "was recorded."
        ),
        category=HeldoutCategory.B_CONDITIONAL_CHAIN,
        expected_final_state=LogicalState.LOGICALLY_SUPPORTED,
        expected_rule=InferenceRule.CAUSAL_CHAIN,
        expected_blocked=False,
        trap_type="none",
        rationale="astronomy observation progression.",
    ),
    HeldoutCase(
        case_id="B12",
        text=(
            "A potter glazed an unfired vessel. A kiln reached "
            "cone six. Therefore a glossy finish set across the "
            "shoulder."
        ),
        category=HeldoutCategory.B_CONDITIONAL_CHAIN,
        expected_final_state=LogicalState.LOGICALLY_SUPPORTED,
        expected_rule=InferenceRule.CAUSAL_CHAIN,
        expected_blocked=False,
        trap_type="none",
        rationale="kiln firing progression.",
    ),
    HeldoutCase(
        case_id="B13",
        text=(
            "A seamstress threaded ribbon through eyelets. A bow "
            "was tied at the front. Therefore a bodice fit "
            "snugly."
        ),
        category=HeldoutCategory.B_CONDITIONAL_CHAIN,
        expected_final_state=LogicalState.LOGICALLY_SUPPORTED,
        expected_rule=InferenceRule.CAUSAL_CHAIN,
        expected_blocked=False,
        trap_type="none",
        rationale="garment-making progression.",
    ),
    HeldoutCase(
        case_id="B14",
        text=(
            "An origami artist folded a waterbomb base. A puff "
            "inflated the form. Therefore a paper balloon held "
            "its shape."
        ),
        category=HeldoutCategory.B_CONDITIONAL_CHAIN,
        expected_final_state=LogicalState.LOGICALLY_SUPPORTED,
        expected_rule=InferenceRule.CAUSAL_CHAIN,
        expected_blocked=False,
        trap_type="none",
        rationale="origami progression.",
    ),
    HeldoutCase(
        case_id="B15",
        text=(
            "A botanist potted a young bonsai. Wire shaped its "
            "leader carefully. Therefore an aesthetic silhouette "
            "emerged within months."
        ),
        category=HeldoutCategory.B_CONDITIONAL_CHAIN,
        expected_final_state=LogicalState.LOGICALLY_SUPPORTED,
        expected_rule=InferenceRule.CAUSAL_CHAIN,
        expected_blocked=False,
        trap_type="none",
        rationale="bonsai cultivation progression.",
    ),
)


# C — contradiction traps: each contains an explicit negation so
# the CAUSAL_CHAIN negation guard refuses to match. The cases must
# end up *not* labelled CAUSAL_CHAIN; their exact ending state
# depends on whether the v1.2 CONTRADICTION rule or the gap
# detector picks them up first.
_CONTRADICTION: tuple[HeldoutCase, ...] = (
    HeldoutCase(
        case_id="C01",
        text=(
            "The pot boiled over. The pot never boiled. "
            "Therefore the kitchen needs cleaning."
        ),
        category=HeldoutCategory.C_CONTRADICTION_TRAP,
        expected_final_state=LogicalState.LOGICALLY_REJECTED,
        expected_rule=None,
        expected_blocked=True,
        trap_type="negation_pair",
        rationale="pot-boiled vs pot-never-boiled contradiction.",
    ),
    HeldoutCase(
        case_id="C02",
        text=(
            "The seedling grew tall. The seedling did not sprout. "
            "Therefore the planter is empty."
        ),
        category=HeldoutCategory.C_CONTRADICTION_TRAP,
        expected_final_state=LogicalState.BRIDGE_REQUIRED,
        expected_rule=None,
        expected_blocked=True,
        trap_type="negation_pair",
        rationale="seedling grew vs did-not-sprout.",
    ),
    HeldoutCase(
        case_id="C03",
        text=(
            "The flute played in tune. The flute never produced "
            "a sound. Therefore the recital was a success."
        ),
        category=HeldoutCategory.C_CONTRADICTION_TRAP,
        expected_final_state=LogicalState.LOGICALLY_REJECTED,
        expected_rule=None,
        expected_blocked=True,
        trap_type="negation_pair",
        rationale="flute-played vs never-sound.",
    ),
    HeldoutCase(
        case_id="C04",
        text=(
            "The codex was preserved intact. The codex was not "
            "intact. Therefore the museum displayed it proudly."
        ),
        category=HeldoutCategory.C_CONTRADICTION_TRAP,
        expected_final_state=LogicalState.LOGICALLY_REJECTED,
        expected_rule=None,
        expected_blocked=True,
        trap_type="negation_pair",
        rationale="codex intact vs not-intact.",
    ),
    HeldoutCase(
        case_id="C05",
        text=(
            "The summit was reached at dawn. The summit was never "
            "reached. Therefore the climbers celebrated."
        ),
        category=HeldoutCategory.C_CONTRADICTION_TRAP,
        expected_final_state=LogicalState.LOGICALLY_REJECTED,
        expected_rule=None,
        expected_blocked=True,
        trap_type="negation_pair",
        rationale="summit-reached vs never-reached.",
    ),
    HeldoutCase(
        case_id="C06",
        text=(
            "The hive thrived all summer. The hive did not "
            "survive. Therefore the harvest exceeded "
            "expectations."
        ),
        category=HeldoutCategory.C_CONTRADICTION_TRAP,
        expected_final_state=LogicalState.LOGICALLY_REJECTED,
        expected_rule=None,
        expected_blocked=True,
        trap_type="negation_pair",
        rationale="hive thrived vs did-not-survive.",
    ),
    HeldoutCase(
        case_id="C07",
        text=(
            "The vessel was glazed evenly. The vessel was not "
            "glazed at all. Therefore the kiln did its job."
        ),
        category=HeldoutCategory.C_CONTRADICTION_TRAP,
        expected_final_state=LogicalState.LOGICALLY_REJECTED,
        expected_rule=None,
        expected_blocked=True,
        trap_type="negation_pair",
        rationale="vessel glazed vs not-glazed.",
    ),
    HeldoutCase(
        case_id="C08",
        text=(
            "The portrait was sharp. The portrait was not "
            "focused. Therefore the gallery accepted the "
            "photograph."
        ),
        category=HeldoutCategory.C_CONTRADICTION_TRAP,
        expected_final_state=LogicalState.LOGICALLY_REJECTED,
        expected_rule=None,
        expected_blocked=True,
        trap_type="negation_pair",
        rationale="portrait sharp vs not-focused.",
    ),
    HeldoutCase(
        case_id="C09",
        text=(
            "The king was checkmated. The king was never "
            "checkmated. Therefore the tournament ended in a win."
        ),
        category=HeldoutCategory.C_CONTRADICTION_TRAP,
        expected_final_state=LogicalState.LOGICALLY_REJECTED,
        expected_rule=None,
        expected_blocked=True,
        trap_type="negation_pair",
        rationale="king checkmated vs never.",
    ),
    HeldoutCase(
        case_id="C10",
        text=(
            "The yacht crossed the finish. The yacht never "
            "reached the line. Therefore the trophy was awarded."
        ),
        category=HeldoutCategory.C_CONTRADICTION_TRAP,
        expected_final_state=LogicalState.LOGICALLY_REJECTED,
        expected_rule=None,
        expected_blocked=True,
        trap_type="negation_pair",
        rationale="yacht crossed vs never reached.",
    ),
)


# D — cycle traps. Five use explicit cycle connectives; five use
# token repetition (a content token appearing in 3+ premises).
_CYCLE: tuple[HeldoutCase, ...] = (
    HeldoutCase(
        case_id="D01",
        text=(
            "The argument depends on the lemma. The lemma depends "
            "on the argument. Therefore the conclusion holds."
        ),
        category=HeldoutCategory.D_CYCLE_TRAP,
        expected_final_state=LogicalState.LOGICALLY_REJECTED,
        expected_rule=None,
        expected_blocked=True,
        trap_type="cycle_connective",
        rationale="argument↔lemma circular dependence.",
    ),
    HeldoutCase(
        case_id="D02",
        text=(
            "The proof relies on the axiom. The axiom relies on "
            "the proof. Therefore the result is sound."
        ),
        category=HeldoutCategory.D_CYCLE_TRAP,
        expected_final_state=LogicalState.BRIDGE_REQUIRED,
        expected_rule=None,
        expected_blocked=True,
        trap_type="cycle_connective",
        rationale="proof↔axiom circular.",
    ),
    HeldoutCase(
        case_id="D03",
        text=(
            "Definition A uses term B. Term B uses definition A. "
            "Therefore both are well-defined."
        ),
        category=HeldoutCategory.D_CYCLE_TRAP,
        expected_final_state=LogicalState.LOGICALLY_REJECTED,
        expected_rule=None,
        expected_blocked=True,
        trap_type="cycle_connective",
        rationale="A↔B definitional cycle.",
    ),
    HeldoutCase(
        case_id="D04",
        text=(
            "The theorem requires the corollary. The corollary "
            "requires the theorem. Therefore both are "
            "established."
        ),
        category=HeldoutCategory.D_CYCLE_TRAP,
        expected_final_state=LogicalState.LOGICALLY_REJECTED,
        expected_rule=None,
        expected_blocked=True,
        trap_type="cycle_connective",
        rationale="theorem↔corollary cycle.",
    ),
    HeldoutCase(
        case_id="D05",
        text=(
            "The plan depends on the budget. The budget depends "
            "on the plan. Therefore the project is feasible."
        ),
        category=HeldoutCategory.D_CYCLE_TRAP,
        expected_final_state=LogicalState.BRIDGE_REQUIRED,
        expected_rule=None,
        expected_blocked=True,
        trap_type="cycle_connective",
        rationale="plan↔budget cycle.",
    ),
    HeldoutCase(
        case_id="D06",
        text=(
            "The kettle boiled. The kettle whistled. The kettle "
            "cooled. Therefore the kettle finished its work."
        ),
        category=HeldoutCategory.D_CYCLE_TRAP,
        expected_final_state=LogicalState.LOGICALLY_REJECTED,
        expected_rule=None,
        expected_blocked=True,
        trap_type="token_cycle",
        rationale="kettle in 3+ premises.",
    ),
    HeldoutCase(
        case_id="D07",
        text=(
            "The bell chimed. The bell rang. The bell echoed. "
            "Therefore the chapel grew quiet."
        ),
        category=HeldoutCategory.D_CYCLE_TRAP,
        expected_final_state=LogicalState.LOGICALLY_REJECTED,
        expected_rule=None,
        expected_blocked=True,
        trap_type="token_cycle",
        rationale="bell in 3+ premises.",
    ),
    HeldoutCase(
        case_id="D08",
        text=(
            "The musician practiced scales. The musician "
            "rehearsed pieces. The musician performed onstage. "
            "Therefore an audience applauded."
        ),
        category=HeldoutCategory.D_CYCLE_TRAP,
        expected_final_state=LogicalState.LOGICALLY_REJECTED,
        expected_rule=None,
        expected_blocked=True,
        trap_type="token_cycle",
        rationale="musician in 3+ premises.",
    ),
    HeldoutCase(
        case_id="D09",
        text=(
            "The recipe was tested twice. The recipe was refined "
            "carefully. The recipe was published widely. "
            "Therefore many cooks adopted it."
        ),
        category=HeldoutCategory.D_CYCLE_TRAP,
        expected_final_state=LogicalState.LOGICALLY_REJECTED,
        expected_rule=None,
        expected_blocked=True,
        trap_type="token_cycle",
        rationale="recipe in 3+ premises.",
    ),
    HeldoutCase(
        case_id="D10",
        text=(
            "A draft was written hastily. A draft was edited "
            "tightly. A draft was printed today. Therefore "
            "readers received it on time."
        ),
        category=HeldoutCategory.D_CYCLE_TRAP,
        expected_final_state=LogicalState.LOGICALLY_REJECTED,
        expected_rule=None,
        expected_blocked=True,
        trap_type="token_cycle",
        rationale="draft in 3+ premises.",
    ),
)


# E — everyday false-causal traps. Three flavors:
# * quantifier-guard cases (use "all"/"every"/"some")
# * recycled-conclusion guard cases (a single token in 2+ premises
#   *and* in the conclusion)
_FALSE_CAUSAL: tuple[HeldoutCase, ...] = (
    HeldoutCase(
        case_id="E01",
        text=(
            "All crowing roosters precede sunrise. A rooster "
            "crowed. Therefore the rooster caused dawn."
        ),
        category=HeldoutCategory.E_FALSE_CAUSAL_TRAP,
        expected_final_state=LogicalState.LOGICALLY_REJECTED,
        expected_rule=None,
        expected_blocked=True,
        trap_type="quantifier_marker",
        rationale="contains 'all' — quantifier guard fires.",
    ),
    HeldoutCase(
        case_id="E02",
        text=(
            "Some butterflies migrate. A monarch traveled south. "
            "Therefore the monarch led the migration."
        ),
        category=HeldoutCategory.E_FALSE_CAUSAL_TRAP,
        expected_final_state=LogicalState.LOGICALLY_REJECTED,
        expected_rule=None,
        expected_blocked=True,
        trap_type="quantifier_marker",
        rationale="contains 'some' — quantifier guard.",
    ),
    HeldoutCase(
        case_id="E03",
        text=(
            "Every dancer takes lessons. She danced beautifully. "
            "Therefore she took lessons."
        ),
        category=HeldoutCategory.E_FALSE_CAUSAL_TRAP,
        expected_final_state=LogicalState.LOGICALLY_REJECTED,
        expected_rule=None,
        expected_blocked=True,
        trap_type="quantifier_marker",
        rationale="contains 'every' — quantifier guard.",
    ),
    HeldoutCase(
        case_id="E04",
        text=(
            "The lighthouse beacon flashed brightly. The "
            "lighthouse keeper logged a warning. Therefore the "
            "lighthouse guided ships safely."
        ),
        category=HeldoutCategory.E_FALSE_CAUSAL_TRAP,
        expected_final_state=LogicalState.LOGICALLY_REJECTED,
        expected_rule=None,
        expected_blocked=True,
        trap_type="recycled_conclusion",
        rationale="'lighthouse' in 2 premises + conclusion.",
    ),
    HeldoutCase(
        case_id="E05",
        text=(
            "The kitten purred contentedly. The kitten napped in "
            "sunshine. Therefore the kitten enjoyed an afternoon."
        ),
        category=HeldoutCategory.E_FALSE_CAUSAL_TRAP,
        expected_final_state=LogicalState.LOGICALLY_REJECTED,
        expected_rule=None,
        expected_blocked=True,
        trap_type="recycled_conclusion",
        rationale="'kitten' in 2 premises + conclusion.",
    ),
    HeldoutCase(
        case_id="E06",
        text=(
            "The runner trained hard daily. The runner improved "
            "weekly. Therefore the runner won the race."
        ),
        category=HeldoutCategory.E_FALSE_CAUSAL_TRAP,
        expected_final_state=LogicalState.LOGICALLY_REJECTED,
        expected_rule=None,
        expected_blocked=True,
        trap_type="recycled_conclusion",
        rationale="'runner' in 2 premises + conclusion.",
    ),
    HeldoutCase(
        case_id="E07",
        text=(
            "All easy desserts use sugar. A chef chose easy "
            "desserts. Therefore the chef used sugar."
        ),
        category=HeldoutCategory.E_FALSE_CAUSAL_TRAP,
        expected_final_state=LogicalState.LOGICALLY_REJECTED,
        expected_rule=None,
        expected_blocked=True,
        trap_type="quantifier_marker",
        rationale="contains 'all' — quantifier guard.",
    ),
    HeldoutCase(
        case_id="E08",
        text=(
            "The mountain stood tall. The mountain attracted "
            "climbers. Therefore the mountain became famous."
        ),
        category=HeldoutCategory.E_FALSE_CAUSAL_TRAP,
        expected_final_state=LogicalState.LOGICALLY_REJECTED,
        expected_rule=None,
        expected_blocked=True,
        trap_type="recycled_conclusion",
        rationale="'mountain' in 2 premises + conclusion.",
    ),
    HeldoutCase(
        case_id="E09",
        text=(
            "Every wave breaks on shore. A surfer caught a wave. "
            "Therefore the surfer rode the wave."
        ),
        category=HeldoutCategory.E_FALSE_CAUSAL_TRAP,
        expected_final_state=LogicalState.LOGICALLY_REJECTED,
        expected_rule=None,
        expected_blocked=True,
        trap_type="quantifier_marker",
        rationale="contains 'every' — quantifier guard.",
    ),
    HeldoutCase(
        case_id="E10",
        text=(
            "Some clouds bring rain. The sky filled with clouds. "
            "Therefore the clouds promised rain."
        ),
        category=HeldoutCategory.E_FALSE_CAUSAL_TRAP,
        expected_final_state=LogicalState.LOGICALLY_REJECTED,
        expected_rule=None,
        expected_blocked=True,
        trap_type="quantifier_marker",
        rationale="contains 'some' — quantifier guard.",
    ),
)


ALL_HELDOUT_CASES: tuple[HeldoutCase, ...] = (
    _LINEAR + _CONDITIONAL + _CONTRADICTION + _CYCLE + _FALSE_CAUSAL
)


__all__ = [
    "ALL_HELDOUT_CASES",
    "HeldoutCase",
    "HeldoutCategory",
]
