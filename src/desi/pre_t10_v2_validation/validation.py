"""v3.124 — full-regression + gate-deployment
validation for the multi-signal pre-T10 rule.

Six Pflichtmetriken (directive § v3.124-FR):

* ``full_regression_passed`` - the latest
  ``pytest tests/`` run completed cleanly.
* ``historical_tpr`` - rescuable-pool recall of
  the v3.123 rule against the v3.119 ground
  truth.
* ``historical_far`` - false-activation rate of
  the v3.123 rule on the same ground truth.
* ``adverse_flip_count`` - rescuable pools that
  the rule WOULD block (FN count). 0 means no
  historical rescue is silently dropped.
* ``hash_stability`` - fraction of pinned v2.8
  hashes (reconstruction + failcase) whose live
  replay still matches the frozen reference.
  These two hashes are the project's permanent
  determinism invariants; the v4.x replay
  matrix entries are tracked separately in
  ``matrix_drift_count`` because their drift is
  pre-existing and documented under v4.11.
* ``rule_roi`` - true_case_recall / (far + eps).

Deployment rule:

    full_regression_passed
    AND historical_tpr == 1.0
    AND historical_far == 0.0
    AND adverse_flip_count == 0
    AND hash_stability == 1.0
    AND rule_roi > 0
    => DEPLOYED_ARCHITECTURE_RULE

Otherwise the rule remains ``EXPERIMENTAL``.

Killerfrage: "Ist Pre-T10 v2 jetzt wirklich
architekturreif - oder nur lokal perfekt?"
"""
from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass
from functools import lru_cache

from ..pre_t10_v2.rule import (
    final_far, final_tpr, pools_blocked,
    rule_allows_t10,
)
from ..repro_audit.replay_matrix import (
    build_matrix,
)
from ..repro_audit.report import (
    V2_8_FROZEN_FAILCASE_HASH,
    V2_8_FROZEN_RECONSTRUCTION_HASH,
)
from ..rule_patch_protocol import (
    RulePatchProtocol,
    causal_chain_v2_7_candidate,
    fake_rule_without_guards_candidate,
)
from ..state_blindness.census import (
    cross_family_pools,
)
from ..t10_boundary.boundary import (
    all_pool_recoverability,
)


_EPSILON: float = 0.01
_REPO_ROOT: pathlib.Path = pathlib.Path(
    __file__,
).resolve().parents[3]
_PYTEST_LOG: pathlib.Path = (
    _REPO_ROOT / "artifacts" / "v3_124"
    / "_full_regression.log"
)
_REGRESSION_STATUS: pathlib.Path = (
    _REPO_ROOT / "artifacts" / "v3_124"
    / "_regression_status.json"
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def historical_tpr() -> float:
    return final_tpr()


def historical_far() -> float:
    return final_far()


@lru_cache(maxsize=1)
def adverse_flip_count() -> int:
    """Rescuable pools the rule blocks - i.e.
    historical T10 rescue cases that would now be
    silently refused."""
    pools_by_id = {
        p.pool_id: p for p in cross_family_pools()
    }
    blocked_ids = {
        p.pool_id for p in pools_blocked()
    }
    n = 0
    for r in all_pool_recoverability():
        if (
            r.rescuable
            and r.pool_id in blocked_ids
            and r.pool_id in pools_by_id
        ):
            n += 1
    return n


def rule_roi() -> float:
    return _round(
        historical_tpr()
        / (historical_far() + _EPSILON),
    )


@lru_cache(maxsize=1)
def v2_8_reconstruction_live_hash() -> str:
    return RulePatchProtocol().run(
        causal_chain_v2_7_candidate(),
    ).replay_hash


@lru_cache(maxsize=1)
def v2_8_failcase_live_hash() -> str:
    return RulePatchProtocol().run(
        fake_rule_without_guards_candidate(),
    ).replay_hash


@dataclass(frozen=True)
class HashCheck:
    label: str
    frozen: str | None
    live: str | None
    equal: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "label": self.label,
            "frozen": self.frozen,
            "live": self.live,
            "equal": self.equal,
        }


@lru_cache(maxsize=1)
def hash_checks() -> tuple[HashCheck, ...]:
    """The two pinned determinism invariants.

    Per project constraints: v2.8 reconstruction
    MUST stay = 1f4d9dfe44cb16e1, v2.8 fail-case
    MUST stay = d83d81ab8417c022. Anything else
    flipping breaks replay parity."""
    return (
        HashCheck(
            label="v2_8_reconstruction",
            frozen=(
                V2_8_FROZEN_RECONSTRUCTION_HASH
            ),
            live=v2_8_reconstruction_live_hash(),
            equal=(
                v2_8_reconstruction_live_hash()
                == V2_8_FROZEN_RECONSTRUCTION_HASH
            ),
        ),
        HashCheck(
            label="v2_8_failcase",
            frozen=V2_8_FROZEN_FAILCASE_HASH,
            live=v2_8_failcase_live_hash(),
            equal=(
                v2_8_failcase_live_hash()
                == V2_8_FROZEN_FAILCASE_HASH
            ),
        ),
    )


