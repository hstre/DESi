"""80 paraphrase groups (8 frames × 10 groups) plus 8 negative
controls — Aufgaben 2 + 7.

The paraphrases are *hand-written*. They use the frame markers
v3.4's :class:`FrameDetector` recognises so the audit measures
detector *invariance* under wording change, not detector coverage.

Groups whose canonical text legitimately surfaces ``FRAME_CONFLICT``
under v3.4 (e.g. bare 'entropy' that triggers both thermodynamic
and information-theoretic buckets) are flagged with
``expected_conflict_allowed=True``.
"""
from __future__ import annotations

from ..frames import FrameKind
from .case import ParaphraseGroup


def _g(
    gid: str,
    frame: FrameKind,
    forbidden: tuple[FrameKind, ...],
    canonical: str,
    *paraphrases: str,
    conflict_allowed: bool = False,
) -> ParaphraseGroup:
    return ParaphraseGroup(
        group_id=gid,
        expected_frame=frame,
        forbidden_frames=forbidden,
        expected_conflict_allowed=conflict_allowed,
        canonical_text=canonical,
        paraphrases=paraphrases,
    )


# ---------------------------------------------------------------------------
# 1. THERMODYNAMIC — 10 groups
# ---------------------------------------------------------------------------

_T_FORBIDDEN: tuple[FrameKind, ...] = (FrameKind.METAPHORICAL,)

THERMODYNAMIC_GROUPS = (
    _g("T01", FrameKind.THERMODYNAMIC, _T_FORBIDDEN,
       "Frame: thermodynamic. Heat conduction occurs through gradients.",
       "Frame: thermodynamic. Heat flows along a temperature gradient.",
       "Frame: thermodynamic. Thermal conduction follows the gradient.",
       "Frame: thermodynamic. Heat traverses temperature gradients.",
       "Frame: thermodynamic. Heat moves through a gradient."),
    _g("T02", FrameKind.THERMODYNAMIC, _T_FORBIDDEN,
       "Frame: thermodynamic. Heat flows from hot to cold reservoirs.",
       "Frame: thermodynamic. Heat travels from hot reservoirs to cold ones.",
       "Frame: thermodynamic. A hot reservoir loses heat to a colder one.",
       "Frame: thermodynamic. Heat conducts hot to cold.",
       "Frame: thermodynamic. Heat dissipates from warmer to cooler bodies."),
    _g("T03", FrameKind.THERMODYNAMIC, _T_FORBIDDEN,
       "Frame: thermodynamic. Temperature has units of kelvin.",
       "Frame: thermodynamic. The temperature unit is the kelvin.",
       "Frame: thermodynamic. We measure temperature in kelvin.",
       "Frame: thermodynamic. Kelvin denotes a temperature scale.",
       "Frame: thermodynamic. Temperature is reported in kelvin."),
    _g("T04", FrameKind.THERMODYNAMIC, _T_FORBIDDEN,
       "Frame: thermodynamic. One joule equals one watt-second of energy.",
       "Frame: thermodynamic. The joule is the SI unit of energy.",
       "Frame: thermodynamic. Energy is measured in joule units.",
       "Frame: thermodynamic. A joule is a unit of energy.",
       "Frame: thermodynamic. Joule equals one newton-meter of work."),
    _g("T05", FrameKind.THERMODYNAMIC, _T_FORBIDDEN,
       "Frame: thermodynamic. A Carnot engine bounds heat-to-work efficiency.",
       "Frame: thermodynamic. The Carnot cycle defines maximum heat-engine efficiency.",
       "Frame: thermodynamic. Heat-engine efficiency cannot exceed the Carnot bound.",
       "Frame: thermodynamic. Carnot limits the heat-engine yield.",
       "Frame: thermodynamic. Carnot's theorem caps heat-to-work conversion."),
    _g("T06", FrameKind.THERMODYNAMIC, _T_FORBIDDEN,
       "Frame: thermodynamic. Thermal conductivity is a material property.",
       "Frame: thermodynamic. Conductivity for heat depends on the material.",
       "Frame: thermodynamic. A material has a characteristic thermal conductivity.",
       "Frame: thermodynamic. Thermal-conductivity values vary by material.",
       "Frame: thermodynamic. Conductivity quantifies heat transport in a material."),
    _g("T07", FrameKind.THERMODYNAMIC, _T_FORBIDDEN,
       "Frame: thermodynamic. Free energy minimisation drives spontaneity.",
       "Frame: thermodynamic. Spontaneous processes minimise free energy.",
       "Frame: thermodynamic. Free-energy minima mark equilibrium.",
       "Frame: thermodynamic. Free-energy minimisation predicts direction.",
       "Frame: thermodynamic. Minimising free energy yields spontaneous flow."),
    _g("T08", FrameKind.THERMODYNAMIC, _T_FORBIDDEN,
       "Frame: thermodynamic. Adiabatic compression raises temperature.",
       "Frame: thermodynamic. Compression without heat exchange increases temperature.",
       "Frame: thermodynamic. Temperature rises under adiabatic compression.",
       "Frame: thermodynamic. Adiabatically compressed gas warms up.",
       "Frame: thermodynamic. An adiabatic squeeze raises the temperature."),
    _g("T09", FrameKind.THERMODYNAMIC, _T_FORBIDDEN,
       "Frame: thermodynamic. Latent heat accompanies phase transitions.",
       "Frame: thermodynamic. Phase changes absorb or release latent heat.",
       "Frame: thermodynamic. Latent heat is exchanged during a phase change.",
       "Frame: thermodynamic. A phase transition involves latent heat.",
       "Frame: thermodynamic. Heat is hidden in latent-heat phase transitions."),
    _g("T10", FrameKind.THERMODYNAMIC, _T_FORBIDDEN,
       "Frame: thermodynamic. Specific heat capacity is energy per kelvin per kilogram.",
       "Frame: thermodynamic. Heat capacity per kilogram has units joule per kelvin.",
       "Frame: thermodynamic. Specific-heat values are joule per kilogram-kelvin.",
       "Frame: thermodynamic. Specific heat is joules per kilogram per kelvin.",
       "Frame: thermodynamic. Heat capacity has joule-per-kelvin-per-kilogram units."),
)


