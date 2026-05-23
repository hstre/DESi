"""Aufgabe 8 — token-level contamination check against every
protected benchmark text.

Protected pool excludes the 143 v4.0 false-support cases (those
are the chains we *want* the patch to flip). It includes:

* v1.5 main benchmark texts
* v2.3 multistep texts
* v3.14 held-out causal texts
* v3.15 adversarial cases
* v3.16 suspension benchmark cases
* every VALID-labeled chain in the v4.0 external corpus

A token is unsafe iff it appears in any protected text that
currently audits as ``LOGICALLY_SUPPORTED`` — flipping it
would create a false negative on existing infrastructure.

Contamination requirement (Aufgabe 8):
``contamination_count == 0`` overall.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..benchmark import ALL_CASES as MAIN_CASES
from ..benchmark_multistep import ALL_MULTISTEP_CASES
from ..causal_redteam.cases import ALL_ADVERSARIAL_CASES
from ..external_probe.corpus import all_chains
from ..external_probe.enums import GroundTruth
from ..frame_benchmark import ALL_FRAME_CASES
from ..heldout_causal import ALL_HELDOUT_CASES
from ..logic.audit import LogicalAuditor, LogicalState
from .extensions import all_extensions


def _normalised(text: str) -> str:
    padded = " " + text.lower() + " "
    for ch in ",.:;!?\"'":
        padded = padded.replace(ch, " ")
    return padded


def _protected_texts() -> tuple[str, ...]:
    # Lazy import to keep this module standalone for tests.
    from ..external_audit_probe import collect_false_support_cases

    fs_texts = {c.text for c in collect_false_support_cases()}
    pool: list[str] = []
    for c in MAIN_CASES:
        pool.append(c.text)
    for c in ALL_MULTISTEP_CASES:
        pool.append(c.text)
    for c in ALL_HELDOUT_CASES:
        pool.append(c.text)
    for c in ALL_ADVERSARIAL_CASES:
        pool.append(c.text)
    for c in ALL_FRAME_CASES:
        pool.append(c.text)
    for c in all_chains():
        if c.ground_truth is GroundTruth.VALID:
            pool.append(c.text)
    auditor = LogicalAuditor()
    out: list[str] = []
    for t in pool:
        if t in fs_texts:
            continue
        a = auditor.audit(t)
        if a.state is LogicalState.LOGICALLY_SUPPORTED:
            out.append(t)
    return tuple(out)


@dataclass(frozen=True)
class TokenContamination:
    cluster: str
    token: str
    hits: int

    def to_dict(self) -> dict[str, object]:
        return {
            "cluster": self.cluster,
            "token": self.token,
            "hits": self.hits,
        }


@dataclass(frozen=True)
class ContaminationReport:
    protected_pool_size: int
    per_token: tuple[TokenContamination, ...]
    total_contamination: int

    def to_dict(self) -> dict[str, object]:
        return {
            "protected_pool_size": self.protected_pool_size,
            "per_token": [t.to_dict() for t in self.per_token],
            "total_contamination": self.total_contamination,
        }


def check() -> ContaminationReport:
    """Run the contamination scan across every v4.3 marker."""
    protected = _protected_texts()
    normed = [_normalised(t) for t in protected]
    per_token: list[TokenContamination] = []
    total = 0
    for cluster, tokens in all_extensions().items():
        for tok in tokens:
            hits = sum(1 for n in normed if tok in n)
            per_token.append(TokenContamination(
                cluster=cluster, token=tok.strip(), hits=hits,
            ))
            total += hits
    return ContaminationReport(
        protected_pool_size=len(protected),
        per_token=tuple(per_token),
        total_contamination=total,
    )


__all__ = [
    "ContaminationReport",
    "TokenContamination",
    "check",
]
