"""Aufgabe 4 — RAW corpus reconstruction.

The v5.2 corpus underwent two waves of conclusion rewrites
during construction:

1. VALID-chain conclusions were rewritten with fresh
   outcome vocabulary so the v5.0 ``MT_OVERLAP_LOOP``
   probe (and via it ``MT_AUDIT_OVER_SUPPORT``) would
   stop firing on legitimate causal language.
2. INVALID-chain conclusions were rewritten to use the
   v5.0 probes' strict vocabulary (``will`` / ``cannot``,
   ``for every X`` / ``across every X``, ``excluded`` /
   ``denied`` / ``withheld``) so the safe-probe hit rate
   would meet the 0.80 threshold.

This module reconstructs the pre-rewrite text (RAW) for
every chain that was edited; chains that were never
rewritten have ``raw_text == final_text``.

The ``RAW_CONCLUSIONS`` table is the audit's ground
truth: each base-chain id maps to the conclusion that
existed *before* the v5.2 edit. The four prefix variants
inherit the same RAW conclusion, so the full RAW corpus
is recovered by substituting the ``Therefore ...`` segment
in each FINAL chain.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..taxonomy_generalization.corpus import (
    GeneralizationChain, all_chains as final_chains,
)


# ---------------------------------------------------------------------------
# RAW conclusions — keyed by base id (chain_id without the
# ``-v{n}`` framing suffix)
# ---------------------------------------------------------------------------


_THEREFORE = "Therefore "


# Each entry: base_id -> raw conclusion sentence (without
# the leading "Therefore" word; we re-prepend on
# substitution).
RAW_CONCLUSIONS: dict[str, str] = {
    # D1 VALID rewrites
    "GEN-1VALID-02":
        "the targeted patch closed the leak within the "
        "observed recovery interval.",
    "GEN-1VALID-03":
        "the covering index reduced query latency in the "
        "next sampling window.",
    "GEN-1VALID-04":
        "the threshold tuning reduced pager noise in the "
        "following on-call period.",
    "GEN-1VALID-05":
        "the shorter TTL eliminated the inconsistent reads "
        "in the monitored window.",
    "GEN-1VALID-06":
        "the circuit breaker limited retry storms during "
        "the validation interval.",
    "GEN-1VALID-07":
        "restoring the pool size returned throughput to "
        "baseline.",
    "GEN-1VALID-08":
        "the disk expansion let the indexer catch up "
        "within the monitored window.",
    "GEN-1VALID-09":
        "the replay drained the queue within the observed "
        "interval.",
    # D2 VALID rewrites
    "GEN-2VALID-04":
        "the plain-error standard followed from the "
        "procedural default in the record.",
    "GEN-2VALID-09":
        "the addendum addressed the prior holding the "
        "dissent cited.",
    # D3 VALID rewrites
    "GEN-3VALID-02":
        "the symptom log triggers the referral mandated "
        "by the protocol.",
    "GEN-3VALID-04":
        "the chart triggers the tapering schedule "
        "described in the guideline.",
    "GEN-3VALID-05":
        "the scheduled imaging conformed to the "
        "protocol's twelve-week window.",
    "GEN-3VALID-08":
        "the documented event meets the protocol's "
        "discontinuation criterion.",
    # D4 VALID rewrites
    "GEN-4VALID-01":
        "the rebuttal addresses the preprocessing "
        "clarification reviewer two requested.",
    "GEN-4VALID-02":
        "the revised table supplies the baseline "
        "reviewer one identified as missing.",
    "GEN-4VALID-03":
        "the appendix table addresses the ablation "
        "reviewer three requested.",
    "GEN-4VALID-04":
        "the definitions answer the metric clarification "
        "reviewer two raised.",
    "GEN-4VALID-05":
        "the comparison table addresses the literature "
        "comparison reviewer one requested.",
    "GEN-4VALID-06":
        "the standard deviations supply the values "
        "reviewer three flagged.",
    "GEN-4VALID-07":
        "the qualification narrows the claim to the "
        "scope reviewer two questioned.",
    "GEN-4VALID-08":
        "the benchmark table provides the timing "
        "reviewer one requested.",
    "GEN-4VALID-09":
        "the appendix matrix addresses the "
        "confusion-matrix request reviewer two raised.",
    # D5 VALID rewrites
    "GEN-5VALID-01":
        "the invocation of dominated convergence is "
        "supported by the verified hypothesis.",
    "GEN-5VALID-02":
        "the lemma supplies the identity the proof "
        "relies on.",
    "GEN-5VALID-03":
        "the inductive step uses a hypothesis the "
        "reviewer has independently verified.",
    "GEN-5VALID-04":
        "the regularity conditions support the appeal "
        "to the uniqueness theorem.",
    "GEN-5VALID-07":
        "the fixed-point argument follows from the "
        "verified continuity.",
    "GEN-5VALID-08":
        "the base case as written supports the "
        "induction from n equals two onward.",
    "GEN-5VALID-09":
        "the mean value theorem applies as the reviewer "
        "has verified.",
    # D1 INVALID rewrites
    "GEN-1INVALID-01":
        "the reviewers concluded that every service "
        "deployed that week must be permanently "
        "rewritten.",
    "GEN-1INVALID-02":
        "the schema migration is conclusively responsible "
        "for every latency regression in the next "
        "quarter.",
    "GEN-1INVALID-03":
        "every alert rule the company ships from now on "
        "will produce no noise at any threshold.",
    "GEN-1INVALID-04":
        "the engineering organisation cannot ever "
        "experience a thread leak again.",
    "GEN-1INVALID-05":
        "the cache layer can be removed from every "
        "service across the platform without "
        "consequence.",
    "GEN-1INVALID-06":
        "the recovery proves the original sizing "
        "decision was a deliberate act of sabotage.",
    "GEN-1INVALID-07":
        "the operations team's storage strategy was the "
        "singular cause of every incident logged that "
        "quarter.",
    "GEN-1INVALID-08":
        "the addition proves the team's earlier risk "
        "assessment was uniformly negligent.",
    "GEN-1INVALID-09":
        "the engineering organisation is conclusively "
        "shown to lack competence in scheduler design.",
    # D2 INVALID rewrites
    "GEN-2INVALID-01":
        "every evidentiary ruling in every future case "
        "must be reviewed under the same standard.",
    "GEN-2INVALID-02":
        "every remand in the jurisdiction's history is "
        "now retroactively vacated.",
    "GEN-2INVALID-03":
        "the trial counsel is conclusively shown to "
        "have committed malpractice.",
    "GEN-2INVALID-04":
        "every prior decision interpreting that term is "
        "overruled by operation of law.",
    "GEN-2INVALID-05":
        "every party in every case is entitled to oral "
        "argument on demand.",
    "GEN-2INVALID-06":
        "counsel must have engaged in improper ex parte "
        "contact.",
    "GEN-2INVALID-07":
        "the entire docket of the lower court must be "
        "reviewed for record integrity.",
    "GEN-2INVALID-08":
        "every party that raises a constitutional issue "
        "obtains de novo review of every other claim.",
    "GEN-2INVALID-09":
        "every dissenting citation must trigger an "
        "addendum from every majority opinion in every "
        "court.",
    # D3 INVALID rewrites
    "GEN-3INVALID-01":
        "every patient on the cohort will respond "
        "identically to therapy.",
    "GEN-3INVALID-02":
        "every clinic in the network will benefit from "
        "doubling its referral capacity.",
    "GEN-3INVALID-03":
        "the intake form is conclusively shown to "
        "capture every relevant adverse reaction "
        "history in the population.",
    "GEN-3INVALID-04":
        "every adjustment in clinical practice must "
        "follow the same four-week tapering window.",
    "GEN-3INVALID-05":
        "the imaging suite must double its capacity to "
        "accommodate every patient on the guideline.",
    "GEN-3INVALID-06":
        "the laboratory's testing volume must increase "
        "across every department.",
    "GEN-3INVALID-07":
        "the agent is uniformly safe across the patient "
        "population and the contraindication list may "
        "be retired.",
    "GEN-3INVALID-08":
        "the agent is conclusively unsafe and must be "
        "withdrawn from every market in the region.",
    "GEN-3INVALID-09":
        "every patient on the agent must immediately "
        "have their dose halved regardless of clearance.",
    # D4 INVALID rewrites
    "GEN-4INVALID-01":
        "every reviewer of every future submission will "
        "find every preprocessing description "
        "sufficient.",
    "GEN-4INVALID-02":
        "the field is conclusively shown to have "
        "neglected baselines as a category for the past "
        "decade.",
    "GEN-4INVALID-03":
        "every paper without ablations must be retracted.",
    "GEN-4INVALID-04":
        "every metric debate in the literature is "
        "settled by the definitions.",
    "GEN-4INVALID-05":
        "the authors' approach is conclusively superior "
        "to every cited prior work in every downstream "
        "task.",
    "GEN-4INVALID-06":
        "the results are now beyond all possible "
        "methodological critique.",
    "GEN-4INVALID-07":
        "the qualification proves that all prior "
        "unqualified claims in the field were "
        "intentionally misleading.",
    "GEN-4INVALID-08":
        "the approach is faster than every method in "
        "every deployment environment.",
    "GEN-4INVALID-09":
        "every future submission must include a "
        "confusion matrix at every reported split "
        "without exception.",
    # D5 INVALID rewrites
    "GEN-5INVALID-01":
        "every interchange of limit and integral in the "
        "wider literature is automatically justified by "
        "the same bound.",
    "GEN-5INVALID-02":
        "every prior lemma in the journal can be reused "
        "without re-verification.",
    "GEN-5INVALID-03":
        "every induction in the field can be replaced "
        "by a single strict-inequality step.",
    "GEN-5INVALID-04":
        "the uniqueness theorem holds in every related "
        "setting regardless of regularity.",
    "GEN-5INVALID-05":
        "every series substitution in the next chapter "
        "is unconditionally valid.",
    "GEN-5INVALID-06":
        "the interchange of integrals holds on every "
        "measure space regardless of finiteness.",
    "GEN-5INVALID-07":
        "every fixed-point claim in the field follows "
        "without further verification.",
    "GEN-5INVALID-08":
        "every induction in the literature can omit "
        "base verification.",
    "GEN-5INVALID-09":
        "every differentiability claim in the "
        "literature follows without further "
        "verification.",
}


def _base_id(chain_id: str) -> str:
    """Strip the framing suffix (``-v{n}``) so the four
    prefix variants share a RAW conclusion."""
    return chain_id.rsplit("-v", 1)[0]


@dataclass(frozen=True)
class ChainPair:
    chain_id: str
    domain: str
    ground_truth: str
    raw_text: str
    final_text: str
    was_rewritten: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "chain_id": self.chain_id,
            "domain": self.domain,
            "ground_truth": self.ground_truth,
            "was_rewritten": self.was_rewritten,
        }


def _swap_conclusion(text: str, raw_concl: str) -> str:
    """Replace the post-``Therefore`` segment of ``text``
    with ``raw_concl``."""
    idx = text.find(_THEREFORE)
    if idx < 0:
        return text  # degenerate, shouldn't happen
    return text[:idx] + _THEREFORE + raw_concl


def reconstruct_pair(
    chain: GeneralizationChain,
) -> ChainPair:
    base = _base_id(chain.chain_id)
    raw_concl = RAW_CONCLUSIONS.get(base)
    if raw_concl is None:
        return ChainPair(
            chain_id=chain.chain_id, domain=chain.domain,
            ground_truth=chain.ground_truth,
            raw_text=chain.text, final_text=chain.text,
            was_rewritten=False,
        )
    raw_text = _swap_conclusion(chain.text, raw_concl)
    return ChainPair(
        chain_id=chain.chain_id, domain=chain.domain,
        ground_truth=chain.ground_truth,
        raw_text=raw_text, final_text=chain.text,
        was_rewritten=True,
    )


def all_pairs() -> tuple[ChainPair, ...]:
    return tuple(
        reconstruct_pair(c) for c in final_chains()
    )


def raw_recovery_rate() -> float:
    """Aufgabe 4 — fraction of FINAL chains for which a
    RAW reconstruction exists (always 1.0: rewritten
    chains map back to their pre-edit conclusion;
    untouched chains map to themselves)."""
    pairs = all_pairs()
    recovered = sum(1 for p in pairs if p.raw_text)
    return round(recovered / len(pairs), 6) if pairs else 0.0


def raw_chains() -> tuple[GeneralizationChain, ...]:
    """Return v5.2 chains with conclusions replaced by
    their RAW pre-edit versions. Schema is otherwise
    identical to the v5.2 corpus."""
    return tuple(
        GeneralizationChain(
            chain_id=c.chain_id, domain=c.domain,
            text=reconstruct_pair(c).raw_text,
            ground_truth=c.ground_truth,
            rationale=c.rationale,
        )
        for c in final_chains()
    )


__all__ = [
    "ChainPair", "RAW_CONCLUSIONS", "all_pairs",
    "raw_chains", "raw_recovery_rate", "reconstruct_pair",
]
