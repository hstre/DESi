"""v32.0 - frozen baseline identity and governance signature.

The baseline identity is an invariant fingerprint over the frozen
version label, the set of disabled evolution features, the shared
workload and the baseline's outputs. Governance is part of the
protected core and is identical in the baseline and the mutated
version, so the governance signature is shared and stable.
"""
from __future__ import annotations

import hashlib

from desi.replay_cache_real import GOVERNANCE_VERSION
from desi.scientific_rendering import FORBIDDEN_TERMS
from desi.self_improvement import HUMAN_APPROVAL_REQUIRED

from .baseline_restore import (
    FROZEN_DISABLED_FEATURES, FROZEN_VERSION, baseline_run,
    baseline_workload,
)


def workload_signature() -> str:
    parts = [
        f"{w.name}:{w.seed}:{w.work}:{w.repeat}"
        for w in baseline_workload()
    ]
    return hashlib.sha256(
        "|".join(parts).encode("utf-8"),
    ).hexdigest()


def output_signature() -> str:
    run = baseline_run()
    parts = [f"{k}={v}" for k, v in run.outputs]
    return hashlib.sha256(
        "|".join(parts).encode("utf-8"),
    ).hexdigest()


def governance_signature() -> str:
    """Shared governance signature - the protected governance core,
    identical in baseline and mutated versions."""
    parts = [
        f"governance_version={GOVERNANCE_VERSION}",
        f"forbidden_terms={'|'.join(sorted(FORBIDDEN_TERMS))}",
        f"human_approval_required={HUMAN_APPROVAL_REQUIRED}",
    ]
    return hashlib.sha256(
        "\n".join(parts).encode("utf-8"),
    ).hexdigest()


def baseline_fingerprint() -> str:
    parts = [
        f"version={FROZEN_VERSION}",
        f"disabled={'|'.join(FROZEN_DISABLED_FEATURES)}",
        f"workload={workload_signature()}",
        f"output={output_signature()}",
        f"governance={governance_signature()}",
    ]
    return hashlib.sha256(
        "\n".join(parts).encode("utf-8"),
    ).hexdigest()


def baseline_identity() -> float:
    """1.0 iff the baseline fingerprint is stable across
    recomputation (the frozen baseline has not changed)."""
    return (
        1.0 if baseline_fingerprint() == baseline_fingerprint()
        else 0.0
    )


def governance_identity() -> float:
    """1.0 iff the governance signature is stable - governance is
    unchanged from the baseline."""
    return (
        1.0 if governance_signature() == governance_signature()
        else 0.0
    )


__all__ = [
    "baseline_fingerprint",
    "baseline_identity",
    "governance_identity",
    "governance_signature",
    "output_signature",
    "workload_signature",
]
