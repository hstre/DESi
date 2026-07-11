"""Deterministic analysis engine — case-study Aufgaben 3, 4, 6, 7, 8.

Everything here is rule-based and reproducible; no LLM is called. It reuses real
DESi machinery rather than re-implementing it:

* ``desi.self_audit.contradictions.find_contradictions`` — the same/​different-value
  contradiction detector — surfaces the three structural conflicts (Aufgabe 3).
* ``desi.memory`` (``Claim`` / ``Provenance`` / ``Relation`` / ``InMemoryStore``) —
  the claim graph with mandatory provenance and ``CONTRADICTS`` edges.

Two small, general helpers are added because DESi has no knowledge-domain router
(it routes tasks, not fields of knowledge): ``source_domain_gate`` and the
``self_sealing_analysis`` falsifiability check. Both are field-agnostic and take
their data from the closed fixture, not from this one text.
"""
from __future__ import annotations

from dataclasses import dataclass

from desi.memory.claim import Claim, ClaimState, Provenance
from desi.memory.relations import Relation, RelationType
from desi.memory.store import InMemoryStore
from desi.self_audit.claim import ClaimKind, ExplicitClaim, make_claim_id
from desi.self_audit.contradictions import Contradiction, find_contradictions

from . import claims as C
from .claims import Domain, ProvenanceKind, Verdict

RUN_ID = "marcognity_muse_spark_v1"


# --------------------------------------------------------------------------- #
# Aufgabe 3 — structural contradictions, via DESi's own detector.
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class NamedContradiction:
    """A key/value inconsistency from the reused detector, with a stable id + gloss.

    ``kind`` names precisely what was found — not every conflict is a *logical*
    contradiction: C1 is (prompt vs. method), C2 is an unresolved pipeline
    inconsistency, C3 is an unsubstantiated independence claim. The detector finds
    all three the same way (same key, different value); the ``kind`` keeps the
    prose honest about their differing strength.
    """

    cid: str
    kind: str
    title: str
    contradiction: Contradiction
    explanation: str


def _explicit(doc: str, line: int, key: str, value: str,
              artifact: str = "") -> ExplicitClaim:
    claim_id = make_claim_id(doc, line, ClaimKind.PHASE, key, value)
    return ExplicitClaim(
        claim_id=claim_id, doc_id=doc, doc_path=doc, line_number=line,
        line_text=value, kind=ClaimKind.PHASE, key=key, value=value,
        referenced_artifact=artifact,
    )


# The three conflicts, expressed as key/value claims the detector groups.
# C1 & C2 are same-document (fire the document branch); C3 spans two documents
# and fires the referenced-artifact branch.
_CONTRA_INPUTS: tuple[tuple[str, str, str, str, ExplicitClaim, ExplicitClaim], ...] = (
    (
        "C1",
        "Widerspruch (logisch)",
        "Prompt ↔ Methode",
        "Die Methode (muse:L206) sagt, das Modell habe keine Anweisungen zu "
        "Verifikation, Quellen oder Stufen erhalten. Der abgedruckte Prompt verlangt "
        "genau diese: ≥5 wissenschaftliche Quellen mit Direktzitaten (muse:L56-58), "
        "eine Zitationskonsistenzprüfung (muse:L64), Datenbanksuchen (muse:L24-27) und "
        "sechs benannte Phasen (muse:L29-47). Das ist ein echter logischer Widerspruch: "
        "beide Aussagen können nicht zugleich wahr sein.",
        _explicit("muse", 206, "epistemic_instructions_given", "none: no verification/sources/stages"),
        _explicit("muse", 56, "epistemic_instructions_given",
                  "required: >=5 references, direct citations, citation-check, six phases"),
    ),
    (
        "C2",
        "Pipeline-Inkonsistenz",
        "VERIFIED ohne zitierbare Evidenz",
        "„VERIFIED“ und „No citations found“ können theoretisch beide zugleich "
        "zutreffen — es ist kein strikter logischer Widerspruch. Der eigentliche Fehler "
        "ist eine unaufgelöste Pipeline-Inkonsistenz: der Skeptical Agent behauptet "
        "Quellenunterstützung (muse:L170-198), nennt aber keine Quelle und keine "
        "Passage (nur „das PubMed-Dokument“); der Citation Checker erkennt zugleich "
        "keine überprüfbaren Referenzen (muse:L201-202) — obwohl der Text acht "
        "Referenzen trägt (muse:L154-161). Beide Resultate werden ohne "
        "Konsistenzprüfung zusammengefügt (code:agent_metacognition L48-66).",
        _explicit("muse", 172, "citable_evidence_for_verified_claims",
                  "asserted: claims supported by 'the PubMed document'"),
        _explicit("muse", 202, "citable_evidence_for_verified_claims",
                  "found: no citable/verifiable reference, no named source or passage"),
    ),
    (
        "C3",
        "Unbelegte Unabhängigkeit",
        "„Independent external validation“ ↔ keine dokumentierte Unabhängigkeit",
        "Dass der Validator technisch nur ein einzelnes llm.invoke ist "
        "(code:skeptical_agent L62), widerlegt Unabhängigkeit nicht per se — ein "
        "externer LLM-Aufruf könnte formal unabhängig sein. Der Konflikt ist enger: die "
        "Methode behauptet „independent external validation“ (muse:L208; muse:L10), ohne "
        "dass auf irgendeiner Achse Unabhängigkeit dokumentiert wäre — organisatorisch, "
        "modellseitig oder evidenzseitig. Der Validator erhält genau die Dokumente, die "
        "schon die Generierung speisten (code:evaluator_prompt L24-28), ist nicht "
        "adversarial abgesichert und nicht reproduzierbar spezifiziert; das README "
        "räumt die geteilte Verzerrung selbst ein (doc:readme L133). Die Unabhängigkeit "
        "ist behauptet, nicht etabliert — eine methodische Fehlklassifikation.",
        _explicit("muse", 208, "validator_independence",
                  "claimed: independent external validation", artifact="marcognity_validator"),
        _explicit("code:evaluator_prompt", 24, "validator_independence",
                  "documented independence: none (evidence-side dependent on the "
                  "generation documents; not adversarial; not reproducibly specified)",
                  artifact="marcognity_validator"),
    ),
)


