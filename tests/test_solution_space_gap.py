"""Acceptance proof for DESi's epistemic solution-space gap analysis (the DESi side of the contract).

Four conditions before this may be called a real solution-space finder:
  1. proposals change with real conflict/evidence/trial data;
  2. they differ from BOTH a frequency heuristic AND a static conflict-kind->affinity lookup
     (the value-add must come from trial/evidence HISTORY, not a table);
  3. every ranking change is traceable to a concrete changed input signal;
  4. intervention-sensitive: a NO-BENEFIT / harmful trial demotes the move (scope-bound); a merely
     TECHNICAL failure does NOT; a successful or conflict-resolving change updates/removes the gap.

A single frozen A / B / B2 / C scenario, so the behaviour is auditable, not asserted in the abstract.
"""

from desi.solution_space_gap import (
    ConflictGap,
    EpistemicGapSnapshot,
    MethodRecord,
    MethodTrial,
    SnapshotProvenance,
    analyze_gaps,
    frequency_baseline,
    static_kind_baseline,
)

_REPERTOIRE = (MethodRecord("m_bdry", ("boundary",)),)


def _A():
    # open hard causal_dispute; CAUSAL most relevant, never tried.
    return EpistemicGapSnapshot(
        conflicts=(ConflictGap("X17", "causal_dispute", "hard", scope=("C-7",),
                               attempted_affinities=(), unresolved_since=1842),),
        method_history=_REPERTOIRE, provenance=SnapshotProvenance("hA", 1842))


def _B():
    # CAUSAL tried 3x on X17 with NO BENEFIT (real methodological failure in scope) -> must demote.
    return EpistemicGapSnapshot(
        conflicts=(ConflictGap("X17", "causal_dispute", "hard", attempted_affinities=("causal",),
                               unresolved_since=1842),),
        method_history=_REPERTOIRE,
        method_trials=(MethodTrial("causal", "X17", "no_benefit", scope="qtt", method_variant="v2",
                                   count=3),),
        provenance=SnapshotProvenance("hB", 1903))


def _B2():
    # CAUSAL tried on X17 but ONLY technical failures (no methodological signal) -> must stay open.
    return EpistemicGapSnapshot(
        conflicts=(ConflictGap("X17", "causal_dispute", "hard", attempted_affinities=("causal",),
                               unresolved_since=1842),),
        method_history=_REPERTOIRE,
        method_trials=(MethodTrial("causal", "X17", "technical_failure", scope="qtt", count=3),),
        provenance=SnapshotProvenance("hB2", 1904))


def _C():
    # resolved -> absent from the snapshot.
    return EpistemicGapSnapshot(conflicts=(), provenance=SnapshotProvenance("hC", 1950))


def _top(snap):
    return [p.missing_affinity for p in analyze_gaps(snap)]


def test_A_untried_relevant_move_is_top_and_justified():
    p = analyze_gaps(_A())[0]
    assert p.missing_affinity == "causal" and p.priority == 1.0
    assert any("never tried" in r for r in p.reason) and any("X17" in r for r in p.reason)
    assert p.provenance == {"snapshot_hash": "hA", "layer9_sequence": 1842}


def test_condition4_no_benefit_demotes_but_is_scope_bound():
    a, b = _top(_A()), _top(_B())
    assert a[0] == "causal" and b[0] == "boundary"     # real failure in scope -> causal demoted
    # the demotion is SCOPE-BOUND and traceable to the no-benefit signal
    causal_b = [p for p in analyze_gaps(_B()) if p.missing_affinity == "causal"][0]
    assert any("no benefit" in r for r in causal_b.reason) and "scope" in "".join(causal_b.reason)


def test_condition4_technical_failure_does_NOT_demote():
    # a purely TECHNICAL failure carries no methodological signal -> causal stays the top gap...
    assert analyze_gaps(_B2())[0].missing_affinity == "causal"
    # ...and THIS is where DESi beats the static table: the static (binary tried/untried) lookup
    # wrongly discards causal (it is "attempted"), DESi keeps it open.
    assert "causal" not in static_kind_baseline(_B2())
    assert _top(_B2())[0] == "causal" != (static_kind_baseline(_B2()) or [None])[0]


def test_condition1_changes_with_state():
    assert _top(_A()) != _top(_B())


def test_condition4_resolution_removes_the_gap():
    assert analyze_gaps(_C()) == []


def test_condition2_beats_frequency_AND_static_via_trial_history():
    # vs frequency: different ordering. vs static table: only DESi reacts to the technical-vs-real
    # failure distinction (B demotes causal, B2 does not) - a static lookup cannot tell them apart.
    assert _top(_A()) != frequency_baseline(_A())
    assert _top(_B()) != _top(_B2())                   # DESi distinguishes the two failure kinds...
    assert static_kind_baseline(_B()) == static_kind_baseline(_B2())   # ...the static table cannot


def test_success_in_another_scope_keeps_the_move_open_here():
    snap = EpistemicGapSnapshot(
        conflicts=(ConflictGap("Z1", "causal_dispute", "hard", attempted_affinities=()),),
        method_trials=(MethodTrial("causal", "OTHER", "success", scope="elsewhere"),))
    p = [x for x in analyze_gaps(snap) if x.missing_affinity == "causal"][0]
    assert p.priority == 1.0 and any("another scope" in r.lower() for r in p.reason)


def test_deterministic():
    assert [p.to_dict() for p in analyze_gaps(_A())] == [p.to_dict() for p in analyze_gaps(_A())]
