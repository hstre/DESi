"""Aufgabe 3 — external corpus assembly.

Five domains plus a negative-control bank, all hand-crafted in
the audit author's own words to match domain conventions.

No DESi runtime output is used. Ground truth is the audit
author's annotation, not a derived label. Each chain is
disjoint from the existing DESi corpora (verified by
``contamination.py``).
"""
from __future__ import annotations

from dataclasses import dataclass

from .enums import Domain, GroundTruth


_TRANSITIONS_PER_CHAIN: int = 4


@dataclass(frozen=True)
class ExternalChain:
    chain_id: str
    domain: Domain
    text: str
    ground_truth: GroundTruth
    rationale: str

    def to_dict(self) -> dict[str, str]:
        return {
            "chain_id": self.chain_id,
            "domain": self.domain.value,
            "text": self.text,
            "ground_truth": self.ground_truth.value,
            "rationale": self.rationale,
        }


# Per-domain templates: a sequence of (subject, verb, object)
# triples that are recombined into 3-sentence chains. Each
# template carries a label and a rationale; the generator
# multiplies them by domain-specific substitution sets.

def _chain(prefix: str, idx: int, premise_a: str,
           premise_b: str, conclusion: str,
           domain: Domain, label: GroundTruth,
           rationale: str) -> ExternalChain:
    text = f"{premise_a}. {premise_b}. Therefore {conclusion}."
    return ExternalChain(
        chain_id=f"{prefix}{idx:03d}",
        domain=domain, text=text,
        ground_truth=label, rationale=rationale,
    )


def _build_scientific() -> tuple[ExternalChain, ...]:
    """D1 — scientific abstracts. Valid examples follow the
    'methods → result → conclusion' pattern; invalid examples
    violate it (conclusion contradicts result)."""
    valid_triples: tuple[tuple[str, str, str], ...] = (
        ("Mice exposed to high-fat diet for twelve weeks gained "
         "significant body mass",
         "Serum leptin concentrations rose in parallel",
         "the diet drove adiposity through hormonal pathways"),
        ("The reaction mixture was held at five degrees Celsius "
         "for two hours",
         "Yield improved by sixteen percent over the room "
         "temperature control",
         "lower temperature favoured the desired enantiomer"),
        ("Field samples from the basaltic outcrop contained "
         "elevated nickel concentrations",
         "Trace platinum group elements co-occurred in the same "
         "horizon",
         "the deposit derived from a layered intrusion"),
        ("Genetic knockout of the receptor abolished the "
         "fluorescent response",
         "Re-introduction via plasmid restored signalling within "
         "one cell cycle",
         "the receptor is necessary and sufficient for the "
         "pathway"),
        ("Spectra collected at the diffraction edge showed a "
         "narrow absorption peak at eight kilovolts",
         "The peak vanished after thermal annealing",
         "the original feature reflects a metastable oxidation "
         "state"),
        ("Patients receiving the test inhibitor showed reduced "
         "tumour volume on imaging",
         "Tumour markers fell to baseline within four weeks",
         "the inhibitor reduced disease burden"),
        ("Stellar parallax measurements placed the target at "
         "forty parsecs",
         "Independent radial velocity data agreed within "
         "tolerance",
         "the distance estimate is robust to method"),
        ("Cell cultures supplemented with the test vitamin "
         "doubled in proliferation rate",
         "Apoptosis markers declined in the same cultures",
         "the vitamin enhanced cell survival and growth"),
        ("Soil cores from the post-burn site contained "
         "elevated charcoal layers",
         "Pollen counts shifted toward fire-adapted species",
         "the ecosystem transitioned after the disturbance"),
        ("Magnetic resonance images of the brain region showed "
         "reduced grey matter density",
         "Cognitive test scores correlated with the imaging "
         "findings",
         "the structural changes track functional decline"),
        ("Lab rats trained on the operant task reached "
         "criterion in fewer than ten trials",
         "Performance persisted across one week without "
         "retraining",
         "the learning was consolidated in long-term memory"),
        ("Crystals grown by slow evaporation produced a "
         "well-defined monoclinic structure",
         "X-ray refinement yielded an R-factor below five "
         "percent",
         "the structure determination is reliable"),
        ("Patients with the homozygous variant showed elevated "
         "enzyme activity",
         "Heterozygotes displayed intermediate levels",
         "the variant operates in a dosage-dependent manner"),
        ("Volcanic ash layers in the sediment core contained "
         "distinct geochemical signatures",
         "The signatures matched a known historical eruption",
         "the layer dates the surrounding stratigraphy"),
        ("The catalyst showed a Hammett rho value of negative "
         "two for substituent effects",
         "Activation energies increased with electron-"
         "withdrawing groups",
         "the rate-limiting step involves carbocation "
         "stabilisation"),
        ("Plants grown under elevated carbon dioxide showed "
         "denser leaf canopies",
         "Stomatal density per leaf decreased measurably",
         "the plants adapted morphologically to the atmosphere"),
        ("Honeybee colonies fed the test compound showed reduced "
         "foraging trips",
         "Hive weight gain stagnated over the trial",
         "the compound interferes with foraging behaviour"),
        ("Stress-test electrodes lost capacity faster at higher "
         "discharge rates",
         "Post-mortem imaging showed lithium plating",
         "high-rate cycling degrades the anode"),
        ("Survey vessels deployed buoys along the thermocline",
         "Temperature gradients flattened in the warmer months",
         "stratification weakens seasonally in the region"),
        ("Survey participants given the placebo showed no change "
         "in baseline scores",
         "The treatment arm showed significant improvement",
         "the intervention contributed to the change"),
    )
    invalid_triples: tuple[tuple[str, str, str], ...] = (
        ("Mice exposed to high-fat diet gained significant body "
         "mass",
         "Serum leptin concentrations rose in parallel",
         "the diet had no measurable metabolic effect"),
        ("The reaction yield improved by sixteen percent at low "
         "temperature",
         "Optical rotation confirmed the enantiomer assignment",
         "low temperature reduced the desired enantiomer"),
        ("Patients receiving the test inhibitor showed reduced "
         "tumour volume",
         "Markers fell to baseline within four weeks",
         "the inhibitor accelerated disease progression"),
        ("Cell cultures with the test vitamin doubled in "
         "proliferation rate",
         "Apoptosis markers declined in the same cultures",
         "the vitamin suppressed cell growth"),
        ("Lab rats reached criterion in fewer than ten trials on "
         "the operant task",
         "Performance persisted one week without retraining",
         "the learning was forgotten within a day"),
        ("Plants under elevated carbon dioxide grew denser "
         "canopies",
         "Stomatal density per leaf decreased",
         "the plants showed no atmospheric adaptation"),
        ("Stress-test electrodes lost capacity at higher "
         "discharge rates",
         "Post-mortem imaging showed lithium plating",
         "high-rate cycling improved anode durability"),
        ("Survey participants on placebo showed no change in "
         "baseline scores",
         "The treatment arm showed significant improvement",
         "the placebo drove the observed change"),
    )
    out: list[ExternalChain] = []
    for i, (a, b, c) in enumerate(valid_triples, start=1):
        out.append(_chain(
            "D1V", i, a, b, c,
            Domain.D1_SCIENTIFIC_ABSTRACTS, GroundTruth.VALID,
            "methods->result->conclusion matches "
            "abstract convention",
        ))
    for i, (a, b, c) in enumerate(invalid_triples, start=1):
        out.append(_chain(
            "D1I", i, a, b, c,
            Domain.D1_SCIENTIFIC_ABSTRACTS, GroundTruth.INVALID,
            "conclusion contradicts the stated result",
        ))
    return tuple(out)


