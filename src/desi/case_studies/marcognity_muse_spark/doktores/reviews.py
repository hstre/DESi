"""The audit content: four source-anchored doctor rule sets (Doktores).

This is a closed, authored review dataset in the same spirit as the parent
case study's ``claims.py`` — every verdict names a stated rule and a source
anchor, so a reader can check the reasoning rather than trust it. The engine
(``engine.py``) only aggregates, synthesises and renders it; it invents nothing.

Adversarial posture: the doctors try to REFUTE, REVISE or BOUND the DESi findings.
The result is deliberately mixed — some findings survive, some are qualified, two
"structural contradiction" labels are downgraded, and dissent is preserved.
"""
from __future__ import annotations

from .models import (
    Confidence,
    ContradictionClass,
    ContradictionReview,
    Decision,
    DoctorVerdict,
    FairnessFinding,
    MethodologyFinding,
    Revision,
    Role,
)


def _v(role: Role, decision: Decision, reason: str, anchors, rule: str = "") -> DoctorVerdict:
    return DoctorVerdict(role, decision, reason, tuple(anchors), rule)


D1 = Role.PROVENANCE_REVIEWER
D2 = Role.METHODOLOGY_REVIEWER
D3 = Role.LOGIC_REVIEWER
D4 = Role.FAIRNESS_REVIEWER

U = Decision.UPHOLD
UQ = Decision.UPHOLD_WITH_QUALIFICATION
REV = Decision.REVISE
REJ = Decision.REJECT
INS = Decision.INSUFFICIENT_MATERIAL

# --------------------------------------------------------------------------- #
# Doktor 1 (+ 2/3/4 where they weigh in) — per-claim verdicts.
# Tuple: (claim_id, [DoctorVerdict...], confidence, dissent[], required_changes[])
# --------------------------------------------------------------------------- #

