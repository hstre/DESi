"""Aufgaben 2 + 3 — inner extractor (CTX_0 only) + outer extractor (CTX_1-3)."""
from __future__ import annotations

from desi.frame_consistency_probe.inner_extractor import extract_inner_frame
from desi.frame_consistency_probe.outer_extractor import extract_outer_frame
from desi.frames import FrameKind


def test_inner_extractor_recognises_explicit_marker() -> None:
    f = extract_inner_frame(
        "Frame: thermodynamic. Heat flows from hot to cold."
    )
    assert f is FrameKind.THERMODYNAMIC


def test_inner_extractor_uses_token_vocabulary() -> None:
    f = extract_inner_frame(
        "The Shannon entropy of a fair coin is one bit."
    )
    assert f is FrameKind.INFORMATION_THEORETIC


def test_inner_extractor_returns_none_on_neutral_text() -> None:
    f = extract_inner_frame("This sentence carries no frame token.")
    assert f is None


def test_inner_extractor_ignores_outer_context() -> None:
    # Even if a frame marker appears in something that looks like a
    # header, the inner extractor sees only the case sentence.
    f = extract_inner_frame("A neutral sentence.")
    assert f is None


def test_outer_extractor_prefers_explicit_frame() -> None:
    v = extract_outer_frame(
        ctx_1="Shannon and bits and channel capacity matter.",
        ctx_2="Section: Thermodynamics — Heat and Energy",
        ctx_3="Frame: information-theoretic",
    )
    assert v.frame is FrameKind.INFORMATION_THEORETIC
    assert v.signal == "explicit_frame"
    assert v.layer == "ctx_3"


def test_outer_extractor_uses_section_header_when_no_frame() -> None:
    v = extract_outer_frame(
        ctx_1="A neutral sentence.",
        ctx_2="Section: Information Theory — Coding and Bits",
        ctx_3="A document without a frame marker.",
    )
    assert v.frame is FrameKind.INFORMATION_THEORETIC
    assert v.signal == "section_header"
    assert v.layer == "ctx_2"


def test_outer_extractor_falls_back_to_domain_repetition() -> None:
    v = extract_outer_frame(
        ctx_1="Shannon's channel and bits dominate the discussion.",
        ctx_2="A bland header without keywords.",
        ctx_3="A document without a frame marker.",
    )
    assert v.frame is FrameKind.INFORMATION_THEORETIC
    assert v.signal == "domain_repetition"


def test_outer_extractor_returns_none_on_silent_layers() -> None:
    v = extract_outer_frame(
        ctx_1="A neutral sentence.",
        ctx_2="Another neutral sentence.",
        ctx_3="Yet a third neutral sentence.",
    )
    assert v.frame is None
    assert v.signal == "none"
    assert v.layer is None


def test_outer_extractor_only_inspects_ctx_1_through_3() -> None:
    # Even if we pass a frame-laden CTX_0-style sentence as the
    # *function argument* meant for CTX_1, it should still be
    # treated as outer evidence — but the extractor never sees CTX_0
    # by design.
    v = extract_outer_frame(
        ctx_1="A neutral sentence.",
        ctx_2="A neutral sentence.",
        ctx_3="A neutral sentence.",
    )
    assert v.frame is None
