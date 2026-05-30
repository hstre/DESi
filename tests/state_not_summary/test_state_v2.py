"""Tests for the DESi-state (not summary) Prototype 2 — deterministic, offline."""
from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "state_not_summary"))
sys.path.insert(0, str(_REPO / "claude_compression"))   # for the shared token_count

import evaluate_v2 as ev  # noqa: E402
import extractor_v2 as ext  # noqa: E402
import rehydrate_v2 as rh  # noqa: E402
import state_v2 as st  # noqa: E402

_FX = _REPO / "state_not_summary" / "fixtures_v2"


def test_empty_state_is_clean_and_under_budget():
    s = st.DesiStateV2()
    assert s.fits_budget()
    assert s.validate_no_prose() == []


def test_state_rejects_prose_in_bodies():
    """A body longer than the structural cap is FLAGGED — schema must catch leaked narrative."""
    s = st.DesiStateV2(decisions=[st.Decision(id="D1",
        body="This is a long narrative sentence with many words that clearly exceeds the budget and is therefore prose, not state.")])
    viols = s.validate_no_prose()
    assert any("prose risk" in v for v in viols)


def test_state_rejects_chat_markers():
    s = st.DesiStateV2(active_claims=[st.Claim(id="C1", body="as we discussed earlier")])
    assert any("chat marker" in v for v in s.validate_no_prose())


def test_extractor_emits_only_marked_entries():
    """Anything outside [MARKER ...] is ignored; the extractor never summarizes the chat."""
    chat = [
        {"role": "user", "content": "We talked about the weather, lunch, fonts."},
        {"role": "user", "content": "[CLAIM C1 evidence=likely] dual-layer preserves anchors"},
        {"role": "user", "content": "another sentence with no markers at all"},
    ]
    s = ext.extract_state(chat)
    assert [c.id for c in s.active_claims] == ["C1"]
    # nothing else was emitted as an entry
    assert s.active_constraints == [] and s.decisions == [] and s.open_conflicts == []
    # no leakage of off-topic words anywhere in the serialized state
    blob = s.serialize().lower()
    for w in ("weather", "lunch", "fonts"):
        assert w not in blob


def test_replaced_decision_is_dropped():
    chat = [
        {"role": "user", "content": "[DECISION D1 since=t1] use Jaccard at 0.6"},
        {"role": "user", "content": "[DECISION D2 since=t2 replaces=D1] use neighbour fingerprints"},
    ]
    s = ext.extract_state(chat)
    ids = [d.id for d in s.decisions]
    assert "D2" in ids and "D1" not in ids


def test_resolved_conflict_is_dropped():
    chat = [{"role": "user", "content": "[CONFLICT K1 claims=C1,C2 status=resolved]"}]
    s = ext.extract_state(chat)
    assert s.open_conflicts == []


def test_round_trip_through_rehydration():
    chat = json.loads((_FX / "chat_compression_pipeline.json").read_text())["chat"]
    s = ext.extract_state(chat)
    block = rh.render(s)
    parsed = rh.parse(block)
    assert parsed.to_dict() == s.to_dict()


def test_evaluator_uses_independent_ground_truth_files():
    """The evaluator must open the ground-truth file directly, not derive it from the extractor."""
    gt_path = _FX / "groundtruth_compression_pipeline.json"
    assert gt_path.exists() and "frozen" in gt_path.read_text()
    r = ev.evaluate_fixture("compression_pipeline")
    # the recall is computed against the file's expected IDs, which the extractor never reads
    assert r["claims"]["total"] == 2 and "C1" in r["claims"]["matched"] and "C2" in r["claims"]["matched"]


def test_workability_is_explicitly_untested():
    r = ev.evaluate_fixture("compression_pipeline")
    assert r["success"]["claude_workable_in_new_chat"] == "UNTESTED_in_this_env"


def test_no_narrative_leakage_on_clean_fixtures():
    for fid in ("compression_pipeline", "governance", "long_session"):
        r = ev.evaluate_fixture(fid)
        assert r["narrative_leakage_terms"] == []
        assert r["schema_violations"] == []


def test_extractor_is_deterministic():
    chat = json.loads((_FX / "chat_long_session.json").read_text())["chat"]
    a = ext.extract_state(chat).to_dict()
    b = ext.extract_state(chat).to_dict()
    assert a == b


def test_known_extractor_limitation_d2_governance_is_documented():
    """Documents the honest miss: governance.D2 uses 'replaces=' with empty value, which is
    malformed marker syntax and is NOT matched. This test pins the current behavior so any
    later 'fix' must be intentional, not a silent retrofit to make the report look better."""
    r = ev.evaluate_fixture("governance")
    assert "D2" in r["decisions"]["missing"]
    # claims/constraints/conflicts still perfect — the miss is isolated
    assert r["claims"]["recall_exact"] == 1.0
    assert r["constraints"]["recall_exact"] == 1.0
    assert r["conflicts"]["recall_exact"] == 1.0


def test_long_session_overshoots_budget_documented():
    """Documents the honest budget overshoot on a marker-dense long session. Pinning this so
    nobody silently trims items just to make 'fits 500' green."""
    r = ev.evaluate_fixture("long_session")
    assert r["state_tokens"] > 500
    assert r["fits_500_budget"] is False
    # but recall on every brief category still passes
    for cat in ("claims", "constraints", "decisions", "conflicts"):
        assert r[cat]["recall_exact"] == 1.0
