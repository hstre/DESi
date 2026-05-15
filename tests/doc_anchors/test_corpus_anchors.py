"""Tests over the **real** anchor corpus — Aufgabe 7.

Every anchor inserted into the v2.x docs by the v3.1 auto-anchor
pass is loaded, validated against its artefact, and required to
resolve to ``VERIFIED``.
"""
from __future__ import annotations

import pathlib
from collections import Counter

from desi.doc_anchors import (
    AnchorVerdict,
    parse_anchors,
    parse_legacy_markers,
    validate_anchors,
)


_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


def _all_anchors():
    anchors = []
    for root in ("docs/memory", "docs/rule_patch_protocol"):
        base = _REPO_ROOT / root
        for p in sorted(base.glob("*.md")):
            rel = p.relative_to(_REPO_ROOT).as_posix()
            anchors.extend(parse_anchors(rel, p.read_text()))
    return tuple(anchors)


def test_corpus_has_at_least_twenty_anchors() -> None:
    anchors = _all_anchors()
    assert len(anchors) >= 20, f"only {len(anchors)} anchors present"


def test_every_anchor_references_existing_artifact() -> None:
    anchors = _all_anchors()
    outcomes = validate_anchors(anchors, repo_root=_REPO_ROOT)
    missing = [
        o for o in outcomes
        if o.verdict is AnchorVerdict.MISSING_ARTIFACT
    ]
    assert not missing, (
        f"missing artefacts for: "
        f"{[o.anchor.artifact for o in missing[:5]]}"
    )


def test_every_anchor_field_resolves() -> None:
    anchors = _all_anchors()
    outcomes = validate_anchors(anchors, repo_root=_REPO_ROOT)
    missing_field = [
        o for o in outcomes
        if o.verdict is AnchorVerdict.MISSING_FIELD
    ]
    assert not missing_field, (
        "fields not found: "
        + ", ".join(o.anchor.field for o in missing_field[:5])
    )


def test_every_anchor_value_matches_artifact() -> None:
    anchors = _all_anchors()
    outcomes = validate_anchors(anchors, repo_root=_REPO_ROOT)
    mismatches = [
        o for o in outcomes
        if o.verdict is AnchorVerdict.VALUE_MISMATCH
    ]
    assert not mismatches, "value mismatches: " + "; ".join(
        f"{o.anchor.doc_path}:{o.anchor.field} "
        f"({o.actual_value} vs {o.anchor.expected})"
        for o in mismatches[:5]
    )


def test_every_anchor_verified() -> None:
    anchors = _all_anchors()
    outcomes = validate_anchors(anchors, repo_root=_REPO_ROOT)
    bad = [o for o in outcomes if o.verdict is not AnchorVerdict.VERIFIED]
    assert not bad, (
        f"{len(bad)} anchor(s) did not verify:\n"
        + "\n".join(
            f"  {o.anchor.doc_path}:L{o.anchor.line_number} "
            f"{o.verdict.value}: {o.reason}"
            for o in bad[:10]
        )
    )


def test_no_duplicate_anchors_within_document() -> None:
    """The same anchor (artifact, field, expected) on the same line
    twice is a duplicate. The same metric appearing in two separate
    paragraphs is fine — each instance carries its own context."""
    anchors = _all_anchors()
    seen: set[tuple[str, int, str, str, str]] = set()
    dupes: list[str] = []
    for a in anchors:
        key = (a.doc_path, a.line_number, a.artifact, a.field, a.expected)
        if key in seen:
            dupes.append(
                f"{a.doc_path}:L{a.line_number} "
                f"{a.artifact}:{a.field}={a.expected}"
            )
        seen.add(key)
    assert not dupes, f"duplicate anchors: {dupes[:5]}"


def test_legacy_exemptions_are_explicit() -> None:
    """Every v0.x and v1.x document must carry the legacy marker."""
    for prefix in ("v0_", "v1_"):
        for p in sorted((_REPO_ROOT / "docs/memory").glob(f"{prefix}*.md")):
            marks = parse_legacy_markers(p.name, p.read_text())
            assert marks, (
                f"{p.name} is pre-v2.0 but carries no "
                "[legacy-unanchored] marker"
            )


def test_v2x_documents_have_no_legacy_exemption() -> None:
    """v2.0+ docs must NOT carry the legacy marker — they have
    proper artefacts."""
    for p in sorted((_REPO_ROOT / "docs/memory").glob("v2_*.md")):
        marks = parse_legacy_markers(p.name, p.read_text())
        assert not marks, (
            f"{p.name} is v2.x but carries the legacy marker"
        )
    for p in sorted((_REPO_ROOT / "docs/memory").glob("v3_*.md")):
        marks = parse_legacy_markers(p.name, p.read_text())
        assert not marks
