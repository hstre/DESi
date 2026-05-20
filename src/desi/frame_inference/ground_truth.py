"""Aufgabe 4 — per-chain ground-truth frame assignment.

Each external chain in the v4.0 corpus is assigned a single
expected ``FrameKind`` based on its domain and the dominant
warrant pattern in its text. This is the audit author's
annotation — it is not derived from any DESi runtime output,
so a strategy that simply mimics ``FrameDetector`` cannot
trivially score the gt.

The mapping is closed: every chain belongs to exactly one
ground-truth frame, and one frame only. ``FRAME_UNDECLARED``
is reserved for the negative-control bank (Aufgabe 8) — real
external chains always carry a single intended frame.
"""
from __future__ import annotations

from ..external_probe.corpus import ExternalChain
from ..external_probe.enums import Domain
from ..frames import FrameKind


_AUTHORITY_VERBS: tuple[str, ...] = (
    " warned", " said", " says", " states", " stated",
    " claims", " claimed", " declares", " declared",
    " announced", " endorsed", " endorse", " suggest",
    " reported", " reports", " voices", " voice",
    " asserted", " asserts", "according to ",
    " concluded", " concludes", " published",
    "celebrity", "celebrities", "pollsters", "industry",
    "appellate", "experts", "specialists",
    "commentators", "executives", "officials",
)


def _domain_default(domain: Domain) -> FrameKind:
    if domain is Domain.D1_SCIENTIFIC_ABSTRACTS:
        return FrameKind.EMPIRICAL_CAUSAL
    if domain is Domain.D2_LEGAL_REASONING:
        return FrameKind.FORMAL_LOGIC
    if domain is Domain.D3_MEDICAL_CASE_REPORTS:
        return FrameKind.EMPIRICAL_CAUSAL
    if domain is Domain.D4_MATHEMATICAL_PROOFS:
        return FrameKind.FORMAL_LOGIC
    if domain is Domain.D5_ADVERSARIAL_REAL_WORLD:
        return FrameKind.AUTHORITY_SPEECH
    return FrameKind.FRAME_UNDECLARED  # NEGATIVE_CONTROL


def ground_truth_frame(chain: ExternalChain) -> FrameKind:
    """Per-chain expected frame.

    Domains 1–4 are canonically single-frame. Domain 5 mixes
    authority-driven and empirical-causal patterns: chains that
    cite or invoke a speaker get ``AUTHORITY_SPEECH``; chains
    that report measurable outcomes without a cited speaker get
    ``EMPIRICAL_CAUSAL``. Negative controls are always
    ``FRAME_UNDECLARED``.
    """
    if chain.domain is Domain.NEGATIVE_CONTROL:
        return FrameKind.FRAME_UNDECLARED
    if chain.domain is not Domain.D5_ADVERSARIAL_REAL_WORLD:
        return _domain_default(chain.domain)
    low = " " + chain.text.lower() + " "
    if any(v in low for v in _AUTHORITY_VERBS):
        return FrameKind.AUTHORITY_SPEECH
    return FrameKind.EMPIRICAL_CAUSAL


__all__ = ["ground_truth_frame"]
