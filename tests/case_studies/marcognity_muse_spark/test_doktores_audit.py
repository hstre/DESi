"""Tests for the adversarial Doktores audit.

Covers the ten required properties: the audit does not auto-reject DESi, dissent
is preserved, C1 can stand as a real contradiction, C2/C3 can be reclassified, the
curated selection is not sold as full coverage, the attestation carries no blanket
truth-seal, every doctor verdict is anchored (or marks the absence), the report is
changed only via documented audit decisions, and a failed audit never reports as a
successful confirmation.
"""
from __future__ import annotations

from pathlib import Path

from desi.case_studies.marcognity_muse_spark.doktores import __main__ as cli
from desi.case_studies.marcognity_muse_spark.doktores import engine, reviews
from desi.case_studies.marcognity_muse_spark.doktores.models import (
    Consensus,
    ContradictionClass,
)


def _reviews():
    return engine.build_claim_reviews()


# 1. Doktores does not auto-reject every DESi finding.
def test_audit_does_not_auto_reject_desi():
    reviews_ = _reviews()
    consensuses = [r.consensus for r in reviews_]
    assert Consensus.UPHOLD in consensuses
    # a majority survive (uphold or uphold_with_qualification), none rejected here
    survived = sum(1 for c in consensuses
                   if c in (Consensus.UPHOLD, Consensus.UPHOLD_WITH_QUALIFICATION))
    assert survived == len(reviews_)
    assert all(c != Consensus.REJECT for c in consensuses)


# 2. Dissent is preserved in the output.
def test_dissent_is_preserved():
    with_dissent = [r for r in _reviews() if r.dissent]
    assert with_dissent, "expected at least one preserved claim-level dissent"
    assert engine.render_dissent_md().strip()
    # C1 carries a minority opinion that must survive to the output
    c1 = next(c for c in reviews.CONTRADICTION_REVIEWS if c.cid == "C1")
    assert c1.minority_opinion


# 3. C1 can stand as a real logical contradiction.
def test_c1_upheld_as_logical_contradiction():
    c1 = next(c for c in reviews.CONTRADICTION_REVIEWS if c.cid == "C1")
    assert c1.upheld is True
    assert c1.reviewed_classification == ContradictionClass.LOGICAL_CONTRADICTION


# 4. C2 can be reclassified to a pipeline inconsistency.
def test_c2_reclassified_pipeline_inconsistency():
    c2 = next(c for c in reviews.CONTRADICTION_REVIEWS if c.cid == "C2")
    assert c2.upheld is False
    assert c2.reviewed_classification == ContradictionClass.PIPELINE_INCONSISTENCY


# 5. C3 can be reclassified to an unsubstantiated independence claim.
def test_c3_reclassified_unsubstantiated_independence():
    c3 = next(c for c in reviews.CONTRADICTION_REVIEWS if c.cid == "C3")
    assert c3.upheld is False
    assert c3.reviewed_classification == ContradictionClass.UNSUBSTANTIATED_CLAIM


# 6. The curated selection is not presented as complete coverage.
def test_curated_not_presented_as_full_coverage():
    summ = engine.audit_summary()
    # attestation flags claim coverage as only passed_with_qualifications, not passed
    assert summ["attestation"]["Claim-Abdeckung"] == "passed_with_qualifications"
    text = engine.render_audit_report_md() + engine.render_attestation_md()
    assert "kuratiert" in text.lower() and "nicht gemessen" in text.lower()


# 7. The attestation carries no blanket truth-seal.
def test_attestation_has_no_blanket_truth_seal():
    att = engine.render_attestation_md()
    assert "bestätigt NICHT die Wahrheit" in att
    assert engine.OVERALL_ATTESTATION.value == "passed_with_qualifications"
    # not a bare "passed"
    assert engine.OVERALL_ATTESTATION.value != "passed"


# 8. Every doctor verdict is anchored (or the absence is marked).
def test_every_doctor_verdict_is_anchored():
    for _cid, verdicts, *_ in reviews.CLAIM_VERDICTS:
        for v in verdicts:
            assert v.source_anchors, f"unanchored verdict by {v.role} on {_cid}"
    for c in reviews.CONTRADICTION_REVIEWS:
        assert c.source_anchors


# 9. The main report is changed only via documented audit decisions.
def test_revisions_are_documented_and_traceable():
    for r in reviews.REVISIONS:
        assert r.target_files and r.audit_finding and r.reason
        assert r.before and r.after
    # C1's report_change_required maps to a logged revision (R1)
    c1 = next(c for c in reviews.CONTRADICTION_REVIEWS if c.cid == "C1")
    assert c1.report_change_required is True
    assert any(rv.rid == "R1" for rv in reviews.REVISIONS)
    # C2/C3 already reflected -> no fresh report change required
    for cid in ("C2", "C3"):
        c = next(x for x in reviews.CONTRADICTION_REVIEWS if x.cid == cid)
        assert c.report_change_required is False


# 10. A failed audit is never reported as a successful confirmation.
def test_failed_audit_returns_nonzero(monkeypatch, tmp_path):
    good = engine.audit_summary()

    def _failed():
        d = dict(good)
        d["overall_attestation"] = "needs_revision"
        return d

    monkeypatch.setattr(engine, "audit_summary", _failed)
    monkeypatch.setattr(cli.engine, "audit_summary", _failed)
    rc = cli.main(["--out-dir", str(tmp_path)])
    assert rc == 1


def test_passing_audit_returns_zero(tmp_path):
    assert cli.main(["--out-dir", str(tmp_path)]) == 0


# reproducibility
def test_audit_is_deterministic(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    engine.write_all(a)
    engine.write_all(b)
    for name in ("claim_reviews.jsonl", "contradiction_reviews.jsonl",
                 "AUDIT_REPORT.md", "ATTESTATION.md", "audit_summary.json",
                 "dissent.md", "REVISION_LOG.md"):
        assert (a / name).read_bytes() == (b / name).read_bytes()


def test_provenance_manifest_records_missing_sources():
    prov = engine.provenance_manifest()
    assert prov["models_used"] == "none"
    assert prov["sources_not_refetched"]
    assert any("PubMed" in s for s in prov["sources_not_refetched"])
    assert Path(engine.CS_DIR / "claims.jsonl").exists()  # a hashed input exists