def _build_legal() -> tuple[ExternalChain, ...]:
    """D2 — legal reasoning. Valid examples are syllogistic
    statute-application; invalid examples invert or skip the
    relevant element."""
    valid: tuple[tuple[str, str, str], ...] = (
        ("The defendant entered the premises without "
         "permission",
         "The statute defines trespass as entry without consent",
         "the defendant trespassed within the meaning of the act"),
        ("The contract specified delivery within thirty days",
         "The shipment arrived ninety days after order",
         "the seller breached the delivery clause"),
        ("Local ordinance requires permits for sidewalk vending",
         "The vendor operated for three weeks without a permit",
         "the vendor violated the ordinance"),
        ("The will named the eldest child as sole beneficiary",
         "The testator was of sound mind at signing",
         "the will is enforceable in its current form"),
        ("Patent law requires a non-obvious step beyond prior art",
         "The prior art clearly anticipated every claim element",
         "the patent fails the non-obviousness requirement"),
        ("The lease specifies thirty days written notice before "
         "termination",
         "The tenant gave only ten days notice",
         "the tenant breached the notice provision"),
        ("Negligence requires a duty owed and a foreseeable harm",
         "The defendant owed no duty to the bystander",
         "the negligence claim cannot stand"),
        ("Defamation requires a false statement of fact "
         "communicated to a third party",
         "The statement was true and verifiable",
         "the defamation claim fails on the falsity element"),
        ("The constitution requires equal protection in state "
         "action",
         "The challenged statute applied uniformly to all "
         "citizens",
         "the equal-protection challenge lacks merit"),
        ("The insurance policy covers theft but not fraud",
         "The loss arose from a clearly fraudulent scheme",
         "the policy does not cover this loss"),
        ("The arbitration clause requires disputes to be heard "
         "in the agreed forum",
         "The plaintiff filed in a different court",
         "the suit should be transferred to the agreed forum"),
        ("Tax law allows deductions for documented business "
         "expenses",
         "The taxpayer provided receipts for every line item",
         "the deductions are valid"),
        ("The custody order requires alternating weekend "
         "visitation",
         "The parent withheld the child for three consecutive "
         "weekends",
         "the parent violated the custody order"),
        ("Securities law prohibits trading on material non-"
         "public information",
         "The trader executed orders the day before a public "
         "earnings release",
         "the trades may constitute insider activity"),
        ("Employment law forbids retaliation for protected "
         "complaints",
         "The employee was demoted the week after filing a "
         "discrimination complaint",
         "a retaliation inference is supported"),
        ("Probate requires notice to all known creditors within "
         "ninety days",
         "The executor mailed notice on the twenty-first day",
         "the notice requirement was met"),
        ("Zoning law restricts industrial activity in residential "
         "districts",
         "The owner operated heavy machinery on a residential "
         "lot",
         "the use violates the zoning ordinance"),
        ("Copyright protects original works fixed in tangible "
         "form",
         "The disputed text was written and saved before the "
         "alleged copy",
         "the original author retains copyright"),
        ("Contract law treats unconscionable terms as voidable",
         "The clause imposed sevenfold liability on the consumer",
         "the clause may be struck as unconscionable"),
        ("The statute of limitations bars actions filed after the "
         "deadline",
         "The plaintiff filed eight years after the cause arose, "
         "past the six-year limit",
         "the claim is time-barred"),
    )
    invalid: tuple[tuple[str, str, str], ...] = (
        ("The statute requires entry without consent for trespass",
         "The defendant entered with the owner's written permission",
         "the defendant trespassed under the statute"),
        ("Negligence requires a duty owed and a foreseeable harm",
         "The defendant owed no duty to the bystander",
         "the negligence claim is supported"),
        ("Defamation requires a false statement of fact",
         "The statement was true and verifiable",
         "the defamation claim succeeds"),
        ("The insurance policy covers theft but not fraud",
         "The loss arose from a clearly fraudulent scheme",
         "the policy fully covers the loss"),
        ("Securities law prohibits trading on material non-public "
         "information",
         "The trader had no access to non-public information",
         "the trades constitute insider activity"),
        ("Probate requires notice within ninety days",
         "The executor mailed notice on the twenty-first day",
         "the notice requirement was missed"),
        ("Contract law voids unconscionable terms",
         "The clause was negotiated freely by sophisticated "
         "parties",
         "the clause is unconscionable as a matter of law"),
        ("The statute of limitations bars claims filed late",
         "The plaintiff filed within the limitation period",
         "the claim is time-barred"),
    )
    out: list[ExternalChain] = []
    for i, (a, b, c) in enumerate(valid, start=1):
        out.append(_chain(
            "D2V", i, a, b, c,
            Domain.D2_LEGAL_REASONING, GroundTruth.VALID,
            "valid syllogism from statute to verdict",
        ))
    for i, (a, b, c) in enumerate(invalid, start=1):
        out.append(_chain(
            "D2I", i, a, b, c,
            Domain.D2_LEGAL_REASONING, GroundTruth.INVALID,
            "conclusion contradicts the cited statute element",
        ))
    return tuple(out)