CLAIM_VERDICTS: tuple[tuple, ...] = (
    ("MET-01",
     [_v(D1, U, "The prompt is printed in full (muse:L12-68) and demands exactly what "
         "the Method (muse:L206) says was absent; the 'contradicted' verdict is derived "
         "correctly from the primary source.", ["muse:L206", "muse:L56-58", "claims.jsonl:MET-01"],
         "R-PROV-VERDICT"),
      _v(D3, U, "A genuine logical contradiction on the experiment's own terms.",
         ["muse:L206", "muse:L29-47"], "R-LOG-CONTRA")],
     Confidence.HIGH, [], []),

    ("MET-02",
     [_v(D1, UQ, "'partially_supported' is the fair call: 'external' holds, 'independent' "
         "is not established. DESi already softened this from an earlier 'contradicted'.",
         ["claims.jsonl:MET-02", "code:evaluator_prompt L24-28"], "R-PROV-VERDICT"),
      _v(D2, U, "Correctly separates the true conjunct (external) from the unproven one "
         "(independent); no overreach.", ["muse:L208", "doc:readme L133"], "R-METH-FAIR")],
     Confidence.HIGH, [], []),

    ("MET-03",
     [_v(D1, U, "No model version, seed, temperature or retrieval snapshot is given; "
         "'unverifiable_from_available_evidence' is exactly the right verdict — not "
         "'false'.", ["muse:L10", "claims.jsonl:MET-03"], "R-PROV-UNVERIF"),
      _v(D2, U, "DESi does not infer falsehood from the missing parameters — a correct "
         "restraint.", ["claims.jsonl:MET-03"], "R-METH-NOFALSEHOOD")],
     Confidence.HIGH, [], []),

    ("VAL-01",
     [_v(D1, UQ, "The load-bearing defect is the MISSING named passage (nothing citable), "
         "which is unassailable. 'source_domain_mismatch' is probable but slightly strong: "
         "PubMed does index some health-law / bioethics material, so strict domain-exclusion "
         "is not certain. Keep the verdict, foreground the missing passage.",
         ["muse:L174-198", "evidence.jsonl:VAL-01", "analysis.py:source_domain_gate"],
         "R-PROV-DOMMIS"),
      _v(D4, REV, "Steelman: if the retrieved 'PubMed document' were a health-law article, "
         "the domain would not be strictly wrong — but no title is given, so it is "
         "unverifiable regardless; the mismatch label overstates certainty.",
         ["muse:L235"], "R-FAIR-STEELMAN")],
     Confidence.MEDIUM,
     ["Minority (fairness): 'source_domain_mismatch' asserts more domain-certainty than the "
      "unnamed source allows; the decisive, uncontested point is the absent passage."],
     ["VAL-01 rationale: foreground 'no citable passage / not evidence' ahead of the strict "
      "PubMed-vs-legal-philosophy domain claim."]),

    ("VAL-02",
     [_v(D1, U, "Correctly distinguishes citation_mismatch from mere missing citation: the "
         "text carries eight well-formed references (muse:L154-161) that the regex extractor "
         "missed — a false negative, not an absence.",
         ["muse:L154-161", "claims.jsonl:VAL-02", "code:extract_citations"], "R-PROV-CITEMIS")],
     Confidence.HIGH, [], []),

    ("VAL-03",
     [_v(D1, UQ, "'supported' is acceptable — it endorses the validator's own correct "
         "self-observation (muse:L235) and the code shows no domain gate; anchor it as such.",
         ["muse:L235", "code:agent_metacognition L48"], "R-PROV-VERDICT")],
     Confidence.MEDIUM, [], []),

    ("EB-01",
     [_v(D3, U, "'interpretation' is right: a theoretical reading of one instance, not a "
         "demonstrated law.", ["muse:L237", "claims.jsonl:EB-01"], "R-LOG-INTERP")],
     Confidence.MEDIUM, [], []),

    ("EB-02",
     [_v(D3, U, "'unsupported' is correct: 'empirically demonstrates ... intrinsic' from a "
         "single uncontrolled run over-reaches even MarCognity's own hedged Boundary doc.",
         ["muse:L237", "doc:epistemic_boundary L119-122"], "R-LOG-OVERREACH"),
      _v(D4, U, "Fair: DESi pins the over-reach on the forum conclusion, not the code or the "
         "hedged construct.", ["doc:epistemic_boundary L119-122"], "R-FAIR-SCOPE")],
     Confidence.HIGH, [], []),

    ("DEF-01", [_v(D1, U, "'interpretation' fits a standard doctrinal definition; not "
                   "adjudicated as true/false.", ["muse:L73"], "R-PROV-TYPE")],
     Confidence.MEDIUM, [], []),
    ("DEF-02", [_v(D1, U, "As DEF-01.", ["muse:L78"], "R-PROV-TYPE")],
     Confidence.MEDIUM, [], []),

    ("ATTR-01", [_v(D1, U, "'unverifiable' appropriate: an attribution needs a locating "
                    "passage the material does not supply.", ["muse:L73"], "R-PROV-UNVERIF")],
     Confidence.HIGH, [], []),
    ("ATTR-02", [_v(D1, U, "As ATTR-01; Di Lucia isn't even in the bibliography.",
                    ["muse:L78"], "R-PROV-UNVERIF")], Confidence.HIGH, [], []),

    ("QUOTE-01", [_v(D1, U, "Direct quote → highest provenance bar; 'unverifiable' correct "
                     "with no exact locus.", ["muse:L103"], "R-PROV-UNVERIF")],
     Confidence.HIGH, [], []),
    ("QUOTE-02", [_v(D1, U, "As QUOTE-01.", ["muse:L107"], "R-PROV-UNVERIF")],
     Confidence.HIGH, [], []),

    ("FACT-01",
     [_v(D1, UQ, "'unverifiable' is defensible and the rationale already flags it as a "
         "checkable, well-known fact (Fuller's eight canons) — recognition is not "
         "verification without a fetched passage.", ["muse:L109"], "R-PROV-UNVERIF")],
     Confidence.MEDIUM, [], []),

    ("HEUR-01",
     [_v(D1, U, "A genuine strength of DESi: the formula is typed 'heuristic_proposal', not "
         "forced into VERIFIED/FAILURE; the text itself says 'in a heuristic way' (muse:L88).",
         ["muse:L88", "muse:L92", "claims.jsonl:HEUR-01"], "R-PROV-TYPE")],
     Confidence.HIGH, [], []),
    ("HEUR-02", [_v(D1, U, "As HEUR-01.", ["muse:L97"], "R-PROV-TYPE")], Confidence.HIGH, [], []),
    ("HEUR-03", [_v(D1, U, "As HEUR-01.", ["muse:L100"], "R-PROV-TYPE")], Confidence.HIGH, [], []),

    ("THEO-01", [_v(D1, U, "'interpretation' fits a theoretical synthesis; unmeasured in the "
                    "material.", ["muse:L113"], "R-PROV-TYPE")], Confidence.MEDIUM, [], []),

    ("EMP-01", [_v(D1, U, "'unverifiable' right: a contestable empirical claim with no source.",
                   ["muse:L85"], "R-PROV-UNVERIF")], Confidence.MEDIUM, [], []),

    ("FACT-02",
     [_v(D1, UQ, "'unverifiable' is defensible: the EU AI Act is real, but the specific "
         "framing ('right to explainability as a component of certainty') is contested and "
         "unsourced here.", ["muse:L143"], "R-PROV-UNVERIF"),
      _v(D4, REV, "Minority: could equally be typed 'interpretation' (a framing) rather than "
         "'unverifiable' (a fact-gap).", ["muse:L143"], "R-FAIR-STEELMAN")],
     Confidence.MEDIUM,
     ["Minority (fairness): FACT-02 straddles juristic-fact and interpretation; either "
      "verdict is defensible."], []),

    ("FACT-03",
     [_v(D1, UQ, "'unverifiable' under the protocol is defensible; the rationale ALREADY "
         "acknowledges the DAO-2016 event is well established and the date matches, so it "
         "does not read as false skepticism. No change required.",
         ["muse:L145", "claims.jsonl:FACT-03"], "R-PROV-UNVERIF"),
      _v(D4, REV, "Minority: applying 'no cited passage' to a universally known public event "
         "is over-cautious in spirit; the verdict is protocol-correct but borderline.",
         ["muse:L145"], "R-FAIR-STEELMAN")],
     Confidence.MEDIUM,
     ["Minority (fairness): the strict 'database/common knowledge is not evidence' rule is "
      "protocol-correct but arguably over-cautious for The DAO (2016)."], []),

    ("NORM-01", [_v(D1, U, "'normative_claim' is correct: a value judgement, not truth-apt.",
                    ["muse:L162"], "R-PROV-TYPE")], Confidence.HIGH, [], []),
)