# ---------------------------------------------------------------------------
# 2. INFORMATION_THEORETIC — 10 groups
# ---------------------------------------------------------------------------

_I_FORBIDDEN: tuple[FrameKind, ...] = (FrameKind.METAPHORICAL,)

INFORMATION_GROUPS = (
    _g("I01", FrameKind.INFORMATION_THEORETIC, _I_FORBIDDEN,
       "Shannon entropy of a fair coin is exactly one bit.",
       "A fair coin carries one bit of Shannon entropy.",
       "Shannon entropy equals one bit for a fair coin.",
       "Fair coins have one-bit Shannon entropy.",
       "One bit of Shannon entropy per fair coin flip."),
    _g("I02", FrameKind.INFORMATION_THEORETIC, _I_FORBIDDEN,
       "Mutual information between two channels is symmetric.",
       "Channel mutual information is symmetric in both arguments.",
       "Mutual information between X and Y equals that of Y and X.",
       "Symmetric mutual information characterises information channels.",
       "Mutual information across a channel is order-independent."),
    _g("I03", FrameKind.INFORMATION_THEORETIC, _I_FORBIDDEN,
       "Channel capacity bounds reliable communication rate in bits.",
       "Reliable channel rate cannot exceed channel capacity bits-per-use.",
       "Channel-capacity in bits limits reliable data throughput.",
       "Reliable bits-per-symbol is bounded by channel capacity.",
       "The channel-capacity bound caps reliable transmission bits."),
    _g("I04", FrameKind.INFORMATION_THEORETIC, _I_FORBIDDEN,
       "Compression ratio is bounded by Shannon entropy in bits.",
       "Shannon entropy bounds achievable compression bits-per-symbol.",
       "Optimal compression in bits matches Shannon entropy.",
       "No compression beats the Shannon entropy bound in bits.",
       "Compression bits are lower-bounded by Shannon's entropy."),
    _g("I05", FrameKind.INFORMATION_THEORETIC, _I_FORBIDDEN,
       "Kolmogorov complexity in bits is uncomputable in the limit.",
       "The Kolmogorov complexity of a string in bits is uncomputable.",
       "Kolmogorov bit-length is uncomputable in general.",
       "Uncomputable Kolmogorov complexity bounds compression in bits.",
       "Kolmogorov-complexity bits cannot be computed exactly."),
    _g("I06", FrameKind.INFORMATION_THEORETIC, _I_FORBIDDEN,
       "Information-theoretic security implies unconditional bit secrecy.",
       "Bit-level information-theoretic security needs no computational assumption.",
       "Unconditional secrecy in bits is information-theoretic security.",
       "Information-theoretic bit secrecy survives unbounded adversaries.",
       "Information-theoretic security guarantees bit secrecy unconditionally."),
    _g("I07", FrameKind.INFORMATION_THEORETIC, _I_FORBIDDEN,
       "Mutual information drops to zero under independence in bits.",
       "Independent variables have zero bits of mutual information.",
       "Mutual information vanishes in bits for independent variables.",
       "Independence implies zero-bit mutual information.",
       "Independent X and Y share zero bits of mutual information."),
    _g("I08", FrameKind.INFORMATION_THEORETIC, _I_FORBIDDEN,
       "Channel capacity for a binary symmetric channel is 1 minus binary entropy in bits.",
       "BSC channel capacity equals one bit minus binary entropy.",
       "For a binary symmetric channel the bits-per-use capacity is one minus binary entropy.",
       "The bits-per-use BSC capacity is the complement of binary entropy.",
       "Binary symmetric channels yield 1-H(p) bits of capacity."),
    _g("I09", FrameKind.INFORMATION_THEORETIC, _I_FORBIDDEN,
       "Bits-per-symbol rate cannot exceed channel capacity in bits.",
       "Per-symbol bit rate is bounded by channel capacity bits.",
       "The bits-per-symbol limit is the bits of channel capacity.",
       "Channel-capacity bits cap the bits-per-symbol throughput.",
       "Bits-per-symbol is at most the channel-capacity bits."),
    _g("I10", FrameKind.INFORMATION_THEORETIC, _I_FORBIDDEN,
       "Shannon's source-coding theorem bounds expected bits-per-symbol.",
       "Source coding bounds the expected bits per symbol by Shannon entropy.",
       "Expected bits-per-symbol cannot beat the Shannon source-coding bound.",
       "Shannon's source-coding limit caps the expected bits per symbol.",
       "Shannon source-coding bounds bits-per-symbol expectation."),
)


