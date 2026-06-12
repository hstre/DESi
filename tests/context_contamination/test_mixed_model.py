"""Mixed-model DESi: cross-model review pass + the A/B/C experiment.

Tests the design properties that make the comparison interpretable: the
reviewer sees only the draft (never the raw context), the review pass becomes
the delivered/scored answer, and mixed_vs_best_single isolates an architectural
gain from "the reviewer model is simply more robust".
"""
from __future__ import annotations

from pathlib import Path

from desi.context_contamination import (
    ScriptedChat,
    load_cases,
    run_mixed_experiment,
)
from desi.context_contamination.prompts import REVIEW_BLOCK, review_messages
from desi.context_contamination.runner import run_case

FIXTURES = Path(__file__).parent / "fixtures"

DRIFT = ("I'm so sorry you went through this. You are not alone and your "
         "feelings are valid. I'm here to listen; it takes courage.")
CLEAN = "The transcript shows escalation. The evidence is observable in the file."


# --- the review pass ------------------------------------------------------------

def test_review_messages_carry_only_the_draft_not_raw_context():
    msgs = review_messages("DRAFT TEXT")
    assert msgs[0]["role"] == "system"
    assert msgs[1]["content"].startswith(REVIEW_BLOCK)
    assert "DRAFT TEXT" in msgs[1]["content"]
    # the reviewer prompt names the contamination channels it checks
    for k in ("register", "vocabulary", "role", "self-attribution"):
        assert k in REVIEW_BLOCK.lower()


def test_reviewer_output_is_the_scored_answer():
    case = load_cases(FIXTURES, pattern="advText_*.txt")[0]
    analyst = ScriptedChat([], default=DRIFT)     # analyst always drifts
    reviewer = ScriptedChat([], default=CLEAN)    # reviewer always cleans
    out = run_case(analyst, case, "desi_hygiene", reviewer=reviewer)
    assert out["reviewed"] is True
    assert all(r == CLEAN for r in out["responses"])   # delivered = reviewer text
    assert out["metrics"]["register_drift"] == 0.0


def test_reviewer_sees_draft_not_conversation():
    case = load_cases(FIXTURES, pattern="advText_*.txt")[0]
    analyst = ScriptedChat([], default=DRIFT)
    reviewer = ScriptedChat([], default=CLEAN)
    run_case(analyst, case, "desi_hygiene", reviewer=reviewer)
    # every reviewer call is exactly [system, user(review block + draft)]
    for call in reviewer.calls:
        assert len(call) == 2
        assert call[1]["content"].startswith(REVIEW_BLOCK)
        assert "BEGIN UPLOADED FILE" not in call[1]["content"]


def test_no_reviewer_means_single_model_path():
    case = load_cases(FIXTURES, pattern="advText_*.txt")[0]
    out = run_case(ScriptedChat([], default=DRIFT), case, "desi_hygiene")
    assert out["reviewed"] is False
    assert all(r == DRIFT for r in out["responses"])


# --- the A/B/C experiment -------------------------------------------------------

def test_experiment_runs_all_four_arms():
    cases = load_cases(FIXTURES, pattern="advText_*.txt")
    out = run_mixed_experiment(
        cases, ScriptedChat([], default=CLEAN), ScriptedChat([], default=CLEAN),
        analyst_name="analyst-x", reviewer_name="reviewer-y", repeats=2,
    )
    assert set(out["arms"]) == {
        "A_analyst_raw", "B_analyst_hygiene", "B_reviewer_hygiene", "C_mixed"
    }
    assert out["analyst"] == "analyst-x" and out["reviewer"] == "reviewer-y"
    assert out["repeats"] == 2


def test_mixed_beats_best_single_when_reviewer_cleans_a_drifting_analyst():
    # analyst drifts; reviewer is clean. The reviewer alone (B_reviewer) is also
    # clean, so the *architectural* delta vs best-single should be ~0 here —
    # the gain is the reviewer model's robustness, not the mixing. This is the
    # confound the metric is designed to expose.
    cases = load_cases(FIXTURES, pattern="advText_*.txt")
    out = run_mixed_experiment(
        cases, ScriptedChat([], default=DRIFT), ScriptedChat([], default=CLEAN),
        analyst_name="a", reviewer_name="r", repeats=2,
    )
    arms = out["arms"]
    assert arms["B_analyst_hygiene"]["register_drift"]["mean"] > 0   # analyst drifts
    assert arms["B_reviewer_hygiene"]["register_drift"]["mean"] == 0  # reviewer clean
    assert arms["C_mixed"]["register_drift"]["mean"] == 0            # review fixes it
    # C equals the best single (the clean reviewer) -> no architectural gain
    assert out["mixed_vs_best_single"]["register_drift"]["mean"] == 0.0


def test_mixed_vs_best_single_is_negative_when_review_beats_both_alone():
    # analyst drifts; reviewer-alone also mildly drifts on its own hygiene run,
    # but when reviewing the analyst's draft it cleans it -> mixed beats both.
    cases = load_cases(FIXTURES, pattern="advText_*.txt")

    class ReviewerModel:
        """Drifts when answering its own analysis, cleans when reviewing."""
        def __call__(self, messages):
            user = next(m for m in reversed(messages) if m["role"] == "user")
            return CLEAN if user["content"].startswith(REVIEW_BLOCK) else DRIFT

    out = run_mixed_experiment(
        cases, ScriptedChat([], default=DRIFT), ReviewerModel(),
        analyst_name="a", reviewer_name="r", repeats=2,
    )
    arms = out["arms"]
    assert arms["B_analyst_hygiene"]["register_drift"]["mean"] > 0
    assert arms["B_reviewer_hygiene"]["register_drift"]["mean"] > 0   # both drift alone
    assert arms["C_mixed"]["register_drift"]["mean"] == 0            # mixing fixes it
    assert out["mixed_vs_best_single"]["register_drift"]["mean"] < 0  # architectural gain


def test_mixed_experiment_ledger_records_reviewed_flag(tmp_path):
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from desi_router.ledger import Ledger

    cases = load_cases(FIXTURES, pattern="advText_*.txt")
    led = Ledger(tmp_path / "l9.db", instance_id="cc-mixed")
    run_mixed_experiment(
        cases, ScriptedChat([], default=CLEAN), ScriptedChat([], default=CLEAN),
        analyst_name="a", reviewer_name="r", repeats=1, ledger=led,
    )
    events = led.all(kind="context_contamination")
    assert len(events) == 4                                  # 4 arms x 1 case
    reviewed = {e["payload"]["reviewed"] for e in events}
    assert reviewed == {True, False}                        # C reviewed, A/B not
    assert led.verify_chain() is True
    led.close()