# --------------------------------------------------------------------------- #
# Doktor 3 — the three conflicts.
# --------------------------------------------------------------------------- #

CONTRADICTION_REVIEWS: tuple[ContradictionReview, ...] = (
    ContradictionReview(
        cid="C1",
        original_classification="structural_contradiction",
        reviewed_classification=ContradictionClass.LOGICAL_CONTRADICTION,
        upheld=True,
        reason="The Method (muse:L206) asserts the model received no verification/source/"
               "stage instructions; the exhibited prompt demands ≥5 sourced references, a "
               "citation-consistency check and six phases (muse:L24-64). On the experiment's "
               "own terms both cannot be true — a genuine logical contradiction.",
        source_anchors=("muse:L206", "muse:L56-58", "muse:L64", "muse:L29-47"),
        minority_opinion="The section header muse:L12 labels the prompt 'prompt used on "
                         "chatgpt (taken from marcognity)', so its provenance is ambiguous; a "
                         "strict reviewer could hold C1 'unresolved' until it is confirmed the "
                         "printed prompt is exactly Muse Spark's. The Method's own wording "
                         "('receives a complex prompt', no instructions) keeps the "
                         "contradiction standing, but the caveat should be recorded.",
        report_change_required=True,
        confidence=Confidence.HIGH,
    ),
    ContradictionReview(
        cid="C2",
        original_classification="structural_contradiction",
        reviewed_classification=ContradictionClass.PIPELINE_INCONSISTENCY,
        upheld=False,
        reason="'Five claims VERIFIED' and 'No citations found or verifiable' can both hold: "
               "the claim-verifier checks against provided documents while the citation module "
               "detects formal bibliographic references — independent subsystems. It is NOT a "
               "logical contradiction. The real defect is VERIFIED without an auditable "
               "evidence passage, and two subsystem outputs merged without reconciliation "
               "(code:agent_metacognition L48-66). DESi's current label already reads "
               "'Pipeline-Inkonsistenz'; the audit confirms it.",
        source_anchors=("muse:L170-198", "muse:L201-202", "code:agent_metacognition L48-66"),
        minority_opinion="",
        report_change_required=False,
        confidence=Confidence.HIGH,
    ),
    ContradictionReview(
        cid="C3",
        original_classification="structural_contradiction",
        reviewed_classification=ContradictionClass.UNSUBSTANTIATED_CLAIM,
        upheld=False,
        reason="A single external llm.invoke does not refute FORMAL independence — it could "
               "be independent. But independence is not operationalised on any axis: not "
               "organizational, not model-side (validator model unspecified), not source-side "
               "(same retrieval), not generation-context-independent (receives the generation "
               "documents, code:evaluator_prompt L24-28), not evaluation-logic-independent, "
               "and run parameters are opaque. So C3 is an unsubstantiated / under-"
               "operationalised independence claim, not a contradiction. DESi's current label "
               "already reads 'Unbelegte Unabhängigkeit'; the audit confirms it.",
        source_anchors=("muse:L208", "muse:L10", "code:evaluator_prompt L24-28",
                        "code:skeptical_agent L62", "doc:readme L133"),
        minority_opinion="",
        report_change_required=False,
        confidence=Confidence.HIGH,
    ),
)