# ---------------------------------------------------------------------------
# 3. ONTOLOGICAL_DISTINGUISHABILITY — 10 groups
# ---------------------------------------------------------------------------

_O_FORBIDDEN: tuple[FrameKind, ...] = (FrameKind.METAPHORICAL,)

ONTOLOGICAL_GROUPS = (
    _g("O01", FrameKind.ONTOLOGICAL_DISTINGUISHABILITY, _O_FORBIDDEN,
       "Two electrons in the same quantum state are indistinguishable.",
       "Electrons in the same state are indistinguishable.",
       "Identical-state electrons are indistinguishable.",
       "Electrons sharing the same state are indistinguishable particles.",
       "Indistinguishable: two electrons in the same state."),
    _g("O02", FrameKind.ONTOLOGICAL_DISTINGUISHABILITY, _O_FORBIDDEN,
       "Frame: ontological distinguishability. The morning star and the evening star are the same object.",
       "Frame: ontological distinguishability. Morning star and evening star refer to the same object.",
       "Frame: ontological distinguishability. They denote the same object: morning star, evening star.",
       "Frame: ontological distinguishability. Both names pick out the same object.",
       "Frame: ontological distinguishability. Same object, two names: morning and evening star."),
    _g("O03", FrameKind.ONTOLOGICAL_DISTINGUISHABILITY, _O_FORBIDDEN,
       "These two atoms are numerically identical in the experiment.",
       "The two atoms count as numerically identical.",
       "Numerically identical atoms feature in the experiment.",
       "Atomic pair is numerically identical in this setup.",
       "Numerically identical: both atoms in this trial."),
    _g("O04", FrameKind.ONTOLOGICAL_DISTINGUISHABILITY, _O_FORBIDDEN,
       "Witness identity was preserved throughout the protocol.",
       "The identity of the witness was preserved by the protocol.",
       "Protocol preserved witness identity end to end.",
       "Witness identity remained preserved by protocol design.",
       "Protocol kept the witness identity intact."),
    _g("O05", FrameKind.ONTOLOGICAL_DISTINGUISHABILITY, _O_FORBIDDEN,
       "Frame: ontological distinguishability. Ontological commitment entails distinguishable referents.",
       "Frame: ontological distinguishability. Ontological commitment requires distinguishable referents.",
       "Frame: ontological distinguishability. Distinguishable referents follow from ontological commitment.",
       "Frame: ontological distinguishability. To commit ontologically is to posit distinguishable referents.",
       "Frame: ontological distinguishability. Ontological commitment yields distinguishable referents."),
    _g("O06", FrameKind.ONTOLOGICAL_DISTINGUISHABILITY, _O_FORBIDDEN,
       "Frame: ontological distinguishability. Indiscernibility of identicals is Leibniz's principle.",
       "Frame: ontological distinguishability. Leibniz formulated indiscernibility of identicals.",
       "Frame: ontological distinguishability. Indistinguishable identicals: Leibniz's law.",
       "Frame: ontological distinguishability. Leibniz: identicals are indistinguishable.",
       "Frame: ontological distinguishability. Identicals are indistinguishable, per Leibniz."),
    _g("O07", FrameKind.ONTOLOGICAL_DISTINGUISHABILITY, _O_FORBIDDEN,
       "The reference of 'Hesperus' and 'Phosphorus' is the same object.",
       "Hesperus and Phosphorus share the same object as reference.",
       "Same object: the reference of Hesperus and Phosphorus.",
       "Both Hesperus and Phosphorus pick out the same object.",
       "Hesperus and Phosphorus refer to the same object."),
    _g("O08", FrameKind.ONTOLOGICAL_DISTINGUISHABILITY, _O_FORBIDDEN,
       "Frame: ontological distinguishability. Identity over time is a metaphysical question.",
       "Frame: ontological distinguishability. Identity-over-time raises a metaphysical question.",
       "Frame: ontological distinguishability. Persistence of identity is a metaphysical matter.",
       "Frame: ontological distinguishability. Identity over time poses a metaphysics question.",
       "Frame: ontological distinguishability. Persistence and identity are metaphysical."),
    _g("O09", FrameKind.ONTOLOGICAL_DISTINGUISHABILITY, _O_FORBIDDEN,
       "Bosons of the same state are indistinguishable particles.",
       "Same-state bosons count as indistinguishable.",
       "Bosons sharing a state are indistinguishable particles.",
       "Indistinguishable: bosons in identical states.",
       "Same-state bosons are indistinguishable."),
    _g("O10", FrameKind.ONTOLOGICAL_DISTINGUISHABILITY, _O_FORBIDDEN,
       "Frame: ontological distinguishability. The morning star is the same object as Venus.",
       "Frame: ontological distinguishability. Venus and the morning star are the same object.",
       "Frame: ontological distinguishability. Same object: morning star and Venus.",
       "Frame: ontological distinguishability. Morning-star equals Venus, same object.",
       "Frame: ontological distinguishability. Venus is the morning-star same object."),
)