def detect_contradictions() -> tuple[NamedContradiction, ...]:
    """Run DESi's contradiction detector over the encoded key/value claims.

    Returns exactly the conflicts the detector finds, matched back to their
    stable ids and human glosses — so the structural claim ('there is a
    contradiction') is produced by reused DESi code, not asserted by prose.
    """
    all_inputs: list[ExplicitClaim] = []
    for _cid, _kind, _t, _e, a, b in _CONTRA_INPUTS:
        all_inputs.extend((a, b))
    found = find_contradictions(tuple(all_inputs))

    by_key = {c.key: c for c in found}
    out: list[NamedContradiction] = []
    for cid, kind, title, expl, a, _b in _CONTRA_INPUTS:
        con = by_key.get(a.key)
        if con is not None:
            out.append(NamedContradiction(cid, kind, title, con, expl))
    return tuple(out)


# --------------------------------------------------------------------------- #
# Aufgabe 8 (partial) — the claim graph, reusing the memory layer.
# --------------------------------------------------------------------------- #

# A few "material fact" nodes so each contradiction edge has two real endpoints.
_MATERIAL_FACTS: tuple[tuple[str, str], ...] = (
    ("PROMPT-01", "The prompt demands >=5 references, direct citations, a "
                  "citation-consistency check, and six phases (muse:L24-64)."),
    ("CODE-01", "No independence is documented for the validator on any axis: it "
                "runs on the generation documents (evaluator_prompt L24-28), is "
                "non-adversarial and not reproducibly specified (skeptical_agent L62)."),
)

# CONTRADICTS edges between real CaseClaim / material-fact nodes.
_CONTRADICTS_EDGES: tuple[tuple[str, str], ...] = (
    ("MET-01", "PROMPT-01"),   # C1
    ("VAL-01", "VAL-02"),      # C2
    ("MET-02", "CODE-01"),     # C3
)

_CONFIDENCE_BY_VERDICT: dict[Verdict, float] = {
    Verdict.SUPPORTED: 0.85,
    Verdict.PARTIALLY_SUPPORTED: 0.55,
    Verdict.CONTRADICTED: 0.1,
    Verdict.UNSUPPORTED: 0.15,
    Verdict.UNVERIFIABLE: 0.3,
    Verdict.INTERPRETATION: 0.5,
    Verdict.HEURISTIC_PROPOSAL: 0.5,
    Verdict.NORMATIVE_CLAIM: 0.5,
    Verdict.CITATION_MISMATCH: 0.1,
    Verdict.SOURCE_DOMAIN_MISMATCH: 0.1,
}