# --------------------------------------------------------------------------- #
# Doktor 2 — methodology.
# --------------------------------------------------------------------------- #

METHODOLOGY_FINDINGS: tuple[MethodologyFinding, ...] = (
    MethodologyFinding("Rekonstruktion des Originalversuchs", Decision.UPHOLD,
        "Purpose, prompt, generated text, validator report, method and conclusion are "
        "reconstructed faithfully and verbatim-anchored (source_material.py).",
        ("source_material.py",)),
    MethodologyFinding("Ist die MarCognity-Validierung extern/unabhängig?", Decision.UPHOLD_WITH_QUALIFICATION,
        "'External' yes (a separate pass, different model family); 'independent' is not "
        "operationalised (C3). DESi's partially_supported verdict is the fair reading.",
        ("muse:L208", "code:evaluator_prompt L24-28")),
    MethodologyFinding("Fairer Umgang mit dem Begriff 'Validierung'", Decision.UPHOLD,
        "DESi does not strawman 'validation'; it credits the README's own caution and "
        "targets the forum conclusion, not the framework wholesale.",
        ("doc:readme L133",)),
    MethodologyFinding("Reproduzierbarkeitsbehauptung", Decision.UPHOLD,
        "DESi's 'unverifiable' for the reproducibility claim is fair — no params are given.",
        ("muse:L10",)),
    MethodologyFinding("Schluss von fehlender Evidenz auf Falschheit?", Decision.UPHOLD,
        "Crucially NO: DESi uses 'unverifiable_from_available_evidence', never 'false', for "
        "unsourced content claims. This is the correct epistemic move.",
        ("claims.jsonl:ATTR-01", "claims.jsonl:QUOTE-01")),
    MethodologyFinding("Kuratierte Auswahl vs. suggerierte Vollständigkeit", Decision.UPHOLD_WITH_QUALIFICATION,
        "The artifacts now state 'curated selection, not measured completeness'. Residual "
        "risk: the headline statistics ('only 4/23 admissible', '18/23 no passage') can still "
        "read as a measured property of the Muse text. A framing caveat is warranted.",
        ("REPORT.md", "summary.json:source_gate_admissible")),
    MethodologyFinding("Fairness des Vergleichs MarCognity vs. DESi", Decision.UPHOLD_WITH_QUALIFICATION,
        "Mostly fair, but the 'Quellenpassung: keine' cell is absolute: MarCognity DOES "
        "retrieve from multiple databases — the failure is gating/provenance, not retrieval. "
        "Credit the genuine design strengths.",
        ("comparison.md",)),
    MethodologyFinding("Werden DESis eigene Grenzen dargestellt?", Decision.UPHOLD,
        "Yes — REPORT.md §8 states them explicitly (curated fixture, no adjudication, small "
        "extensions).", ("REPORT.md",)),
)


# --------------------------------------------------------------------------- #
# Doktor 4 — steelman + over-reach flags.
# --------------------------------------------------------------------------- #

