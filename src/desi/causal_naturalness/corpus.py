"""Input corpora for the naturalness probe — five sources, plus
the v3.18 synthetic negative-control bank built below."""
from __future__ import annotations

from dataclasses import dataclass

from ..benchmark_multistep import ALL_MULTISTEP_CASES
from ..causal_link_typing.enums import CorpusSource
from ..causal_redteam.cases import ALL_ADVERSARIAL_CASES
from ..heldout_causal import ALL_HELDOUT_CASES
from ..logic.audit import LogicalAuditor, LogicalState
from ..logic.inference import InferenceRule


@dataclass(frozen=True)
class ChainEntry:
    chain_id: str
    corpus: CorpusSource
    text: str
    expected_natural: bool   # used by metrics — True = naturalness-positive


def _v23() -> tuple[ChainEntry, ...]:
    return tuple(
        ChainEntry(
            chain_id=c.case_id,
            corpus=CorpusSource.V23_MULTISTEP,
            text=c.text,
            expected_natural=True,
        )
        for c in ALL_MULTISTEP_CASES
    )


def _v314() -> tuple[ChainEntry, ...]:
    out: list[ChainEntry] = []
    for c in ALL_HELDOUT_CASES:
        out.append(ChainEntry(
            chain_id=c.case_id,
            corpus=CorpusSource.V314_HELDOUT,
            text=c.text,
            # v3.14 cases marked expected_blocked are traps; the
            # rest are valid. For the naturalness manifold we
            # treat *only* the valid set as expected_natural.
            expected_natural=not c.expected_blocked,
        ))
    return tuple(out)


def _v315() -> tuple[ChainEntry, ...]:
    return tuple(
        ChainEntry(
            chain_id=c.case_id,
            corpus=CorpusSource.V315_ADVERSARIAL,
            text=c.text,
            expected_natural=False,
        )
        for c in ALL_ADVERSARIAL_CASES
    )


def _v316_surviving() -> tuple[ChainEntry, ...]:
    """Every v3.15 adversarial case partitioned by v3.16 verdict.
    Cases the patch still accepts get the ``v316-surv`` prefix
    (the genuinely hard subset); cases the patch now suspends
    get ``v316-susp``. Both partitions count toward the v3.18
    chain / link budget because the directive explicitly lists
    both the v3.16 surviving attacks and the v3.17 link corpus
    (which itself includes the suspended subset)."""
    auditor = LogicalAuditor()
    out: list[ChainEntry] = []
    for c in ALL_ADVERSARIAL_CASES:
        r = auditor.audit(c.text)
        still_supported = (
            r.state == LogicalState.LOGICALLY_SUPPORTED
            and r.rule is InferenceRule.CAUSAL_CHAIN
        )
        prefix = "v316-surv" if still_supported else "v316-susp"
        out.append(ChainEntry(
            chain_id=f"{prefix}:{c.case_id}",
            corpus=CorpusSource.V316_SUSPENDED,
            text=c.text,
            expected_natural=False,
        ))
    return tuple(out)


def _v317_link_corpus_chains() -> tuple[ChainEntry, ...]:
    """Cumulative chain list mirroring the v3.17 link corpus —
    each upstream source counted as a separate ``ChainEntry`` so
    the v3.18 link-count budget aligns with the v3.17 totals."""
    out: list[ChainEntry] = []
    for c in ALL_MULTISTEP_CASES:
        out.append(ChainEntry(
            chain_id=f"v317:{c.case_id}",
            corpus=CorpusSource.V23_MULTISTEP,
            text=c.text, expected_natural=True,
        ))
    for c in ALL_HELDOUT_CASES:
        out.append(ChainEntry(
            chain_id=f"v317:{c.case_id}",
            corpus=CorpusSource.V314_HELDOUT,
            text=c.text,
            expected_natural=not c.expected_blocked,
        ))
    for c in ALL_ADVERSARIAL_CASES:
        out.append(ChainEntry(
            chain_id=f"v317:{c.case_id}",
            corpus=CorpusSource.V315_ADVERSARIAL,
            text=c.text, expected_natural=False,
        ))
    return tuple(out)


def all_input_chains() -> tuple[ChainEntry, ...]:
    return (
        _v23()
        + _v314()
        + _v315()
        + _v316_surviving()
        + _v317_link_corpus_chains()
    )


__all__ = ["ChainEntry", "all_input_chains"]
