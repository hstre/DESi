"""Atomic claims + verdict/evidence model — case-study Aufgaben 2, 4, 5.

The *machinery* here (the ``ClaimType`` / ``Verdict`` / ``Domain`` enums and the
``CaseClaim`` / ``Evidence`` dataclasses) is a small, general, reusable epistemic
vocabulary — deliberately not welded to this one text. The *data* (the ``CLAIMS``
and ``EVIDENCE`` tuples) is a closed fixture for this specific material, in exactly
the style of the other DESi case studies (e.g. ``desi.paper_integrity.claims``).

DESi's own boundary applies to this file too: the verdicts below are a structured,
auditable *decomposition*, not a pronouncement that the underlying legal
philosophy is right or wrong. Where the honest answer is "the material supplies no
checkable evidence", the verdict says exactly that rather than guessing.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from . import source_material as S


class ClaimType(str, Enum):
    """Epistemic kind of a claim — drives which evidence would settle it.

    General across epistemic case studies; the last three are the meta-layer a
    validation experiment adds on top of ordinary content claims.
    """

    DEFINITION = "definition"
    AUTHOR_ATTRIBUTION = "author_attribution"
    DIRECT_QUOTE = "direct_quote"
    HISTORICAL_FACT = "historical_fact"
    JURISTIC_FACT = "juristic_fact"
    EMPIRICAL = "empirical"
    THEORETICAL_INTERPRETATION = "theoretical_interpretation"
    NORMATIVE = "normative"
    HEURISTIC_MODEL = "heuristic_model"
    METHODOLOGICAL = "methodological"          # a claim about the experiment
    CLAIM_ABOUT_VALIDATOR = "claim_about_validator"
    CLAIM_ABOUT_BOUNDARY = "claim_about_epistemic_boundary"


class Verdict(str, Enum):
    """Closed verdict vocabulary (case-study Aufgabe 5).

    Deliberately richer than VERIFIED / FAILURE: a heuristic model is not "false",
    a normative claim is not "unsupported", and a database hit in the wrong domain
    is a *mismatch*, not a confirmation.
    """

    SUPPORTED = "supported"
    PARTIALLY_SUPPORTED = "partially_supported"
    CONTRADICTED = "contradicted"
    UNSUPPORTED = "unsupported"
    UNVERIFIABLE = "unverifiable_from_available_evidence"
    INTERPRETATION = "interpretation"
    HEURISTIC_PROPOSAL = "heuristic_proposal"
    NORMATIVE_CLAIM = "normative_claim"
    CITATION_MISMATCH = "citation_mismatch"
    SOURCE_DOMAIN_MISMATCH = "source_domain_mismatch"


class Domain(str, Enum):
    """Knowledge domain a claim belongs to — the routing key for source-gating."""

    LEGAL_PHILOSOPHY = "legal_philosophy"
    LAW_POSITIVE = "positive_law"           # statutes, cases, legal facts
    ECONOMICS = "economics"
    SOCIOLOGY = "sociology"
    COGNITIVE_SCIENCE = "cognitive_science"
    TECH_HISTORY = "technology_history"
    ML_EPISTEMOLOGY = "ml_epistemology"     # claims about LLM behaviour
    EXPERIMENT_META = "experiment_methodology"


class EvidenceStrength(str, Enum):
    NONE = "none"
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"


class ProvenanceKind(str, Enum):
    """How the *found* source relates to the claim it was used for."""

    PRIMARY = "primary"
    SECONDARY = "secondary"
    SEMANTIC_ONLY = "semantic_similarity_only"   # topical overlap, no derivation
    NONE = "none"                                # no concrete source at all


@dataclass(frozen=True)
class CaseClaim:
    """One atomic claim plus its typed, routed, judged record."""

    claim_id: str
    text: str
    claim_type: ClaimType
    domain: Domain
    source: S.SourceRef                 # exact anchor in the material
    required_evidence: str             # what WOULD settle this claim
    verdict: Verdict
    rationale: str
    uncertainty: str = ""
    contradiction_ids: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict:
        return {
            "claim_id": self.claim_id,
            "text": self.text,
            "claim_type": self.claim_type.value,
            "domain": self.domain.value,
            "source": self.source.cite(),
            "source_quote": self.source.quote,
            "required_evidence": self.required_evidence,
            "verdict": self.verdict.value,
            "rationale": self.rationale,
            "uncertainty": self.uncertainty,
            "contradiction_ids": list(self.contradiction_ids),
        }


@dataclass(frozen=True)
class Evidence:
    """The evidence actually available for a claim in the experiment material.

    For most content claims here the honest record is ``ProvenanceKind.NONE`` with
    an empty passage — because the validator named no concrete source or passage.
    That emptiness is the finding, and it is recorded, not hidden.
    """

    claim_id: str
    domain: Domain
    required_source_kind: str
    source_used: str                 # what the experiment actually leaned on
    source_domain: Domain | None
    provenance_kind: ProvenanceKind
    concrete_passage: str            # "" when none was ever cited
    strength: EvidenceStrength
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "claim_id": self.claim_id,
            "domain": self.domain.value,
            "required_source_kind": self.required_source_kind,
            "source_used": self.source_used,
            "source_domain": self.source_domain.value if self.source_domain else None,
            "provenance_kind": self.provenance_kind.value,
            "concrete_passage": self.concrete_passage,
            "strength": self.strength.value,
            "notes": self.notes,
        }


# --------------------------------------------------------------------------- #
# The closed claim fixture for this specific material.
# --------------------------------------------------------------------------- #

_NO_SOURCE = "(none — the validator cited only 'the PubMed document', no title/passage)"

CLAIMS: tuple[CaseClaim, ...] = (
    # -- methodological self-claims about the experiment --------------------- #
    CaseClaim(
        "MET-01",
        "Muse Spark received no epistemic instructions (no requests for "
        "verification, sources, or stages).",
        ClaimType.METHODOLOGICAL, Domain.EXPERIMENT_META, S.METHOD_NO_INSTRUCTIONS,
        "The prompt actually sent to the model.",
        Verdict.CONTRADICTED,
        "The reproduced prompt (muse:L24-27, L56-58, L64) explicitly demands "
        "arXiv/PubMed/OpenAlex sources, >=5 references with direct citations, a "
        "citation-consistency check, and six named Phases (muse:L29-47). The "
        "'no instructions' claim is contradicted by the experiment's own prompt.",
        uncertainty="None on the direction of the conflict; the prompt is printed in full.",
        contradiction_ids=("C1",),
    ),
    CaseClaim(
        "MET-02",
        "The validation is external and independent (any 'independent external "
        "validator').",
        ClaimType.METHODOLOGICAL, Domain.EXPERIMENT_META, S.METHOD_EXTERNAL_VALIDATION,
        "The validator's implementation and the inputs it receives.",
        Verdict.PARTIALLY_SUPPORTED,
        "'External' holds literally — it is a separate call, here even a different "
        "model family (Muse Spark vs. a Llama validator). But 'independent' is not "
        "documented on any axis: the validator receives exactly the generation "
        "documents (code:evaluator_prompt L24-28), is non-adversarial and not "
        "reproducibly specified. A single external llm.invoke does not by itself "
        "REFUTE independence — but it does not ESTABLISH it either; here the "
        "'independent' label is a methodological misclassification, not a demonstrated "
        "property (the README concedes the shared bias, doc:readme L133).",
        uncertainty="'External' is uncontested; only the *documented* independence "
        "(organizational / model-side / evidence-side) is missing.",
        contradiction_ids=("C3",),
    ),
    CaseClaim(
        "MET-03",
        "The procedure is fully reproducible.",
        ClaimType.METHODOLOGICAL, Domain.EXPERIMENT_META, S.REPRODUCIBLE_CLAIM,
        "Model version, decoding settings, seed, retrieval snapshot, run logs.",
        Verdict.UNVERIFIABLE,
        "No model version, temperature, seed, or retrieval snapshot is given for "
        "either Muse Spark or the validator; LLM calls are non-deterministic by "
        "default. Reproducibility is asserted, not demonstrated. Per the case-study "
        "rules we do not speculate about Muse Spark's unknown settings.",
        uncertainty="High — the run parameters are simply absent.",
    ),
    # -- claims about the validator / its report ---------------------------- #
    CaseClaim(
        "VAL-01",
        "Five general legal claims are 'VERIFIED' because supported by 'the "
        "PubMed document'.",
        ClaimType.CLAIM_ABOUT_VALIDATOR, Domain.LEGAL_PHILOSOPHY, S.REPORT_ALL_VERIFIED,
        "A primary legal-philosophy source with a quoted passage per claim.",
        Verdict.SOURCE_DOMAIN_MISMATCH,
        "PubMed indexes biomedical literature; the claims are legal philosophy "
        "(Kelsen/Hart/Bobbio). 'Supported by the PubMed document' is a "
        "domain-mismatched source, and no document title or passage is named. A "
        "database hit is not evidence.",
        uncertainty="We cannot inspect the retrieved abstract (not printed); the "
        "mismatch is established by the validator's own wording and the code path.",
        contradiction_ids=("C2",),
    ),
    CaseClaim(
        "VAL-02",
        "No citations were found or verifiable in the text.",
        ClaimType.CLAIM_ABOUT_VALIDATOR, Domain.EXPERIMENT_META, S.REPORT_NO_CITATIONS,
        "The reference list in the text and the citation extractor's behaviour.",
        Verdict.CITATION_MISMATCH,
        "The text carries eight well-formed references (muse:L154-161: Kelsen 1960, "
        "Hart 1961, Bobbio 1993, Fuller 1969, Luhmann 1986, Guastini 1986, Tamanaha "
        "2001, Kaplow 1992). 'No citations found' is a false negative of the regex "
        "extractor (code:extract_citations). The deeper problem is the unresolved "
        "pipeline inconsistency C2: the Skeptical Agent asserts source support without "
        "naming a source or passage, while the citation checker finds no verifiable "
        "references, and both are merged without a consistency check "
        "(code:agent_metacognition L48-66) — 'VERIFIED' and 'no citations' need not "
        "logically contradict, but here they stand un-reconciled.",
        uncertainty="Whether each reference is bibliographically correct is NOT "
        "asserted here (not independently checked); only that references plainly exist.",
        contradiction_ids=("C2",),
    ),
    CaseClaim(
        "VAL-03",
        "The validator anchored verification to databases inconsistent with the "
        "domain (legal philosophy attributed to PubMed).",
        ClaimType.CLAIM_ABOUT_VALIDATOR, Domain.EXPERIMENT_META, S.CONCLUSION_DOMAIN_MISMATCH,
        "The validator's retrieval configuration and report.",
        Verdict.SUPPORTED,
        "This self-observation is correct and matches the code: there is no "
        "domain gating on the source set (code:agent_metacognition L48 feeds "
        "whatever was retrieved). The experiment correctly *notices* the mismatch — "
        "then, in EB-02, mis-reads what it implies.",
    ),
    # -- claims about the Epistemic Boundary -------------------------------- #
    CaseClaim(
        "EB-01",
        "Statistical consistency tends to structurally override historical truth.",
        ClaimType.CLAIM_ABOUT_BOUNDARY, Domain.ML_EPISTEMOLOGY, S.CONCLUSION_BOUNDARY_IN_VALIDATOR,
        "A controlled study over many items with a falsifiable metric.",
        Verdict.INTERPRETATION,
        "A theoretical reading of the one observed failure. Plausible as a framing "
        "but presented as a demonstrated law; a single mismatched-retrieval "
        "instance cannot establish a structural tendency.",
        uncertainty="No sample size, controls, or falsifier — n=1 anecdote.",
    ),
    CaseClaim(
        "EB-02",
        "This empirically demonstrates the residual uncertainty regime is an "
        "intrinsic characteristic of the autoregressive architecture.",
        ClaimType.CLAIM_ABOUT_BOUNDARY, Domain.ML_EPISTEMOLOGY, S.CONCLUSION_BOUNDARY_IN_VALIDATOR,
        "Multi-model, multi-domain controlled evaluation with stated falsification "
        "conditions.",
        Verdict.UNSUPPORTED,
        "'Empirically demonstrates ... intrinsic' is unsupported by one uncontrolled "
        "run. It also over-reaches beyond MarCognity's OWN Epistemic Boundary doc "
        "(doc:epistemic_boundary L119-122: 'latent construct, not directly "
        "observable ... causal mechanisms not identified ... further controlled "
        "experimental validation is required'). The forum conclusion is stronger "
        "than the repository it cites.",
        uncertainty="This is the self-sealing move (see contradictions.md / analysis).",
    ),
    # -- content: definitions ----------------------------------------------- #
    CaseClaim(
        "DEF-01",
        "Legal certainty = predictability of legal consequences, broken into "
        "knowability / stability / determinacy.",
        ClaimType.DEFINITION, Domain.LEGAL_PHILOSOPHY, S.DEF_CERTAINTY,
        "Standard doctrinal sources; the specific attribution is a separate claim "
        "(ATTR-01).",
        Verdict.INTERPRETATION,
        "A coherent, broadly standard doctrinal definition. Marked as an "
        "interpretive framing, not adjudicated true/false; its verifiability rides "
        "on the attribution ATTR-01, which the material does not evidence.",
    ),
    CaseClaim(
        "DEF-02",
        "Effectiveness of law = degree of empirical realization; three-dimensional "
        "(compliance / application / enforcement).",
        ClaimType.DEFINITION, Domain.LEGAL_PHILOSOPHY, S.DEF_EFFECTIVENESS,
        "Standard doctrinal sources; attribution handled in ATTR-02.",
        Verdict.INTERPRETATION,
        "As DEF-01: a reasoned definitional framing; the Kelsen/Di Lucia attribution "
        "is the checkable part and is unevidenced in the material.",
    ),
    # -- content: author attributions & direct quotes ----------------------- #
    CaseClaim(
        "ATTR-01",
        "The three-dimensional systematization of certainty follows Guastini and "
        "Bobbio.",
        ClaimType.AUTHOR_ATTRIBUTION, Domain.LEGAL_PHILOSOPHY, S.DEF_CERTAINTY,
        "The cited authors' texts, with locating passages.",
        Verdict.UNVERIFIABLE,
        "A checkable attribution routed to legal philosophy. The experiment "
        "provides no passage from Guastini or Bobbio; the PubMed 'verification' is "
        "domain-mismatched. DESi does not itself adjudicate the attribution here.",
        uncertainty="Guastini (1986) is in the text's own bibliography; that is a "
        "citation, not a verified locating passage.",
    ),
    CaseClaim(
        "ATTR-02",
        "The three-dimensional distinction of effectiveness is Kelsen's, taken up "
        "by Di Lucia.",
        ClaimType.AUTHOR_ATTRIBUTION, Domain.LEGAL_PHILOSOPHY, S.DEF_EFFECTIVENESS,
        "Kelsen's and Di Lucia's texts, with locating passages.",
        Verdict.UNVERIFIABLE,
        "No passage supplied; Di Lucia is not even in the bibliography. Routed to "
        "legal philosophy; unevidenced in the material.",
    ),
    CaseClaim(
        "QUOTE-01",
        'Kelsen: "a legal order is considered valid if its norms are on the whole '
        'effective".',
        ClaimType.DIRECT_QUOTE, Domain.LEGAL_PHILOSOPHY, S.QUOTE_KELSEN,
        "The exact locus in Kelsen (Reine Rechtslehre) — a direct quote demands the "
        "highest provenance.",
        Verdict.UNVERIFIABLE,
        "A quotation mark raises the evidence bar to an exact page/edition. The "
        "material provides none; the validator checked nothing quote-specific. Not "
        "adjudicated here.",
        uncertainty="Direct quotes are the most provenance-hungry claim type and the "
        "least served by abstract-level retrieval.",
    ),
    CaseClaim(
        "QUOTE-02",
        'Bobbio: "the problem of the effectiveness of law is the problem of the '
        'correspondence between the prescriptive model and actual behavior".',
        ClaimType.DIRECT_QUOTE, Domain.LEGAL_PHILOSOPHY, S.QUOTE_BOBBIO,
        "The exact locus in Bobbio (Teoria generale del diritto).",
        Verdict.UNVERIFIABLE,
        "As QUOTE-01: exact-locus evidence required and absent.",
    ),
    # -- content: historical / doctrinal fact ------------------------------- #
    CaseClaim(
        "FACT-01",
        "Fuller lists eight canons of certainty (enumerated).",
        ClaimType.HISTORICAL_FACT, Domain.LEGAL_PHILOSOPHY, S.FACT_FULLER_EIGHT,
        "Fuller, The Morality of Law (1969), ch. 2.",
        Verdict.UNVERIFIABLE,
        "A crisply checkable doctrinal fact (Fuller's eight principles of legality), "
        "routed to a primary legal-philosophy source. The experiment evidences it "
        "with nothing. Note (analyst, not evidence): this is well-known and the "
        "enumeration looks correct, but this case study did not fetch Fuller to "
        "confirm it.",
        uncertainty="Marked unverifiable to respect the rule that recognition is not "
        "verification without a cited passage.",
    ),
    # -- content: heuristic models (must NOT be scored true/false) ---------- #
    CaseClaim(
        "HEUR-01",
        "Certainty index C = alpha*Ch + beta*St + gamma*Ge (alpha+beta+gamma=1).",
        ClaimType.HEURISTIC_MODEL, Domain.LEGAL_PHILOSOPHY, S.HEUR_C,
        "Not applicable — a heuristic construction, not an empirical finding.",
        Verdict.HEURISTIC_PROPOSAL,
        "The text itself flags it as heuristic (muse:L88 'in a heuristic way'). With "
        "no derivation or empirical calibration it is an author's own construction — "
        "neither true nor false, and specifically NOT to be reported as 'verified'.",
    ),
    CaseClaim(
        "HEUR-02",
        "Effectiveness index E = w1*Comp + w2*Appl + w3*Esec.",
        ClaimType.HEURISTIC_MODEL, Domain.LEGAL_PHILOSOPHY, S.HEUR_E,
        "Not applicable — heuristic construction.",
        Verdict.HEURISTIC_PROPOSAL,
        "As HEUR-01: an unvalidated own-construction weighting; a category the "
        "binary VERIFIED/FAILURE scheme cannot represent.",
    ),
    CaseClaim(
        "HEUR-03",
        "Interdependence function E = f(C, K, L), with K institutional capital, L "
        "social legitimation.",
        ClaimType.HEURISTIC_MODEL, Domain.LEGAL_PHILOSOPHY, S.HEUR_INTERDEP,
        "Not applicable — heuristic construction.",
        Verdict.HEURISTIC_PROPOSAL,
        "A proposed functional form with no specified functional shape or data. "
        "Heuristic proposal.",
    ),
    # -- content: theoretical interpretation & empirical / juristic facts --- #
    CaseClaim(
        "THEO-01",
        "Certainty and effectiveness stand in a curvilinear (threshold) "
        "relationship (economic analysis of law).",
        ClaimType.THEORETICAL_INTERPRETATION, Domain.ECONOMICS, S.THEO_CURVILINEAR,
        "Empirical law-and-economics literature testing the threshold.",
        Verdict.INTERPRETATION,
        "A theoretical synthesis attributed to Coase/Posner-style analysis. Presented "
        "as reasoning, not measured; reasonable but unmeasured in the material.",
    ),
    CaseClaim(
        "EMP-01",
        "During COVID-19, Italian DPCMs showed high effectiveness but low certainty.",
        ClaimType.EMPIRICAL, Domain.LAW_POSITIVE, S.EMP_COVID_DPCM,
        "Empirical/legal studies of the DPCM litigation and compliance record.",
        Verdict.UNVERIFIABLE,
        "A contestable empirical-historical claim with no source in the material. "
        "Plausible as illustration; not evidenced, and 'effectiveness/certainty' are "
        "used here without the operational metrics the text itself proposes.",
        uncertainty="Empirically arguable both ways; no data given.",
    ),
    CaseClaim(
        "FACT-02",
        "The EU AI Act introduces a right to explainability as a new component of "
        "certainty.",
        ClaimType.JURISTIC_FACT, Domain.LAW_POSITIVE, S.FACT_EU_AI_ACT,
        "The AI Act text and secondary legal analysis of any 'right to explanation'.",
        Verdict.UNVERIFIABLE,
        "A juristic-factual claim plus an interpretive framing ('component of "
        "certainty'). The existence and scope of a 'right to explanation' is itself "
        "legally contested; the material cites nothing. Routed to positive law, "
        "unevidenced.",
    ),
    CaseClaim(
        "FACT-03",
        "The DAO hack of 2016 illustrates how absolute code-rigidity produces new "
        "uncertainty.",
        ClaimType.HISTORICAL_FACT, Domain.TECH_HISTORY, S.FACT_DAO_HACK,
        "A primary/secondary account of the 2016 DAO incident.",
        Verdict.UNVERIFIABLE,
        "The event (The DAO, 2016) is well established in general knowledge and the "
        "date matches; but the material supplies no source, and a database/common "
        "knowledge is not evidence under this protocol. Not adjudicated here.",
    ),
    # -- content: normative ------------------------------------------------- #
    CaseClaim(
        "NORM-01",
        "The task of a mature legal science is not to resolve the certainty/"
        "effectiveness tension but to design institutions that manage it.",
        ClaimType.NORMATIVE, Domain.LEGAL_PHILOSOPHY, S.NORM_MATURE_SCIENCE,
        "Not applicable — a normative recommendation, not a truth-apt claim.",
        Verdict.NORMATIVE_CLAIM,
        "A value judgement about what legal science 'ought' to do. Not verifiable "
        "against sources; correctly typed as normative rather than forced into "
        "VERIFIED/FAILURE.",
    ),
)


EVIDENCE: tuple[Evidence, ...] = (
    Evidence("MET-01", Domain.EXPERIMENT_META, "the prompt text itself",
             "The reproduced prompt (muse:L12-68).", Domain.EXPERIMENT_META,
             ProvenanceKind.PRIMARY,
             "Always provide scientific references ... at least 5 scientific "
             "references ... direct citations (muse:L56-58); six Phases "
             "(muse:L29-47); verify citation consistency (muse:L64).",
             EvidenceStrength.STRONG,
             "Primary and decisive: the experiment's own prompt refutes its "
             "'no instructions' method statement."),
    Evidence("MET-02", Domain.EXPERIMENT_META, "validator implementation",
             "code:skeptical_agent L62; code:evaluator_prompt L24-28.",
             Domain.EXPERIMENT_META, ProvenanceKind.PRIMARY,
             "res = llm.invoke(prompt.strip()); the evaluator 'receives ... the "
             "reference documents used for generation'.",
             EvidenceStrength.STRONG,
             "One LLM call over the generation context; independence is overstated."),
    Evidence("MET-03", Domain.EXPERIMENT_META, "run parameters / logs",
             _NO_SOURCE, None, ProvenanceKind.NONE, "",
             EvidenceStrength.NONE,
             "No version/seed/temperature/retrieval snapshot given for either model."),
    Evidence("VAL-01", Domain.LEGAL_PHILOSOPHY, "primary legal-philosophy passage",
             "'the PubMed document' (unnamed abstract).", Domain.COGNITIVE_SCIENCE,
             ProvenanceKind.SEMANTIC_ONLY, "",
             EvidenceStrength.NONE,
             "Source-domain mismatch (biomedical DB for legal philosophy); no title "
             "or passage; topical-string overlap at most."),
    Evidence("VAL-02", Domain.EXPERIMENT_META, "the text's reference list",
             "muse:L154-161 (eight references present).", Domain.LEGAL_PHILOSOPHY,
             ProvenanceKind.PRIMARY,
             "Kelsen (1960); Hart (1961); Bobbio (1993); Fuller (1969); Luhmann "
             "(1986); Guastini (1986); Tamanaha (2001); Kaplow (1992).",
             EvidenceStrength.STRONG,
             "References demonstrably exist, so 'no citations found' is a false "
             "negative of the regex extractor (code:extract_citations) — not a "
             "judgement that they are wrong."),
    Evidence("VAL-03", Domain.EXPERIMENT_META, "validator config + report",
             "muse:L235 self-report; code:agent_metacognition L48 (no domain gate).",
             Domain.EXPERIMENT_META, ProvenanceKind.PRIMARY,
             "'assigning the authorship of concepts from the philosophy of law to "
             "PubMed sources'.", EvidenceStrength.MODERATE,
             "The self-observation is correct; the code confirms the absence of "
             "domain gating."),
    Evidence("EB-01", Domain.ML_EPISTEMOLOGY, "controlled multi-item study",
             _NO_SOURCE, None, ProvenanceKind.NONE, "",
             EvidenceStrength.NONE, "Interpretation of a single instance."),
    Evidence("EB-02", Domain.ML_EPISTEMOLOGY, "controlled multi-model evaluation",
             "Contradicted by MarCognity's own boundary doc.", Domain.ML_EPISTEMOLOGY,
             ProvenanceKind.SECONDARY,
             "doc:epistemic_boundary L119-122: 'latent construct, not directly "
             "observable ... causal mechanisms not identified ... further "
             "controlled experimental validation is required'.",
             EvidenceStrength.WEAK,
             "The repository's own document is more cautious than the forum claim; "
             "n=1 cannot 'empirically demonstrate' an 'intrinsic' architecture law."),
    Evidence("DEF-01", Domain.LEGAL_PHILOSOPHY, "doctrinal source", _NO_SOURCE,
             None, ProvenanceKind.NONE, "", EvidenceStrength.NONE,
             "Standard framing; attribution unevidenced (see ATTR-01)."),
    Evidence("DEF-02", Domain.LEGAL_PHILOSOPHY, "doctrinal source", _NO_SOURCE,
             None, ProvenanceKind.NONE, "", EvidenceStrength.NONE,
             "Standard framing; attribution unevidenced (see ATTR-02)."),
    Evidence("ATTR-01", Domain.LEGAL_PHILOSOPHY, "Guastini/Bobbio passage",
             _NO_SOURCE, None, ProvenanceKind.NONE, "", EvidenceStrength.NONE,
             "Guastini (1986) appears in the bibliography as a citation, not a "
             "located supporting passage."),
    Evidence("ATTR-02", Domain.LEGAL_PHILOSOPHY, "Kelsen/Di Lucia passage",
             _NO_SOURCE, None, ProvenanceKind.NONE, "", EvidenceStrength.NONE,
             "Di Lucia is not even in the bibliography."),
    Evidence("QUOTE-01", Domain.LEGAL_PHILOSOPHY, "exact page in Kelsen",
             _NO_SOURCE, None, ProvenanceKind.NONE, "", EvidenceStrength.NONE,
             "Direct quote needs an exact locus; none given."),
    Evidence("QUOTE-02", Domain.LEGAL_PHILOSOPHY, "exact page in Bobbio",
             _NO_SOURCE, None, ProvenanceKind.NONE, "", EvidenceStrength.NONE,
             "Direct quote needs an exact locus; none given."),
    Evidence("FACT-01", Domain.LEGAL_PHILOSOPHY, "Fuller (1969), ch. 2",
             _NO_SOURCE, None, ProvenanceKind.NONE, "", EvidenceStrength.NONE,
             "Checkable and well-known, but not fetched here; recognition != "
             "verification."),
    Evidence("HEUR-01", Domain.LEGAL_PHILOSOPHY, "n/a (heuristic)", "n/a",
             None, ProvenanceKind.NONE, "", EvidenceStrength.NONE,
             "By type not evidence-bearing; must not be scored true/false."),
    Evidence("HEUR-02", Domain.LEGAL_PHILOSOPHY, "n/a (heuristic)", "n/a",
             None, ProvenanceKind.NONE, "", EvidenceStrength.NONE,
             "By type not evidence-bearing."),
    Evidence("HEUR-03", Domain.LEGAL_PHILOSOPHY, "n/a (heuristic)", "n/a",
             None, ProvenanceKind.NONE, "", EvidenceStrength.NONE,
             "By type not evidence-bearing."),
    Evidence("THEO-01", Domain.ECONOMICS, "law-and-economics study", _NO_SOURCE,
             None, ProvenanceKind.NONE, "", EvidenceStrength.NONE,
             "Reasoned synthesis; unmeasured in the material."),
    Evidence("EMP-01", Domain.LAW_POSITIVE, "empirical DPCM study", _NO_SOURCE,
             None, ProvenanceKind.NONE, "", EvidenceStrength.NONE,
             "Contestable empirical claim, no data cited."),
    Evidence("FACT-02", Domain.LAW_POSITIVE, "AI Act text + legal analysis",
             _NO_SOURCE, None, ProvenanceKind.NONE, "", EvidenceStrength.NONE,
             "The scope of any 'right to explanation' is itself contested."),
    Evidence("FACT-03", Domain.TECH_HISTORY, "account of the 2016 DAO hack",
             _NO_SOURCE, None, ProvenanceKind.NONE, "", EvidenceStrength.NONE,
             "Well-established event; still uncited in the material."),
    Evidence("NORM-01", Domain.LEGAL_PHILOSOPHY, "n/a (normative)", "n/a",
             None, ProvenanceKind.NONE, "", EvidenceStrength.NONE,
             "Value judgement; not truth-apt."),
)


def claims_by_id() -> dict[str, CaseClaim]:
    return {c.claim_id: c for c in CLAIMS}


def evidence_by_id() -> dict[str, Evidence]:
    return {e.claim_id: e for e in EVIDENCE}


__all__ = [
    "ClaimType", "Verdict", "Domain", "EvidenceStrength", "ProvenanceKind",
    "CaseClaim", "Evidence", "CLAIMS", "EVIDENCE", "claims_by_id", "evidence_by_id",
]
