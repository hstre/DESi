"""GSM-Symbolic DESi arm - Level-A/B state extractor tests.

Covers the deterministic structuring (no arithmetic, Level C excluded),
the NoOp heuristic against the three P2 negative controls, and - just as
importantly - the heuristic's two pinned blind spots, so the limitation
is documented in code rather than overclaimed.
"""
from __future__ import annotations

from desi.gsm_symbolic import (
    clause_is_suspected_irrelevant,
    extract_all,
    extract_state,
    has_number,
    load_dataset,
    noop_detection_metrics,
    normalized_tasks,
    split_clauses,
)


def _task(name: str, instance_id: str):
    for t in normalized_tasks(name):
        if t.instance_id == instance_id:
            return t
    raise AssertionError(instance_id)


# --- structuring (Level A/B, no solving) --------
def test_state_extracts_clauses_and_quantities() -> None:
    t = _task("gsm_symbolic_ref", "gsm_sym_t01_i0")
    s = extract_state(t)
    assert s.answer_type == "integer"
    # The question clause is detected as core.
    assert any(c.is_core for c in s.clauses)
    # Relevant quantities are surfaced but never combined.
    assert set(s.quantities()) == {"12", "7", "5"}


def test_state_has_no_answer_field() -> None:
    # Level C is excluded: the state never carries a derived answer.
    d = extract_state(_task("gsm_symbolic_ref", "gsm_sym_t01_i0")).to_dict()
    assert "answer" not in d
    assert set(d) == {
        "task_id", "answer_type", "quantities",
        "relevant_clauses", "irrelevant_clauses",
    }


def test_extract_all_covers_every_task() -> None:
    states = extract_all()
    assert len(states) == 33
    for s in states:
        assert s.clauses


# --- NoOp clause flagged on a real P2 noop ------
def test_noop_clause_flagged_irrelevant() -> None:
    s = extract_state(_task("gsm_symbolic_p2_ref", "gsm_p2_t01_i1"))
    irrelevant = [c.text for c in s.irrelevant_clauses()]
    assert any("painted blue" in c for c in irrelevant)
    # The numeric core/earning clause is kept.
    assert set(s.quantities()) >= {"12", "7", "5"}


# --- negative controls: all three roles ---------
def test_noop_detection_separates_three_controls() -> None:
    m = noop_detection_metrics()
    per = m["per_role"]
    # noop must be flagged; load_bearing / adversarial must be kept.
    assert per["noop"] == {"correct": 3, "total": 3}
    assert per["load_bearing"] == {"correct": 3, "total": 3}
    assert per["adversarial_similar"] == {"correct": 3, "total": 3}
    assert m["accuracy"] == 1.0


# --- pinned blind spots (documented limitation) -
def test_blind_spot_numeric_decoy_noop_is_missed() -> None:
    """A noop clause carrying a decoy number is wrongly KEPT: the numeric
    cue is a proxy for relevance, not relevance itself."""
    decoy = "Her locker number is 42"
    assert has_number(decoy)
    # not flagged irrelevant -> false negative (heuristic fails here).
    assert clause_is_suspected_irrelevant(decoy, is_core=False) is False


def test_blind_spot_wordy_adversarial_is_wrongly_dropped() -> None:
    """An adversarial clause that hides its operand in words ('half') is
    wrongly FLAGGED irrelevant -> false positive."""
    wordy = "By the way, she gives half of the bonus back"
    assert not has_number(wordy)
    assert clause_is_suspected_irrelevant(wordy, is_core=False) is True


# --- determinism --------------------------------
def test_split_and_state_are_deterministic() -> None:
    q = load_dataset("gsm_symbolic_p2_ref").instances()[1].question
    assert split_clauses(q) == split_clauses(q)
    t = _task("gsm_symbolic_p2_ref", "gsm_p2_t01_i1")
    assert extract_state(t).to_dict() == extract_state(t).to_dict()