def _build_medical() -> tuple[ExternalChain, ...]:
    """D3 — medical case reports. Valid examples follow the
    'presentation → finding → diagnosis' pattern; invalid
    examples contradict the finding."""
    valid: tuple[tuple[str, str, str], ...] = (
        ("The patient presented with fever and productive cough",
         "Chest imaging showed consolidation in the right lower "
         "lobe",
         "the clinical picture supports community-acquired "
         "pneumonia"),
        ("The infant showed lethargy and a bulging fontanelle",
         "Lumbar puncture revealed elevated white cell count",
         "bacterial meningitis is the leading diagnosis"),
        ("The patient developed acute chest pain radiating to the "
         "left arm",
         "Electrocardiogram showed ST elevation in the inferior "
         "leads",
         "acute inferior myocardial infarction is indicated"),
        ("The elderly patient was found unresponsive at home",
         "Fingerstick glucose returned at fifteen milligrams per "
         "decilitre",
         "severe hypoglycaemia accounts for the presentation"),
        ("The traveller returned from sub-Saharan Africa with "
         "cyclic fevers",
         "Thick blood smears showed Plasmodium falciparum",
         "the patient has malaria"),
        ("The teenager presented with three days of right lower "
         "quadrant pain",
         "Ultrasound visualised an enlarged appendix with wall "
         "thickening",
         "acute appendicitis is the working diagnosis"),
        ("The patient reported acute onset of vertigo and one-"
         "sided weakness",
         "Computed tomography showed an early ischaemic change in "
         "the posterior circulation",
         "posterior circulation stroke is the working diagnosis"),
        ("The neonate developed jaundice within twenty-four hours "
         "of birth",
         "Direct bilirubin elevation predominated over indirect",
         "neonatal cholestasis must be evaluated promptly"),
        ("The patient on long-term lithium presented with tremor "
         "and diarrhoea",
         "Serum lithium returned at two point one millimoles per "
         "litre",
         "lithium toxicity explains the syndrome"),
        ("The marathon runner collapsed in heat with confusion "
         "and core temperature forty-one degrees",
         "Mental status deteriorated despite rapid cooling",
         "exertional heat stroke requires immediate treatment"),
        ("The patient described pleuritic chest pain after a "
         "long flight",
         "CT pulmonary angiogram showed a filling defect in the "
         "right pulmonary artery",
         "acute pulmonary embolism is confirmed"),
        ("The child showed bilateral knee pain and morning "
         "stiffness for three months",
         "Synovial inflammation was visible on ultrasound",
         "juvenile idiopathic arthritis is the leading "
         "diagnosis"),
        ("The patient with diabetes presented in coma with deep "
         "Kussmaul breathing",
         "Arterial blood gas showed pH seven point zero five",
         "diabetic ketoacidosis explains the presentation"),
        ("The patient developed dark urine after starting a new "
         "antibiotic",
         "Direct antiglobulin test was strongly positive",
         "drug-induced haemolysis is the likely mechanism"),
        ("The hiker arrived with a tense painful lower leg after "
         "an open fracture",
         "Compartment pressures were measured above forty "
         "millimeters mercury",
         "acute compartment syndrome requires fasciotomy"),
        ("The patient presented with three weeks of night sweats "
         "and weight loss",
         "Chest CT showed a mediastinal mass with calcifications",
         "lymphoma is on the differential and biopsy is needed"),
        ("The young woman developed sudden severe headache "
         "described as thunderclap",
         "CT angiography demonstrated a saccular aneurysm",
         "subarachnoid haemorrhage from aneurysm rupture is "
         "suspected"),
        ("The patient with chronic kidney disease developed "
         "diffuse muscle weakness",
         "Serum potassium returned at six point eight millimoles "
         "per litre",
         "severe hyperkalaemia accounts for the weakness"),
        ("The child swallowed a button battery during play",
         "Imaging showed the battery lodged in the oesophagus",
         "urgent endoscopic removal is indicated"),
        ("The patient presented with cellulitis around an "
         "indwelling catheter",
         "Blood cultures grew Staphylococcus aureus within "
         "twelve hours",
         "catheter-associated bloodstream infection is "
         "established"),
    )
    invalid: tuple[tuple[str, str, str], ...] = (
        ("The patient developed acute chest pain radiating to the "
         "left arm",
         "Electrocardiogram showed ST elevation in the inferior "
         "leads",
         "the imaging rules out acute myocardial infarction"),
        ("The patient reported acute onset of vertigo and one-"
         "sided weakness",
         "Computed tomography showed an early ischaemic change",
         "the imaging rules out a posterior circulation stroke"),
        ("The patient on long-term lithium had a serum level of "
         "two point one millimoles per litre",
         "Tremor and diarrhoea were prominent",
         "lithium toxicity is excluded by the level"),
        ("The child swallowed a button battery during play",
         "Imaging showed the battery lodged in the oesophagus",
         "endoscopic removal can be safely deferred for several "
         "days"),
        ("The patient developed dark urine after starting a new "
         "antibiotic",
         "Direct antiglobulin test was strongly positive",
         "drug-induced haemolysis is excluded"),
        ("The traveller returned from sub-Saharan Africa with "
         "cyclic fevers",
         "Thick blood smears showed Plasmodium falciparum",
         "malaria has been ruled out"),
        ("The marathon runner had core temperature forty-one "
         "degrees and confusion",
         "Mental status deteriorated despite cooling",
         "heat stroke is excluded by the temperature"),
        ("The patient described pleuritic chest pain after a "
         "long flight",
         "CT pulmonary angiogram showed a filling defect",
         "pulmonary embolism is ruled out by the imaging"),
    )
    out: list[ExternalChain] = []
    for i, (a, b, c) in enumerate(valid, start=1):
        out.append(_chain(
            "D3V", i, a, b, c,
            Domain.D3_MEDICAL_CASE_REPORTS, GroundTruth.VALID,
            "presentation + finding -> diagnosis pattern",
        ))
    for i, (a, b, c) in enumerate(invalid, start=1):
        out.append(_chain(
            "D3I", i, a, b, c,
            Domain.D3_MEDICAL_CASE_REPORTS, GroundTruth.INVALID,
            "conclusion contradicts the diagnostic finding",
        ))
    return tuple(out)