# ---------------------------------------------------------------------------
# 4. METAPHORICAL — 10 groups
# ---------------------------------------------------------------------------

_M_FORBIDDEN: tuple[FrameKind, ...] = (
    FrameKind.TOOL_COMPUTABLE,
)

METAPHORICAL_GROUPS = (
    _g("M01", FrameKind.METAPHORICAL, _M_FORBIDDEN,
       "The market is nervous, like a herd of deer.",
       "Markets behave like a nervous herd.",
       "Like a deer-herd the market is jumpy.",
       "The trading floor is like a deer in headlights.",
       "Like a herd, the market spooks at every shock."),
    _g("M02", FrameKind.METAPHORICAL, _M_FORBIDDEN,
       "Loosely speaking, time flies.",
       "Time flies, loosely speaking.",
       "Loosely speaking, time has wings.",
       "Loosely speaking, time is fleeting.",
       "Loosely speaking, time slips away."),
    _g("M03", FrameKind.METAPHORICAL, _M_FORBIDDEN,
       "He spoke as if he were the king of his domain.",
       "As if a king, he ruled his domain in speech.",
       "He talked as if he commanded an empire.",
       "As if he owned the country, he gave his speech.",
       "He addressed them as if their king."),
    _g("M04", FrameKind.METAPHORICAL, _M_FORBIDDEN,
       "In a sense every particle is everywhere at once.",
       "In a sense, particles are ubiquitous.",
       "In a sense particles occupy all positions.",
       "In a sense each particle is everywhere.",
       "In a sense particles spread across space."),
    _g("M05", FrameKind.METAPHORICAL, _M_FORBIDDEN,
       "Metaphorically, the company has a heart of stone.",
       "Metaphorically speaking, this firm is stone-hearted.",
       "Metaphorically, the company's heart is stone.",
       "Metaphorically, the firm has a stone heart.",
       "Metaphorically the firm is heart-of-stone."),
    _g("M06", FrameKind.METAPHORICAL, _M_FORBIDDEN,
       "Loosely speaking the algorithm runs in linear time.",
       "Loosely speaking, runtime grows linearly.",
       "Loosely speaking, the algorithm scales linearly.",
       "Loosely speaking, complexity is linear.",
       "Loosely speaking, the runtime is order n."),
    _g("M07", FrameKind.METAPHORICAL, _M_FORBIDDEN,
       "Frame: metaphorical. Code can smell bad.",
       "Frame: metaphorical. Bad-smelling code is a phrase.",
       "Frame: metaphorical. Code-smell is shorthand for poor design.",
       "Frame: metaphorical. We talk of code that smells bad.",
       "Frame: metaphorical. Some code stinks."),
    _g("M08", FrameKind.METAPHORICAL, _M_FORBIDDEN,
       "Like a fortress, the firewall stood firm.",
       "The firewall stood like a fortress wall.",
       "Like a castle wall, the firewall held.",
       "Like a fortified gate, the firewall did not yield.",
       "The firewall, like a stronghold, did not fall."),
    _g("M09", FrameKind.METAPHORICAL, _M_FORBIDDEN,
       "In a sense the cloud weeps when it rains.",
       "In a sense, rain is the sky's tears.",
       "In a sense the heavens cry.",
       "In a sense clouds shed tears as rain.",
       "In a sense the rain is clouds weeping."),
    _g("M10", FrameKind.METAPHORICAL, _M_FORBIDDEN,
       "Loosely speaking memory is the brain's library.",
       "Loosely speaking the brain houses a memory-library.",
       "Loosely speaking memories live in a brain-library.",
       "Loosely speaking the brain's library holds memories.",
       "Loosely speaking the brain shelves memories like a library."),
)


# ---------------------------------------------------------------------------
# 5. FORMAL_LOGIC — 10 groups (all use explicit marker to avoid
#    detection collisions with EMPIRICAL_CAUSAL 'because' etc.)
# ---------------------------------------------------------------------------

_F_FORBIDDEN: tuple[FrameKind, ...] = (FrameKind.AUTHORITY_SPEECH,)

