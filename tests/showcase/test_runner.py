"""Tests for the ShowcaseRunner — artefact bundles for S2/S6/S7."""
from __future__ import annotations

import json
import pathlib

import pytest

from desi.showcase import SHOWCASE_IDS, ShowcaseArtifacts, ShowcaseRunner


# ---------------------------------------------------------------------------
# Surface
# ---------------------------------------------------------------------------


def test_showcase_ids_are_exactly_S2_S6_S7() -> None:
    assert SHOWCASE_IDS == ("S2", "S6", "S7")


def test_runner_rejects_scenarios_outside_the_showcase_set(tmp_path) -> None:
    runner = ShowcaseRunner(out_dir=tmp_path)
    with pytest.raises(ValueError):
        runner.run("S1", seed=42)


# ---------------------------------------------------------------------------
# Completeness: every required file is produced per scenario
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("sid", SHOWCASE_IDS)
def test_run_produces_all_required_files(tmp_path, sid: str) -> None:
    runner = ShowcaseRunner(out_dir=tmp_path)
    arts = runner.run(sid, seed=42)
    for p in arts.paths():
        assert p.exists(), f"missing artefact: {p.name}"
        assert p.stat().st_size > 0, f"empty artefact: {p.name}"


def test_run_all_produces_all_three_bundles_plus_baseline(tmp_path) -> None:
    runner = ShowcaseRunner(out_dir=tmp_path)
    artifacts = runner.run_all(seed=42)
    assert set(artifacts.keys()) == set(SHOWCASE_IDS)
    for sid, arts in artifacts.items():
        assert isinstance(arts, ShowcaseArtifacts)
        assert arts.directory == tmp_path / sid
    baseline = tmp_path / "baseline_notes.md"
    assert baseline.exists()
    body = baseline.read_text()
    for sid in SHOWCASE_IDS:
        assert sid in body
        assert "Klassischer LLM-Pfad" in body
        assert "DESi-Pfad" in body


# ---------------------------------------------------------------------------
# Artefact content
# ---------------------------------------------------------------------------


def test_summary_json_carries_full_audit(tmp_path) -> None:
    runner = ShowcaseRunner(out_dir=tmp_path)
    arts = runner.run("S2", seed=11)
    payload = json.loads(arts.summary_json.read_text())
    assert payload["scenario_id"] == "S2"
    assert payload["seed"] == 11
    assert payload["passed"] is True
    assert payload["evaluation_id"].startswith("eval_")
    assert payload["counts"]["timeline_events"] > 0
    assert payload["counts"]["snapshots"] >= 2


def test_timeline_md_is_a_markdown_table(tmp_path) -> None:
    runner = ShowcaseRunner(out_dir=tmp_path)
    arts = runner.run("S2", seed=42)
    md = arts.timeline_md.read_text()
    # Header + separator + at least one data row.
    rows = [line for line in md.splitlines() if line.startswith("|")]
    assert len(rows) > 2
    assert "tick" in rows[0]
    assert "event_type" in rows[0]
    assert "run_started" in md
    assert "run_ended" in md


def test_snapshot_files_are_parseable_json(tmp_path) -> None:
    runner = ShowcaseRunner(out_dir=tmp_path)
    arts = runner.run("S6", seed=42)
    start = json.loads(arts.snapshot_start_json.read_text())
    end = json.loads(arts.snapshot_end_json.read_text())
    assert start["label"] == "start"
    assert end["label"] == "end"
    # The end snapshot for S6 has 2 claims and no MERGED_INTO.
    assert end["counts"]["claims"] == 2
    rel_types = {r["rel_type"] for r in end["relations"]}
    assert "MERGED_INTO" not in rel_types


def test_end_cypher_uses_merge_only(tmp_path) -> None:
    runner = ShowcaseRunner(out_dir=tmp_path)
    arts = runner.run("S7", seed=42)
    cy = arts.snapshot_end_cypher.read_text()
    statement_lines = [
        l for l in cy.splitlines()
        if l and not l.startswith("//")
    ]
    assert statement_lines, "expected at least one Cypher statement"
    assert all("MERGE" in l for l in statement_lines), \
        "every Cypher statement in the snapshot export must be a MERGE"


