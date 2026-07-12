"""Tests for the background-reviewer red-team HARNESS.

Covers catch, false positives (over-flagging), clean controls, stability across
repeated runs, the external slot, determinism, and the honest 'harness not result'
framing.
"""
from __future__ import annotations

import json
from pathlib import Path

from desi.case_studies.marcognity_muse_spark.redteam import __main__ as cli
from desi.case_studies.marcognity_muse_spark.redteam import bench
from desi.case_studies.marcognity_muse_spark.redteam.failure_modes import (
    CONTROL_PROBES,
    FAILURE_PROBES,
    PROBES,
    Flag,
)
from desi.case_studies.marcognity_muse_spark.redteam.reviewers import (
    DesiReviewer,
    ExternalReviewer,
    NaiveWholeTextReviewer,
)


def test_five_failure_modes_and_two_controls():
    assert len(FAILURE_PROBES) == 5 and len(CONTROL_PROBES) == 2
    assert {p.must_flag for p in FAILURE_PROBES} == set(Flag)
    for p in FAILURE_PROBES:
        assert p.source_anchor and p.claim_ids and p.must_flag in p.applicable_flags
    for p in CONTROL_PROBES:
        assert p.must_flag is None and p.applicable_flags == frozenset()


def test_desi_reference_catches_all_with_zero_false_positives():
    s = bench.score(DesiReviewer())
    assert s["caught"] == 5 and s["positives"] == 5
    assert s["false_positives"] == 0                 # the reference does not over-flag
    assert s["controls_clean"] == 2                  # and stays quiet on clean controls
    assert s["stability"] == 1.0


def test_naive_baseline_catches_none_but_benchmark_discriminates():
    s = bench.score(NaiveWholeTextReviewer())
    assert s["caught"] == 0 and s["false_positives"] == 0 and s["controls_clean"] == 2
    assert bench.scorecard()["discriminating"] is True


def test_false_positives_and_controls_are_measured(tmp_path: Path):
    # a trigger-happy reviewer: wrong flag on a failure probe + a flag on a clean control
    payload = {"name": "trigger-happy",
               "flags": {"P1-untraceable": ["self_sealing"],
                         "C1-clean-citation": ["untraceable_citation"]}}
    p = tmp_path / "th.json"
    p.write_text(json.dumps(payload), encoding="utf-8")
    s = bench.score(ExternalReviewer.from_json(p))
    assert s["caught"] == 0                           # never raised a correct target flag
    assert s["false_positives"] == 2                  # self_sealing on P1 + flag on C1
    assert s["controls_clean"] == 1                   # C1 no longer clean, C2 still clean


def test_external_runs_give_stability(tmp_path: Path):
    payload = {"name": "flaky",
               "runs": [{"P2-domain": ["source_domain_mismatch"], "P4-overclaim": ["overclaim"]},
                        {"P2-domain": ["source_domain_mismatch"]}]}
    p = tmp_path / "flaky.json"
    p.write_text(json.dumps(payload), encoding="utf-8")
    s = bench.score(ExternalReviewer.from_json(p))
    assert s["runs"] == 2
    assert s["caught"] == 2                           # representative run catches P2 and P4
    # P2 caught 2/2, P4 caught 1/2, others 0 → mean = 0.3
    assert s["stability"] == 0.3


def test_external_reviewer_ignores_unknown_flags(tmp_path: Path):
    p = tmp_path / "x.json"
    p.write_text(json.dumps({"name": "x", "flags": {"P1-untraceable": ["not_a_flag"]}}),
                 encoding="utf-8")
    s = bench.score(ExternalReviewer.from_json(p))
    assert s["caught"] == 0 and s["false_positives"] == 0


def test_report_is_honest_harness_not_result():
    report = bench.render_report_md()
    assert "HARNESS" in report or "Harness" in report
    assert "kein Ergebnis" in report
    assert "Claude Science" in report
    assert "Referenz" in report and "per Konstruktion" in report
    assert "Architektur-Effizienz" in report          # the durable framing
    assert "external" in report.lower()               # the slot to fill


def test_cli_self_checks_reference_and_writes(tmp_path: Path):
    rc = cli.main(["--out-dir", str(tmp_path)])
    assert rc == 0                                     # reference: 5/5 catch, 0 FP
    for name in ("REDTEAM.md", "redteam_results.jsonl", "redteam_scorecard.json"):
        assert (tmp_path / name).exists()


def test_results_jsonl_line_auditable(tmp_path: Path):
    bench.write_results_jsonl(tmp_path / "r.jsonl")
    lines = (tmp_path / "r.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2 * len(PROBES)               # 2 default reviewers × 7 probes
    for ln in lines:
        rec = json.loads(ln)
        assert rec["reviewer"] and rec["probe_key"] and "false_positives" in rec


def test_deterministic(tmp_path: Path):
    a, b = tmp_path / "a", tmp_path / "b"
    bench.write_all(a)
    bench.write_all(b)
    for name in ("REDTEAM.md", "redteam_results.jsonl", "redteam_scorecard.json"):
        assert (a / name).read_bytes() == (b / name).read_bytes()
