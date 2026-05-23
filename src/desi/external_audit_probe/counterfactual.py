"""Aufgabe 8 — counterfactual probe.

For every failure cluster we propose a *hypothetical* extension
of the relevant v3.16 marker bucket with the surface tokens
observed in the cluster, and measure two numbers:

* ``counterfactual_reduction`` — how many false-support cases in
  the cluster would flip to ``LOGICALLY_REJECTED`` if the token
  were added to the marker bucket,
* ``contamination_risk`` — how many currently-passing benchmark
  cases would *break* (flip from supported to suspended) under
  the same extension.

The probe never patches the runtime; both numbers are measured
by re-applying the (read-only) :func:`_contains_marker`
predicate against the same texts the audit consults, with the
extended marker list.

A cluster is marked UNSAFE if any of its candidate extensions
causes contamination > 0.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..benchmark import ALL_CASES as MAIN_CASES
from ..benchmark_multistep import ALL_MULTISTEP_CASES
from ..heldout_causal import ALL_HELDOUT_CASES
from ..logic.audit import LogicalAuditor, LogicalState
from ..logic.inference import InferenceRule
from .cases import FalseSupportCase
from .classifier import Classification
from .enums import ExternalAuditFailure


# The cluster → relevant v3.16 bucket mapping. Tokens proposed
# from one cluster only extend the corresponding bucket.
_CLUSTER_BUCKET: dict[ExternalAuditFailure, str] = {
    ExternalAuditFailure.HIDDEN_NEGATION:
        "v316_negation_extensions",
    ExternalAuditFailure.QUANTIFIER_DRIFT:
        "v316_quantifier_extensions",
    ExternalAuditFailure.AUTHORITY_CONTAMINATION:
        "v316_authority_like_verbs",
    ExternalAuditFailure.METAPHOR_CONTAMINATION:
        "v316_metaphor_markers",
    ExternalAuditFailure.TOOL_CONTAMINATION:
        "v316_number_words",
    ExternalAuditFailure.CYCLE_DISGUISE:
        "v316_cycle_ref_extensions",
}


def _passing_benchmark_texts() -> tuple[str, ...]:
    """Texts of every benchmark case that currently audits as
    ``LOGICALLY_SUPPORTED`` under any rule. The counterfactual
    contamination check asks: would the candidate token suspend
    one of these?
    """
    auditor = LogicalAuditor()
    out: list[str] = []
    for case in MAIN_CASES:
        a = auditor.audit(case.text)
        if a.state is LogicalState.LOGICALLY_SUPPORTED:
            out.append(case.text)
    for case in ALL_MULTISTEP_CASES:
        a = auditor.audit(case.text)
        if a.state is LogicalState.LOGICALLY_SUPPORTED:
            out.append(case.text)
    for case in ALL_HELDOUT_CASES:
        a = auditor.audit(case.text)
        if a.state is LogicalState.LOGICALLY_SUPPORTED:
            out.append(case.text)
    return tuple(out)


def _normalised(text: str) -> str:
    padded = " " + text.lower() + " "
    for ch in ",.:;!?\"'":
        padded = padded.replace(ch, " ")
    return padded


def _present(token: str, text: str) -> bool:
    return token in _normalised(text)


@dataclass(frozen=True)
class ClusterCounterfactual:
    cluster: str
    bucket: str
    candidate_tokens: tuple[str, ...]
    counterfactual_reduction: int
    contamination_risk: int
    unsafe: bool
    per_token: dict[str, dict[str, int]]

    def to_dict(self) -> dict[str, object]:
        return {
            "cluster": self.cluster,
            "bucket": self.bucket,
            "candidate_tokens": list(self.candidate_tokens),
            "counterfactual_reduction":
                self.counterfactual_reduction,
            "contamination_risk": self.contamination_risk,
            "unsafe": self.unsafe,
            "per_token": dict(self.per_token),
        }


def _cluster_tokens(
    cases: tuple[FalseSupportCase, ...],
    classifications: tuple[Classification, ...],
    cluster: ExternalAuditFailure,
) -> tuple[str, ...]:
    seen: list[str] = []
    case_index = {c.chain_id: c for c in cases}
    for cls in classifications:
        if cls.failure_class != cluster.value:
            continue
        for tok in cls.matched_surface_tokens:
            wrapped = f" {tok.strip()} "
            if wrapped not in seen:
                seen.append(wrapped)
    return tuple(seen)


def evaluate_cluster(
    cluster: ExternalAuditFailure,
    cases: tuple[FalseSupportCase, ...],
    classifications: tuple[Classification, ...],
    benchmark_texts: tuple[str, ...],
) -> ClusterCounterfactual | None:
    if cluster not in _CLUSTER_BUCKET:
        return None
    candidate_tokens = _cluster_tokens(
        cases, classifications, cluster,
    )
    bucket_label = _CLUSTER_BUCKET[cluster]
    cluster_cases = tuple(
        c for c, cls in zip(cases, classifications)
        if cls.failure_class == cluster.value
    )
    per_token: dict[str, dict[str, int]] = {}
    reduction = 0
    contamination = 0
    reduced_ids: set[str] = set()
    contam_texts: set[str] = set()
    for tok in candidate_tokens:
        red = sum(
            1 for c in cluster_cases if _present(tok, c.text)
        )
        contam = sum(
            1 for t in benchmark_texts if _present(tok, t)
        )
        per_token[tok.strip()] = {
            "cases_reduced": red,
            "benchmark_hits": contam,
        }
        for c in cluster_cases:
            if _present(tok, c.text):
                reduced_ids.add(c.chain_id)
        for t in benchmark_texts:
            if _present(tok, t):
                contam_texts.add(t)
    reduction = len(reduced_ids)
    contamination = len(contam_texts)
    return ClusterCounterfactual(
        cluster=cluster.value,
        bucket=bucket_label,
        candidate_tokens=tuple(t.strip() for t in candidate_tokens),
        counterfactual_reduction=reduction,
        contamination_risk=contamination,
        unsafe=(contamination > 0),
        per_token={k: per_token[k] for k in sorted(per_token)},
    )


def evaluate_all(
    cases: tuple[FalseSupportCase, ...],
    classifications: tuple[Classification, ...],
) -> tuple[ClusterCounterfactual, ...]:
    benchmark = _passing_benchmark_texts()
    out: list[ClusterCounterfactual] = []
    for cluster in _CLUSTER_BUCKET:
        result = evaluate_cluster(
            cluster, cases, classifications, benchmark,
        )
        if result is not None:
            out.append(result)
    return tuple(out)


__all__ = [
    "ClusterCounterfactual", "evaluate_all", "evaluate_cluster",
]