def build_claim_graph() -> InMemoryStore:
    """Materialise the claims as a real DESi memory graph.

    Each claim becomes a provenance-carrying ``Claim``; the three structural
    conflicts become ``CONTRADICTS`` relations. This is the reused
    provenance/graph substrate, not a bespoke structure.
    """
    store = InMemoryStore()
    prov = Provenance(source="marcognity_muse_spark_case_study", run_id=RUN_ID,
                      operator_path=("case_study", "claim_extraction"))
    ids: dict[str, str] = {}

    for cc in C.CLAIMS:
        claim = Claim(
            claim_id=cc.claim_id, content=cc.text,
            method=f"case_study/{cc.claim_type.value}",
            state=ClaimState.PROPOSED,
            confidence=_CONFIDENCE_BY_VERDICT.get(cc.verdict, 0.5),
            provenance=prov,
        )
        store.add_claim(claim)
        ids[cc.claim_id] = claim.claim_id

    for fid, text in _MATERIAL_FACTS:
        claim = Claim(claim_id=fid, content=text, method="case_study/material_fact",
                      state=ClaimState.CONFIRMED, confidence=0.9, provenance=prov)
        store.add_claim(claim)
        ids[fid] = claim.claim_id

    for src, tgt in _CONTRADICTS_EDGES:
        store.add_relation(Relation(
            source_claim_id=ids[src], target_claim_id=ids[tgt],
            rel_type=RelationType.CONTRADICTS,
        ))
    return store


def graph_summary() -> dict:
    store = build_claim_graph()
    claims = list(store.all_claims())
    contradicts = [
        r for c in claims
        for r in store.relations_for(c.claim_id, rel_type=RelationType.CONTRADICTS)
    ]
    return {
        "claim_nodes": len(claims),
        "contradicts_edges": len(contradicts),
        "run_id": RUN_ID,
    }


# --------------------------------------------------------------------------- #
# Aufgabe 4 & 6 — domain routing / source-gating.
# --------------------------------------------------------------------------- #

# Which source domains are *admissible* evidence for a claim domain. General,
# field-agnostic table; a biomedical database is simply not on the legal list.
_ADMISSIBLE_SOURCE_DOMAINS: dict[Domain, frozenset[Domain]] = {
    Domain.LEGAL_PHILOSOPHY: frozenset({Domain.LEGAL_PHILOSOPHY}),
    Domain.LAW_POSITIVE: frozenset({Domain.LAW_POSITIVE, Domain.LEGAL_PHILOSOPHY}),
    Domain.ECONOMICS: frozenset({Domain.ECONOMICS}),
    Domain.SOCIOLOGY: frozenset({Domain.SOCIOLOGY}),
    Domain.COGNITIVE_SCIENCE: frozenset({Domain.COGNITIVE_SCIENCE}),
    Domain.TECH_HISTORY: frozenset({Domain.TECH_HISTORY}),
    Domain.ML_EPISTEMOLOGY: frozenset({Domain.ML_EPISTEMOLOGY}),
    Domain.EXPERIMENT_META: frozenset({Domain.EXPERIMENT_META}),
}


@dataclass(frozen=True)
class GateResult:
    claim_id: str
    claim_domain: Domain
    source_domain: Domain | None
    provenance_kind: ProvenanceKind
    admissible: bool
    reason: str


def source_domain_gate(claim_id: str) -> GateResult:
    """Gate the evidence actually used for a claim against its domain.

    A source is admissible only if its domain is on the claim domain's allow-list
    AND it is more than semantic-similarity-only. This is the check MarCognity
    lacks: it accepted a PubMed abstract for a legal-philosophy claim.
    """
    cc = C.claims_by_id()[claim_id]
    ev = C.evidence_by_id().get(claim_id)
    if ev is None or ev.source_domain is None:
        return GateResult(claim_id, cc.domain, None, ProvenanceKind.NONE, False,
                          "no concrete source supplied")
    on_list = ev.source_domain in _ADMISSIBLE_SOURCE_DOMAINS.get(cc.domain, frozenset())
    semantic = ev.provenance_kind == ProvenanceKind.SEMANTIC_ONLY
    admissible = on_list and not semantic
    if not on_list:
        reason = (f"source-domain mismatch: {ev.source_domain.value} is not "
                  f"admissible for {cc.domain.value}")
    elif semantic:
        reason = "semantic-similarity only: topical overlap without provenance"
    else:
        reason = "admissible source domain"
    return GateResult(claim_id, cc.domain, ev.source_domain, ev.provenance_kind,
                      admissible, reason)


def source_gate_findings() -> tuple[GateResult, ...]:
    return tuple(source_domain_gate(c.claim_id) for c in C.CLAIMS)


# --------------------------------------------------------------------------- #
# Aufgabe 6 — omission analysis (what the validator never looked at).
# --------------------------------------------------------------------------- #

# The five claim ids the MarCognity report actually examined (all general
# definitional/relational statements — muse:L170-198).
_VALIDATOR_EXAMINED = frozenset({"DEF-01", "DEF-02", "VAL-01"})