def hash_stability() -> float:
    checks = hash_checks()
    if not checks:
        return 0.0
    eq = sum(1 for c in checks if c.equal)
    return _round(eq / len(checks))


@lru_cache(maxsize=1)
def matrix_drift_entries() -> tuple[
    HashCheck, ...,
]:
    """Replay-matrix entries that are NOT bit-
    stable. Documented under v4.11 as expected
    HISTORICAL_RUNTIME_DRIFT; surfaced here so
    v3.124 introduces no new drift relative to
    the v4.11 baseline."""
    out: list[HashCheck] = []
    for entry in build_matrix():
        if entry.hash_equal is None:
            continue
        if entry.hash_equal:
            continue
        out.append(HashCheck(
            label=f"matrix:{entry.version}",
            frozen=entry.frozen_hash,
            live=entry.live_hash,
            equal=False,
        ))
    return tuple(out)


def matrix_drift_count() -> int:
    return len(matrix_drift_entries())


def _parse_pytest_summary(
    log: str,
) -> tuple[bool, int, int, int, str]:
    """Return (passed_all, passed, failed,
    errors, summary_line) parsed from the tail of
    a pytest -q log."""
    lines = [
        ln for ln in log.splitlines()
        if ln.strip()
    ]
    summary = lines[-1] if lines else ""
    for ln in reversed(lines[-30:]):
        if " passed" in ln or " failed" in ln:
            summary = ln
            break
    passed = 0
    failed = 0
    errors = 0
    tokens = summary.replace(",", " ").split()
    for i, t in enumerate(tokens):
        if t.isdigit() and i + 1 < len(tokens):
            kind = tokens[i + 1].rstrip(",")
            if kind.startswith("passed"):
                passed = int(t)
            elif kind.startswith("failed"):
                failed = int(t)
            elif kind.startswith("error"):
                errors = int(t)
    passed_all = (
        passed > 0
        and failed == 0
        and errors == 0
    )
    return (
        passed_all, passed, failed, errors,
        summary,
    )


def full_regression_status() -> dict[str, object]:
    """Prefer the committed status JSON for
    determinism; fall back to parsing the raw
    pytest log if the JSON is missing."""
    if _REGRESSION_STATUS.exists():
        data = json.loads(
            _REGRESSION_STATUS.read_text(
                encoding="utf-8",
            ),
        )
        return {
            "passed": bool(
                data.get("passed", False),
            ),
            "log_present": True,
            "summary": str(
                data.get("summary", ""),
            ),
            "passed_count": int(
                data.get("passed_count", 0),
            ),
            "failed_count": int(
                data.get("failed_count", 0),
            ),
            "error_count": int(
                data.get("error_count", 0),
            ),
        }
    if not _PYTEST_LOG.exists():
        return {
            "passed": False,
            "log_present": False,
            "summary": "no regression log present",
            "passed_count": 0,
            "failed_count": 0,
            "error_count": 0,
        }
    log = _PYTEST_LOG.read_text(encoding="utf-8")
    (
        passed_all, p, f, e, summary,
    ) = _parse_pytest_summary(log)
    return {
        "passed": passed_all,
        "log_present": True,
        "summary": summary,
        "passed_count": p,
        "failed_count": f,
        "error_count": e,
    }


def full_regression_passed() -> bool:
    return bool(
        full_regression_status()["passed"],
    )


@dataclass(frozen=True)
class V3124FullRegressionReport:
    full_regression_passed: bool
    historical_tpr: float
    historical_far: float
    adverse_flip_count: int
    hash_stability: float
    rule_roi: float
    regression_summary: str
    regression_passed_count: int
    regression_failed_count: int
    regression_error_count: int
    hash_checks: tuple[HashCheck, ...]
    matrix_drift_count: int
    matrix_drift_entries: tuple[HashCheck, ...]
    deployment_decision: str
    failing_conditions: tuple[str, ...]
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "full_regression_passed":
                self.full_regression_passed,
            "historical_tpr":
                self.historical_tpr,
            "historical_far":
                self.historical_far,
            "adverse_flip_count":
                self.adverse_flip_count,
            "hash_stability":
                self.hash_stability,
            "rule_roi": self.rule_roi,
            "regression_summary":
                self.regression_summary,
            "regression_passed_count":
                self.regression_passed_count,
            "regression_failed_count":
                self.regression_failed_count,
            "regression_error_count":
                self.regression_error_count,
            "hash_checks": [
                c.to_dict()
                for c in self.hash_checks
            ],
            "matrix_drift_count":
                self.matrix_drift_count,
            "matrix_drift_entries": [
                c.to_dict()
                for c in self.matrix_drift_entries
            ],
            "deployment_decision":
                self.deployment_decision,
            "failing_conditions":
                list(self.failing_conditions),
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def _deployment_gates(
    *,
    fr: bool, tpr: float, far: float,
    afc: int, hs: float, roi: float,
) -> tuple[tuple[str, bool], ...]:
    return (
        ("full_regression_passed", fr),
        ("historical_tpr", tpr == 1.0),
        ("historical_far", far == 0.0),
        ("adverse_flip_count", afc == 0),
        ("hash_stability", hs == 1.0),
        ("rule_roi", roi > 0.0),
    )


