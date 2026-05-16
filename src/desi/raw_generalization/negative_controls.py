"""Aufgabe 9 — 100 NCs for the raw split evaluation.

Five closed kinds (``NCKind``):

* RAW_VALID_PROBE_TRAP    — VALID chain whose conclusion
  triggers a v5.0 safe probe (probe channel says fire,
  taxonomy channel says NOT MT_OTHER). Audit must record
  the safe-probe firing as a *probe false activation*,
  independent of taxonomy assignment.
* RAW_INVALID_PARAPHRASE  — INVALID chain that lacks any
  strict-probe vocabulary; the cascade still classifies
  it into an ``MT_*`` class (typically
  MT_NOVEL_ENTITY / MT_AUDIT_OVER_SUPPORT).
* AMBIGUITY_DECOY         — AMBIGUOUS chain with hedge
  tokens; classifier must return
  MT_AMBIGUITY_DECISIVENESS.
* OVERLAP_ILLUSION        — VALID chain with heavy
  token repetition; safe-probe channel reports
  MT_OVERLAP_LOOP fires; taxonomy channel reports the
  chain still classifies normally.
* DOMAIN_HYBRID           — chain mixing two adjacent
  domain vocabularies; the cascade should still pick a
  canonical ``MT_*`` class (typically MT_MODAL_ASYMMETRY
  via "will + every X" tail).

For each NC we record the expected channel-specific
behaviour. NC accuracy = fraction of NCs whose taxonomy
assignment AND probe-firing pattern both match
expectation.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..methodology_transfer.probe_generator import (
    probe_fires,
)
from ..taxonomy_generalization.classifier import (
    classify_chain,
)
from ..taxonomy_generalization.corpus import (
    GeneralizationChain,
)
from ..taxonomy_generalization.probe_transfer import (
    SAFE_PROBE_CLASSES,
)
from .enums import NCKind


@dataclass(frozen=True)
class RawNC:
    nc_id: str
    kind: str
    text: str
    domain: str
    ground_truth: str
    expected_taxonomy_in: tuple[str, ...]
    expected_any_probe_fires: bool


def _make(
    prefix: str, items: tuple[str, ...],
    kind: NCKind, domain: str, ground_truth: str,
    expected_in: tuple[str, ...],
    probe_fires_flag: bool,
) -> tuple[RawNC, ...]:
    return tuple(
        RawNC(
            nc_id=f"{prefix}{i:03d}", kind=kind.value,
            text=t, domain=domain,
            ground_truth=ground_truth,
            expected_taxonomy_in=expected_in,
            expected_any_probe_fires=probe_fires_flag,
        )
        for i, t in enumerate(items, start=1)
    )


# ---------------------------------------------------------------------------
# RAW_VALID_PROBE_TRAP — VALID chain with conclusion that
# fires MT_OVERLAP_LOOP via heavy token overlap. The
# probe channel must register a false activation; the
# taxonomy channel will classify the chain into some MT_*
# (often MT_OVERLAP_LOOP).
# ---------------------------------------------------------------------------

_VALID_TRAPS = tuple(
    (
        f"Productivity in cell {i} rose during cycle {i}. "
        f"Audit findings in cell {i} cleared each cycle {i} "
        f"review. Therefore productivity in cell {i} rose "
        f"during cycle {i} across the cycle {i} review."
    )
    for i in range(1, 21)
)


# ---------------------------------------------------------------------------
# RAW_INVALID_PARAPHRASE — INVALID chain with no strict
# probe vocabulary; expected to land in an MT_* class but
# no safe probe fires.
# ---------------------------------------------------------------------------

_INVALID_PARAPHRASE = tuple(
    (
        f"The audit team logged steady readings on day {i}. "
        f"The reviewer compiled the findings. Therefore "
        f"the program is conclusively shown to require a "
        f"complete overhaul of every comparable office "
        f"protocol in the region."
    )
    for i in range(1, 21)
)


# ---------------------------------------------------------------------------
# AMBIGUITY_DECOY — AMBIGUOUS GT, hedge in conclusion;
# cascade should pick MT_AMBIGUITY_DECISIVENESS via the
# label-gated rule.
# ---------------------------------------------------------------------------

_AMBIGUITY_DECOY = tuple(
    (
        f"The pilot reduced wait times in two clinics on "
        f"day {i}. Patient satisfaction climbed in both "
        f"clinics. Therefore the protocol may also benefit "
        f"longer-stay patients during round {i}."
    )
    for i in range(1, 21)
)


# ---------------------------------------------------------------------------
# OVERLAP_ILLUSION — VALID chain with overlap-heavy
# wording; probe channel reports overlap, taxonomy
# channel still assigns an MT_* class.
# ---------------------------------------------------------------------------

_OVERLAP_ILLUSION = tuple(
    (
        f"Volume on channel zeta-{i} grew each zeta-{i} "
        f"month. Conversion on channel zeta-{i} tracked "
        f"zeta-{i} growth. Therefore zeta-{i} channel "
        f"volume grew each zeta-{i} month across the "
        f"zeta-{i} review."
    )
    for i in range(1, 21)
)


# ---------------------------------------------------------------------------
# DOMAIN_HYBRID — chain blending medical + legal +
# proof vocabulary in premises with a modal+universal
# overreach in the conclusion. Expected: MT_MODAL_ASYMMETRY,
# at least one safe probe fires (MT-P01).
# ---------------------------------------------------------------------------

_DOMAIN_HYBRID = tuple(
    (
        f"The court admitted the postmortem reading {i} "
        f"into evidence. The reviewer verified the "
        f"theorem citation {i}. Therefore for every "
        f"comparable matter on the docket the panel will "
        f"apply the same standard."
    )
    for i in range(1, 21)
)


def all_raw_ncs() -> tuple[RawNC, ...]:
    return (
        _make(
            "NC-VT-", _VALID_TRAPS,
            NCKind.RAW_VALID_PROBE_TRAP,
            "synthetic", "VALID",
            expected_in=(
                "MT_OVERLAP_LOOP",
                "MT_AUDIT_OVER_SUPPORT",
                "MT_NOVEL_ENTITY",
            ),
            probe_fires_flag=True,
        )
        + _make(
            "NC-IP-", _INVALID_PARAPHRASE,
            NCKind.RAW_INVALID_PARAPHRASE,
            "synthetic", "INVALID",
            expected_in=(
                "MT_NOVEL_ENTITY",
                "MT_AUDIT_OVER_SUPPORT",
                "MT_MODAL_ASYMMETRY",
                "MT_UNIVERSAL_LEAP",
            ),
            probe_fires_flag=False,
        )
        + _make(
            "NC-AD-", _AMBIGUITY_DECOY,
            NCKind.AMBIGUITY_DECOY,
            "synthetic", "AMBIGUOUS",
            expected_in=("MT_AMBIGUITY_DECISIVENESS",),
            probe_fires_flag=False,
        )
        + _make(
            "NC-OI-", _OVERLAP_ILLUSION,
            NCKind.OVERLAP_ILLUSION,
            "synthetic", "VALID",
            expected_in=(
                "MT_OVERLAP_LOOP",
                "MT_NOVEL_ENTITY",
                "MT_AUDIT_OVER_SUPPORT",
            ),
            probe_fires_flag=True,
        )
        + _make(
            "NC-DH-", _DOMAIN_HYBRID,
            NCKind.DOMAIN_HYBRID,
            "synthetic", "INVALID",
            expected_in=("MT_MODAL_ASYMMETRY",),
            probe_fires_flag=True,
        )
    )


def _any_probe_fires(text: str) -> bool:
    return any(
        probe_fires(p, text) for p in SAFE_PROBE_CLASSES
    )


def classify_nc(
    nc: RawNC,
) -> tuple[str, bool]:
    chain = GeneralizationChain(
        chain_id=nc.nc_id, domain=nc.domain,
        text=nc.text, ground_truth=nc.ground_truth,
        rationale=nc.kind,
    )
    assigned = classify_chain(chain).assigned_class
    fires = _any_probe_fires(nc.text)
    return assigned, fires


def classification_accuracy() -> float:
    ncs = all_raw_ncs()
    correct = 0
    for nc in ncs:
        assigned, fires = classify_nc(nc)
        tax_ok = assigned in nc.expected_taxonomy_in
        probe_ok = fires == nc.expected_any_probe_fires
        if tax_ok and probe_ok:
            correct += 1
    return round(correct / len(ncs), 6)


__all__ = [
    "RawNC", "all_raw_ncs",
    "classification_accuracy", "classify_nc",
]
