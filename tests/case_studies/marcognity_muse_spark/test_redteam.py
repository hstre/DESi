"""Tests for the background-reviewer red-team benchmark."""
from __future__ import annotations

import json
from pathlib import Path

from desi.case_studies.marcognity_muse_spark.redteam import __main__ as cli
from desi.case_studies.marcognity_muse_spark.redteam import bench
from desi.case_studies.marcognity_muse_spark.redteam.failure_modes import PROBES, Flag
from desi.case_studies.marcognity_muse_spark.redteam.reviewers import (
    DesiReviewer,
    ExternalReviewer,
    NaiveWholeTextReviewer,
)


def test_five_failure_modes_each_anchored():
    assert len(PROBES) == 5
    assert {p.failure_mode for p in PROBES} == set(Flag)
    for p in PROBES:
        assert p.source_anchor and p.claim_ids  # every probe traces to the material
        assert p.must_flag == p.failure_mode


def test_desi_reference_catches_all_five():
    s = bench.score(DesiReviewer())
    assert s["caught"] == 5 and s["total"] == 5
    assert all(s["per_mode"].values())


def test_naive_whole_text_catches_none_so_benchmark_discriminates():
    s = bench.score(NaiveWholeTextReviewer())
    assert s["caught"] == 0
    card = bench.scorecard()
    assert card["discriminating"] is True


def test_scorecard_and_report_are_honest_about_reference_by_construction():
    card = bench.scorecard()
    assert "per Konstruktion" in card["note"]
    report = bench.render_report_md()
    assert "Referenz" in report and "kein unabhängiger" in report
    assert "Claude Science" in report


def test_external_reviewer_scored_from_json(tmp_path: Path):
    payload = {"name": "probe-reviewer",
               "flags": {"P2-domain": ["source_domain_mismatch"],
                         "P4-overclaim": ["overclaim"]}}
    p = tmp_path / "ext.json"
    p.write_text(json.dumps(payload), encoding="utf-8")
    ext = ExternalReviewer.from_json(p)
    s = bench.score(ext)
    assert s["caught"] == 2                       # only the two provided modes
    assert s["per_mode"]["source_domain_mismatch"] is True
    assert s["per_mode"]["overclaim"] is True
    assert s["per_mode"]["self_sealing"] is False


def test_external_reviewer_ignores_unknown_flags(tmp_path: Path):
    p = tmp_path / "ext.json"
    p.write_text(json.dumps({"name": "x", "flags": {"P1-untraceable": ["not_a_real_flag"]}}),
                 encoding="utf-8")
    ext = ExternalReviewer.from_json(p)
    assert bench.score(ext)["caught"] == 0        # unknown flag ≠ a catch


def test_cli_writes_artifacts_and_self_checks(tmp_path: Path):
    rc = cli.main(["--out-dir", str(tmp_path)])
    assert rc == 0                                 # reference passes its 5/5 self-check
    for name in ("REDTEAM.md", "redteam_results.jsonl", "redteam_scorecard.json"):
        assert (tmp_path / name).exists()


def test_results_jsonl_is_line_auditable(tmp_path: Path):
    bench.write_results_jsonl(tmp_path / "r.jsonl")
    lines = (tmp_path / "r.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2 * len(PROBES)           # 2 default reviewers × 5 probes
    for ln in lines:
        rec = json.loads(ln)
        assert rec["reviewer"] and rec["probe_key"] and "caught" in rec


def test_deterministic(tmp_path: Path):
    a, b = tmp_path / "a", tmp_path / "b"
    bench.write_all(a)
    bench.write_all(b)
    for name in ("REDTEAM.md", "redteam_results.jsonl", "redteam_scorecard.json"):
        assert (a / name).read_bytes() == (b / name).read_bytes()
