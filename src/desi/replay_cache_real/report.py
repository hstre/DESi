"""v29.1 - Real Replay Cache Branch report.

Pflichtmetriken (directive § v29.1):

* runtime_reduction
* artifact_hash_stability
* stale_state_rejection
* governance_preservation
* replay_stability

Killerfrage: "Kann DESi reale Infrastrukturverbesserungen
durchfuehren ohne epistemischen Drift zu erzeugen?"

The cache turns the baseline's repeated rebuilds into one
recompute per distinct workload (a real, measured reduction in
recompute operations) while every output hash stays
byte-identical, governance is untouched and stale keys are
rejected. Branch-isolated; nothing is merged.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from desi.scientific_rendering import FORBIDDEN_TERMS
from desi.replay_cache_evolution import (
    baseline_recompute_count, output_hashes as baseline_hashes,
)

from .cache_keys import GOVERNANCE_VERSION
from .memoization import (
    cached_output_hashes, cached_recompute_count, cached_run,
)
from .render_cache import render_reuse_demo, render_reuse_is_exact
from .replay_cache import stale_state_rejection

VERDICT_REAL = "REAL_CACHE_NO_DRIFT"
VERDICT_DRIFT = "CACHE_INTRODUCES_DRIFT"
VERDICT_HALT = "CACHE_DRIFT_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_REAL, VERDICT_DRIFT, VERDICT_HALT,
)

_REDUCTION_FLOOR = 0.20


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def runtime_reduction() -> float:
    """Measured reduction in recompute operations (cache misses)
    versus the baseline, in [0, 1]. Deterministic and real."""
    base = baseline_recompute_count()
    if base == 0:
        return 0.0
    cached = cached_recompute_count()
    return _round((base - cached) / base)


def artifact_hash_stability() -> float:
    """Fraction of workloads whose cached output hash equals the
    baseline (uncached) hash, in [0, 1]."""
    base = baseline_hashes()
    cached = cached_output_hashes()
    if not base:
        return 0.0
    same = sum(
        1 for k, v in base.items() if cached.get(k) == v
    )
    return _round(same / len(base))


def _governance_fingerprint() -> str:
    parts = list(sorted(FORBIDDEN_TERMS)) + [GOVERNANCE_VERSION]
    return hashlib.sha256(
        "\n".join(parts).encode("utf-8"),
    ).hexdigest()


def governance_preservation() -> float:
    """1.0 iff the governance fingerprint is unchanged by running
    the cache (the cache touches no governance)."""
    before = _governance_fingerprint()
    cached_run()  # exercise the cache
    after = _governance_fingerprint()
    return 1.0 if before == after else 0.0


def replay_stability() -> float:
    a = cached_output_hashes()
    b = cached_output_hashes()
    if a != b:
        return 0.0
    # cached output must equal baseline output (no drift)
    return 1.0 if a == baseline_hashes() else 0.0


def _signature() -> str:
    parts = [
        f"{k}={v}"
        for k, v in sorted(cached_output_hashes().items())
    ]
    parts.append(f"reduction={runtime_reduction()}")
    return hashlib.sha256(
        "\n".join(parts).encode("utf-8"),
    ).hexdigest()


def _recommendation(
    *, replay: float, reduction: float, hashes: float,
    stale: float, governance: float,
) -> str:
    if replay < 1.0:
        return VERDICT_HALT
    if (
        hashes < 1.0
        or governance < 1.0
        or stale < 1.0
    ):
        return VERDICT_DRIFT
    if reduction < _REDUCTION_FLOOR:
        return VERDICT_HALT
    return VERDICT_REAL


@dataclass(frozen=True)
class V291Report:
    baseline_recompute_count: int
    cached_recompute_count: int
    runtime_reduction: float
    artifact_hash_stability: float
    stale_state_rejection: float
    governance_preservation: float
    replay_stability: float
    render_reuse_exact: bool
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "baseline_recompute_count":
                self.baseline_recompute_count,
            "cached_recompute_count": self.cached_recompute_count,
            "runtime_reduction": self.runtime_reduction,
            "artifact_hash_stability": self.artifact_hash_stability,
            "stale_state_rejection": self.stale_state_rejection,
            "governance_preservation":
                self.governance_preservation,
            "replay_stability": self.replay_stability,
            "render_reuse_exact": self.render_reuse_exact,
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def build_report() -> V291Report:
    reduction = runtime_reduction()
    hashes = artifact_hash_stability()
    stale = stale_state_rejection()
    governance = governance_preservation()
    replay = replay_stability()
    halt = replay < 1.0
    render_counter, _ = render_reuse_demo()
    verdict = _recommendation(
        replay=replay, reduction=reduction, hashes=hashes,
        stale=stale, governance=governance,
    )
    rationale = (
        f"INFO: baseline {baseline_recompute_count()} recomputes "
        f"-> cached {cached_recompute_count()} recomputes (one "
        f"per distinct workload)",
        "INFO: deterministic memoization with replay-bound keys; "
        "no hidden mutable state, no artifact rewriting; "
        "branch-isolated, nothing merged",
        f"{'PASS' if reduction >= _REDUCTION_FLOOR else 'FAIL'}: "
        f"runtime_reduction {reduction} >= 0.20 (measured "
        f"recompute reduction)",
        f"{'PASS' if hashes >= 1.0 else 'FAIL'}: "
        f"artifact_hash_stability {hashes} (cached outputs "
        f"byte-identical to baseline)",
        f"{'PASS' if stale >= 1.0 else 'FAIL'}: "
        f"stale_state_rejection {stale} (every changed lineage "
        f"key rejected)",
        f"{'PASS' if governance >= 1.0 else 'FAIL'}: "
        f"governance_preservation {governance} (governance "
        f"fingerprint unchanged)",
        f"INFO: render_reuse_exact {render_reuse_is_exact()} "
        f"({render_counter.hits} render hits)",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay} (signature "
        f"{_signature()[:12]})",
    )
    return V291Report(
        baseline_recompute_count=baseline_recompute_count(),
        cached_recompute_count=cached_recompute_count(),
        runtime_reduction=reduction,
        artifact_hash_stability=hashes,
        stale_state_rejection=stale,
        governance_preservation=governance,
        replay_stability=replay,
        render_reuse_exact=render_reuse_is_exact(),
        halt=halt,
        recommendation=verdict,
        rationale=rationale,
    )


def build_branch_artifact() -> dict[str, object]:
    return {
        "schema_version": "v29_1_replay_cache_branch",
        "disclaimer": (
            "A real, branch-isolated replay cache: deterministic "
            "memoization with replay-bound cache keys, exact "
            "render reuse and lineage-aware invalidation. The "
            "cache turns the baseline's repeated rebuilds into "
            "one recompute per distinct workload - a measured "
            "reduction in recompute operations - while every "
            "output hash stays byte-identical, governance is "
            "untouched and stale keys are rejected. No hidden "
            "mutable state, no nondeterministic invalidation, no "
            "replay bypass, no artifact rewriting. Nothing is "
            "merged; human approval is mandatory. Replay-stable."
        ),
        "report_verdicts": list(REPORT_VERDICTS),
        "branch": "proposal/replay_cache_v1",
        "baseline_recompute_count": baseline_recompute_count(),
        "cached_recompute_count": cached_recompute_count(),
        "runtime_reduction": runtime_reduction(),
        "artifact_hash_stability": artifact_hash_stability(),
        "stale_state_rejection": stale_state_rejection(),
        "governance_preservation": governance_preservation(),
        "replay_stability": replay_stability(),
        "render_reuse_exact": render_reuse_is_exact(),
        "cached_output_hashes": dict(
            sorted(cached_output_hashes().items())),
        "signature": _signature(),
        "recommendation": build_report().recommendation,
    }


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_DRIFT",
    "VERDICT_HALT",
    "VERDICT_REAL",
    "V291Report",
    "artifact_hash_stability",
    "build_branch_artifact",
    "build_report",
    "governance_preservation",
    "replay_stability",
    "runtime_reduction",
]