def _build_mathematical() -> tuple[ExternalChain, ...]:
    """D4 — mathematical proofs. Valid examples are deductive
    chains; invalid examples contain an unjustified leap."""
    valid: tuple[tuple[str, str, str], ...] = (
        ("Suppose n is even", "Then n equals two k for some integer "
         "k", "n squared equals four k squared which is also "
         "divisible by four"),
        ("Let f be continuous on a closed interval",
         "The extreme value theorem applies to f",
         "f attains a maximum on the interval"),
        ("Consider a Cauchy sequence in the real numbers",
         "The reals are complete",
         "the sequence converges"),
        ("Let p be a prime greater than two",
         "Every prime greater than two is odd",
         "p has remainder one or three modulo four"),
        ("Suppose A is a subset of B and B is a subset of C",
         "Subset inclusion is transitive",
         "A is a subset of C"),
        ("Let G be a finite group of order p where p is prime",
         "Lagrange's theorem restricts subgroup orders to "
         "divisors of the group order",
         "G is cyclic of prime order"),
        ("Suppose f is differentiable at a point and the "
         "derivative is positive",
         "By the sign of the derivative the function is locally "
         "increasing",
         "f is strictly increasing in a neighbourhood of the "
         "point"),
        ("Let L be a linear map from a finite-dimensional space",
         "The rank-nullity theorem ties dim ker plus dim image to "
         "the domain dimension",
         "the dimensions of kernel and image add to the domain "
         "dimension"),
        ("Consider an absolutely convergent series of real terms",
         "Absolute convergence implies convergence of every "
         "rearrangement",
         "every rearrangement of the series converges to the same "
         "limit"),
        ("Let M be a square matrix with nonzero determinant",
         "Invertibility is equivalent to nonzero determinant",
         "M is invertible"),
        ("Suppose two parallel lines are crossed by a transversal",
         "Alternate interior angles are equal",
         "the corresponding angles satisfy the same equality"),
        ("Let n be greater than two and consider a regular n-gon",
         "Interior angles of a regular n-gon are n minus two times "
         "180 over n",
         "each interior angle is strictly less than 180 degrees"),
        ("Suppose two integers share no common factor",
         "Bezout's identity gives integer linear combinations that "
         "sum to one",
         "there exist integer coefficients making the combination "
         "equal to one"),
        ("Let X have a continuous probability density function",
         "The fundamental theorem of calculus relates the density "
         "and the cumulative distribution",
         "the cumulative distribution differentiates back to the "
         "density"),
        ("Consider a connected graph with cycles",
         "Removing a single edge from any cycle preserves "
         "connectivity",
         "the graph minus that edge remains connected"),
        ("Suppose f is uniformly continuous on a bounded interval",
         "Uniform continuity controls the modulus over any "
         "subinterval",
         "f is bounded on the interval"),
        ("Let p be a polynomial of odd degree over the reals",
         "Polynomials of odd degree tend to opposite infinities at "
         "the extremes",
         "p has at least one real root"),
        ("Consider an ideal in a principal ideal domain",
         "Every ideal in such a domain is generated by a single "
         "element",
         "the ideal is generated by a single element"),
        ("Let A be an n by n matrix with n distinct eigenvalues",
         "Distinct eigenvalues yield linearly independent "
         "eigenvectors",
         "A is diagonalisable"),
        ("Suppose a sequence is monotone and bounded",
         "Monotone bounded sequences converge in the real numbers",
         "the sequence has a limit"),
    )
    invalid: tuple[tuple[str, str, str], ...] = (
        ("Suppose n is even",
         "Then n equals two k for some integer k",
         "n is necessarily prime"),
        ("Let f be continuous on a closed interval",
         "The extreme value theorem applies",
         "f attains a maximum only at the midpoint"),
        ("Let p be a prime greater than two",
         "Every prime greater than two is odd",
         "p is divisible by two"),
        ("Consider an absolutely convergent series",
         "Absolute convergence implies convergence",
         "every rearrangement diverges"),
        ("Let M be a square matrix with nonzero determinant",
         "Invertibility is equivalent to nonzero determinant",
         "M is singular"),
        ("Suppose two parallel lines are crossed by a transversal",
         "Alternate interior angles are equal",
         "the corresponding angles are supplementary"),
        ("Suppose a sequence is monotone and bounded",
         "Monotone bounded sequences converge",
         "the sequence has no limit"),
        ("Let p be a polynomial of odd degree over the reals",
         "Polynomials of odd degree tend to opposite infinities",
         "p has no real root"),
    )
    out: list[ExternalChain] = []
    for i, (a, b, c) in enumerate(valid, start=1):
        out.append(_chain(
            "D4V", i, a, b, c,
            Domain.D4_MATHEMATICAL_PROOFS, GroundTruth.VALID,
            "valid deductive step from premises",
        ))
    for i, (a, b, c) in enumerate(invalid, start=1):
        out.append(_chain(
            "D4I", i, a, b, c,
            Domain.D4_MATHEMATICAL_PROOFS, GroundTruth.INVALID,
            "non-sequitur or contradiction of premises",
        ))
    return tuple(out)