FORMAL_LOGIC_GROUPS = (
    _g("F01", FrameKind.FORMAL_LOGIC, _F_FORBIDDEN,
       "Frame: formal logic. Modus ponens preserves truth.",
       "Frame: formal logic. Truth is preserved by modus ponens.",
       "Frame: formal logic. Modus ponens is truth-preserving.",
       "Frame: formal logic. Truth survives modus ponens.",
       "Frame: formal logic. Modus ponens is a valid inference rule."),
    _g("F02", FrameKind.FORMAL_LOGIC, _F_FORBIDDEN,
       "Frame: formal logic. From A->B and B->C we derive A->C.",
       "Frame: formal logic. A->B plus B->C entails A->C.",
       "Frame: formal logic. A->C follows from A->B and B->C.",
       "Frame: formal logic. The chain A->B, B->C yields A->C.",
       "Frame: formal logic. A->C is derivable from A->B and B->C."),
    _g("F03", FrameKind.FORMAL_LOGIC, _F_FORBIDDEN,
       "Frame: formal logic. Every x is at least one y in this domain.",
       "Frame: formal logic. Every x in the domain is one or more y.",
       "Frame: formal logic. Every x maps to at least one y.",
       "Frame: formal logic. Every x is at least one y here.",
       "Frame: formal logic. Each x in the domain is one or more y."),
    _g("F04", FrameKind.FORMAL_LOGIC, _F_FORBIDDEN,
       "Frame: formal logic. A syllogism with two universal premises closes deductively.",
       "Frame: formal logic. Two universal premises close a syllogism deductively.",
       "Frame: formal logic. Deductive closure follows from two universal premises in a syllogism.",
       "Frame: formal logic. A syllogism closes when both premises are universal.",
       "Frame: formal logic. With two universals a syllogism is deductively closed."),
    _g("F05", FrameKind.FORMAL_LOGIC, _F_FORBIDDEN,
       "Frame: formal logic. P and not-P entails any proposition.",
       "Frame: formal logic. From P and not-P any proposition follows.",
       "Frame: formal logic. A contradiction entails anything.",
       "Frame: formal logic. Anything follows from P and not-P.",
       "Frame: formal logic. Explosion: from a contradiction, anything."),
    _g("F06", FrameKind.FORMAL_LOGIC, _F_FORBIDDEN,
       "Frame: formal logic. Universal instantiation specialises a quantified claim.",
       "Frame: formal logic. A universal claim specialises by instantiation.",
       "Frame: formal logic. Universal instantiation drops the quantifier.",
       "Frame: formal logic. Instantiating a universal yields a specific claim.",
       "Frame: formal logic. From universal to instance: universal instantiation."),
    _g("F07", FrameKind.FORMAL_LOGIC, _F_FORBIDDEN,
       "Frame: formal logic. Existential generalisation introduces a quantifier.",
       "Frame: formal logic. Adding the existential quantifier is generalisation.",
       "Frame: formal logic. Existential generalisation lifts an instance.",
       "Frame: formal logic. From an instance to an existential quantifier.",
       "Frame: formal logic. Quantifying existentially generalises a claim."),
    _g("F08", FrameKind.FORMAL_LOGIC, _F_FORBIDDEN,
       "Frame: formal logic. Conjunction introduction needs both conjuncts.",
       "Frame: formal logic. Both conjuncts are required to introduce a conjunction.",
       "Frame: formal logic. Forming a conjunction needs each conjunct in hand.",
       "Frame: formal logic. Conjunction-introduction requires the two conjuncts.",
       "Frame: formal logic. To introduce a conjunction, supply both conjuncts."),
    _g("F09", FrameKind.FORMAL_LOGIC, _F_FORBIDDEN,
       "Frame: formal logic. De Morgan's laws govern negation across conjunction and disjunction.",
       "Frame: formal logic. De Morgan: negation flips conjunction and disjunction.",
       "Frame: formal logic. De Morgan rules swap conjunction and disjunction under negation.",
       "Frame: formal logic. De Morgan's law links negation, conjunction, disjunction.",
       "Frame: formal logic. Negation distributes via De Morgan across and/or."),
    _g("F10", FrameKind.FORMAL_LOGIC, _F_FORBIDDEN,
       "Frame: formal logic. A syllogism with one negative premise yields a negative conclusion.",
       "Frame: formal logic. Negative premise forces negative conclusion in a syllogism.",
       "Frame: formal logic. One negative premise in a syllogism gives a negative conclusion.",
       "Frame: formal logic. A syllogism's conclusion is negative if any premise is.",
       "Frame: formal logic. Syllogistic negation propagates to the conclusion."),
)


# ---------------------------------------------------------------------------
# 6. EMPIRICAL_CAUSAL — 10 groups
# ---------------------------------------------------------------------------

_C_FORBIDDEN: tuple[FrameKind, ...] = (FrameKind.FORMAL_LOGIC,)

