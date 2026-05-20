"""Patchability + contamination probe — Aufgaben 5 + 6.

For each cluster the audit produces a hypothetical patch fingerprint
(the closed set of *content tokens* shared by every member, modulo
explicit Frame markers and trivial words). Contamination probe asks:
**would adding those tokens to the v3.4 detector affect any case
from the protected benchmarks?**
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..benchmark import ALL_CASES as MAIN_CASES
from ..benchmark_multistep import ALL_MULTISTEP_CASES
from ..frame_benchmark import ALL_FRAME_CASES
from ..tools.benchmark import ALL_TOOL_CASES
from .clusters import FailureCluster
from .extractor import FrameFailureRecord


# Closed list of trivial tokens we ignore when extracting "shared
# tokens" — stopwords, punctuation, and v3.4 marker fragments.
_STOPWORDS: frozenset[str] = frozenset({
    "the", "a", "an", "and", "or", "but", "is", "are", "was", "were",
    "be", "been", "being", "of", "in", "on", "at", "to", "for",
    "with", "by", "from", "as", "than", "then", "if", "while",
    "this", "that", "these", "those", "it", "they",
    "frame:", "frame", "thermodynamic", "information-theoretic",
    "information", "theoretic", "ontological", "distinguishability",
    "metaphorical", "formal", "logic", "empirical", "causal",
    "authority", "tool", "computable", "undeclared",
})


def _content_tokens(text: str) -> set[str]:
    s = text.lower()
    for ch in ",.;:!?\"'`":
        s = s.replace(ch, " ")
    out: set[str] = set()
    for tok in s.split():
        if tok in _STOPWORDS:
            continue
        if len(tok) < 3:
            continue
        out.add(tok)
    return out


def _shared_tokens(records: list[FrameFailureRecord]) -> tuple[str, ...]:
    if not records:
        return ()
    common = _content_tokens(records[0].text)
    for r in records[1:]:
        common &= _content_tokens(r.text)
    return tuple(sorted(common))


# Protected text pools per benchmark — used by the contamination
# probe to count how many cases a hypothetical patch would touch.
def _benchmark_text_pools() -> dict[str, tuple[str, ...]]:
    return {
        "v1_5_main": tuple(c.text for c in MAIN_CASES),
        "v1_9_tools": tuple(c.text for c in ALL_TOOL_CASES),
        "v2_3_multistep": tuple(c.text for c in ALL_MULTISTEP_CASES),
        "v3_4_frame": tuple(c.text for c in ALL_FRAME_CASES),
    }


# v2.7 causal_chain regression cases live as R2 + R3 subsets of v2.3 +
# the rule fires only on linear chains; we re-use the v2.3 multistep
# texts for the v2.7 contamination probe.
def _causal_chain_text_pool() -> tuple[str, ...]:
    return tuple(
        c.text for c in ALL_MULTISTEP_CASES
        if c.category.value.startswith("R2") or c.category.value.startswith("R3")
    )


@dataclass(frozen=True)
class ContaminationProbe:
    cluster_id: str
    candidate_tokens: tuple[str, ...]
    per_benchmark_hits: dict[str, int]
    contamination_risk: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "cluster_id": self.cluster_id,
            "candidate_tokens": list(self.candidate_tokens),
            "per_benchmark_hits": dict(self.per_benchmark_hits),
            "contamination_risk": self.contamination_risk,
        }


@dataclass(frozen=True)
class PatchabilityVerdict:
    cluster_id: str
    safe_patch_candidate: bool
    reason: str
    contamination: ContaminationProbe

    def to_dict(self) -> dict[str, Any]:
        return {
            "cluster_id": self.cluster_id,
            "safe_patch_candidate": self.safe_patch_candidate,
            "reason": self.reason,
            "contamination": self.contamination.to_dict(),
        }


def probe_contamination(
    cluster: FailureCluster,
    failures: tuple[FrameFailureRecord, ...],
) -> ContaminationProbe:
    members = [f for f in failures if f.case_id in set(cluster.members)]
    tokens = _shared_tokens(members)
    pools = _benchmark_text_pools()
    pools["v2_7_causal_chain"] = _causal_chain_text_pool()

    per_hits: dict[str, int] = {}
    total = 0
    for name, texts in sorted(pools.items()):
        # A benchmark text is "touched" iff the full token set
        # appears (as substrings) inside it. We require ALL
        # candidate tokens to be present so the probe is
        # conservative.
        hits = 0
        for t in texts:
            low = t.lower()
            if tokens and all(tok in low for tok in tokens):
                hits += 1
        per_hits[name] = hits
        total += hits

    # contamination_risk = hits / sum_of_pool_sizes — a strict
    # zero is the only safe value the directive accepts.
    total_pool = sum(len(v) for v in pools.values())
    risk = round(total / total_pool, 6) if total_pool > 0 else 0.0
    return ContaminationProbe(
        cluster_id=cluster.cluster_id,
        candidate_tokens=tokens,
        per_benchmark_hits=per_hits,
        contamination_risk=risk,
    )


def assess_patchability(
    cluster: FailureCluster,
    failures: tuple[FrameFailureRecord, ...],
) -> PatchabilityVerdict:
    probe = probe_contamination(cluster, failures)
    members = [f for f in failures if f.case_id in set(cluster.members)]
    same_class = all(
        f.failure_type is members[0].failure_type for f in members[1:]
    )
    same_lex = bool(probe.candidate_tokens)
    if cluster.size < 3:
        return PatchabilityVerdict(
            cluster_id=cluster.cluster_id,
            safe_patch_candidate=False,
            reason=f"cluster size {cluster.size} < 3",
            contamination=probe,
        )
    if not same_class:
        return PatchabilityVerdict(
            cluster_id=cluster.cluster_id,
            safe_patch_candidate=False,
            reason="members do not share a single failure class",
            contamination=probe,
        )
    if not same_lex:
        return PatchabilityVerdict(
            cluster_id=cluster.cluster_id,
            safe_patch_candidate=False,
            reason="members share no content tokens",
            contamination=probe,
        )
    if probe.contamination_risk > 0:
        return PatchabilityVerdict(
            cluster_id=cluster.cluster_id,
            safe_patch_candidate=False,
            reason=(
                f"contamination_risk = {probe.contamination_risk}"
            ),
            contamination=probe,
        )
    return PatchabilityVerdict(
        cluster_id=cluster.cluster_id,
        safe_patch_candidate=True,
        reason="size>=3 + same class + shared tokens + zero contamination",
        contamination=probe,
    )


__all__ = [
    "ContaminationProbe",
    "PatchabilityVerdict",
    "assess_patchability",
    "probe_contamination",
]
