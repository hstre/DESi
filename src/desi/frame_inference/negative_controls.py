"""Aufgabe 8 — 100 external-style frame ambiguities.

These fixtures are *not* added to the v4.0 corpus; they form a
separate evaluation set for frame inference. Every entry is
designed so that a competent strategy refuses to commit to a
single frame — the ground-truth label is therefore always
``FrameKind.FRAME_UNDECLARED``. A strategy "detects" the
ambiguity iff it returns ``None`` (or ``FRAME_UNDECLARED``).

Six pattern families are present, the same families enumerated
in the v4.1 directive (Aufgabe 8):

* entropy collisions — fires both ``THERMODYNAMIC`` and
  ``INFORMATION_THEORETIC`` rule buckets,
* metaphorised equations — ``like a`` and ``modus ponens``
  meet in one sentence,
* authority in scientific prose — a cited speaker delivers an
  empirical result,
* legal quantifier drift — ``every plaintiff`` collides with
  ``the statute``,
* mathematical rhetorical flourishes — ``Cauchy sequence``
  used as a simile,
* context poisoning — chains adjacent to a confidently-framed
  cohort that would inherit the wrong frame under F4.

Each family contributes a balanced number of fixtures and the
final list is exactly 100 long. No fixture matches any DESi
corpus chain above a 0.20 token-Jaccard threshold — the
contamination check at Aufgabe 9 verifies that bound holds.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..frames import FrameKind


@dataclass(frozen=True)
class FrameNC:
    nc_id: str
    text: str
    family: str
    rationale: str
    expected_frame: FrameKind = FrameKind.FRAME_UNDECLARED


_ENTROPY: tuple[tuple[str, str], ...] = (
    ("Researchers measured the entropy of the channel under "
     "varying heat conditions and reported elevated readings.",
     "entropy + heat → ambiguous between thermo and info-theoretic"),
    ("The lab notebook recorded entropy growth across the "
     "experimental temperature ramp without further qualification.",
     "entropy + temperature → both buckets fire"),
    ("Following the workshop the team described entropy as the "
     "central concept for both heat dissipation and signal "
     "compression.",
     "entropy spans both compression and dissipation"),
    ("In the seminar notes entropy was treated as a quantity that "
     "increases under temperature gradients and channel noise alike.",
     "entropy linked to temperature gradients and channel noise"),
    ("The textbook chapter on entropy interleaved discussions of "
     "Kelvin scaling and Shannon coding without distinguishing them.",
     "kelvin + shannon entwined under entropy"),
    ("A guest lecture treated entropy as the same variable in the "
     "Carnot engine analysis and in the source-coding theorem.",
     "carnot + source-coding under one entropy variable"),
    ("Workshop slides described entropy as quantifiable along "
     "joule-kelvin gradients and along codeword-length axes at "
     "once.",
     "entropy with joule-kelvin and codeword axes"),
    ("The conference summary characterised entropy as a single "
     "magnitude common to heat exchange and channel capacity.",
     "entropy framed as cross-domain magnitude"),
    ("In the review article entropy was described as the master "
     "concept linking thermodynamic loss and information loss.",
     "ambiguous master-concept framing"),
    ("Notebook entries used entropy to label both the heat-bath "
     "term and the channel mutual-information term in the same "
     "table.",
     "table entry collapses both senses"),
    ("Lecture transcripts treat entropy as a temperature-scaled "
     "quantity and as bits per use in alternating slides.",
     "alternating senses across slides"),
    ("A workshop poster reported entropy results with mixed "
     "units of joules and bits in adjacent columns.",
     "mixed unit columns force ambiguity"),
    ("The summer-school handout described entropy with the same "
     "symbol for the heat reservoir and the channel ensemble.",
     "shared symbol across reservoirs and ensembles"),
    ("The post-graduate primer used the word entropy throughout "
     "without ever fixing whether it referred to a kelvin or a "
     "bit context.",
     "no disambiguation across primer"),
    ("Reading-group notes wrote that entropy is conserved across "
     "the engine cycle and across the noisy channel without "
     "distinction.",
     "false conservation across both senses"),
)


_METAPHOR_EQUATIONS: tuple[tuple[str, str], ...] = (
    ("The argument behaves like a syllogism in which every premise "
     "all a are b becomes a metaphor for organisational momentum.",
     "syllogism + metaphor in one sentence"),
    ("Loosely speaking the manager applies modus ponens to every "
     "memo as if the office ran on first-order logic.",
     "modus ponens used as simile"),
    ("In a sense the recurrence relation is like a tide and the "
     "team's pace is described as if every step were a lemma.",
     "tide simile + lemma simile collide"),
    ("Strategic planning is figuratively a theorem whose corollaries "
     "are like seasonal weather patterns rather than deductions.",
     "theorem stripped of deductive force"),
    ("The proof outline reads like an analogy in which every "
     "if and only if collapses into a sales metaphor.",
     "if-and-only-if reduced to metaphor"),
    ("The mentor framed the optimisation problem as if it were a "
     "river finding its bed, while invoking calculus terms in "
     "passing.",
     "calculus reduced to imagery"),
    ("Internal memos discussed the algorithm as though it were a "
     "lattice of lemmas illuminated by an unstoppable engine of "
     "intuition.",
     "lattice + engine metaphors with formal terms"),
    ("The whitepaper described the recursion as figuratively a "
     "spiral staircase ascended by suppose-and-conclude rhetoric.",
     "spiral staircase masks the deduction"),
    ("Loosely speaking the workshop participants treated the "
     "induction step as if it were a melody resolving into a chord.",
     "induction equated to musical resolution"),
    ("In the executive summary the rank-nullity theorem was "
     "described metaphorically as a balance scale weighing intent.",
     "rank-nullity stripped to metaphor"),
    ("Trade-press copy painted the proof of Pythagoras as a "
     "boulder rolling downhill under the force of cultural inertia.",
     "pythagorean proof as boulder"),
    ("Conference small-talk reduced the diagonalisation theorem to "
     "a kind of tidal lullaby with mathematical garnish.",
     "diagonalisation as lullaby"),
    ("The marketing deck framed the convergence proof as if it were "
     "a kindling fire ready to consume the market.",
     "convergence-as-fire metaphor"),
    ("The keynote treated the prime-number theorem as a heartbeat "
     "underlying the rhythm of macroeconomic forecasts.",
     "prime number theorem as heartbeat"),
    ("In figurative tone the speaker compared the matrix inverse "
     "to a key turning in a metaphysical lock.",
     "matrix inverse as key in lock"),
)


_AUTHORITY_IN_SCIENCE: tuple[tuple[str, str], ...] = (
    ("Professor Halton states that the cell ruptures when the "
     "membrane potential exceeds a measured threshold across "
     "repeated trials.",
     "authority-verb wraps empirical result"),
    ("Dr Yamane published that mitochondrial uptake doubled in the "
     "treated culture across three independent runs.",
     "publication verb + measured doubling"),
    ("The institute's director claimed that nitrogen fixation "
     "improved by twelve percent in field plots last season.",
     "director claims empirical percentage"),
    ("According to the working group, polymerisation rates declined "
     "linearly with the substrate concentration measured.",
     "according to + linear decline"),
    ("The senior physicist asserted that the resonance frequency "
     "shifted by half a hertz under cryogenic cooling.",
     "asserted + cryogenic measurement"),
    ("In the closing remarks the dean reported that diagnostic "
     "accuracy improved across the cohort year over year.",
     "dean reports diagnostic improvement"),
    ("Industry consultants declared that crop yields recovered "
     "after the irrigation protocol was revised in the trial plots.",
     "consultants declare empirical recovery"),
    ("The lead investigator announced that pathogen counts in the "
     "soil dropped to undetectable levels after fumigation.",
     "investigator announces an empirical drop"),
    ("A regulatory adviser concluded that ferritin levels stabilised "
     "across the patient registry within six months.",
     "adviser concludes empirical stabilisation"),
    ("Visiting professor Lin said the catalyst's activity halved "
     "every time the pH was lowered past five.",
     "professor says with measured halving"),
    ("The trade-press analyst reported that battery cycling losses "
     "dropped sharply after the new electrolyte was deployed.",
     "analyst reports empirical loss drop"),
    ("Spokespersons for the consortium claimed that copper isotope "
     "ratios shifted in the post-eruption sediment cores.",
     "spokesperson claims isotope ratios"),
    ("Officials publicly said that vaccination uptake correlated "
     "tightly with reported case counts in the regional bulletin.",
     "officials say + tight correlation"),
    ("Editorial commentary declared that mortality fell across the "
     "intervention arm in the published clinical bulletin.",
     "editorial declares empirical mortality drop"),
    ("In the panel summary the moderator said the metabolic rate "
     "of the cohort tracked closely with caffeine intake records.",
     "moderator-said + cohort metabolism tracking"),
)


_LEGAL_QUANTIFIERS: tuple[tuple[str, str], ...] = (
    ("Every defendant who entered the premises without consent is, "
     "under the relevant statute, treated as having trespassed.",
     "every-defendant + statute → logic + legal"),
    ("All taxpayers who file before the statutory deadline are "
     "entitled to the deduction by every operative provision.",
     "all-taxpayers + statutory deadline"),
    ("For every plaintiff with documented standing the constitution "
     "guarantees a hearing, and every clause of the act echoes the "
     "guarantee.",
     "for-every + constitution"),
    ("Each tenant with a notarised lease and proof of residence is "
     "by definition protected from summary eviction under the act.",
     "each-tenant + by-definition"),
    ("All licensees that complete the prescribed training are "
     "considered, by every term of the ordinance, qualified for "
     "renewal.",
     "all-licensees + ordinance"),
    ("Every appellant who serves notice within thirty days is, by "
     "the strict terms of the regulation, entitled to a stay.",
     "every-appellant + regulation"),
    ("All claimants who meet the residency requirement are, by "
     "definition, included in the registered benefit pool.",
     "all-claimants + by-definition"),
    ("Each beneficiary listed in the will is, by every operative "
     "clause, treated as having a present interest in the estate.",
     "each-beneficiary + every-clause"),
    ("Every employer subject to the safety code is bound, under "
     "each section, to maintain a documented training programme.",
     "every-employer + each-section"),
    ("For all parties to the contract, the arbitration clause is, "
     "by the express words of the agreement, mandatory.",
     "for-all-parties + arbitration"),
    ("Every witness subpoenaed by the court is, by definition under "
     "the procedural rule, compelled to appear at the hearing.",
     "every-witness + procedural rule"),
    ("All inheritors named in the codicil are, by each operative "
     "phrase, granted a share equivalent to that of the primary "
     "beneficiaries.",
     "all-inheritors + each-phrase"),
    ("Every shareholder who attended the meeting is, by the bylaws "
     "in their current form, entitled to vote on every resolution "
     "presented.",
     "every-shareholder + bylaws + every-resolution"),
    ("All licensees whose certifications are current are, by every "
     "section of the licensing code, fit to practise within the "
     "jurisdiction.",
     "all-licensees + every-section"),
    ("Every plaintiff who establishes prima facie standing is, by "
     "definition of the rule, entitled to discovery from each named "
     "defendant.",
     "every-plaintiff + by-definition + each-named"),
)


_MATH_FLOURISHES: tuple[tuple[str, str], ...] = (
    ("His patience converged like a Cauchy sequence in the warm "
     "evening light, leaving no room for further doubt.",
     "Cauchy sequence as simile"),
    ("Loosely speaking the project plan unfolded like a polynomial "
     "of odd degree, crossing every milestone exactly once.",
     "polynomial-degree simile"),
    ("Her arguments were as transitive as an inclusion of subsets, "
     "carrying weight from premise to conclusion effortlessly.",
     "subset-inclusion simile"),
    ("Like a sequence that is monotone and bounded, the team's "
     "morale rose steadily toward some unseen limit.",
     "monotone-bounded simile"),
    ("The negotiation proceeded as if every concession were a "
     "lemma supporting the eventual theorem of agreement.",
     "lemma-theorem simile"),
    ("In a sense his rhetoric was a continuous function on a closed "
     "interval, attaining its maximum exactly when needed.",
     "extreme-value-theorem simile"),
    ("Her recall of the data was as transitive as alternating "
     "interior angles, with every implication visibly preserved.",
     "alternating-angle simile"),
    ("The market behaved like an absolutely convergent series, "
     "rearranging itself overnight without changing the headline "
     "total.",
     "absolute-convergence simile"),
    ("Loosely speaking the panel's reasoning had the structure of "
     "modus ponens dressed up in seasonal allusions.",
     "modus-ponens-as-decoration"),
    ("The CEO's confidence was as inevitable as a divergent harmonic "
     "series, growing past every conceivable bound.",
     "harmonic-divergence simile"),
    ("Like a graph in which every vertex is incident to every other, "
     "the executive team's communication appeared exhaustively "
     "connected.",
     "complete-graph simile"),
    ("In a sense the manager's diagonalisation argument was a way "
     "of saying nobody had attended on time.",
     "diagonalisation-as-excuse"),
    ("The architect described her concept as a polynomial whose "
     "roots were emotional rather than algebraic.",
     "polynomial-with-emotional-roots"),
    ("Her speech read like an induction step with the base case "
     "tacitly understood as cultural common ground.",
     "induction-base-as-cultural"),
    ("Like an ideal in a principal ideal domain, the founder's "
     "vision was generated by a single guiding insight.",
     "ideal-in-PID simile"),
)


_CONTEXT_POISON: tuple[tuple[str, str], ...] = (
    ("Workshop hosts moved straight from the patient cohort summary "
     "into a freewheeling discussion of celestial poetry.",
     "medical context bleeds into poetic flourish"),
    ("After the bench experiment write-up the chair gave a long "
     "speech praising the founders in lofty rhetorical style.",
     "experiment context jumps to founder eulogy"),
    ("The chapter on operative statutes was followed without warning "
     "by an aside on the metaphor of judicial sunlight.",
     "legal text drifts into metaphor"),
    ("Between successive lemmas the lecturer inserted a folksy "
     "anecdote about how every theorem felt like an old friend.",
     "between-lemmas folksy aside"),
    ("After the safety-audit bullet list, the speaker reflected on "
     "how every quarterly report resembles a sunrise of intent.",
     "audit bullets followed by sunrise metaphor"),
    ("The proceedings paired a chemistry yield table with a poetic "
     "reflection on entropy as the soul of the laboratory.",
     "yield-table + soul-of-the-lab metaphor"),
    ("The handbook moved from a clinical case discussion into a "
     "first-person musing on language and possibility.",
     "clinical-case + first-person musing"),
    ("After the contractual exegesis the panel wandered into a "
     "discussion of authority as a kind of music in the boardroom.",
     "contract-exegesis + boardroom-music"),
    ("In the appendix the maths chapter was followed by a personal "
     "essay describing convergence as a kind of solitude.",
     "math + solitude essay"),
    ("Between two strict syllogisms the lecturer paused to lament "
     "the lost romance of slide-rule typography.",
     "syllogisms split by typography lament"),
    ("The annual report mixed sales tables with an extended simile "
     "comparing the new product to a forgotten lullaby.",
     "tables + lullaby simile"),
    ("Just after the dose-response section the editor included a "
     "long meditation on how science is itself a kind of jazz.",
     "dose-response + jazz meditation"),
    ("Following the proof of the rank-nullity theorem the editor "
     "added a tender sketch of a sleeping cat.",
     "rank-nullity + sleeping cat sketch"),
    ("The compliance chapter ended on a poetic note about "
     "documentation as a long quiet river of memory.",
     "compliance + memory river"),
    ("In a foreword to the legal manual the author described every "
     "statute as a slowly cooling star in the night sky.",
     "legal manual + cooling-star image"),
    ("The proceedings transitioned without warning from a chemistry "
     "yield discussion to a soliloquy about the smell of rain.",
     "yield discussion + smell-of-rain soliloquy"),
    ("After the clinical trial summary the chairperson recited a "
     "favourite limerick about the inevitability of paperwork.",
     "trial summary + limerick"),
    ("The benchmark report ended on a quiet paragraph about how "
     "every footnote feels like the sea at low tide.",
     "benchmark + low-tide footnote"),
    ("Within one paragraph the textbook moved from a careful proof "
     "of Bezout's identity to a personal recipe for spinach soup.",
     "Bezout + spinach soup"),
    ("Between sections on litigation strategy the writer paused for "
     "a wistful page about train stations seen at dawn.",
     "litigation + train-station wistfulness"),
    ("After a clean derivation of the closed-form integral the "
     "preface returned to a memory of harbour bells at autumn.",
     "integral derivation + harbour bells"),
    ("The textbook closed a chapter on commutative rings with a "
     "personal note about the silence of empty libraries.",
     "rings + library-silence personal note"),
    ("Between the trial protocol and the consent form the editor "
     "placed a brief reflection on the geometry of waiting rooms.",
     "trial-protocol + waiting-room geometry"),
    ("After a thorough treatment of the dominated convergence "
     "theorem the appendix included a recipe for elderflower tea.",
     "dominated convergence + elderflower recipe"),
    ("The committee summary moved from a vote tally into a "
     "monologue about how every motion feels like an old lighthouse.",
     "vote tally + lighthouse monologue"),
)


def _make_family(
    base: tuple[tuple[str, str], ...], family: str, prefix: str,
) -> tuple[FrameNC, ...]:
    out: list[FrameNC] = []
    for i, (text, rationale) in enumerate(base, start=1):
        out.append(FrameNC(
            nc_id=f"{prefix}{i:03d}", text=text,
            family=family, rationale=rationale,
        ))
    return tuple(out)


def all_negative_controls() -> tuple[FrameNC, ...]:
    out: list[FrameNC] = []
    out.extend(_make_family(
        _ENTROPY, "entropy_collision", "NC-EC",
    ))
    out.extend(_make_family(
        _METAPHOR_EQUATIONS, "metaphorised_equation", "NC-ME",
    ))
    out.extend(_make_family(
        _AUTHORITY_IN_SCIENCE, "authority_in_science", "NC-AS",
    ))
    out.extend(_make_family(
        _LEGAL_QUANTIFIERS, "legal_quantifier_drift", "NC-LQ",
    ))
    out.extend(_make_family(
        _MATH_FLOURISHES, "mathematical_flourish", "NC-MF",
    ))
    out.extend(_make_family(
        _CONTEXT_POISON, "context_poison", "NC-CP",
    ))
    return tuple(out)


__all__ = ["FrameNC", "all_negative_controls"]
