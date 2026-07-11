"""Tests for the MarCognity / Muse Spark 1.1 case study.

Covers the five findings the case study is required to demonstrate (Aufgabe 7):
the prompt/method contradiction, the PubMed<->legal-philosophy source-domain
mismatch, empirical-vs-heuristic separation, missing concrete evidence passages,
and the self-sealing conclusion — plus reproducibility and reuse checks.
"""
from __future__ import annotations

import json
from pathlib import Path

from desi.case_studies.marcognity_muse_spark import analysis, claims, report
from desi.case_studies.marcognity_muse_spark.claims import (
    ClaimType,
    ProvenanceKind,
    Verdict,
)


# 1. The prompt/method contradiction is surfaced by DESi's OWN detector.
def test_prompt_method_contradiction_detected():
    cons = {nc.cid: nc for nc in analysis.detect_contradictions()}
    assert "C1" in cons
    c1 = cons["C1"].contradiction
    assert c1.scope == "document:muse"
    # two conflicting values for the same key, found by find_contradictions
    assert len(c1.values) == 2
    joined = " ".join(c1.values)
    assert "none" in joined and "required" in joined


def test_all_three_structural_contradictions_present():
    cids = {nc.cid for nc in analysis.detect_contradictions()}
    assert cids == {"C1", "C2", "C3"}


# 2. PubMed vs legal-philosophy is caught as a source-domain mismatch.
def test_source_domain_mismatch_pubmed_vs_legal_philosophy():
    gate = analysis.source_domain_gate("VAL-01")
    assert gate.admissible is False
    assert "mismatch" in gate.reason or "semantic" in gate.reason
    # and the claim's verdict names it explicitly
    val01 = claims.claims_by_id()["VAL-01"]
    assert val01.verdict == Verdict.SOURCE_DOMAIN_MISMATCH


def test_no_content_claim_is_verified_on_a_pubmed_hit():
    # nothing legal is marked plainly SUPPORTED via a biomedical source
    for gate in analysis.source_gate_findings():
        cc = claims.claims_by_id()[gate.claim_id]
        if gate.source_domain is not None and gate.source_domain.value == "cognitive_science":
            assert cc.verdict != Verdict.SUPPORTED


# 3. The formulas are heuristic proposals, not empirical/verified.
def test_formulas_are_heuristic_not_empirical():
    for cid in ("HEUR-01", "HEUR-02", "HEUR-03"):
        cc = claims.claims_by_id()[cid]
        assert cc.claim_type == ClaimType.HEURISTIC_MODEL
        assert cc.verdict == Verdict.HEURISTIC_PROPOSAL
        # explicitly NOT classified true/false
        assert cc.verdict not in (Verdict.SUPPORTED, Verdict.CONTRADICTED,
                                  Verdict.UNSUPPORTED)


def test_verdicts_are_not_binary_verified_failure():
    used = {c.verdict for c in claims.CLAIMS}
    # more than two verdict kinds are actually exercised
    assert len(used) >= 6
    assert Verdict.HEURISTIC_PROPOSAL in used
    assert Verdict.NORMATIVE_CLAIM in used
    assert Verdict.UNVERIFIABLE in used


# 4. Claims the validator "verified" have no concrete evidence passage.
def test_missing_concrete_evidence_passages():
    ev = claims.evidence_by_id()
    # VAL-01: the five 'VERIFIED' legal claims rested on no concrete passage
    assert ev["VAL-01"].concrete_passage == ""
    assert ev["VAL-01"].provenance_kind in (ProvenanceKind.NONE,
                                            ProvenanceKind.SEMANTIC_ONLY)
    # every direct quote / author attribution lacks a located passage
    for cid in ("QUOTE-01", "QUOTE-02", "ATTR-01", "ATTR-02"):
        assert ev[cid].concrete_passage == ""
        assert ev[cid].provenance_kind == ProvenanceKind.NONE


def test_omission_analysis_flags_ignored_highvalue_claims():
    om = analysis.omission_analysis()
    assert "direct_quote" in om["ignored_by_type"]
    assert "author_attribution" in om["ignored_by_type"]
    assert om["ignored_content_claims"] >= 10


# 5. The conclusion is self-sealing and states no falsifier.
def test_self_sealing_conclusion():
    ss = analysis.self_sealing_analysis()
    assert ss.is_self_sealing is True
    assert ss.falsifiers_stated_in_experiment is False
    assert ss.would_support and ss.would_refute


# -- reuse + reproducibility ------------------------------------------------ #

def test_claim_graph_reuses_memory_layer_with_contradicts_edges():
    from desi.memory.relations import RelationType
    from desi.memory.store import InMemoryStore

    store = analysis.build_claim_graph()
    assert isinstance(store, InMemoryStore)
    edges = [
        r for c in store.all_claims()
        for r in store.relations_for(c.claim_id, rel_type=RelationType.CONTRADICTS)
    ]
    assert len(edges) == 3  # C1, C2, C3


def test_every_claim_has_a_source_anchor_and_rationale():
    for c in claims.CLAIMS:
        assert c.source.doc and c.source.locator
        assert c.rationale.strip()
        # every claim id has an evidence record
        assert c.claim_id in claims.evidence_by_id()


def test_reproduction_is_deterministic(tmp_path: Path):
    a = tmp_path / "a"
    b = tmp_path / "b"
    report.write_all(a)
    report.write_all(b)
    for name in ("claims.jsonl", "evidence.jsonl", "contradictions.md",
                 "comparison.md", "summary.json"):
        assert (a / name).read_bytes() == (b / name).read_bytes()


def test_claims_jsonl_is_line_auditable(tmp_path: Path):
    report.write_claims_jsonl(tmp_path / "claims.jsonl")
    lines = (tmp_path / "claims.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == len(claims.CLAIMS)
    for ln in lines:
        rec = json.loads(ln)  # each line parses standalone
        assert rec["claim_id"] and rec["source"] and rec["verdict"]
