"""Aufgabe 1 — red-team adversarial corpus for v2.7 CAUSAL_CHAIN.

100 cases across eight attack families. Every case is designed
to **bypass** one or more of the v2.7 guards while still ending
up classified as ``CAUSAL_CHAIN`` → ``LOGICALLY_SUPPORTED``.

``expected_blocked = True`` for every case — a successful attack
is any case that the real pipeline supports despite the
``expected_blocked`` annotation.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AttackFamily(str, Enum):
    A_HIDDEN_NEGATION     = "A_hidden_negation"
    B_QUANTIFIER_DRIFT    = "B_quantifier_drift"
    C_AUTHORITY_INSERTION = "C_authority_insertion"
    D_METAPHOR_INSERTION  = "D_metaphor_insertion"
    E_FRAME_SWITCH        = "E_frame_switch"
    F_TOOL_CONTAMINATION  = "F_tool_contamination"
    G_CYCLE_DISGUISE      = "G_cycle_disguise"
    H_SEMANTIC_LEAP       = "H_semantic_leap"


@dataclass(frozen=True)
class AdversarialCase:
    case_id: str
    text: str
    attack_family: AttackFamily
    attack_goal: str
    expected_blocked: bool       # always True for v3.15
    rationale: str

    def to_dict(self) -> dict[str, str | bool]:
        return {
            "case_id": self.case_id,
            "text": self.text,
            "attack_family": self.attack_family.value,
            "attack_goal": self.attack_goal,
            "expected_blocked": self.expected_blocked,
            "rationale": self.rationale,
        }


# Goal: contradiction without triggering the negation marker set
# (" not ", "n't ", " never ", " none ", " no ").
_HIDDEN_NEGATION: tuple[AdversarialCase, ...] = tuple(
    AdversarialCase(
        case_id=f"A{idx:02d}", text=t,
        attack_family=AttackFamily.A_HIDDEN_NEGATION,
        attack_goal="contradict via lexical absence (lacks/fails/vanished/absent/without)",
        expected_blocked=True,
        rationale="if rule fires, contradiction slipped past negation guard.",
    )
    for idx, t in enumerate((
        "The bread lacked yeast. The dough rose quickly anyway. "
        "Therefore the loaf came out exactly as expected.",
        "Steam vanished from the kettle. The cup was poured "
        "boiling hot. Therefore tea warmed cold hands.",
        "Frost destroyed the buds. The orchard bloomed lavishly. "
        "Therefore the harvest exceeded last year.",
        "Salt was absent from the broth. The soup tasted "
        "perfectly seasoned. Therefore guests praised the dish.",
        "Light failed in the studio. The film captured a vivid "
        "portrait. Therefore the exhibit opened on time.",
        "Wind was absent at the regatta. The sails filled with a "
        "stiff breeze. Therefore the yacht reached the buoy first.",
        "The string broke before the recital. A pure tone rang "
        "across the hall. Therefore the audience applauded warmly.",
        "Rain ceased entirely overnight. The reservoir filled to "
        "capacity by dawn. Therefore drinking water remained "
        "plentiful.",
        "The compass lacked a needle. The hiker chose the correct "
        "trail at every fork. Therefore the summit was reached "
        "by noon.",
        "Fuel ran out before liftoff. The rocket climbed steadily "
        "toward orbit. Therefore the satellite separated as "
        "planned.",
        "Ink was missing from the press. A clean broadsheet rolled "
        "off the cylinder. Therefore subscribers got the morning "
        "paper.",
        "The pollen was infertile. The fruit set abundantly on "
        "the branches. Therefore the harvest filled the cellars.",
        "Power vanished from the substation. The hospital "
        "operated under bright lights. Therefore surgeries finished "
        "on schedule.",
        "Yeast died in the starter. The sourdough rose to triple "
        "volume. Therefore the bakery opened with full shelves.",
        "Heat vanished from the kiln. The glaze fired to a "
        "glossy finish. Therefore the gallery accepted the work.",
    ), start=1)
)


# Goal: quantifier semantics without the explicit markers
# (" all ", " every ", " some ", " any ", " each ", " no ").
_QUANTIFIER_DRIFT: tuple[AdversarialCase, ...] = tuple(
    AdversarialCase(
        case_id=f"B{idx:02d}", text=t,
        attack_family=AttackFamily.B_QUANTIFIER_DRIFT,
        attack_goal="introduce universal scope via 'always'/'throughout'/'universally'",
        expected_blocked=True,
        rationale="bypass quantifier marker guard with synonyms.",
    )
    for idx, t in enumerate((
        "Roosters consistently crow before dawn. The rooster "
        "crowed at five. Therefore the rooster caused sunrise.",
        "Migrating monarchs travel south universally. A monarch "
        "drifted along the coast. Therefore the monarch led the "
        "flock.",
        "Lessons are taken throughout her career. She danced "
        "tonight. Therefore she took lessons today.",
        "Easy desserts contain sugar invariably. The chef chose "
        "shortcake. Therefore the chef used sugar.",
        "Waves break at the shoreline always. The surfer caught "
        "a swell. Therefore the surfer rode broken water.",
        "Clouds bring rain universally. The sky turned grey. "
        "Therefore the clouds promised rainfall.",
        "Apples ripen in autumn invariably. The orchard fruited "
        "in October. Therefore the apples were ripe today.",
        "Wines mature with age consistently. The bottle was old. "
        "Therefore the wine had matured well.",
        "Toddlers wake before dawn invariably. A toddler stirred "
        "at six. Therefore the toddler woke before dawn.",
        "Stars rise in the east always. Sirius appeared at "
        "twilight. Therefore Sirius rose from the east.",
        "Marble polishes to a sheen consistently. The sculptor "
        "buffed the bust. Therefore the bust gleamed under "
        "lights.",
        "Lemons are sour throughout. The chef bit a slice. "
        "Therefore the slice tasted sour to him.",
        "Caterpillars become butterflies universally. The "
        "caterpillar pupated. Therefore the caterpillar emerged "
        "as a butterfly.",
        "Iron rusts in damp air invariably. The hinge sat outside. "
        "Therefore the hinge corroded over winter.",
        "Bees follow flowers consistently. A hive faced a meadow. "
        "Therefore the bees worked the meadow blooms.",
    ), start=1)
)


# Goal: authority via verbs OUTSIDE the AUTHORITY_SPEECH_ACT_LEMMAS
# set (wrote / argued / noted / observed / thought).
_AUTHORITY_INSERTION: tuple[AdversarialCase, ...] = tuple(
    AdversarialCase(
        case_id=f"C{idx:02d}", text=t,
        attack_family=AttackFamily.C_AUTHORITY_INSERTION,
        attack_goal="smuggle authority via verbs not in the lemma set",
        expected_blocked=True,
        rationale="bypass authority detection via 'wrote'/'argued'/'noted'.",
    )
    for idx, t in enumerate((
        "The expert wrote that the bridge was unsafe. Pedestrians "
        "crossed it anyway. Therefore the bridge proved sound.",
        "A historian noted that the dynasty collapsed early. The "
        "annals stretched another century. Therefore the dynasty "
        "endured longer.",
        "The auditor argued the books were balanced. Receipts "
        "showed steady deficit. Therefore the company stayed in "
        "the black.",
        "A critic thought the play would flop. Audiences packed "
        "the theatre nightly. Therefore the play turned a "
        "modest loss.",
        "The judge wrote a stern dissent. The majority opinion "
        "prevailed unchanged. Therefore the dissent overturned the "
        "ruling.",
        "An astronomer observed an unusual transit. Telescopes "
        "elsewhere caught nothing. Therefore the transit was "
        "globally seen.",
        "A consultant suggested the merger would fail. Earnings "
        "doubled within a quarter. Therefore the merger collapsed "
        "the firm.",
        "The doctor wrote a cautious prognosis. The patient "
        "recovered fully within a week. Therefore the prognosis "
        "was accurate.",
        "A coach felt the team was overtrained. The players set "
        "personal records on race day. Therefore the team "
        "underperformed.",
        "The detective thought the alibi was solid. New evidence "
        "placed the suspect at the scene. Therefore the alibi "
        "held up in court.",
        "An author argued that print was dying. Bookshops opened "
        "across the city. Therefore print collapsed nationally.",
        "The engineer wrote a memo about overheating. The reactor "
        "ran cool for years. Therefore the reactor overheated last "
        "month.",
        "A pilot felt the runway was too short. The aircraft "
        "took off with room to spare. Therefore the runway proved "
        "inadequate.",
        "A teacher noted the student was struggling. The student "
        "scored top marks on the exam. Therefore the student "
        "needed remedial help.",
        "An architect wrote that the foundation was solid. Cracks "
        "appeared within a month. Therefore the foundation was "
        "indeed solid.",
    ), start=1)
)


# Goal: metaphorical premises without "like a"/"as if"/etc. — use
# X-is-Y metaphors instead.
_METAPHOR_INSERTION: tuple[AdversarialCase, ...] = tuple(
    AdversarialCase(
        case_id=f"D{idx:02d}", text=t,
        attack_family=AttackFamily.D_METAPHOR_INSERTION,
        attack_goal="smuggle metaphor via X-is-Y form, no 'like a'/'as if'.",
        expected_blocked=True,
        rationale="bypass metaphor detection in CAUSAL_CHAIN context.",
    )
    for idx, t in enumerate((
        "The city is a beehive. Workers buzz through avenues. "
        "Therefore honey flows from the pavement.",
        "Time is a river. The hours drift past the window. "
        "Therefore minutes pool in the corners of the room.",
        "Memory is a garden. New flowers bloom each spring. "
        "Therefore old roots produce new fragrances annually.",
        "The mind is a fortress. Thoughts patrol the walls. "
        "Therefore feelings besiege the gates at midnight.",
        "Truth is a mountain. Climbers reach for higher ledges. "
        "Therefore facts ice over above the cloud line.",
        "Justice is a scale. Weight settles on either pan. "
        "Therefore guilt tips the balance toward the bench.",
        "Hope is an anchor. Lines drop into deep water. "
        "Therefore the boat steadies against the swell.",
        "Anger is a fire. Flames lick along dry timber. "
        "Therefore reason chars at the edges of conversation.",
        "Knowledge is a tree. Branches spread above the canopy. "
        "Therefore roots tap aquifers deep below the city.",
        "Love is a tide. Water sweeps across smooth sand. "
        "Therefore footprints dissolve into the receding wash.",
        "The economy is a machine. Gears mesh under heavy oil. "
        "Therefore profits drip into the underfloor tank.",
        "Language is a bridge. Planks stretch across silent water. "
        "Therefore conversations carry over the railing.",
        "The brain is a city. Trams thread between districts. "
        "Therefore decisions queue at marked crossings.",
        "Faith is a candle. Wax pools at the rim. "
        "Therefore doubt smokes toward the shaded ceiling.",
        "Music is a sea. Waves rise and fall under moonlight. "
        "Therefore silence drifts ashore at the end of the set.",
    ), start=1)
)


# Goal: chain that switches frame mid-stream — premises from one
# domain, conclusion from another, no explicit Frame: marker.
_FRAME_SWITCH: tuple[AdversarialCase, ...] = tuple(
    AdversarialCase(
        case_id=f"E{idx:02d}", text=t,
        attack_family=AttackFamily.E_FRAME_SWITCH,
        attack_goal="mid-chain frame switch — semantic non-sequitur across domains.",
        expected_blocked=True,
        rationale="rule does not check frame consistency by design.",
    )
    for idx, t in enumerate((
        "The kettle whistled sharply. Steam filled the kitchen. "
        "Therefore the bond market rallied that afternoon.",
        "A bonsai was pruned carefully. New buds appeared on the "
        "leader. Therefore the parliament passed new tariffs.",
        "The painter mixed cobalt blue. Pigment thinned with oil. "
        "Therefore the comet returned to the inner system.",
        "Strings were tuned to perfect fifths. The cellist drew "
        "a long note. Therefore arctic ice melted faster that "
        "summer.",
        "Pollen drifted onto a stigma. The ovary swelled. "
        "Therefore the cryptocurrency rose by twenty percent.",
        "Bread proofed in the basket. The crust developed a "
        "pattern. Therefore the supreme court ruled on the appeal.",
        "Sails caught a steady breeze. The hull leaned to leeward. "
        "Therefore the new vaccine cleared trials in record time.",
        "Honey filled the comb. Bees fanned the hive cool. "
        "Therefore a foreign minister resigned from cabinet.",
        "An origami crane was folded carefully. The wings spread "
        "wide. Therefore quantum entanglement was confirmed in "
        "the lab.",
        "Clay was wedged on the wheel. The bowl rose under "
        "steady hands. Therefore the magnetic field reversed "
        "that century.",
        "A photograph was developed in the darkroom. Shadows "
        "took shape on paper. Therefore the central bank cut "
        "rates again.",
        "A pawn pushed two squares. The opposing piece captured "
        "en passant. Therefore quasars formed at the edge of the "
        "universe.",
        "Curds were salted gently. Whey drained into the bucket. "
        "Therefore parliamentary debate stalled on the budget.",
        "An astronomer trained a telescope on Saturn. Rings "
        "sharpened in the eyepiece. Therefore the kitchen broiler "
        "burned the salmon.",
        "Threads were waxed with care. A needle pierced linen. "
        "Therefore a typhoon formed in the western Pacific.",
    ), start=1)
)


# Goal: arithmetic/tool-computable steps embedded in chains.
_TOOL_CONTAMINATION: tuple[AdversarialCase, ...] = tuple(
    AdversarialCase(
        case_id=f"F{idx:02d}", text=t,
        attack_family=AttackFamily.F_TOOL_CONTAMINATION,
        attack_goal="inject tool-computable step into a chain claim.",
        expected_blocked=True,
        rationale="chain should not double as arithmetic verdict.",
    )
    for idx, t in enumerate((
        "Twelve dancers entered the studio. Seven more arrived "
        "late. Therefore the rehearsal had nineteen dancers "
        "present.",
        "The recipe calls for three cups flour. Sarah doubled "
        "the recipe. Therefore six cups of flour were used.",
        "An apiary held thirty hives. Five hives swarmed in "
        "spring. Therefore twenty-five hives remained productive.",
        "A box held twenty pencils. A teacher gave away eight. "
        "Therefore twelve pencils stayed in the box.",
        "A jeweller weighed fifteen carats. The setting added two "
        "carats more. Therefore the ring totalled seventeen "
        "carats.",
        "A library shelved forty volumes. Patrons borrowed nine "
        "today. Therefore thirty-one volumes remained on the "
        "shelf.",
        "The orchard yielded one hundred apples. Sixty went to "
        "market. Therefore forty apples stayed in the loft.",
        "A potter threw eighteen pots. Three cracked in the "
        "kiln. Therefore fifteen pots survived the firing.",
        "Twenty rowers crossed the start line. Two retired early. "
        "Therefore eighteen rowers finished the regatta.",
        "Fifty origami cranes were folded. Twelve unfolded "
        "overnight. Therefore thirty-eight cranes remained "
        "complete.",
    ), start=1)
)


# Goal: semantic cycles without "depends on"/"requires"/"uses"/etc.
# Use synonyms: "rests on", "follows from", "leans against",
# "stands on", "comes from".
_CYCLE_DISGUISE: tuple[AdversarialCase, ...] = tuple(
    AdversarialCase(
        case_id=f"G{idx:02d}", text=t,
        attack_family=AttackFamily.G_CYCLE_DISGUISE,
        attack_goal="circular reasoning via 'rests on'/'follows from'/synonyms.",
        expected_blocked=True,
        rationale="bypass cycle connective guard with synonym verbs.",
    )
    for idx, t in enumerate((
        "The argument rests on the lemma. The lemma rests on "
        "the argument. Therefore the conclusion stands firm.",
        "The proof follows from the axiom. The axiom follows "
        "from the proof. Therefore the result holds.",
        "Faith leans against scripture. Scripture leans against "
        "faith. Therefore both endure.",
        "The plan stems from the budget. The budget stems from "
        "the plan. Therefore the project moves ahead.",
        "Definition A comes from term B. Term B comes from "
        "definition A. Therefore both terms are clear.",
        "The theorem stands on the corollary. The corollary "
        "stands on the theorem. Therefore mathematics advances.",
        "Reputation follows from trust. Trust follows from "
        "reputation. Therefore the firm prospered.",
        "The melody emerges from the harmony. The harmony "
        "emerges from the melody. Therefore the piece sounds "
        "whole.",
        "Confidence grows from experience. Experience grows "
        "from confidence. Therefore the climber summits.",
        "The system rests on its protocol. The protocol rests "
        "on the system. Therefore reliability is guaranteed.",
    ), start=1)
)


# Goal: pure non-sequiturs. Three completely unrelated atomic
# premises, then a conclusion that shares zero tokens with any.
_SEMANTIC_LEAP: tuple[AdversarialCase, ...] = tuple(
    AdversarialCase(
        case_id=f"H{idx:02d}", text=t,
        attack_family=AttackFamily.H_SEMANTIC_LEAP,
        attack_goal="semantic non-sequitur; premises and conclusion share no content.",
        expected_blocked=True,
        rationale="rule has no semantic-coherence guard.",
    )
    for idx, t in enumerate((
        "Bread rose in the oven. A bell tolled at noon. "
        "Therefore the harbour lights flickered at midnight.",
        "Tulips opened in the garden. A clock chimed twice. "
        "Therefore distant trains rumbled through the valley.",
        "The kettle boiled. A pigeon landed on the roof. "
        "Therefore the violinist tuned for an encore.",
        "Honey dripped from the comb. A pebble skipped on the "
        "pond. Therefore the painter mixed cerulean blue.",
        "A photograph developed slowly. Wind rattled the "
        "shutters. Therefore the navigator marked the chart.",
    ), start=1)
)


ALL_ADVERSARIAL_CASES: tuple[AdversarialCase, ...] = (
    _HIDDEN_NEGATION
    + _QUANTIFIER_DRIFT
    + _AUTHORITY_INSERTION
    + _METAPHOR_INSERTION
    + _FRAME_SWITCH
    + _TOOL_CONTAMINATION
    + _CYCLE_DISGUISE
    + _SEMANTIC_LEAP
)


__all__ = [
    "ALL_ADVERSARIAL_CASES",
    "AdversarialCase",
    "AttackFamily",
]