def omission_analysis() -> dict:
    """Which claim types the validator examined vs ignored.

    The report touched only a handful of broad definitional claims and ignored
    every direct quote, author attribution, heuristic model, empirical, juristic,
    and normative claim — exactly the claims whose evidence bar is highest.
    """
    examined_types = {c.claim_type.value for c in C.CLAIMS
                      if c.claim_id in _VALIDATOR_EXAMINED}
    ignored = [c for c in C.CLAIMS if c.claim_id not in _VALIDATOR_EXAMINED
               and c.claim_type not in (C.ClaimType.METHODOLOGICAL,
                                        C.ClaimType.CLAIM_ABOUT_VALIDATOR,
                                        C.ClaimType.CLAIM_ABOUT_BOUNDARY)]
    ignored_by_type: dict[str, list[str]] = {}
    for c in ignored:
        ignored_by_type.setdefault(c.claim_type.value, []).append(c.claim_id)
    return {
        "examined_claim_ids": sorted(_VALIDATOR_EXAMINED),
        "examined_types": sorted(examined_types),
        "ignored_content_claims": len(ignored),
        "ignored_by_type": {k: sorted(v) for k, v in sorted(ignored_by_type.items())},
        "note": "Direct quotes and author attributions — the highest-provenance "
                "claim types — were never examined.",
    }


# --------------------------------------------------------------------------- #
# Aufgabe 7 — self-sealing / falsifiability analysis.
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class SelfSealingAnalysis:
    is_self_sealing: bool
    would_support: tuple[str, ...]
    would_weaken: tuple[str, ...]
    would_refute: tuple[str, ...]
    falsifiers_stated_in_experiment: bool
    reason: str

    def to_dict(self) -> dict:
        return {
            "is_self_sealing": self.is_self_sealing,
            "would_support": list(self.would_support),
            "would_weaken": list(self.would_weaken),
            "would_refute": list(self.would_refute),
            "falsifiers_stated_in_experiment": self.falsifiers_stated_in_experiment,
            "reason": self.reason,
        }


def self_sealing_analysis() -> SelfSealingAnalysis:
    """Does every possible validator outcome get read as confirmation?

    The conclusion (muse:L237) reads the validator's *failure* as proof of the
    Epistemic Boundary 'even within the validator itself'. But a successful
    validation would equally have been read as confirmation (the verifiability
    gap made visible). When both outcomes confirm, the hypothesis is unfalsifiable
    as run — and the experiment states no falsification condition.
    """
    return SelfSealingAnalysis(
        is_self_sealing=True,
        would_support=(
            "Validator flags unverifiable claims -> the confidence/verifiability "
            "gap is 'made visible' (the stated goal).",
            "Validator fails / mis-attributes sources -> read as the Boundary "
            "'even within the validator' (muse:L237).",
        ),
        would_weaken=(
            "A pre-registered outcome where the validator, given domain-correct "
            "sources, verifies claims with quoted passages — NOT provided.",
        ),
        would_refute=(
            "A control showing the residual failures vanish under proper "
            "source-gating and provenance (i.e. the failures are a pipeline "
            "defect, not an 'intrinsic architecture' property) — NOT provided.",
        ),
        falsifiers_stated_in_experiment=False,
        reason=(
            "Both a working and a failing validator are interpreted as confirming "
            "the Epistemic Boundary, and no outcome is designated as disconfirming. "
            "As run, the hypothesis is self-sealing. (MarCognity's own Boundary doc "
            "is more careful — doc:epistemic_boundary L119-122 asks for controlled "
            "validation — so the self-sealing is in the forum conclusion, not "
            "necessarily the underlying construct.)"
        ),
    )


# --------------------------------------------------------------------------- #
# Verdict distribution (for the report summary).
# --------------------------------------------------------------------------- #

def verdict_distribution() -> dict[str, int]:
    dist: dict[str, int] = {}
    for c in C.CLAIMS:
        dist[c.verdict.value] = dist.get(c.verdict.value, 0) + 1
    return dict(sorted(dist.items()))


def evidence_strength_distribution() -> dict[str, int]:
    dist: dict[str, int] = {}
    for e in C.EVIDENCE:
        dist[e.strength.value] = dist.get(e.strength.value, 0) + 1
    return dict(sorted(dist.items()))


__all__ = [
    "RUN_ID", "NamedContradiction", "detect_contradictions", "build_claim_graph",
    "graph_summary", "GateResult", "source_domain_gate", "source_gate_findings",
    "omission_analysis", "SelfSealingAnalysis", "self_sealing_analysis",
    "verdict_distribution", "evidence_strength_distribution",
]
