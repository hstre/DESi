"""Aufgabe 5 — hypothetical-rule contamination probe.

Models a hypothetical CAUSAL_CHAIN restriction that accepts a
chain only if **every** link is in ``ALLOWED_LINK_TYPES``. Then
counts:

* how many v2.3 chains remain valid
* how many v3.14 chains remain valid (used as recall floor)
* how many v3.15 attacks still slip through (false-positive
  contamination — must be 0 for a recommendation)
"""
from __future__ import annotations

from dataclasses import dataclass

from .classifier import classify_link
from .enums import CorpusSource, LinkType
from .extractor import Link, per_corpus_links


ALLOWED_LINK_TYPES: frozenset[LinkType] = frozenset({
    LinkType.PHYSICAL_CAUSAL,
    LinkType.INSTITUTIONAL_CAUSAL,
    LinkType.LOGICAL_IMPLICATION,
})


def _chains_from_links(links: tuple[Link, ...]) -> dict[str, list[Link]]:
    out: dict[str, list[Link]] = {}
    for l in links:
        out.setdefault(l.chain_id, []).append(l)
    for k in out:
        out[k].sort(key=lambda x: x.index)
    return out


@dataclass(frozen=True)
class CorpusOutcome:
    corpus: str
    chain_count: int
    chains_all_allowed: int
    chains_any_disallowed: int

    @property
    def survival_rate(self) -> float:
        return (
            round(self.chains_all_allowed / self.chain_count, 6)
            if self.chain_count else 0.0
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "corpus": self.corpus,
            "chain_count": self.chain_count,
            "chains_all_allowed": self.chains_all_allowed,
            "chains_any_disallowed": self.chains_any_disallowed,
            "survival_rate": self.survival_rate,
        }


@dataclass(frozen=True)
class ContaminationReport:
    allowed_link_types: tuple[str, ...]
    per_corpus: dict[str, CorpusOutcome]
    contamination_count: int           # v3.15 chains that slip through
    contamination_rate: float
    v23_survival_rate: float           # baseline preservation
    v314_survival_rate: float          # heldout_recall under hypothetical
    v315_attack_reduction: float

    def to_dict(self) -> dict[str, object]:
        return {
            "allowed_link_types": list(self.allowed_link_types),
            "per_corpus": {
                k: v.to_dict() for k, v in self.per_corpus.items()
            },
            "contamination_count": self.contamination_count,
            "contamination_rate": self.contamination_rate,
            "v23_survival_rate": self.v23_survival_rate,
            "v314_survival_rate": self.v314_survival_rate,
            "v315_attack_reduction": self.v315_attack_reduction,
        }


def _evaluate_corpus(corpus_name: str,
                     links: tuple[Link, ...]) -> CorpusOutcome:
    chains = _chains_from_links(links)
    all_allowed = 0
    any_disallowed = 0
    for chain_links in chains.values():
        types = {classify_link(l) for l in chain_links}
        if types.issubset(ALLOWED_LINK_TYPES):
            all_allowed += 1
        else:
            any_disallowed += 1
    return CorpusOutcome(
        corpus=corpus_name,
        chain_count=len(chains),
        chains_all_allowed=all_allowed,
        chains_any_disallowed=any_disallowed,
    )


def run_contamination_probe() -> ContaminationReport:
    per = per_corpus_links()
    outcomes: dict[str, CorpusOutcome] = {}
    for name, links in per.items():
        outcomes[name] = _evaluate_corpus(name, links)

    v23 = outcomes[CorpusSource.V23_MULTISTEP.value]
    v314 = outcomes[CorpusSource.V314_HELDOUT.value]
    v315 = outcomes[CorpusSource.V315_ADVERSARIAL.value]

    # Under the hypothetical rule a v3.15 attack is "contamination"
    # iff every link in it falls within ALLOWED_LINK_TYPES — the
    # rule would still let it through.
    contamination_count = v315.chains_all_allowed
    contamination_rate = (
        round(contamination_count / v315.chain_count, 6)
        if v315.chain_count else 0.0
    )
    v315_attack_reduction = round(
        1.0 - contamination_rate, 6,
    )

    return ContaminationReport(
        allowed_link_types=tuple(
            t.value for t in sorted(ALLOWED_LINK_TYPES, key=lambda x: x.value)
        ),
        per_corpus=outcomes,
        contamination_count=contamination_count,
        contamination_rate=contamination_rate,
        v23_survival_rate=v23.survival_rate,
        v314_survival_rate=v314.survival_rate,
        v315_attack_reduction=v315_attack_reduction,
    )


__all__ = [
    "ALLOWED_LINK_TYPES",
    "ContaminationReport",
    "CorpusOutcome",
    "run_contamination_probe",
]
