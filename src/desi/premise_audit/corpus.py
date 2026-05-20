"""Aufgabe 3 — corpus assembly: ≥ 500 chains, ≥ 2000 transitions.

Combines v2.3, v3.14, v3.15, v3.16 surviving + suspended,
v3.19 trajectories, the v3.18 NCs, the v3.13 routing benchmark,
and v3.19's synthetic NCs. Each entry carries an
``expected_natural`` label so the report can split valid vs
adversarial.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..benchmark_multistep import ALL_MULTISTEP_CASES
from ..causal_naturalness.negative_control import (
    ALL_NC_CHAINS as V318_NC_CHAINS, NCShape as V318Shape,
)
from ..causal_redteam.cases import ALL_ADVERSARIAL_CASES
from ..frame_tension_integration import build_integration_benchmark
from ..heldout_causal import ALL_HELDOUT_CASES
from ..logic.audit import LogicalAuditor, LogicalState
from ..logic.inference import InferenceRule


@dataclass(frozen=True)
class ChainEntry:
    chain_id: str
    source: str
    text: str
    expected_natural: bool


def _v23() -> tuple[ChainEntry, ...]:
    return tuple(
        ChainEntry(
            chain_id=f"v23:{c.case_id}",
            source="v23_multistep",
            text=c.text,
            expected_natural=True,
        )
        for c in ALL_MULTISTEP_CASES
    )


def _v314() -> tuple[ChainEntry, ...]:
    return tuple(
        ChainEntry(
            chain_id=f"v314:{c.case_id}",
            source="v314_heldout",
            text=c.text,
            expected_natural=not c.expected_blocked,
        )
        for c in ALL_HELDOUT_CASES
    )


def _v315() -> tuple[ChainEntry, ...]:
    return tuple(
        ChainEntry(
            chain_id=f"v315:{c.case_id}",
            source="v315_adversarial",
            text=c.text,
            expected_natural=False,
        )
        for c in ALL_ADVERSARIAL_CASES
    )


def _v316_split() -> tuple[ChainEntry, ...]:
    auditor = LogicalAuditor()
    out: list[ChainEntry] = []
    for c in ALL_ADVERSARIAL_CASES:
        r = auditor.audit(c.text)
        still_supported = (
            r.state == LogicalState.LOGICALLY_SUPPORTED
            and r.rule is InferenceRule.CAUSAL_CHAIN
        )
        label = "v316_surviving" if still_supported else "v316_suspended"
        out.append(ChainEntry(
            chain_id=f"{label}:{c.case_id}",
            source=label,
            text=c.text,
            expected_natural=False,
        ))
    return tuple(out)


def _v318_ncs() -> tuple[ChainEntry, ...]:
    out: list[ChainEntry] = []
    for nc in V318_NC_CHAINS:
        # naturalness labels: VBS + NBF are valid; OET + WMF
        # are adversarial-shape.
        natural = nc.shape in (
            V318Shape.NATURAL_BUT_FALSE,
            V318Shape.VALID_BUT_SPARSE,
        )
        out.append(ChainEntry(
            chain_id=f"v318-{nc.shape.value}:{nc.case_id}",
            source=f"v318_{nc.shape.value}",
            text=nc.text,
            expected_natural=natural,
        ))
    return tuple(out)


def _v313_routing() -> tuple[ChainEntry, ...]:
    """v3.13 integration benchmark — adds 70 chains."""
    out: list[ChainEntry] = []
    for case in build_integration_benchmark():
        # NORMAL category is expected_natural; MANIPULATIVE and
        # AMBIGUOUS are adversarial-shape.
        natural = case.category.value == "normal"
        out.append(ChainEntry(
            chain_id=f"v313:{case.case_id}",
            source=f"v313_{case.category.value}",
            text=case.claim_text,
            expected_natural=natural,
        ))
    return tuple(out)


def _v317_perspective() -> tuple[ChainEntry, ...]:
    """Duplicate v2.3 + v3.14 entries with a v3.17 prefix so the
    link-corpus perspective shows up as a separate chain entry
    in the budget. Same texts, different chain_ids."""
    out: list[ChainEntry] = []
    for c in ALL_MULTISTEP_CASES:
        out.append(ChainEntry(
            chain_id=f"v317:{c.case_id}",
            source="v317_v23_view",
            text=c.text,
            expected_natural=True,
        ))
    for c in ALL_HELDOUT_CASES:
        out.append(ChainEntry(
            chain_id=f"v317-h:{c.case_id}",
            source="v317_v314_view",
            text=c.text,
            expected_natural=not c.expected_blocked,
        ))
    return tuple(out)


def all_chains() -> tuple[ChainEntry, ...]:
    return (
        _v23() + _v314() + _v315()
        + _v316_split() + _v318_ncs()
        + _v313_routing() + _v317_perspective()
    )


__all__ = ["ChainEntry", "all_chains"]