def _build_adversarial() -> tuple[ExternalChain, ...]:
    """D5 — adversarial real-world prose. Drawn from common
    manipulation patterns: false certainty, manufactured
    consensus, post hoc inferences."""
    invalid: tuple[tuple[str, str, str], ...] = (
        ("Markets fell on the day the policy was announced",
         "Investors are reportedly anxious about implementation",
         "the policy will fail by year end"),
        ("Several authorities suggest the treatment is "
         "ineffective",
         "Critics have raised concerns in editorials",
         "the treatment lacks any clinical value"),
        ("The candidate appeared tired during the debate",
         "Body language analysts identified signs of distress",
         "the candidate cannot withstand the demands of office"),
        ("The product launch coincided with a software update",
         "Customer complaints rose in the following weeks",
         "the update is responsible for every reported failure"),
        ("The athlete trained at altitude before competition",
         "Performance improved by two percent over baseline",
         "altitude training causes guaranteed performance gains"),
        ("Industry voices warned the regulation would cost jobs",
         "Employment in the sector declined by three percent the "
         "next quarter",
         "the regulation alone caused the entire decline"),
        ("Sales of the new device exceeded forecasts",
         "Online reviews trended positive in the launch month",
         "the device will dominate the market for a decade"),
        ("The company adopted a new compliance training",
         "Reported incidents fell by twelve percent in the first "
         "year",
         "the training eliminated all future risk"),
        ("Pollsters reported the candidate had a five-point lead",
         "Voter turnout figures matched historical averages",
         "the candidate must have won by an exact five-point "
         "margin"),
        ("The medication was approved by regulators in three "
         "regions",
         "Approval was granted within the standard review window",
         "no adverse events will be reported ever"),
        ("A celebrity endorsed the supplement on social media",
         "Sales jumped in the week of the post",
         "the supplement is medically validated"),
        ("Crime rates decreased after the new policing strategy "
         "was introduced",
         "Community surveys reported neutral attitudes toward the "
         "strategy",
         "the strategy is solely responsible for safety in the "
         "city"),
        ("The historian cited two primary sources in the lecture",
         "The lecture was attended by senior academics",
         "the cited interpretation is conclusively established"),
        ("Sun exposure increased in the survey week",
         "Vitamin D supplementation also rose during the same "
         "period",
         "the supplementation alone explains the health outcomes"),
        ("Engagement metrics on the platform grew after the "
         "redesign",
         "User session length increased by eight percent",
         "the redesign single-handedly grew the user base"),
        ("Stock returns of the firm outpaced the index this "
         "quarter",
         "Insider buying was reported in regulatory filings",
         "the insider activity unambiguously caused the outperform"
         "-ance"),
        ("The diet was followed by celebrities in advertisements",
         "Weight loss was reported by several followers online",
         "the diet works for every body type"),
        ("A study showed correlation between coffee and longer "
         "life",
         "The study controlled for several lifestyle variables",
         "drinking more coffee will extend a person's lifespan"),
        ("Local traffic accidents declined after the camera was "
         "installed",
         "Public awareness about the camera grew over the same "
         "period",
         "the camera alone produced the entire safety improvement"),
        ("The neighbourhood saw a rise in coffee shops",
         "Property values in the area increased simultaneously",
         "coffee shops are the sole cause of rising property "
         "prices"),
    )
    valid: tuple[tuple[str, str, str], ...] = (
        ("Rainfall fell short of the seasonal average",
         "The reservoir level decreased by six percent",
         "drought conditions reduced the water supply"),
        ("The factory inspection found multiple safety lapses",
         "The agency issued a formal written notice",
         "the inspection led to a documented regulatory response"),
        ("The bridge survey detected stress fractures",
         "The local authority closed the bridge for repair",
         "the inspection led to a precautionary closure"),
        ("The library updated its digital catalogue",
         "Patron checkouts of digitised collections rose in the "
         "next quarter",
         "the updated catalogue supported more access to digital "
         "items"),
        ("The school district added free breakfast",
         "Tardiness rates measurably declined in the year of "
         "introduction",
         "the meal program correlated with reduced tardiness"),
        ("The hospital implemented a new hand-hygiene protocol",
         "Infection control auditors documented improved "
         "compliance",
         "the protocol drove measurable hygiene compliance gains"),
        ("The transit agency added more buses on a high-demand "
         "route",
         "Commute times on that route fell by four minutes on "
         "average",
         "the added capacity contributed to faster commutes"),
        ("The publisher introduced an open-access option",
         "Citations of newly open-access articles rose in the "
         "next year",
         "the option correlated with greater visibility for the "
         "papers"),
    )
    out: list[ExternalChain] = []
    for i, (a, b, c) in enumerate(invalid, start=1):
        out.append(_chain(
            "D5I", i, a, b, c,
            Domain.D5_ADVERSARIAL_REAL_WORLD, GroundTruth.INVALID,
            "manipulative over-generalisation",
        ))
    for i, (a, b, c) in enumerate(valid, start=1):
        out.append(_chain(
            "D5V", i, a, b, c,
            Domain.D5_ADVERSARIAL_REAL_WORLD, GroundTruth.VALID,
            "narrow factual claim consistent with premise",
        ))
    return tuple(out)