FAIRNESS_FINDINGS: tuple[FairnessFinding, ...] = (
    FairnessFinding("steelman",
        "'External validation' most charitably means a separate evaluation pass distinct from "
        "generation — which is literally what happens; the word need not imply full "
        "organisational independence.", ("muse:L208",)),
    FairnessFinding("steelman",
        "The framework's building blocks are methodologically reasonable: claim decomposition, "
        "multi-source retrieval (arXiv/PubMed/OpenAlex/Zenodo), and an explicit skeptical "
        "prompt that asks for per-claim support. The failure is in gating and provenance, not "
        "in the idea.", ("doc:readme L56-67",)),
    FairnessFinding("steelman",
        "MarCognity's own README is markedly more careful than the forum post: it concedes the "
        "evaluator may share biases and is 'not for production' — so the over-reach is in the "
        "forum conclusion, not the code.", ("doc:readme L133", "doc:readme L84")),
    FairnessFinding("steelman",
        "As a hedged descriptive hypothesis about residual verification error, the 'Epistemic "
        "Boundary' is a legitimate (if unproven) research framing, consistent with known LLM "
        "calibration limits; its Boundary doc even walked back the earlier '8-15%' claim.",
        ("doc:epistemic_boundary L74-78", "doc:epistemic_boundary L119-122")),
    FairnessFinding("overreach_flag",
        "DESi's 'source_domain_mismatch' asserts more domain-certainty than an unnamed source "
        "allows; the decisive, uncontested defect is the missing citable passage.",
        ("claims.jsonl:VAL-01",)),
    FairnessFinding("overreach_flag",
        "The '18/23 no evidence passage' / '4/23 admissible' headlines risk being read as a "
        "measured property of the Muse text rather than a property of the experiment's supplied "
        "evidence over 23 curated claims.", ("summary.json",)),
    FairnessFinding("overreach_flag",
        "Labelling all three findings 'structural contradictions' (original framing) was too "
        "strong for C2 and C3 — corrected to pipeline-inconsistency and unsubstantiated "
        "independence.", ("contradictions.md",)),
)


# --------------------------------------------------------------------------- #
# Revisions the audit MANDATES for the parent case study (applied AFTER the run).
# --------------------------------------------------------------------------- #

REVISIONS: tuple[Revision, ...] = (
    Revision(
        "R1",
        ("analysis.py", "REPORT.md", "contradiction_reviews.jsonl"),
        "C1 explanation ends: '... Ein echter Widerspruch: beide Aussagen können nicht "
        "zugleich wahr sein.'",
        "Adds an audit caveat: the prompt section header (muse:L12) labels the prompt "
        "'prompt used on chatgpt (taken from marcognity)', so its provenance is ambiguous; "
        "the contradiction still holds on the Method's own wording, but the caveat is recorded.",
        "Doktor 3 minority opinion on C1 (prompt-provenance ambiguity).",
        "C1 survives as a logical contradiction, but the audit requires the provenance caveat "
        "to be transparent about the one residual uncertainty.",
    ),
    Revision(
        "R2",
        ("claims.py", "claims.jsonl", "evidence.jsonl"),
        "VAL-01 rationale leads with 'PubMed indexes biomedical literature ... domain-"
        "mismatched source'.",
        "VAL-01 rationale leads with the unassailable point — no named source or passage, so "
        "not evidence — and treats the domain-mismatch as the probable, secondary reason.",
        "Doktor 1 + Doktor 4: source_domain_mismatch overstates domain-certainty for an "
        "unnamed source.",
        "Foregrounds the decisive, uncontested defect; keeps the verdict but lowers the "
        "certainty of the domain claim.",
    ),
    Revision(
        "R4",
        ("REPORT.md",),
        "§4 opens: 'Von 23 Claims haben nur 4 eine domänenzulässige ... Evidenz'.",
        "Adds a caveat that '4/23 admissible' and '18/23 no passage' describe the experiment's "
        "SUPPLIED evidence over the 23 CURATED claims — not a measured groundedness of the Muse "
        "text.",
        "Doktor 2 + Doktor 4 over-reach flag on the headline statistics.",
        "Prevents the numbers being read as a measured coverage/groundedness property.",
    ),
    Revision(
        "R5",
        ("REPORT.md", "fairness_review.md"),
        "The comparison and fairness sections do not explicitly credit MarCognity's genuine "
        "design strengths.",
        "Adds a sentence crediting MarCognity's real strengths (claim decomposition, "
        "multi-source retrieval, an explicit skeptical pass) and locating the fault in gating "
        "and provenance, not in the idea.",
        "Doktor 4 steelman.",
        "Fairness: the case study should name what the framework gets right before what it "
        "gets wrong.",
    ),
)


__all__ = [
    "CLAIM_VERDICTS", "CONTRADICTION_REVIEWS", "METHODOLOGY_FINDINGS",
    "FAIRNESS_FINDINGS", "REVISIONS",
]
