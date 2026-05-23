"""Tests for ReadOnlyMemoryView — reads work, writes are not on the surface."""
from __future__ import annotations

import pytest

from desi.memory import (
    InMemoryStore,
    MemoryRecorder,
    ReadOnlyMemoryView,
    RelationType,
)


@pytest.fixture()
def populated_view() -> tuple[ReadOnlyMemoryView, dict]:
    """Build a recorder + view + a small fixture graph.

    Returns the view and a context dict with the seeded claim ids.
    """
    rec = MemoryRecorder(InMemoryStore())
    rec.start_run(model="claude-opus-4-7")
    root = rec.record_claim(content="quantum mechanics is incomplete",
                            method="human")
    child_a = rec.record_claim(content="hidden variables exist",
                               method="T6")
    child_b = rec.record_claim(content="quantum mechanics is incomplete in this regime",
                               method="T6")
    rec.record_relation(source=child_a, target=root,
                        rel_type=RelationType.DERIVES_FROM)
    rec.record_relation(source=child_b, target=root,
                        rel_type=RelationType.REFINES)
    rec.record_operator_event(operator_name="T6",
                              output_claims=(child_a.claim_id,))
    rec.record_operator_event(operator_name="T1",
                              output_claims=(child_b.claim_id,))
    view = rec.read_only_view()
    return view, {"root": root.claim_id,
                  "child_a": child_a.claim_id,
                  "child_b": child_b.claim_id}


# ---------------------------------------------------------------------------
# Reads
# ---------------------------------------------------------------------------


def test_get_claim(populated_view) -> None:
    view, ctx = populated_view
    c = view.get_claim(ctx["root"])
    assert c is not None
    assert c.content == "quantum mechanics is incomplete"


def test_get_claim_missing_returns_none(populated_view) -> None:
    view, _ = populated_view
    assert view.get_claim("c_missing") is None


def test_find_related_returns_neighbours(populated_view) -> None:
    view, ctx = populated_view
    related_to_root = view.find_related(ctx["root"], direction="in")
    ids = {c.claim_id for c in related_to_root}
    assert ctx["child_a"] in ids
    assert ctx["child_b"] in ids


def test_find_related_filters_by_type(populated_view) -> None:
    view, ctx = populated_view
    derives = view.find_related(ctx["root"], direction="in",
                                rel_type=RelationType.DERIVES_FROM)
    ids = {c.claim_id for c in derives}
    assert ids == {ctx["child_a"]}


def test_find_similar_returns_high_overlap_first(populated_view) -> None:
    view, ctx = populated_view
    sims = view.find_similar("quantum mechanics is incomplete in some regime")
    assert sims, "expected at least one similar claim"
    # The two claims that share the phrase "quantum mechanics is incomplete"
    # should both appear; the longer-overlap one should rank first.
    ids = [c.claim_id for c in sims]
    assert ctx["root"] in ids
    assert ctx["child_b"] in ids


def test_find_similar_with_no_overlap_returns_empty(populated_view) -> None:
    view, _ = populated_view
    sims = view.find_similar("zebra giraffe rhinoceros")
    assert sims == []


def test_get_branch_history_walks_derivation(populated_view) -> None:
    view, ctx = populated_view
    history = view.get_branch_history(ctx["child_a"])
    ids = {c.claim_id for c in history}
    # child_a -[DERIVES_FROM]-> root
    assert ctx["root"] in ids


def test_get_operator_history_filters_by_name(populated_view) -> None:
    view, _ = populated_view
    t6 = view.get_operator_history("T6")
    assert len(t6) == 1
    assert t6[0].operator_code == "T6"
    t99 = view.get_operator_history("T99")
    assert t99 == []


# ---------------------------------------------------------------------------
# Write-attempt rejection: technical enforcement
# ---------------------------------------------------------------------------


def test_view_has_no_write_attributes() -> None:
    view = ReadOnlyMemoryView(InMemoryStore())
    forbidden = [
        "add_claim", "add_relation", "add_run", "add_event",
        "record_claim", "record_revision", "record_relation",
        "record_operator_event", "merge_claims", "split_claim",
        "start_run", "end_run",
    ]
    for attr in forbidden:
        assert not hasattr(view, attr), \
            f"ReadOnlyMemoryView must not expose {attr}"


def test_view_underlying_store_is_name_mangled() -> None:
    view = ReadOnlyMemoryView(InMemoryStore())
    # The store is accessible only through the name-mangled attribute.
    # Calling it ``_store`` directly returns nothing.
    assert getattr(view, "_store", None) is None


def test_view_cannot_set_attributes() -> None:
    view = ReadOnlyMemoryView(InMemoryStore())
    # __slots__ defines exactly one (mangled) attribute and the view
    # has no public mutator. AttributeError is fine here.
    with pytest.raises((AttributeError, TypeError)):
        view.add_claim = lambda *args, **kwargs: None  # type: ignore[attr-defined]