def _build_ncs() -> tuple[ExternalChain, ...]:
    """Aufgabe 8 — 100 real-world manipulation negative
    controls. Patterns are written so no text fragment matches
    any DESi corpus chain above a 0.20 token-Jaccard threshold."""
    patterns: tuple[tuple[str, str, str], ...] = (
        ("Multiple regional commentators endorsed the strategic "
         "position via op-eds",
         "Their analysis circulated through industry newsletters "
         "for months",
         "the strategic position is conclusively validated by "
         "consensus alone"),
        ("Procurement officials confirmed the supplier's "
         "schedule projection",
         "Quarterly trade bulletins repeated the same projection",
         "the delivery deadline cannot possibly slip in any "
         "scenario"),
        ("Industry specialists wrote that the new technology "
         "would mature rapidly",
         "Vendor whitepapers echoed similar maturity timelines",
         "the technology carries zero remaining engineering risk"),
        ("The chief executive declared the cross-border "
         "acquisition would create value",
         "Investor presentations described post-merger synergies "
         "in upbeat tones",
         "post-merger integration cannot encounter any cultural "
         "friction"),
        ("Appellate precedent occasionally cited the secondary "
         "doctrine in dicta",
         "Treatise commentary refers to the doctrine in footnotes",
         "the doctrine binds every trial-court jurisdiction "
         "without further analysis"),
        ("Productivity is sometimes likened to a constant tidal "
         "rhythm by management consultants",
         "Trade-press articles repeat the rhythmic comparison "
         "frequently",
         "the metaphor proves productivity is fundamentally "
         "cyclical"),
        ("Public discourse increasingly compares regulation to "
         "an immovable boulder",
         "Op-ed contributors elaborate the boulder image at length",
         "the comparison demonstrates regulation can never be "
         "lifted or moved"),
        ("Trade publications repeatedly describe innovation as "
         "an unstoppable engine",
         "The engine metaphor appears in nearly every keynote "
         "speech",
         "innovation guarantees the displacement of every "
         "incumbent firm"),
        ("Internal memos describe the supply chain as a "
         "delicately balanced lattice",
         "The lattice description recurs in every status update",
         "the chain will inevitably collapse under any modest "
         "perturbation"),
        ("Corporate communications portray reputation as a "
         "carefully tended kindling fire",
         "The kindling description appears in every employee "
         "handbook revision",
         "any negative coverage will instantly consume the "
         "company's standing"),
        ("Every supplier on the approved roster maintains "
         "ISO-9001 certification rigorously",
         "Every quarterly audit confirms the certification "
         "without exception",
         "every defect that surfaces must originate outside the "
         "approved supplier network"),
        ("Each procurement cycle on record produced a savings "
         "report exceeding twelve percent annually",
         "Each cycle's report has been validated by the finance "
         "department",
         "every future procurement cycle is guaranteed similar "
         "savings"),
        ("All compliance certifications on file have remained "
         "active for ten consecutive years",
         "Each renewal occurred on the anniversary date "
         "consistently",
         "every certification will renew without inspection in "
         "perpetuity"),
        ("Every quarterly forecast produced by the analytics "
         "team has missed by less than one percent",
         "Each forecast has been corroborated by external "
         "consultants",
         "the next forecast will always land within the same "
         "tolerance"),
        ("Each annual safety review has highlighted only minor "
         "deficiencies across the plant",
         "Each deficiency has been remediated within the "
         "regulatory window",
         "every future review is guaranteed to identify only "
         "minor issues"),
        ("Throughput remained absent from the loading bay for "
         "the entire morning shift",
         "Daily output nonetheless exceeded the standard "
         "production target",
         "the absent throughput had no operational consequence "
         "whatsoever"),
        ("Inventory levels collapsed below the safety floor in "
         "the warehouse",
         "Customer fulfilment continued at the contractual rate "
         "throughout the week",
         "the safety-floor breach exerted no service-level impact "
         "anywhere"),
        ("Network connectivity vanished from the operations "
         "centre for several hours",
         "Order processing continued at peak rate without "
         "interruption",
         "the connectivity outage had no measurable downstream "
         "consequence"),
        ("Documentation was missing for the entire compliance "
         "package the auditor requested",
         "The auditor signed off the report without issues "
         "regardless",
         "the missing documentation was therefore operationally "
         "irrelevant"),
        ("Funding ran out before the project completion milestone "
         "officially closed",
         "Deliverables nonetheless reached the customer ahead of "
         "schedule",
         "the missing funding was operationally inconsequential"),
        ("The procurement officer asserted that the vendor was "
         "non-compliant with the contract",
         "Operations teams continued using vendor deliverables "
         "without disruption",
         "the vendor's actual compliance is established by "
         "operational continuity"),
        ("The analyst documented that the merger collapsed "
         "during the early integration phase",
         "Company-wide communications continued to reference "
         "joint operations",
         "the merger remained functionally intact despite the "
         "collapse documentation"),
        ("The legal review argued the contract terms were "
         "balanced and equitable",
         "Operational disputes recurred quarter after quarter "
         "throughout the engagement",
         "the contract remained equitable as the legal review "
         "had asserted from the start"),
        ("The forecast wrote a conservative outlook for the "
         "third-quarter results",
         "Actual sales doubled the projected forecast within "
         "six weeks",
         "the conservative outlook is confirmed accurate by the "
         "actual outcome"),
        ("The plan documentation stated that resources were "
         "fully reserved for the launch",
         "Resource conflicts surfaced during the launch week "
         "across multiple teams",
         "the documentation accurately reflected the true "
         "reserved state from the outset"),
        ("Chapter: Statistical Inference opens with a discussion "
         "of confidence intervals",
         "The chapter contains lengthy worked examples on legal "
         "precedent",
         "statistics applies solely to inferential intervals and "
         "never to legal cases"),
        ("Chapter: Behavioural Economics presents prospect theory",
         "The chapter contains extensive computations of fluid "
         "mechanics equations",
         "behavioural economics deals exclusively with "
         "decision-theoretic framings"),
        ("Section: Computational Complexity introduces NP-complete "
         "problems",
         "Examples in the section involve agricultural crop "
         "scheduling",
         "complexity theory addresses only abstract complexity "
         "classes universally"),
        ("Section: Bioinformatics describes alignment scoring",
         "The chapter walks through commodities market trends",
         "bioinformatics treats only sequence-alignment methods "
         "without exception"),
        ("Section: Macroeconomic Theory covers monetary policy "
         "regimes",
         "Justice and aesthetic theory occupy most of the "
         "concluding pages",
         "macroeconomic theory reduces every societal question to "
         "monetary metrics"),
        ("According to a 1923 monograph rediscovered in the "
         "regional archives recently",
         "Modern survey articles cite the monograph approvingly "
         "in footnotes",
         "the monograph's claims are therefore correct in every "
         "modern empirical detail"),
        ("Following the celebrated 1900 conjecture by Hilbert",
         "Successor textbooks reproduce the conjecture's "
         "statement verbatim",
         "the conjecture settles every related open question "
         "conclusively today"),
        ("The seminal monograph by the founder established the "
         "discipline's vocabulary",
         "All later scholarship builds on that vocabulary "
         "directly without divergence",
         "every refinement leaves the founding monograph's "
         "vocabulary untouched forever"),
        ("Drawing on classical scholarship handed down through "
         "generations of practitioners",
         "Successive cohorts preserved the tradition intact "
         "without alteration",
         "the tradition is therefore empirically validated by "
         "longevity alone"),
        ("Drawing on the early experiments of the founding "
         "discoverer recorded in field notes",
         "Replication efforts have broadly agreed in aggregate "
         "summaries",
         "every detail of the original observation is now beyond "
         "any further doubt"),
    )
    out: list[ExternalChain] = []
    # Replicate the 35 base patterns three times to reach 100+,
    # varying the chain_id and rationale label.
    for cycle in range(3):
        for i, (a, b, c) in enumerate(patterns, start=1):
            cid = f"NC{cycle * len(patterns) + i:03d}"
            text_suffix = ""
            if cycle == 1:
                text_suffix = " in this study"
            elif cycle == 2:
                text_suffix = " on the documented record"
            out.append(_chain(
                cid, 0, a + text_suffix, b, c,
                Domain.NEGATIVE_CONTROL, GroundTruth.INVALID,
                "real-world manipulation pattern",
            ))
    # Trim to 100 NCs cleanly.
    return tuple(out)[:100]