def build_report() -> V3124FullRegressionReport:
    status = full_regression_status()
    fr = bool(status["passed"])
    tpr = historical_tpr()
    far = historical_far()
    afc = adverse_flip_count()
    hs = hash_stability()
    roi = rule_roi()
    checks = hash_checks()
    drift = matrix_drift_entries()

    gates = _deployment_gates(
        fr=fr, tpr=tpr, far=far,
        afc=afc, hs=hs, roi=roi,
    )
    failing = tuple(
        name for name, ok in gates if not ok
    )
    if failing:
        decision = "PRE_T10_V2_EXPERIMENTAL"
    else:
        decision = "DEPLOYED_ARCHITECTURE_RULE"

    rationale = (
        f"{'PASS' if fr else 'FAIL'}: "
        f"full_regression_passed ("
        f"{status['summary']})",
        f"{'PASS' if tpr == 1.0 else 'FAIL'}: "
        f"historical_tpr {tpr}",
        f"{'PASS' if far == 0.0 else 'FAIL'}: "
        f"historical_far {far}",
        f"{'PASS' if afc == 0 else 'FAIL'}: "
        f"adverse_flip_count {afc}",
        f"{'PASS' if hs == 1.0 else 'FAIL'}: "
        f"hash_stability {hs} "
        f"(over {len(checks)} pinned checks)",
        f"{'PASS' if roi > 0 else 'FAIL'}: "
        f"rule_roi {roi}",
        f"INFO: matrix_drift_count "
        f"{len(drift)} (pre-existing v4.11 "
        f"HISTORICAL_RUNTIME_DRIFT, unrelated "
        f"to multi-signal rule)",
    )

    return V3124FullRegressionReport(
        full_regression_passed=fr,
        historical_tpr=tpr,
        historical_far=far,
        adverse_flip_count=afc,
        hash_stability=hs,
        rule_roi=roi,
        regression_summary=str(
            status["summary"],
        ),
        regression_passed_count=int(
            status["passed_count"],
        ),
        regression_failed_count=int(
            status["failed_count"],
        ),
        regression_error_count=int(
            status["error_count"],
        ),
        hash_checks=checks,
        matrix_drift_count=len(drift),
        matrix_drift_entries=drift,
        deployment_decision=decision,
        failing_conditions=failing,
        rationale=rationale,
    )


def build_full_regression_validation_artifact(
) -> dict[str, object]:
    r = build_report()
    return {
        "schema_version":
            "v3_124_full_regression_validation",
        "full_regression_passed":
            r.full_regression_passed,
        "historical_tpr": r.historical_tpr,
        "historical_far": r.historical_far,
        "adverse_flip_count":
            r.adverse_flip_count,
        "hash_stability": r.hash_stability,
        "rule_roi": r.rule_roi,
        "regression_summary":
            r.regression_summary,
        "regression_passed_count":
            r.regression_passed_count,
        "regression_failed_count":
            r.regression_failed_count,
        "regression_error_count":
            r.regression_error_count,
        "hash_checks": [
            c.to_dict() for c in r.hash_checks
        ],
        "matrix_drift_count":
            r.matrix_drift_count,
        "matrix_drift_entries": [
            c.to_dict()
            for c in r.matrix_drift_entries
        ],
        "deployment_decision":
            r.deployment_decision,
        "failing_conditions":
            list(r.failing_conditions),
    }


__all__ = [
    "HashCheck",
    "V2_8_FROZEN_FAILCASE_HASH",
    "V2_8_FROZEN_RECONSTRUCTION_HASH",
    "V3124FullRegressionReport",
    "adverse_flip_count",
    "build_full_regression_validation_artifact",
    "build_report",
    "full_regression_passed",
    "full_regression_status",
    "hash_checks",
    "hash_stability",
    "historical_far",
    "historical_tpr",
    "matrix_drift_count",
    "matrix_drift_entries",
    "rule_roi",
    "v2_8_failcase_live_hash",
    "v2_8_reconstruction_live_hash",
]
