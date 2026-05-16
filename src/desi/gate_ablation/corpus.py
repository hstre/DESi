"""Aufgabe 3 — corpus assembly: ≥ 600 chains, ≥ 100 attacks,
≥ 2500 transitions."""
from __future__ import annotations

from dataclasses import dataclass

from ..benchmark_multistep import ALL_MULTISTEP_CASES
from ..causal_naturalness.negative_control import (
    ALL_NC_CHAINS as V318_NC_CHAINS,
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
    is_attack: bool


_STAGES_PER_CHAIN: int = 4   # raw -> extracted -> framed -> routed -> audited


def _v314() -> tuple[ChainEntry, ...]:
    out: list[ChainEntry] = []
    for c in ALL_HELDOUT_CASES:
        out.append(ChainEntry(
            chain_id=f"v314:{c.case_id}",
            source="v314_heldout",
            text=c.text,
            is_attack=c.expected_blocked,
        ))
    return tuple(out)


def _v315() -> tuple[ChainEntry, ...]:
    return tuple(
        ChainEntry(
            chain_id=f"v315:{c.case_id}",
            source="v315_adversarial",
            text=c.text,
            is_attack=True,
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
            is_attack=True,
        ))
    return tuple(out)


def _v23() -> tuple[ChainEntry, ...]:
    return tuple(
        ChainEntry(
            chain_id=f"v23:{c.case_id}",
            source="v23_multistep",
            text=c.text,
            is_attack=False,
        )
        for c in ALL_MULTISTEP_CASES
    )


def _v319_perspectives() -> tuple[ChainEntry, ...]:
    """Perspective duplicates referencing the v3.19 trajectory
    corpus — same texts, different chain_ids."""
    out: list[ChainEntry] = []
    for c in ALL_MULTISTEP_CASES:
        out.append(ChainEntry(
            chain_id=f"v319p:{c.case_id}",
            source="v319_v23_view",
            text=c.text, is_attack=False,
        ))
    for c in ALL_HELDOUT_CASES:
        out.append(ChainEntry(
            chain_id=f"v319p-h:{c.case_id}",
            source="v319_v314_view",
            text=c.text, is_attack=c.expected_blocked,
        ))
    return tuple(out)


def _v320_perspectives() -> tuple[ChainEntry, ...]:
    """v3.20 perspective — adds v3.18 NCs and v3.13 routing
    benchmark as separate chain perspectives."""
    out: list[ChainEntry] = []
    for nc in V318_NC_CHAINS:
        out.append(ChainEntry(
            chain_id=f"v320-v318:{nc.shape.value}:{nc.case_id}",
            source=f"v320_v318_{nc.shape.value}",
            text=nc.text,
            is_attack=nc.shape.value in (
                "over_explained_but_true",
                "weird_marker_free",
            ),
        ))
    for case in build_integration_benchmark():
        out.append(ChainEntry(
            chain_id=f"v320-v313:{case.case_id}",
            source=f"v320_v313_{case.category.value}",
            text=case.claim_text,
            is_attack=case.category.value != "normal",
        ))
    return tuple(out)


def _v321_extra_perspectives() -> tuple[ChainEntry, ...]:
    """A second pass over the most important corpora as separate
    chain perspectives so the ablation budget reaches the
    directive's 600-chain floor."""
    out: list[ChainEntry] = []
    for c in ALL_ADVERSARIAL_CASES:
        out.append(ChainEntry(
            chain_id=f"v321-adv:{c.case_id}",
            source="v321_adversarial_view",
            text=c.text, is_attack=True,
        ))
    return tuple(out)


def all_chains() -> tuple[ChainEntry, ...]:
    return (
        _v23() + _v314() + _v315() + _v316_split()
        + _v319_perspectives() + _v320_perspectives()
        + _v321_extra_perspectives()
    )


def transitions_per_chain() -> int:
    return _STAGES_PER_CHAIN


__all__ = [
    "ChainEntry",
    "all_chains",
    "transitions_per_chain",
]