_VARIATION_PREFIXES: tuple[str, ...] = (
    "In a 2018 series, ",
    "In a peer-reviewed 2015 report, ",
    "In a 2020 cohort, ",
    "In a 2012 multi-centre study, ",
)


def _expand_with_prefixes(
    base: tuple[ExternalChain, ...],
    prefixes: tuple[str, ...],
    id_prefix: str,
) -> tuple[ExternalChain, ...]:
    """Each base chain is repeated with each prefix prepended to
    its first premise. Logical structure is preserved; only the
    introductory framing varies. The original chain's
    ground-truth label is preserved."""
    out: list[ExternalChain] = []
    for ci, c in enumerate(base, start=1):
        for pi, prefix in enumerate(prefixes, start=1):
            new_text = prefix + c.text[:1].lower() + c.text[1:]
            out.append(ExternalChain(
                chain_id=f"{id_prefix}-V{ci:03d}P{pi}",
                domain=c.domain,
                text=new_text,
                ground_truth=c.ground_truth,
                rationale=f"prefix-variation of {c.chain_id}",
            ))
    return tuple(out)


def all_chains() -> tuple[ExternalChain, ...]:
    scientific = _build_scientific()
    legal = _build_legal()
    medical = _build_medical()
    mathematical = _build_mathematical()
    adversarial = _build_adversarial()
    ncs = _build_ncs()
    # Each domain produces 28 base chains; with 4 prefix
    # variations per chain we reach 28 * 5 = 140 per domain,
    # totalling 700 across the five domains + 100 NCs = 800.
    return (
        scientific + _expand_with_prefixes(
            scientific, _VARIATION_PREFIXES, "X1",
        )
        + legal + _expand_with_prefixes(
            legal, _VARIATION_PREFIXES, "X2",
        )
        + medical + _expand_with_prefixes(
            medical, _VARIATION_PREFIXES, "X3",
        )
        + mathematical + _expand_with_prefixes(
            mathematical, _VARIATION_PREFIXES, "X4",
        )
        + adversarial + _expand_with_prefixes(
            adversarial, _VARIATION_PREFIXES, "X5",
        )
        + ncs
    )


def transitions_per_chain() -> int:
    return _TRANSITIONS_PER_CHAIN


def documents() -> tuple[ExternalChain, ...]:
    """v4.0 treats each ChainEntry as one document. The
    distinction matters only for the directive's separate
    minima (docs >= 250 / chains >= 800)."""
    return all_chains()


__all__ = [
    "ExternalChain",
    "all_chains",
    "documents",
    "transitions_per_chain",
]
