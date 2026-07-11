"""Frozen, verbatim capture of the analysed material — case-study Aufgabe 1.

The originals are **not** altered here. Every analytical claim in this package
points back to one of these ``SourceRef`` anchors (document + line + verbatim
quote), so any verdict is traceable to an exact passage — the discipline the
case study demands and the one MarCognity's own report is shown to lack.

Provenance of the captured text (retrieved 2026-07-11):

* ``muse``  — ``epistemic_stress_test/Epistemic Integrity Stress Test Muse Spark 1.1``
  in github.com/elly99-AI/MarCognity-AI (the file named in the Hugging Face
  forum title). Line numbers are 1-based into that file.
* ``code`` files — the referenced MarCognity source modules, same repo, ``main``.
* The Hugging Face thread (user ``elly99``, 2026-07-10, Zenodo DOI
  10.5281/zenodo.20509721) reproduces the same ``muse`` document; the repo file
  is used as the citable primary because it is stable and line-addressable.

This module contains only *quotations of the material under study* — not new
assertions about the world — so it neither needs nor claims external evidence.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SourceRef:
    """One verbatim, addressable anchor into the analysed material."""

    doc: str          # short document id, e.g. "muse" or "code:skeptical_agent"
    locator: str      # line number(s) or symbol, e.g. "L206" or "L48"
    quote: str        # verbatim excerpt (unmodified)

    def cite(self) -> str:
        return f"{self.doc}:{self.locator}"

    def to_dict(self) -> dict[str, str]:
        return {"doc": self.doc, "locator": self.locator, "quote": self.quote}


# Stable document ids and their real origins, for the report's provenance table.
DOCUMENTS: dict[str, str] = {
    "muse": (
        "github.com/elly99-AI/MarCognity-AI — epistemic_stress_test/"
        "'Epistemic Integrity Stress Test Muse Spark 1.1' (main)"
    ),
    "code:skeptical_agent": "MarCognity-AI src/reasoning/skeptical_agent (main)",
    "code:agent_metacognition": "MarCognity-AI src/reasoning/agent_metacognition.py (main)",
    "code:extract_citations": "MarCognity-AI src/evaluation/Extract_Citations (main)",
    "code:evaluator_prompt": (
        "MarCognity-AI benchmark/evaluation_protocol/epistemic_evaluator_prompt.txt (main)"
    ),
    "code:scientific_verification": "MarCognity-AI src/science/scientific_verification.py (main)",
    "doc:epistemic_boundary": "MarCognity-AI Epistemic Boundary.md (main)",
    "doc:readme": "MarCognity-AI README.md (main)",
    "forum": (
        "discuss.huggingface.co/t/epistemic-stress-test-muse-spark-1-1-"
        "validated-by-marcognity-ai/177655 (user elly99, 2026-07-10)"
    ),
}


# --- the experiment's self-description ------------------------------------- #

METHOD_NO_INSTRUCTIONS = SourceRef(
    "muse", "L206",
    "The Muse Spark 1.1  model receives a complex prompt and produces a "
    "structured response. No epistemic instructions (requests for verification, "
    "sources, stages, etc.) are provided.",
)

PROMPT_REQUIRES_REFERENCES = SourceRef(
    "muse", "L56-58",
    "Always provide scientific references to validate claims. [...] Include at "
    "least 5 scientific references, preferably peer-reviewed, and direct "
    "citations from articles when possible.",
)
PROMPT_REQUIRES_STAGES = SourceRef(
    "muse", "L29-47",
    "Phase 1: Problem Analysis [...] Phase 2: Theoretical and/or Mathematical "
    "Development [...] Phase 3: Visualization [...] Phase 4: Tone Optimization "
    "[...] Phase 5: Summary [...] Phase 6: Future Implications",
)
PROMPT_REQUIRES_CITATION_CHECK = SourceRef(
    "muse", "L64",
    "Evaluate the quality of the methodology and verify citation consistency.",
)
PROMPT_REQUIRES_DB_SEARCH = SourceRef(
    "muse", "L24-27",
    "Relevant scientific articles: - arXiv: {arxiv_search} - PubMed: "
    "{pubmed_search} - OpenAlex: {openalex_search}",
)

METHOD_EXTERNAL_VALIDATION = SourceRef(
    "muse", "L208-209",
    "External Validation The generated text is sent to MarCognity-AI. An "
    "epistemic analysis protocol is applied based on: ...",
)
REPRODUCIBLE_CLAIM = SourceRef(
    "muse", "L10",
    "The procedure is fully reproducible and can be replicated with any closed "
    "autoregressive model and any independent external validator.",
)

# --- the validator's report ------------------------------------------------ #

REPORT_ALL_VERIFIED = SourceRef(
    "muse", "L170-198",
    'CLAIM: "Legal certainty and legal effectiveness are two fundamental '
    'concepts..." STATUS: VERIFIED REASON: The claim is supported by the '
    'provided documents, specifically the PubMed document ... [five claims, all '
    "STATUS: VERIFIED, each 'supported by the PubMed document'].",
)
REPORT_NO_CITATIONS = SourceRef(
    "muse", "L201-202",
    "VERIFIED BIBLIOGRAPHIC REFERENCES\nNo citations found or verifiable in the text.",
)
CONCLUSION_DOMAIN_MISMATCH = SourceRef(
    "muse", "L235",
    "the validator anchored its verification to databases that were clearly "
    "inconsistent with the domain being addressed (assigning the authorship of "
    "concepts from the philosophy of law to PubMed sources).",
)

# --- the self-sealing conclusion ------------------------------------------- #

CONCLUSION_BOUNDARY_IN_VALIDATOR = SourceRef(
    "muse", "L237",
    "The test proved so profound that it revealed the Epistemic Boundary even "
    "within the validator itself, proving that statistical consistency tends to "
    "structurally override historical truth. This phenomenon empirically "
    "demonstrates that the residual uncertainty regime is not an isolated flaw "
    "of the generative model (Muse Spark), but an intrinsic characteristic of "
    "the autoregressive architecture, which also influences the automated "
    "evaluation and monitoring processes.",
)

# --- the generated legal text (objects of the content claims) -------------- #

DEF_CERTAINTY = SourceRef(
    "muse", "L73",
    "Legal certainty (Rechtssicherheit, rule of law in its formal sense) "
    "indicates the possibility for the legal subject to predict with reasonable "
    "reliability the legal consequences of their actions. It can be analytically "
    "broken down into three dimensions, following the systematization of "
    "Guastini and Bobbio",
)
DEF_EFFECTIVENESS = SourceRef(
    "muse", "L78",
    "Effectiveness of law (Wirksamkeit, efficacy) indicates instead the degree "
    "of empirical realization of the law. It is also three-dimensional, "
    "according to the classical distinction of Kelsen taken up by Di Lucia",
)
QUOTE_KELSEN = SourceRef(
    "muse", "L103",
    'For Kelsen, effectiveness is a condition of validity of the legal order as '
    'a whole ... "a legal order is considered valid if its norms are on the '
    'whole effective".',
)
QUOTE_BOBBIO = SourceRef(
    "muse", "L107",
    'Bobbio ... "the problem of the effectiveness of law is the problem of the '
    'correspondence between the prescriptive model and actual behavior".',
)
FACT_FULLER_EIGHT = SourceRef(
    "muse", "L109",
    "Fuller lists eight canons of certainty (generality, promulgation, "
    "non-retroactivity, clarity, non-contradiction, possibility, constancy, "
    "congruence between norm and action)",
)
HEURISTIC_PREAMBLE = SourceRef(
    "muse", "L87-88",
    "Phase 2: Theoretical development and critical formalization\nWe can "
    "formalize the two quantities in a heuristic way.",
)
HEUR_C = SourceRef(
    "muse", "L92-93",
    "C = alpha*Ch + beta*St + gamma*Ge  where Ch is semantic clarity, St "
    "temporal stability, Ge generality, with alpha+beta+gamma = 1.",
)
HEUR_E = SourceRef(
    "muse", "L97-98",
    "E = w1*Comp + w2*Appl + w3*Esec  where Comp is compliance, Appl "
    "jurisdictional application, Esec forced enforcement.",
)
HEUR_INTERDEP = SourceRef(
    "muse", "L100",
    "There is an interdependence function E = f(C, K, L) where K is "
    "institutional capital and L social legitimation.",
)
THEO_CURVILINEAR = SourceRef(
    "muse", "L113",
    "certainty and effectiveness are in a curvilinear, not linear, "
    "relationship. Up to a threshold, increasing determinacy increases "
    "compliance ... Beyond the threshold, hyper-regulation produces rigidity",
)
EMP_COVID_DPCM = SourceRef(
    "muse", "L85",
    "during the COVID-19 pandemic, the DPCMs in Italy showed high immediate "
    "effectiveness through rapidly modifiable decrees, but low certainty",
)
FACT_EU_AI_ACT = SourceRef(
    "muse", "L143",
    "The EU AI Act proposal introduces the right to explainability as a new "
    "component of certainty.",
)
FACT_DAO_HACK = SourceRef(
    "muse", "L145",
    'as the case of The DAO hack 2016 demonstrates, absolute rigidification '
    "produces new uncertainty when code diverges from social expectations.",
)
NORM_MATURE_SCIENCE = SourceRef(
    "muse", "L162",
    "The task of a mature legal science is not to resolve the tension, but to "
    "design institutions capable of managing it in a reflective and justifiable "
    "way.",
)
BIBLIOGRAPHY = SourceRef(
    "muse", "L154-161",
    "Kelsen (1960) Reine Rechtslehre; Hart (1961) The Concept of Law; Bobbio "
    "(1993) Teoria generale del diritto; Fuller (1969) The Morality of Law; "
    "Luhmann (1986) A Sociological Theory of Law; Guastini (1986); Tamanaha "
    "(2001); Kaplow (1992) Rules versus Standards, Duke Law Journal 42(3).",
)

# --- the validator's implementation (evidence about MarCognity itself) ----- #

CODE_SKEPTIC_IS_ONE_LLM_CALL = SourceRef(
    "code:skeptical_agent", "L62",
    "res = llm.invoke(prompt.strip())   # the entire 'Skeptical Agent' is one "
    "LLM call over the same model",
)
CODE_EVALUATOR_NOT_INDEPENDENT = SourceRef(
    "code:evaluator_prompt", "L24-28",
    "Epistemic evaluation is performed by an independent LLM acting as a "
    "skeptical agent. The evaluator receives: - the generated response - the "
    "reference documents used for generation",
)
CODE_SOURCE_IS_GENERATION_CONTEXT = SourceRef(
    "code:agent_metacognition", "L48",
    "skeptical_report = skeptical_agent(question, response_text, context_docs)  "
    "# context_docs = the same retrieval that fed generation",
)
CODE_COHERENCE_OPTIMIZED = SourceRef(
    "code:agent_metacognition", "L33-43",
    "for i in range(max_iter): ... score = evaluate_coherence(...); if score < "
    "0.7: response_text = improve_response(...)  # the loop optimizes coherence",
)
CODE_CITATION_SUBSYSTEM_DECOUPLED = SourceRef(
    "code:agent_metacognition", "L48-66",
    "skeptical_report = skeptical_agent(...); verified_refs = await "
    "verify_citations(response_text)  # two independent subsystems concatenated, "
    "never reconciled: one says VERIFIED, the other 'No citations found'.",
)
CODE_CITATION_IS_PRESENCE_HIT = SourceRef(
    "code:scientific_verification", "L18-30",
    'pubmed_res = await search_pubmed_async(citation) ... "valid_pubmed": '
    "bool(pubmed_res)  # a database hit counts as valid; no passage is read",
)
BOUNDARY_DOC_HEDGED = SourceRef(
    "doc:epistemic_boundary", "L119-122",
    "The Epistemic Boundary is a latent descriptive construct, not a directly "
    "observable object ... Causal mechanisms underlying the residual regime are "
    "not fully identified ... Further controlled experimental validation is "
    "required.",
)
README_EVALUATOR_SHARES_BIAS = SourceRef(
    "doc:readme", "L133",
    "The use of an LLM as independent evaluator introduces a known "
    "methodological limitation: the evaluator may share epistemic biases with "
    "the evaluated system.",
)


__all__ = ["SourceRef", "DOCUMENTS"]