EMPIRICAL_GROUPS = (
    _g("C01", FrameKind.EMPIRICAL_CAUSAL, _C_FORBIDDEN,
       "Heavy rainfall causes localised flooding.",
       "Localised flooding results in damaged streets after rain.",
       "Power outages led to data loss during the storm.",
       "Drought resulted in crop failure last summer.",
       "The pipeline failure led to product loss."),
    _g("C02", FrameKind.EMPIRICAL_CAUSAL, _C_FORBIDDEN,
       "Inflation rose because of supply-chain disruptions.",
       "Supply disruptions led to inflation rising.",
       "Price increases resulted from logistics breakdowns.",
       "Inflationary pressure led to higher prices.",
       "Logistic failures caused inflation to climb."),
    _g("C03", FrameKind.EMPIRICAL_CAUSAL, _C_FORBIDDEN,
       "Heat waves caused widespread power blackouts.",
       "Blackouts resulted from sustained heat-wave conditions.",
       "Hot weather led to power outages across the region.",
       "Power outages were due to severe heat waves.",
       "Power blackouts resulted from extended heat-wave temperatures."),
    _g("C04", FrameKind.EMPIRICAL_CAUSAL, _C_FORBIDDEN,
       "Pandemic conditions led to economic recession.",
       "Recession results in lost jobs across many sectors.",
       "The pandemic resulted in recessionary pressures.",
       "Pandemic led to widespread economic decline.",
       "Economic recession was caused by pandemic shutdowns."),
    _g("C05", FrameKind.EMPIRICAL_CAUSAL, _C_FORBIDDEN,
       "Currency devaluation led to imports becoming expensive.",
       "Imports became expensive because of devaluation.",
       "The devalued currency results in costlier imports.",
       "Cost of imports rose due to currency devaluation.",
       "Devaluation caused import prices to climb."),
    _g("C06", FrameKind.EMPIRICAL_CAUSAL, _C_FORBIDDEN,
       "Algorithm tuning led to lower latency in the cluster.",
       "Latency dropped because of algorithm tuning.",
       "The tuned algorithm resulted in latency reductions.",
       "Tuning the algorithm led to lower observed latency.",
       "Lower latency was caused by recent tuning."),
    _g("C07", FrameKind.EMPIRICAL_CAUSAL, _C_FORBIDDEN,
       "Vaccine rollout led to a measurable drop in cases.",
       "Case counts dropped because of widespread vaccination.",
       "Cases fell as a result of vaccine deployment.",
       "Vaccination led to a drop in case numbers.",
       "Cases were reduced because of vaccine coverage."),
    _g("C08", FrameKind.EMPIRICAL_CAUSAL, _C_FORBIDDEN,
       "Sustained stress led to chronic health decline.",
       "Chronic stress resulted in deteriorating health.",
       "Health worsened due to ongoing stress.",
       "Long-term stress led to declining health.",
       "Stress caused chronic health problems over time."),
    _g("C09", FrameKind.EMPIRICAL_CAUSAL, _C_FORBIDDEN,
       "Factory openings led to local population growth.",
       "Population growth resulted from new factories opening.",
       "Local populations grew because of factory expansion.",
       "Factory expansion led to demographic growth.",
       "Growth in population was caused by new factories."),
    _g("C10", FrameKind.EMPIRICAL_CAUSAL, _C_FORBIDDEN,
       "Trade-war tariffs led to higher consumer prices.",
       "Consumer prices rose because of tariff increases.",
       "Higher tariffs resulted in costlier consumer goods.",
       "Tariff hikes led to inflation in consumer prices.",
       "Consumer-price increases were caused by tariffs."),
)


# ---------------------------------------------------------------------------
# 7. AUTHORITY_SPEECH — 10 groups
# ---------------------------------------------------------------------------

_A_FORBIDDEN: tuple[FrameKind, ...] = (FrameKind.FORMAL_LOGIC,)

