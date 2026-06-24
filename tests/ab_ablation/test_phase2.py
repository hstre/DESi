"""Phase-2 ablation regression: F/G/H distinctness, retrieval baselines, confidence_while_wrong,
multi-turn persistence wiring, and that the run emits all 11 conditions."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "ab_evidence"))

import ablation_run2 as r2  # noqa: E402
from ablation_conditions import build_condition, contradict_state  # noqa: E402
from build_state import state_for_variant_B  # noqa: E402
from degeneration import confidence_while_wrong  # noqa: E402
from retrieval import RETRIEVAL, build_retrieval  # noqa: E402

CASE = "case1_architecture"


def _user(payload):
    return payload["messages"][0]["content"]


def test_F_is_empty_state():
    p = build_condition(CASE, "F_empty_state")
    assert "DESi state" not in _user(p) and "Notes" not in _user(p)
    assert p["input_token_estimate"] < build_condition(CASE, "B_normal_desi")["input_token_estimate"]


def test_G_neutral_irrelevant_not_contradictory_and_budget_matched():
    b = build_condition(CASE, "B_normal_desi")["input_token_estimate"]
    g = build_condition(CASE, "G_neutral_irrelevant")
    u = _user(g).lower()
    assert "tenant" not in u and "schema" not in u          # no target leak
    assert "garden" in u or "tomatoes" in u or "compost" in u   # genuinely different domain
    assert abs(g["input_token_estimate"] - b) / b <= 0.10      # ≈ B budget


def test_H_contradicts_target_same_topic():
    h = build_condition(CASE, "H_contradiction_wrong")
    u = _user(h).lower()
    assert "tenant" in u                                       # keeps the target's topic
    assert "against" in u or "false" in u or "lifted" in u or "opposite" in u  # contradicts stance
    # contradiction is a deterministic transform of the case's own state
    cont = contradict_state(state_for_variant_B(CASE))
    assert cont["decisions"][0]["what"].startswith("decided AGAINST:")


def test_CGH_are_distinct():
    c = _user(build_condition(CASE, "C_wrong_slice"))
    g = _user(build_condition(CASE, "G_neutral_irrelevant"))
    h = _user(build_condition(CASE, "H_contradiction_wrong"))
    assert c != g != h and c != h
    assert "tomatoes" in g.lower() and "tomatoes" not in c.lower() and "tomatoes" not in h.lower()


def test_retrieval_budget_and_no_governance_metadata():
    b = build_condition(CASE, "B_normal_desi")["input_token_estimate"]
    for m in RETRIEVAL:
        p = build_retrieval(CASE, m, target_tokens=b)
        assert p["input_token_estimate"] <= b                  # packed to (not over) B's budget
        assert p["input_token_estimate"] / b >= 0.7            # but uses most of it
        u = _user(p)
        for token in ('"active_claims"', '"id"', '"what"'):    # no DESi governance metadata
            assert token not in u
        assert "Retrieved excerpts" in u


def test_confidence_while_wrong():
    assert confidence_while_wrong(90, 0.2)["confident_while_wrong"] is True
    assert confidence_while_wrong(90, 0.9)["confident_while_wrong"] is False
    assert confidence_while_wrong(40, 0.2)["confident_while_wrong"] is False
    assert confidence_while_wrong(None, 0.2)["confident_while_wrong"] is False


def test_strip_confidence_line():
    clean, conf = r2._strip_conf("- a\n- b\nCONFIDENCE: 75")
    assert conf == 75.0 and "CONFIDENCE" not in clean and "- a" in clean


def test_lifecycle_cases_build_and_set_the_supersession_trap():
    # The new discriminative cases: the chat contains superseded/ruled-out content that retrieval
    # surfaces, while the curated DESi slice (B) holds only the live state.
    for case, stale in (("case_s1_lifecycle", ("leak",)), ("case_s2_lifecycle", ("forever",))):
        b = build_condition(case, "B_normal_desi")
        assert b["input_token_estimate"] > 0
        r1 = build_retrieval(case, "R1_bm25", target_tokens=b["input_token_estimate"])
        r1_text = r1["messages"][0]["content"].lower()
        assert any(s in r1_text for s in stale)              # retrieval surfaces the stale content
        assert all(s not in b["messages"][0]["content"].lower() for s in stale)  # B excludes it


def test_auto_state_parse_normalises_to_categories():
    import auto_state
    raw = ('here is the state {"decisions": [{"id": "D1", "what": "use streaming"}], '
           '"active_claims": ["schema drift is real"], "open_questions": []} done')
    st = auto_state._parse(raw)
    assert set(st) == {"active_claims", "active_constraints", "decisions", "open_conflicts",
                       "open_questions"}
    assert st["decisions"][0]["what"] == "use streaming"
    assert st["active_claims"][0]["what"] == "schema drift is real"   # bare string normalised
    assert st["active_constraints"] == [] and st["open_questions"] == []
    assert auto_state._parse("no json here") == {k: [] for k in st}    # malformed -> empty, not crash


def test_b_payload_from_state_is_b_styled():
    from ablation_conditions import b_payload_from_state
    state = {"decisions": [{"id": "D1", "what": "use the vault"}], "active_claims": [],
             "active_constraints": [], "open_conflicts": [], "open_questions": []}
    p = b_payload_from_state(CASE, state)
    assert p["condition"] == "B_auto_constructed" and p["slice_source"] == "auto_extracted"
    assert "use the vault" in p["messages"][0]["content"] and p["input_token_estimate"] > 0


def test_neural_retriever_when_available():
    import retrieval
    if not retrieval.neural_available():
        import pytest
        pytest.skip("no neural embedder installed")
    b = build_condition(CASE, "B_normal_desi")["input_token_estimate"]
    p = build_retrieval(CASE, "R2n_neural", target_tokens=b)
    assert p["input_token_estimate"] <= b and "Retrieved excerpts" in p["messages"][0]["content"]


def test_run_emits_all_conditions_and_persistence_with_stub():
    def stub(system, messages):
        # echoes a fixed answer + a confidence line; deterministic
        return {"text": "- open conflict: a vs b\n- none\nCONFIDENCE: 80"}

    out = r2.run((CASE,), responder=stub, reps=2, tag="selftest")
    assert out["backend_status"] == "STUB_TEST"
    conds = out["cases"][0]["conditions"]
    assert set(conds) == set(r2.ALL_CONDITIONS) and len(r2.ALL_CONDITIONS) == 11
    for c in r2.ALL_CONDITIONS:
        assert "recall" in conds[c] and "degeneration" in conds[c]
    # persistence ran for C and H (2 conditions × 1 case)
    assert {p["condition"] for p in out["persistence"]} == {"C_wrong_slice", "H_contradiction_wrong"}
    txt = r2.report(out)
    assert "Specific comparisons" in txt and "invalid_claim_persistence" in txt