# ---------------------------------------------------------------------------
# Analysis.md structure
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("sid", SHOWCASE_IDS)
def test_analysis_md_has_all_four_required_sections(tmp_path, sid: str) -> None:
    runner = ShowcaseRunner(out_dir=tmp_path)
    arts = runner.run(sid, seed=42)
    body = arts.analysis_md.read_text()
    # Required section headings, in order.
    for heading in ("## Problem",
                    "## DESi Verhalten",
                    "## Endzustand",
                    "## Warum relevant?"):
        assert heading in body, f"{sid} missing section: {heading}"


def test_s2_analysis_records_contradictions(tmp_path) -> None:
    runner = ShowcaseRunner(out_dir=tmp_path)
    arts = runner.run("S2", seed=42)
    body = arts.analysis_md.read_text()
    assert "`CONTRADICTS`" in body
    assert "C001" in body and "C002" in body and "C003" in body


def test_s6_analysis_records_guard_block(tmp_path) -> None:
    runner = ShowcaseRunner(out_dir=tmp_path)
    arts = runner.run("S6", seed=42)
    body = arts.analysis_md.read_text()
    assert "Guard blocked" in body
    assert "merge_claims" in body
    assert "surface_similarity_only" in body


def test_s7_analysis_keeps_legacy_and_new_claim_visible(tmp_path) -> None:
    runner = ShowcaseRunner(out_dir=tmp_path)
    arts = runner.run("S7", seed=42)
    body = arts.analysis_md.read_text()
    assert "C_legacy_old" in body
    assert "C_legacy" in body
    assert "hearsay" in body
    assert "T6" in body


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


def _strip_volatile(payload: dict) -> dict:
    """Drop fields that vary between runs (timestamps, uuid-derived ids)."""
    if isinstance(payload, dict):
        out = {}
        for k, v in payload.items():
            if k in {"timestamp", "evaluation_id", "ts",
                     "created_at", "started_at", "finished_at",
                     "prov_timestamp", "event_id", "run_id",
                     "prov_run_id"}:
                continue
            out[k] = _strip_volatile(v)
        return out
    if isinstance(payload, list):
        return [_strip_volatile(x) for x in payload]
    return payload


@pytest.mark.parametrize("sid", SHOWCASE_IDS)
def test_same_seed_produces_structurally_identical_artifacts(
    tmp_path, sid: str,
) -> None:
    a_dir = tmp_path / "a"
    b_dir = tmp_path / "b"
    a = ShowcaseRunner(out_dir=a_dir).run(sid, seed=99)
    b = ShowcaseRunner(out_dir=b_dir).run(sid, seed=99)
    # Timeline.md must be byte-identical (no wall-clock fields).
    assert a.timeline_md.read_text() == b.timeline_md.read_text()
    # Snapshots compare equal once volatile fields are stripped.
    for path_a, path_b in [
        (a.snapshot_start_json, b.snapshot_start_json),
        (a.snapshot_end_json,   b.snapshot_end_json),
    ]:
        pa = _strip_volatile(json.loads(path_a.read_text()))
        pb = _strip_volatile(json.loads(path_b.read_text()))
        assert pa == pb, f"snapshot differs for {sid}"
    # Summary compares equal once timestamp / evaluation_id are stripped.
    sa = _strip_volatile(json.loads(a.summary_json.read_text()))
    sb = _strip_volatile(json.loads(b.summary_json.read_text()))
    assert sa == sb


def test_baseline_notes_is_deterministic_between_runs(tmp_path) -> None:
    a = tmp_path / "a"
    b = tmp_path / "b"
    ShowcaseRunner(out_dir=a).run_all(seed=7)
    ShowcaseRunner(out_dir=b).run_all(seed=7)
    # baseline_notes.md derives from hand-written descriptions only.
    assert (a / "baseline_notes.md").read_text() \
        == (b / "baseline_notes.md").read_text()