AUTHORITY_GROUPS = (
    _g("A01", FrameKind.AUTHORITY_SPEECH, _A_FORBIDDEN,
       "Professor Smith says the conclusion holds.",
       "Smith claims the conclusion is valid.",
       "Smith stated the result holds.",
       "Smith claimed the verdict.",
       "Smith states the conclusion holds."),
    _g("A02", FrameKind.AUTHORITY_SPEECH, _A_FORBIDDEN,
       "The committee declared the verdict.",
       "The committee announced its verdict.",
       "The committee stated the verdict.",
       "The committee proved the verdict.",
       "The committee claimed the verdict was unanimous."),
    _g("A03", FrameKind.AUTHORITY_SPEECH, _A_FORBIDDEN,
       "According to the report the experiment succeeded.",
       "According to the auditor the test passed.",
       "According to the team the outcome was successful.",
       "According to the chair the run was a success.",
       "According to the lab the experiment succeeded."),
    _g("A04", FrameKind.AUTHORITY_SPEECH, _A_FORBIDDEN,
       "The vendor states the device passes all tests.",
       "The vendor reports the device passes.",
       "The vendor claims the device works.",
       "The vendor said the device is reliable.",
       "The vendor announced device certification."),
    _g("A05", FrameKind.AUTHORITY_SPEECH, _A_FORBIDDEN,
       "Dr Lin published proof that the conjecture holds.",
       "Lin reported proof of the conjecture.",
       "Lin claimed proof of the conjecture.",
       "Lin published the conjecture proof.",
       "Lin announced a proof of the conjecture."),
    _g("A06", FrameKind.AUTHORITY_SPEECH, _A_FORBIDDEN,
       "The spokesperson announced new safety guidelines.",
       "The spokesperson stated new safety rules.",
       "The spokesperson claimed safety guidelines were updated.",
       "The spokesperson declared the new safety policy.",
       "The spokesperson reported new safety guidelines."),
    _g("A07", FrameKind.AUTHORITY_SPEECH, _A_FORBIDDEN,
       "The court ruled in favour of the plaintiff.",
       "According to the court the ruling favours plaintiff.",
       "The court declared in favour of the plaintiff.",
       "The court announced its ruling for the plaintiff.",
       "The court stated the ruling supports the plaintiff."),
    _g("A08", FrameKind.AUTHORITY_SPEECH, _A_FORBIDDEN,
       "The CEO declared a new strategy at the conference.",
       "The CEO announced a new strategy.",
       "The CEO stated the new strategy.",
       "The CEO claimed a new strategy direction.",
       "The CEO published the strategy summary."),
    _g("A09", FrameKind.AUTHORITY_SPEECH, _A_FORBIDDEN,
       "The auditor reported a clean balance sheet.",
       "The auditor stated the books are clean.",
       "The auditor claimed no irregularities.",
       "The auditor announced a clean audit.",
       "The auditor published a clean report."),
    _g("A10", FrameKind.AUTHORITY_SPEECH, _A_FORBIDDEN,
       "The witness stated the suspect was present.",
       "The witness said the suspect was on site.",
       "The witness claimed presence of the suspect.",
       "The witness reported seeing the suspect.",
       "The witness declared the suspect was present."),
)


# ---------------------------------------------------------------------------
# 8. TOOL_COMPUTABLE — 10 groups
# ---------------------------------------------------------------------------

_TC_FORBIDDEN: tuple[FrameKind, ...] = (FrameKind.METAPHORICAL,)

TOOL_GROUPS = (
    _g("X01", FrameKind.TOOL_COMPUTABLE, _TC_FORBIDDEN,
       "What is 2 + 2 ?",
       "Compute 2 + 2.",
       "Calculate the value 2 + 2.",
       "What is the value of 2 + 2 ?",
       "Evaluate the expression 2 + 2."),
    _g("X02", FrameKind.TOOL_COMPUTABLE, _TC_FORBIDDEN,
       "Calculate 17 * 23.",
       "Compute the product 17 * 23.",
       "Evaluate 17 * 23.",
       "What is 17 * 23 ?",
       "Find the value of 17 * 23."),
    _g("X03", FrameKind.TOOL_COMPUTABLE, _TC_FORBIDDEN,
       "How many days from 2020-01-01 to 2020-12-31 ?",
       "Compute days between 2020-01-01 and 2020-12-31.",
       "Calculate the day count from 2020-01-01 to 2020-12-31.",
       "Days between 2020-01-01 and 2020-12-31: how many ?",
       "What is the day count 2020-01-01 to 2020-12-31 ?"),
    _g("X04", FrameKind.TOOL_COMPUTABLE, _TC_FORBIDDEN,
       "Compute the sum 1 + 2 + 3 + 4 + 5.",
       "What is the sum 1 + 2 + 3 + 4 + 5 ?",
       "Calculate 1 + 2 + 3 + 4 + 5.",
       "Evaluate 1 + 2 + 3 + 4 + 5.",
       "Find the value of 1 + 2 + 3 + 4 + 5."),
    _g("X05", FrameKind.TOOL_COMPUTABLE, _TC_FORBIDDEN,
       "Is 144 = 12 * 12 ?",
       "Compute whether 144 = 12 * 12.",
       "Is 12 * 12 = 144 ?",
       "Check that 144 = 12 * 12.",
       "Verify 12 * 12 = 144."),
    _g("X06", FrameKind.TOOL_COMPUTABLE, _TC_FORBIDDEN,
       "What is 25 % of 200 ?",
       "Calculate 25 % of 200.",
       "Compute 25 % of 200.",
       "How many 25 % of 200 ?",
       "Evaluate 25 % of 200."),
    _g("X07", FrameKind.TOOL_COMPUTABLE, _TC_FORBIDDEN,
       "How many vowels in 'mississippi' ?",
       "Compute the vowel count for 'mississippi'.",
       "How many vowels appear in 'mississippi' ?",
       "Calculate vowels in 'mississippi'.",
       "How many vowel letters does 'mississippi' have ?"),
    _g("X08", FrameKind.TOOL_COMPUTABLE, _TC_FORBIDDEN,
       "Compute the value 3 * 4 - 2.",
       "Calculate 3 * 4 - 2.",
       "What is 3 * 4 - 2 ?",
       "Evaluate 3 * 4 - 2.",
       "Find 3 * 4 - 2."),
    _g("X09", FrameKind.TOOL_COMPUTABLE, _TC_FORBIDDEN,
       "Compute 100 / 4.",
       "Calculate 100 / 4.",
       "What is the value 100 / 4 ?",
       "Evaluate 100 / 4.",
       "Find 100 / 4."),
    _g("X10", FrameKind.TOOL_COMPUTABLE, _TC_FORBIDDEN,
       "Compute the difference 50 - 17.",
       "Calculate 50 - 17.",
       "What is 50 - 17 ?",
       "Evaluate 50 - 17.",
       "Find the value 50 - 17."),
)


