"""Aufgaben 2 + 4 — split TENSION targets and assign causes."""
from __future__ import annotations

from desi.frame_tension_audit.enums import (
    TensionAuditClass,
    TensionFailureCause,
)
from desi.frame_tension_audit.extractor import extract_tension_targets
from desi.frame_tension_audit.splitter import split_tension_targets


def test_outcome_count_matches_target_count() -> None:
    targets = extract_tension_targets()
    outs = split_tension_targets(targets)
    assert len(outs) == len(targets)


def test_audit_class_always_set() -> None:
    for o in split_tension_targets(extract_tension_targets()):
        assert isinstance(o.audit_class, TensionAuditClass)


def test_true_tension_carries_no_failure_cause() -> None:
    for o in split_tension_targets(extract_tension_targets()):
        if o.audit_class is TensionAuditClass.TRUE_TENSION:
            assert o.failure_cause is None, o.target.case_id


def test_false_and_ambiguous_carry_exactly_one_cause() -> None:
    for o in split_tension_targets(extract_tension_targets()):
        if o.audit_class in (
            TensionAuditClass.FALSE_TENSION,
            TensionAuditClass.AMBIGUOUS_TENSION,
        ):
            assert isinstance(
                o.failure_cause, TensionFailureCause,
            ), o.target.case_id


def test_split_is_deterministic() -> None:
    a = [o.to_dict() for o in split_tension_targets(
        extract_tension_targets(),
    )]
    b = [o.to_dict() for o in split_tension_targets(
        extract_tension_targets(),
    )]
    assert a == b


def test_hard_inner_marker_yields_true_tension() -> None:
    # Sanity: cases like "Shannon entropy of the message
    # distribution is one bit." under a thermo outer must be TRUE
    # because the inner has a hard info-theoretic marker.
    outs = {
        o.target.case_id: o
        for o in split_tension_targets(extract_tension_targets())
    }
    if "manip:M01" in outs:
        assert outs["manip:M01"].audit_class is (
            TensionAuditClass.TRUE_TENSION
        )
