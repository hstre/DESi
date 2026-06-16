"""Acceptance proof for the epistemic solution-space gap analysis (DESi side of the Kevin contract).

The four conditions the analysis must meet BEFORE it may be called a real solution-space finder:
  1. proposals change with real conflict/evidence/trial data;
  2. they differ traceably from a keyword/frequency heuristic;
  3. every ranking change is traceable to a concrete changed input signal;
  4. it is intervention-sensitive: a successful / unsuccessful / conflict-resolving trial changes or
     removes the blind spot as expected.

Driven by a single frozen A/B/C scenario so the behaviour is auditable, not asserted in the abstract.
"""

from desi.solution_space_gap import (
    ConflictGap,
    EpistemicGapSnapshot,
    MethodRecord,
    SnapshotProvenance,
    analyze_gaps,
    frequency_baseline,
)


def _snapshot_A():
    # A: a hard, open causal_dispute; CAUSAL is the most relevant move and has never been tried.
    return EpistemicGapSnapshot(
        conflicts=(ConflictGap(id="X17", kind="causal_dispute", severity="hard",
                               scope=("C-7", "C-9"), attempted_affinities=(),
                               unresolved_since=1842),),
        method_history=(MethodRecord("m_bdry", ("boundary",), positive_trials=2),),
        provenance=SnapshotProvenance("hashA", 1842))


def _snapshot_B():
    # B: the SAME conflict, but CAUSAL has now been tried 3x on it without success.
    return EpistemicGapSnapshot(
        conflicts=(ConflictGap(id="X17", kind="causal_dispute", severity="hard",
                               scope=("C-7", "C-9"), attempted_affinities=("causal",),
                               unresolved_since=1842),),
        method_history=(MethodRecord("m_causal", ("causal",), contexts_tested=("X17",),
                                     negative_trials=3),),
        provenance=SnapshotProvenance("hashB", 1903))


def _snapshot_C():
    # C: the conflict has been resolved by new evidence -> it is simply absent from the snapshot.
    return EpistemicGapSnapshot(conflicts=(), provenance=SnapshotProvenance("hashC", 1950))


def _top(snap):
    return [p.missing_affinity for p in analyze_gaps(snap)]


def test_A_untried_relevant_move_is_top():
    props = analyze_gaps(_snapshot_A())
    assert props and props[0].missing_affinity == "causal"
    assert props[0].priority == 1.0 and props[0].expected_information_gain == "high"
    # the proposal is justified by the concrete signals (traceable)
    assert any("never tried" in r for r in props[0].reason)
    assert any("X17" in r for r in props[0].reason)
    # non-authoritative + carries provenance
    assert props[0].provenance["snapshot_hash"] == "hashA"
    assert props[0].provenance["layer9_sequence"] == 1842


def test_condition_4a_intervention_demotes_a_failed_move():
    a_top, b_top = _top(_snapshot_A()), _top(_snapshot_B())
    assert a_top[0] == "causal"                       # A: causal leads
    assert b_top[0] != "causal"                       # B: after 3 failed trials, causal is demoted
    assert b_top[0] == "boundary"                     # the next untried relevant move rises
    # condition 3: the change is traceable to the trial signal
    causal_in_b = [p for p in analyze_gaps(_snapshot_B()) if p.missing_affinity == "causal"]
    assert causal_in_b and any("without success" in r for r in causal_in_b[0].reason)


def test_condition_1_proposals_change_with_state():
    assert _top(_snapshot_A()) != _top(_snapshot_B())  # different epistemic state -> different ranking


def test_condition_4b_resolution_removes_the_blind_spot():
    props = analyze_gaps(_snapshot_C())
    assert props == []                                 # resolved conflict -> no proposal at all
    assert not any("X17" in p.target for p in props)


def test_condition_2_differs_from_frequency_heuristic():
    snap = _snapshot_A()
    assert _top(snap) != frequency_baseline(snap)      # conflict-driven, not an affinity-count sort


def test_a_move_that_already_worked_is_not_a_gap():
    snap = EpistemicGapSnapshot(
        conflicts=(ConflictGap(id="Y1", kind="causal_dispute", severity="hard",
                               attempted_affinities=("causal",)),),
        method_history=(MethodRecord("m", ("causal",), contexts_tested=("Y1",), positive_trials=2),))
    assert all(p.missing_affinity != "causal" for p in analyze_gaps(snap))  # solved -> not proposed


def test_deterministic():
    assert [p.to_dict() for p in analyze_gaps(_snapshot_A())] == \
           [p.to_dict() for p in analyze_gaps(_snapshot_A())]