# ---------------------------------------------------------------------------
# Master corpus
# ---------------------------------------------------------------------------


ALL_GROUPS: tuple[ParaphraseGroup, ...] = (
    THERMODYNAMIC_GROUPS
    + INFORMATION_GROUPS
    + ONTOLOGICAL_GROUPS
    + METAPHORICAL_GROUPS
    + FORMAL_LOGIC_GROUPS
    + EMPIRICAL_GROUPS
    + AUTHORITY_GROUPS
    + TOOL_GROUPS
)


# ---------------------------------------------------------------------------
# Negative controls — Aufgabe 7
# ---------------------------------------------------------------------------


from dataclasses import dataclass


@dataclass(frozen=True)
class NegativeControl:
    """One paraphrase pair where the frame *legitimately* shifts."""

    nc_id: str
    text_a: str
    text_b: str
    frame_a: FrameKind
    frame_b: FrameKind


NEGATIVE_CONTROLS: tuple[NegativeControl, ...] = (
    NegativeControl(
        nc_id="N01-thermo-vs-info",
        text_a="Frame: thermodynamic. Entropy increases in a closed physical system.",
        text_b="Frame: information-theoretic. Entropy of a message distribution is one bit.",
        frame_a=FrameKind.THERMODYNAMIC,
        frame_b=FrameKind.INFORMATION_THEORETIC,
    ),
    NegativeControl(
        nc_id="N02-info-vs-metaphor",
        text_a="Shannon entropy bounds compression in bits.",
        text_b="Loosely speaking, the brain compresses memories like a poet.",
        frame_a=FrameKind.INFORMATION_THEORETIC,
        frame_b=FrameKind.METAPHORICAL,
    ),
    NegativeControl(
        nc_id="N03-ontological-vs-empirical",
        text_a="Frame: ontological distinguishability. Hesperus and Phosphorus refer to the same object.",
        text_b="Heavy rainfall causes localised flooding.",
        frame_a=FrameKind.ONTOLOGICAL_DISTINGUISHABILITY,
        frame_b=FrameKind.EMPIRICAL_CAUSAL,
    ),
    NegativeControl(
        nc_id="N04-metaphor-vs-tool",
        text_a="Like a fortress, the firewall stood firm.",
        text_b="Compute the sum 1 + 2 + 3.",
        frame_a=FrameKind.METAPHORICAL,
        frame_b=FrameKind.TOOL_COMPUTABLE,
    ),
    NegativeControl(
        nc_id="N05-formal-vs-causal",
        text_a="Frame: formal logic. Modus ponens preserves truth.",
        text_b="Drought resulted in crop failure last summer.",
        frame_a=FrameKind.FORMAL_LOGIC,
        frame_b=FrameKind.EMPIRICAL_CAUSAL,
    ),
    NegativeControl(
        nc_id="N06-causal-vs-authority",
        text_a="Inflation rose because of supply-chain disruptions.",
        text_b="The auditor reported a clean balance sheet.",
        frame_a=FrameKind.EMPIRICAL_CAUSAL,
        frame_b=FrameKind.AUTHORITY_SPEECH,
    ),
    NegativeControl(
        nc_id="N07-authority-vs-tool",
        text_a="Professor Smith says the conclusion holds.",
        text_b="What is 17 * 23 ?",
        frame_a=FrameKind.AUTHORITY_SPEECH,
        frame_b=FrameKind.TOOL_COMPUTABLE,
    ),
    NegativeControl(
        nc_id="N08-tool-vs-thermo",
        text_a="Compute 100 / 4.",
        text_b="Frame: thermodynamic. Adiabatic compression raises temperature.",
        frame_a=FrameKind.TOOL_COMPUTABLE,
        frame_b=FrameKind.THERMODYNAMIC,
    ),
)


__all__ = [
    "ALL_GROUPS",
    "AUTHORITY_GROUPS",
    "EMPIRICAL_GROUPS",
    "FORMAL_LOGIC_GROUPS",
    "INFORMATION_GROUPS",
    "METAPHORICAL_GROUPS",
    "NEGATIVE_CONTROLS",
    "NegativeControl",
    "ONTOLOGICAL_GROUPS",
    "THERMODYNAMIC_GROUPS",
    "TOOL_GROUPS",
]
